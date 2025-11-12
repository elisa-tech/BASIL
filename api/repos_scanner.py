import fnmatch
import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional, Callable

logger = logging.getLogger(__name__)
# Ensure logger prints to the terminal by default (once)
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setLevel(logging.INFO)
    _console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_console_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class RepoScanner:
    """
    Utilities to clone a Git repository into a per-user temporary folder,
    checkout a target branch, strip the VCS metadata (.git), and inspect files.
    """

    files = []
    user_id = None

    def __init__(self, user_id: str) -> None:
        """
        Initialize the scanner.

        If base_temp_dir is not provided, a directory under the system temp
        directory will be used: <tmp>/basil/repos
        """
        default_root = Path(tempfile.gettempdir()) / "basil" / "repos" / user_id
        self.base_temp_dir = default_root
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        self.user_id = user_id

    def __del__(self) -> None:
        """
        Delete the scanner.
        """
        self.clear_user_temp()

    def clone_to_user_temp(self, repo_url: str, branch: str) -> str:
        """
        Clone the repository at repo_url into the user's temporary folder and
        checkout the given branch. After cloning, remove the .git folder.

        Returns the absolute path to the cloned working directory.
        """
        user_root = self._get_user_root()
        user_root.mkdir(parents=True, exist_ok=True)

        target_dir = user_root / self._generate_repo_dir_name(repo_url, branch)
        if target_dir.exists():
            # Avoid accidental reuse; create a unique directory instead
            target_dir = user_root / f"{target_dir.name}-{uuid.uuid4().hex[:8]}"

        # Perform a shallow clone of the target branch into target_dir
        self._git_clone(repo_url=repo_url, branch=branch, target_dir=target_dir)

        self.git_version = self._git_version(target_dir=target_dir)

        # Remove the .git directory to leave a clean working copy
        self._remove_git_dir(target_dir)

        logger.info(f"Cloned repository {repo_url} to {target_dir}")
        return str(target_dir)

    def clear_user_temp(self) -> None:
        """Remove the entire temporary folder for the given user."""
        user_root = self._get_user_root()
        if user_root.exists():
            shutil.rmtree(user_root)

    def list_all_files(self, root_dir: str, include_hidden: bool = False) -> List[str]:
        """
        Return a list of all file paths (relative to root_dir) contained within root_dir.
        Directories are not included.
        """
        root_path = Path(root_dir).resolve()
        files: List[str] = []
        for path in root_path.rglob("*"):
            if path.is_file():
                rel = path.relative_to(root_path)
                if not include_hidden and any(part.startswith(".") for part in rel.parts):
                    continue
                files.append(str(rel))
        files.sort()
        self.files = files
        return files

    def list_files(
        self, root_dir: str, include_hidden: bool = False, filename_pattern: str = "", folder_pattern: str = ""
    ) -> List[str]:
        """
        List all files in the given root directory.
        """
        if not self.files:
            files = self.list_all_files(root_dir, include_hidden)
        else:
            files = self.files
        if filename_pattern:
            files = [f for f in files if fnmatch.fnmatch(os.path.basename(f), filename_pattern)]
        if folder_pattern:
            # If pattern has glob chars, match against the directory path; else treat as substring
            has_glob = any(ch in folder_pattern for ch in ["*", "?", "[", "]"])
            if has_glob:
                files = [f for f in files if fnmatch.fnmatch(os.path.dirname(f), folder_pattern)]
            else:
                files = [f for f in files if folder_pattern in os.path.dirname(f)]
        return files

    # Internal helpers

    def _get_user_root(self) -> Path:
        safe_user_id = self._sanitize(self.user_id)
        return self.base_temp_dir / safe_user_id

    def _generate_repo_dir_name(self, repo_url: str, branch: str) -> str:
        repo_name = self._derive_repo_name(repo_url)
        safe_branch = self._sanitize(branch)
        return f"{repo_name}-{safe_branch}-{uuid.uuid4().hex[:6]}"

    @staticmethod
    def _derive_repo_name(repo_url: str) -> str:
        """
        Best-effort extraction of a repository name from a URL or local path.
        """
        tail = repo_url.rstrip("/").split("/")[-1]
        if tail.endswith(".git"):
            tail = tail[:-4]
        return RepoScanner._sanitize(tail) or "repo"

    @staticmethod
    def _sanitize(value: str) -> str:
        """
        Sanitize a string to be safe for use as a directory name.
        """
        safe = "".join(ch if ch.isalnum() or ch in "-._" else "-" for ch in value.strip())
        return safe.strip("-._") or "value"

    @staticmethod
    def _git_clone(repo_url: str, branch: str, target_dir: Path) -> None:
        """
        Run 'git clone' to clone a single branch shallowly into target_dir.
        """
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            branch,
            "--single-branch",
            repo_url,
            str(target_dir),
        ]
        RepoScanner._run(cmd, cwd=None)

    @staticmethod
    def _git_version(target_dir: str) -> str:
        """
        Get the version of the repository at the given branch.
        """
        cmd = ["git", "describe", "--tags", "--always", "--long", "--dirty"]
        return RepoScanner._run(cmd, cwd=target_dir)

    @staticmethod
    def _remove_git_dir(target_dir: Path) -> None:
        """
        Remove the .git directory if it exists inside target_dir.
        """
        git_dir = target_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

    @staticmethod
    def _safe_join(root_dir: str, relative_path: str) -> str:
        """
        Safely join root_dir and relative_path ensuring the result stays under root_dir.
        """
        root = Path(root_dir).resolve()
        joined = (root / relative_path).resolve()
        # Ensure the resolved path is within the root directory
        try:
            joined.relative_to(root)
        except ValueError:
            raise FileNotFoundError("Requested file is outside the allowed directory")
        if not joined.exists() or not joined.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return str(joined)

    @staticmethod
    def _run(cmd: List[str], cwd: Optional[os.PathLike] = None) -> str:
        """
        Run a subprocess and return stdout. Raise a descriptive error if it fails.
        """
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return (completed.stdout or "").strip()
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}\n"
                f"stdout:\n{exc.stdout}\n"
                f"stderr:\n{exc.stderr}"
            ) from exc

    def _skip_items(self, elements: List[dict], skip_top_items: int = 0, skip_bottom_items: int = 0) -> List[dict]:
        """
        Skip top and bottom items from the list of elements.
        Remove duplicates from the list of elements.
        """
        # sort elements by index
        elements.sort(key=lambda x: x.get("index", 0))

        # skip top items
        if skip_top_items > 0:
            elements = elements[skip_top_items:]

        # skip bottom items
        if skip_bottom_items > 0:
            elements = elements[:-skip_bottom_items]

        # remove duplicates keeping the order
        seen = set()
        unique_elements = []
        for d in elements:
            t = tuple(sorted(d.items()))
            if t not in seen:
                seen.add(t)
                unique_elements.append(d)

        return unique_elements

    # ---------- Generic text scanning utilities (to reduce duplication) ----------

    @staticmethod
    def _make_line_checker(
        match_type: str, match_string: str, strip: bool, case_sensitive: bool
    ) -> Callable[[str], bool]:
        """
        Build a predicate that checks a single line against the given condition.
        match_type: one of ["startswith", "endswith", "contains", "not_contains", "equal", "regex"]
        """
        if not case_sensitive:
            match_string_cmp = match_string.lower()
        else:
            match_string_cmp = match_string

        def normalize(line: str) -> str:
            value = line.strip() if strip else line
            return value if case_sensitive else value.lower()

        if match_type == "startswith":
            return lambda line: normalize(line).startswith(match_string_cmp)
        if match_type == "endswith":
            return lambda line: normalize(line).endswith(match_string_cmp)
        if match_type == "contains":
            return lambda line: match_string_cmp in normalize(line)
        if match_type == "not_contains":
            return lambda line: match_string_cmp not in normalize(line)
        if match_type == "equal":
            return lambda line: normalize(line) == match_string_cmp
        if match_type == "regex":
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(match_string, flags)
            except re.error as exc:
                raise ValueError(f"Invalid regular expression: {match_string}") from exc
            return lambda line: pattern.search(line.strip() if strip else line) is not None
        raise ValueError(f"Unsupported match_type: {match_type}")

    @staticmethod
    def _collect_matches_for_lines(
        lines: List[str],
        initial_index: int,
        check_line: Callable[[str], bool],
        output_mode: str,
    ) -> List[dict]:
        """
        Scan provided lines with check_line and build elements.
        output_mode:
          - "from": element text starts from the matching index
          - "to":   element text is from top up to the matching index (excluded)
        """
        results: List[dict] = []
        for idx, line in enumerate(lines):
            if check_line(line):
                if output_mode == "from":
                    results.append(
                        {
                            "index": initial_index + idx,
                            "text": "\n".join(lines[idx:]),
                        }
                    )
                elif output_mode == "to":
                    results.append(
                        {
                            "index": initial_index,
                            "text": "\n".join(lines[:idx]),
                        }
                    )
                else:
                    raise ValueError(f"Unsupported output_mode: {output_mode}")
        return results

    def _scan_text_by_elements(
        self,
        text: str,
        elements: List[dict],
        match_type: str,
        match_string: str,
        strip: bool,
        case_sensitive: bool,
        output_mode: str,
        skip_top_items: int,
        skip_bottom_items: int,
    ) -> dict:
        """
        Generic scanner to reduce duplication across start__/end__/... helpers.
        """
        results = {
            "text": text,
            "elements": [],
        }
        if not text:
            return results

        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type=match_type,
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
        )

        # If elements are not provided, scan the whole text
        if not elements:
            results["elements"] = self._collect_matches_for_lines(
                lines=lines,
                initial_index=0,
                check_line=check_line,
                output_mode=output_mode,
            )
            return results

        # If elements are provided, scan each element["text"] with initial index element["index"]
        aggregated: List[dict] = []
        for el in elements:
            el_lines = el.get("text", "").splitlines()
            initial_index = el.get("index", 0)
            aggregated.extend(
                self._collect_matches_for_lines(
                    lines=el_lines,
                    initial_index=initial_index,
                    check_line=check_line,
                    output_mode=output_mode,
                )
            )
        results["elements"] = self._skip_items(
            elements=aggregated, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items
        )
        return results

    def start__lines_starting_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections starting at specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a dictionary with:
          - original text
          - list of dictionaries with:
            + index of starting line
            + text: portion of text starting from the identified line
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="startswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__lines_starting_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections starting at specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a dictionary with:
          - original text
          - list of dictionaries with:
            + index of starting line
            + text: portion of text starting from top to the identified line
        """

        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="startswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="to",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def closest__lines_starting_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections starting at specific lines and extend elements to provide a new text
        starting from the identified line that is the one matching the condition with the closest index.
        - Extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a dictionary with:
          - original text
          - list of dictionaries with:
            + index of starting line
            + text: portion of text starting from top to the identified line
        """

        def text_to_elements(
            lines: List[str], match_string: str = "", strip: bool = False, case_sensitive: bool = False
        ) -> List[dict]:
            check_line = self._make_line_checker(
                match_type="startswith",
                match_string=match_string,
                strip=strip,
                case_sensitive=case_sensitive,
            )
            return self._collect_matches_for_lines(
                lines=lines,
                initial_index=0,
                check_line=check_line,
                output_mode="from",
            )

        results = {
            "text": text,
            "elements": [],
        }

        lines = text.splitlines()

        # No elements provided: use every non-empty line as a starting point
        closest_elements = text_to_elements(
            lines=lines, match_string=match_string, strip=strip, case_sensitive=case_sensitive
        )

        # Elements provided: match lines that start with any element["text"]
        for el in elements:
            el_index = el.get("index", 0)
            new_element_closest_index = None
            new_element_closest_text = None
            for idx, closest_el in enumerate(closest_elements):
                closest_el_index = closest_el.get("index", 0)
                closest_el_text = closest_el.get("text", "")
                if new_element_closest_index is None or (
                    abs(closest_el_index - el_index) < abs(new_element_closest_index - el_index)
                ):
                    new_element_closest_index = closest_el_index
                    new_element_closest_text = closest_el_text

            if new_element_closest_index is not None:
                results["elements"].append({"index": new_element_closest_index, "text": new_element_closest_text})

        results["elements"] = self._skip_items(
            elements=results["elements"], skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items
        )
        return results

    def start__lines_ending_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections ending with specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a dictionary with:
          - original text
          - list of dictionaries with:
            + index of ending line
            + text: portion of text ending with the identified line
        """

        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="endswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def start__lines_containing(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections containing specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a dictionary with:
          - original text
          - list of dictionaries with:
            + index of starting line
            + text: portion of text starting from the identified line
        """

        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="contains",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def start__lines_not_containing(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections not containing specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a dictionary with:
          - original text
          - list of dictionaries with:
            + index of not containing line
            + text: portion of text not containing the identified line
        """

        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="not_contains",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def start__lines_equal(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections equal to specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a dictionary with:
          - original text
          - list of dictionaries with:
            + index of equal line
            + text: portion of text equal to the identified line
        """

        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="equal",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def start__lines_regex(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections where a line matches the given regular expression and start from that line.
        Returns structure with 'text' and list of elements {index, text}.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="regex",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__lines_regex(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections where a line matches the given regular expression and end at that line.
        Returns structure with 'text' and list of elements {index, text}.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="regex",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            output_mode="to",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def closest__lines_regex(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> dict:
        """
        Analyze text for sections where a line matches the given regular expression and extend elements
        to provide a new text starting from the closest matching line index.
        Returns structure with 'text' and list of elements {index, text}.
        """
        results = {
            "text": text,
            "elements": [],
        }

        if not text or not elements:
            return results

        lines = text.splitlines()

        # Build candidate matches from entire text using regex
        check_line = self._make_line_checker(
            match_type="regex",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
        )
        closest_elements = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )

        # For each provided element, pick the candidate with closest index
        for el in elements:
            el_index = el.get("index", 0)
            new_element_closest_index = None
            new_element_closest_text = None
            for closest_el in closest_elements:
                closest_el_index = closest_el.get("index", 0)
                closest_el_text = closest_el.get("text", "")
                if new_element_closest_index is None or (
                    abs(closest_el_index - el_index) < abs(new_element_closest_index - el_index)
                ):
                    new_element_closest_index = closest_el_index
                    new_element_closest_text = closest_el_text

            if new_element_closest_index is not None:
                results["elements"].append({"index": new_element_closest_index, "text": new_element_closest_text})

        results["elements"] = self._skip_items(
            elements=results["elements"], skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items
        )
        return results

    def _remove_empty_lines(self, elements: List[dict]) -> List[dict]:
        """
        Remove empty lines from the list of elements.
        Returns a list of dictionaries with:
          - index of line from text
          - text: portion of text equal to the identified line
        """

        for el in elements:
            lines = el.get("text", "").splitlines()
            tmp = "\n".join([line for line in lines if line.strip()])
            el["text"] = tmp

        return elements

    def _extend_content_of_elements(self, direction: str, count: int, text: str, elements: List[dict]) -> List[dict]:
        """
        Extend elements in the list of elements.
        - direction: "up" or "down"
        - count: number of lines to extend the content of each element
        - text: original text to extract the new element content
        - elements: list of dictionaries with:
          - index of line from text
          - text: portion of text equal to the identified line
        """
        results = []

        text_lines = text.splitlines()

        if direction not in ["up", "down"]:
            raise ValueError(f"Invalid direction: {direction}")

        for el in elements:
            index = el.get("index", 0)
            element_lines = el.get("text", "").splitlines()
            element_lines_count = len(element_lines)

            if direction == "up":
                start_index = min(max(0, index - count), len(text_lines))
                end_index = index + element_lines_count
            else:
                start_index = index
                end_index = min(max(0, index + count), len(text_lines))

            el["index"] = start_index
            el["text"] = "\n".join(text_lines[start_index:end_index])
            results.append(el)
        return results

    def _extract_split_from_elements(self, text: str, elements: List[dict], delimiter: str, index: int) -> List[dict]:
        """
        Extract a split from the list of elements.
        - elements: list of dictionaries with:
          - index of line from original text
          - text: portion of originaltext
        - delimiter: delimiter to split the elementtext
        - index: index of the occourence of the split we want to extract
        Returns a list of dictionaries with:
          - index of the split from original text
          - text: portion of text extracted with the split
        """

        if not delimiter:
            raise ValueError("Delimiter is not valid")

        if index < 0:
            raise ValueError("Index is not valid")

        ret = {"text": "text", "elements": []}

        for el in elements:
            element_index = el.get("index", 0)
            element_text = el.get("text", "")
            split_elements = element_text.split(delimiter)
            tmp = {"index": 0, "text": ""}
            if split_elements:
                if index < len(split_elements):
                    tmp["text"] = split_elements[index]
                    # Calculate the index of the split in the original text
                    # consider the len of the text to the line number index from the input element
                    # add to it the len of the text before the split occurrence
                    tmp["index"] = len("\n".join(text.splitlines()[:element_index]))
                    if index > 0:
                        tmp["index"] += len(delimiter.join(split_elements[:index]))
                    ret["elements"].append(tmp)

        return ret


class FilesScanner:

    def __init__(self, files: List[str] = [], repo_folder: str = ""):
        self.files = files
        self.repo_folder = repo_folder

    def filter_files_by_content(
        self, files: List[str] = [], contains: List[str] = [], not_contains: List[str] = []
    ) -> List[str]:
        """
        Filter the files list to only include files that contain all of the given match strings.
        contains list is used in OR condition
        not_contains list is used in OR condition
        """
        ret = []

        if not files:
            files = self.files

        for curr_file in self.files:
            curr_file_content = self.get_file_content(filepath=os.path.join(self.repo_folder, curr_file))
            if contains:
                for curr_str_match in contains:
                    if curr_str_match in curr_file_content:
                        ret.append(curr_file)
                        break
            if not_contains and curr_file in ret:
                for curr_str_match in not_contains:
                    if curr_str_match in curr_file_content:
                        ret.pop(curr_file)
                        break
        return ret

    def get_file_content(self, filepath: str, encoding: str = "utf-8") -> str:
        """
        Read and return the text content
        Raises FileNotFoundError if the file does not exist.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, "r", encoding=encoding) as f:
            return f.read()


class ArtifactsScanner:

    api = None
    scan_config = {}
    user_id = None

    def __init__(self, user_id: str, api: Optional[dict] = {}, scan_config: Optional[dict] = {}) -> None:
        self.api = api
        self.scan_config = scan_config
        self.user_id = user_id

    def scan(self) -> str:

        api = []
        if not self.scan_config.get("api", None):
            return ValueError("Scan configuration do not have `api` key")

        apis_config = self.scan_config.get("api", [])

        for curr_api_config in apis_config:
            if not curr_api_config.get("repo", None):
                return ValueError("Scan configuration error: `api` do not have `repo` key")

            if not curr_api_config.get("ref", None):
                return ValueError("Scan configuration error: `api` do not have `ref` key")

            for idx, curr_api in enumerate(curr_api_config.get("name", [])):
                curr_api_config["api"] = curr_api
                api_reference_documents = self.search__api_reference_document(api_config=curr_api_config)
                if api_reference_documents:
                    api_reference_document = api_reference_documents[0]
                    api.append(
                        {
                            "api": curr_api,
                            "library": curr_api_config.get("library", ""),
                            "library_version": curr_api_config.get("library_version", "").replace(
                                "__ref__", curr_api_config.get("ref", "")
                            ),
                            "api_reference_document": api_reference_document,
                        }
                    )

        logger.info(f"Api: {api}")

    def search__api_reference_document(self, api_config: dict) -> List[str]:
        """
        Using the scan_config, search the API reference document for the given api
        """

        repo_scanner = RepoScanner(user_id=self.user_id)
        repo_scanner.clone_to_user_temp(repo_url=api_config.get("repo"), branch=api_config.get("ref"))

        filename_pattern = api_config.get("filename_pattern", "")
        filename_pattern = filename_pattern.replace("__api__", api_config.get("api", ""))
        folder_pattern = api_config.get("folder_pattern", "")
        folder_pattern = folder_pattern.replace("__api__", api_config.get("api", ""))

        files = repo_scanner.list_files(
            root_dir=repo_scanner.base_temp_dir,
            include_hidden=api_config.get("hidden", False),
            filename_pattern=filename_pattern,
            folder_pattern=folder_pattern,
        )

        file_scanner = FilesScanner(files=files, repo_folder=repo_scanner.base_temp_dir)
        logger.info(f"files: {len(files)}")

        filter_file_by_content_contains = api_config.get("contains", [])
        filter_file_by_content_not_contains = api_config.get("not_contains", [])
        filtered_files = file_scanner.filter_files_by_content(
            files=files, contains=filter_file_by_content_contains, not_contains=filter_file_by_content_not_contains
        )

        if filtered_files:
            logger.info(f"Found {len(filtered_files)} files matching the criteria")
        return filtered_files


if __name__ == "__main__":
    scanner = ArtifactsScanner(
        user_id="test",
        api="test",
        scan_config={
            "api": [
                {
                    "name": ["api1", "api2"],
                    "library": "library name",
                    "library_version": "__ref__",
                    "repo": "https://github.com/elisa-tech/BASIL.git",
                    "ref": "main",
                    "filename_pattern": "*.py",
                    "folder_pattern": "*examples*",
                    "hidden": False,
                    "contains": ["api_get_sw_components("],
                    "not_contains": [],
                    "snippets": [
                        {
                            "name": "api_get_sw_components",
                            "start": {
                                "line_contains": [],
                                "closest": {""},
                            },
                            "end": {
                                "line_not_contains": ["#"],
                            },
                        }
                    ],
                }
            ],
        },
    )
    scanner.scan()
