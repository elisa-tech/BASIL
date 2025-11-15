import argparse
import datetime
import fnmatch
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Callable, List, Optional

import yaml

currentdir = Path(__file__).resolve().parent
sys.path.insert(1, str(currentdir.parent))

from db.db_orm import DbInterface  # noqa E402
from db.models.api import ApiModel  # noqa E402
from db.models.api_document import ApiDocumentModel  # noqa E402
from db.models.api_justification import ApiJustificationModel  # noqa E402
from db.models.api_sw_requirement import ApiSwRequirementModel  # noqa E402
from db.models.api_test_case import ApiTestCaseModel  # noqa E402
from db.models.api_test_specification import ApiTestSpecificationModel  # noqa E402
from db.models.document import DocumentModel  # noqa E402
from db.models.document_document import DocumentDocumentModel  # noqa E402
from db.models.justification import JustificationModel  # noqa E402
from db.models.sw_requirement import SwRequirementModel  # noqa E402
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel  # noqa E402
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel  # noqa E402
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel  # noqa E402
from db.models.test_case import TestCaseModel  # noqa E402
from db.models.test_specification import TestSpecificationModel  # noqa E402
from db.models.test_specification_test_case import TestSpecificationTestCaseModel  # noqa E402
from db.models.user import UserModel  # noqa E402

from api import USER_FILES_BASE_DIR  # noqa E402

logger = logging.getLogger(__name__)
# Ensure logger prints to the terminal by default (once)
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setLevel(logging.INFO)
    _console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_console_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class TraceabilityGenerator:
    """
    Generate traceability from the scan results.
    """

    def __init__(self, traceability: dict, user_id: int, logfile: str) -> None:
        self.traceability = traceability
        self.user_id = user_id
        self.dbi = DbInterface()
        self.logfile = logfile

        # search user
        self.user = self.dbi.session.query(UserModel).filter(UserModel.id == self.user_id).first()
        if not self.user:
            raise ValueError(f"User with id {self.user_id} not found")

    def generate_api_justifications(self, api_model, snippet: dict, justifications: List[dict]):
        # ApiJustifications
        api_justifications = []
        for justification in snippet["justifications"]:
            new_justification = self._get_or_create_justification(justification_dict=justification)

            new_api_justification = ApiJustificationModel(
                api=api_model,
                justification=new_justification,
                section=snippet["section"],
                offset=snippet["offset"],
                coverage=justification["coverage"],
                created_by=self.user,
            )
            api_justifications.append(new_api_justification)

        self.dbi.session.add_all(api_justifications)
        self.dbi.session.commit()
        return api_justifications

    def _get_or_create_justification(self, justification_dict: dict) -> JustificationModel:
        existing = (
            self.dbi.session.query(JustificationModel)
            .filter(JustificationModel.description == justification_dict.get("description", ""))
            .all()
        )
        if existing:
            return existing[0]
        new_justification = JustificationModel(
            description=justification_dict.get("description", ""), created_by=self.user
        )
        self.dbi.session.add(new_justification)
        self.dbi.session.commit()
        return new_justification

    def generate_api_documents(self, api_model, snippet: dict, documents: List[dict]):
        # ApiDocuments
        api_documents = []
        for document in documents:
            new_document = self._get_or_create_document(doc_dict=document)

            new_api_document = ApiDocumentModel(
                api=api_model,
                document=new_document,
                section=snippet["section"],
                offset=snippet["offset"],
                coverage=document["coverage"],
                created_by=self.user,
            )
            api_documents.append(new_api_document)
            self.dbi.session.add(new_api_document)
            self.dbi.session.commit()

            # Recursively create DocumentDocumentModel links for nested documents
            children = document.get("documents", []) or []
            if not children:
                continue
            parent_mapping_api = new_api_document
            self._generate_nested_documents(
                parent_mapping_api=parent_mapping_api,
                parent_mapping_document=None,
                children_documents=children,
                snippet=snippet,
            )

        self.dbi.session.add_all(api_documents)
        self.dbi.session.commit()

        return api_documents

    def _get_or_create_document(self, doc_dict: dict) -> DocumentModel:
        existing = (
            self.dbi.session.query(DocumentModel)
            .filter(DocumentModel.title == doc_dict.get("title", ""))
            .filter(DocumentModel.description == doc_dict.get("description", ""))
            .filter(DocumentModel.document_type == doc_dict.get("document_type", ""))
            .filter(DocumentModel.spdx_relation == doc_dict.get("spdx_relation", ""))
            .filter(DocumentModel.url == doc_dict.get("url", ""))
            .all()
        )
        if existing:
            return existing[0]
        new_doc = DocumentModel(
            title=doc_dict.get("title", ""),
            description=doc_dict.get("description", ""),
            document_type=doc_dict.get("document_type", ""),
            spdx_relation=doc_dict.get("spdx_relation", ""),
            url=doc_dict.get("url", ""),
            section="",
            offset=-1,
            valid=0,
            created_by=self.user,
        )
        self.dbi.session.add(new_doc)
        self.dbi.session.commit()
        return new_doc

    def _generate_nested_documents(
        self,
        parent_mapping_api: Optional[ApiDocumentModel],
        parent_mapping_document: Optional[DocumentDocumentModel],
        children_documents: List[dict],
        snippet: dict,
    ) -> List[DocumentDocumentModel]:
        """
        Recursively create DocumentDocumentModel mappings for nested documents.
        The parent can be either an ApiDocumentModel (top-level) or another DocumentDocumentModel.
        """
        logger.info(f" - Generating nested documents for {len(children_documents)} children")
        created_links: List[DocumentDocumentModel] = []
        for child in children_documents:
            mapped_child_doc = self._get_or_create_document(child)
            link = DocumentDocumentModel(
                document_mapping_document=parent_mapping_document,
                document_mapping_api=parent_mapping_api,
                document=mapped_child_doc,
                section=snippet["section"],
                offset=snippet["offset"],
                coverage=child.get("coverage", 0),
                created_by=self.user,
            )
            self.dbi.session.add(link)
            self.dbi.session.commit()
            created_links.append(link)
            # Recurse into grandchildren
            grand_children = child.get("documents", []) or []
            if grand_children:
                self._generate_nested_documents(
                    parent_mapping_api=None,
                    parent_mapping_document=link,
                    children_documents=grand_children,
                    snippet=snippet,
                )
        return created_links

    def generate_api_software_requirements(self, api_model, snippet: dict, software_requirements: List[dict]):
        # ApiSoftwareRequirements
        api_software_requirements = []
        for software_requirement in software_requirements:
            new_software_requirement = self._get_or_create_software_requirement(
                software_requirement_dict=software_requirement
            )
            new_api_software_requirement = ApiSwRequirementModel(
                api=api_model,
                sw_requirement=new_software_requirement,
                section=snippet["section"],
                offset=snippet["offset"],
                coverage=software_requirement["coverage"],
                created_by=self.user,
            )
            api_software_requirements.append(new_api_software_requirement)
            self.dbi.session.add(new_api_software_requirement)
            self.dbi.session.commit()

            # Map test specifications directly under this software requirement
            test_specifications = software_requirement.get("test_specifications", []) or []
            if test_specifications:
                logger.info(f" - Generating {len(test_specifications)} test specifications")
            for ts in test_specifications:
                ts_model = self._get_or_create_test_specification(test_specification_dict=ts)
                ts_link = SwRequirementTestSpecificationModel(
                    sw_requirement_mapping_api=new_api_software_requirement,
                    sw_requirement_mapping_sw_requirement=None,
                    test_specification=ts_model,
                    coverage=ts.get("coverage", 0),
                    created_by=self.user,
                )
                self.dbi.session.add(ts_link)
                self.dbi.session.commit()

            # Map test cases directly under this software requirement
            test_cases = software_requirement.get("test_cases", []) or []
            if test_cases:
                logger.info(f" - Generating {len(test_cases)} test cases")
            for tc in test_cases:
                tc_model = self._get_or_create_test_case(test_case_dict=tc)
                tc_link = SwRequirementTestCaseModel(
                    sw_requirement_mapping_api=new_api_software_requirement,
                    sw_requirement_mapping_sw_requirement=None,
                    test_case=tc_model,
                    coverage=tc.get("coverage", 0),
                    created_by=self.user,
                )
                self.dbi.session.add(tc_link)
                self.dbi.session.commit()

            # Recursively create SwRequirementSwRequirementModel links for nested software requirements
            children = software_requirement.get("software_requirements", []) or []
            if not children:
                continue
            parent_mapping_api = new_api_software_requirement
            self._generate_nested_sw_requirements(
                parent_mapping_api=parent_mapping_api,
                parent_mapping_sw_requirement=None,
                children_sw_requirements=children,
            )
        return api_software_requirements

    def _get_or_create_software_requirement(self, software_requirement_dict: dict) -> SwRequirementModel:
        existing = (
            self.dbi.session.query(SwRequirementModel)
            .filter(SwRequirementModel.title == software_requirement_dict.get("title", ""))
            .filter(SwRequirementModel.description == software_requirement_dict.get("description", ""))
            .all()
        )
        if existing:
            return existing[0]
        new_software_requirement = SwRequirementModel(
            title=software_requirement_dict.get("title", ""),
            description=software_requirement_dict.get("description", ""),
            created_by=self.user,
        )
        self.dbi.session.add(new_software_requirement)
        self.dbi.session.commit()
        return new_software_requirement

    def _generate_nested_sw_requirements(
        self,
        parent_mapping_api: Optional[ApiSwRequirementModel],
        parent_mapping_sw_requirement: Optional[SwRequirementSwRequirementModel],
        children_sw_requirements: List[dict],
    ) -> List[SwRequirementSwRequirementModel]:
        """
        Recursively create SwRequirementSwRequirementModel mappings for nested software requirements.
        The parent can be either an ApiSwRequirementModel (top-level) or another SwRequirementSwRequirementModel.
        """
        logger.info(f" - Generating nested software requirements for {len(children_sw_requirements)} children")
        created_links: List[SwRequirementSwRequirementModel] = []
        for child in children_sw_requirements:
            mapped_child_sw = self._get_or_create_software_requirement(software_requirement_dict=child)
            link = SwRequirementSwRequirementModel(
                sw_requirement_mapping_api=parent_mapping_api,
                sw_requirement_mapping_sw_requirement=parent_mapping_sw_requirement,
                sw_requirement=mapped_child_sw,
                coverage=child.get("coverage", 0),
                created_by=self.user,
            )
            self.dbi.session.add(link)
            self.dbi.session.commit()
            created_links.append(link)

            # Map test specifications under this nested software requirement link
            test_specifications = child.get("test_specifications", []) or []
            for ts in test_specifications:
                ts_model = self._get_or_create_test_specification(test_specification_dict=ts)
                ts_link = SwRequirementTestSpecificationModel(
                    sw_requirement_mapping_api=None,
                    sw_requirement_mapping_sw_requirement=link,
                    test_specification=ts_model,
                    coverage=ts.get("coverage", 0),
                    created_by=self.user,
                )
                self.dbi.session.add(ts_link)
                self.dbi.session.commit()

            # Map test cases under this nested software requirement link
            test_cases = child.get("test_cases", []) or []
            for tc in test_cases:
                tc_model = self._get_or_create_test_case(test_case_dict=tc)
                tc_link = SwRequirementTestCaseModel(
                    sw_requirement_mapping_api=None,
                    sw_requirement_mapping_sw_requirement=link,
                    test_case=tc_model,
                    coverage=tc.get("coverage", 0),
                    created_by=self.user,
                )
                self.dbi.session.add(tc_link)
                self.dbi.session.commit()
            # Recurse into grandchildren
            grand_children = child.get("software_requirements", []) or []
            if grand_children:
                self._generate_nested_sw_requirements(
                    parent_mapping_api=None,
                    parent_mapping_sw_requirement=link,
                    children_sw_requirements=grand_children,
                )
        return created_links

    def generate_api_test_specifications(self, api_model, snippet: dict, test_specifications: List[dict]):
        # ApiTestSpecifications
        api_test_specifications = []
        for test_specification in test_specifications:
            new_test_specification = self._get_or_create_test_specification(test_specification_dict=test_specification)

            new_api_test_specification = ApiTestSpecificationModel(
                api=api_model,
                test_specification=new_test_specification,
                section=snippet["section"],
                offset=snippet["offset"],
                coverage=test_specification["coverage"],
                created_by=self.user,
            )
            api_test_specifications.append(new_api_test_specification)
        self.dbi.session.add_all(api_test_specifications)
        self.dbi.session.commit()
        return api_test_specifications

    def _get_or_create_test_specification(self, test_specification_dict: dict) -> TestSpecificationModel:
        existing = (
            self.dbi.session.query(TestSpecificationModel)
            .filter(TestSpecificationModel.title == test_specification_dict.get("title", ""))
            .filter(TestSpecificationModel.test_description == test_specification_dict.get("test_description", ""))
            .filter(TestSpecificationModel.expected_behavior == test_specification_dict.get("expected_behavior", ""))
            .filter(TestSpecificationModel.preconditions == test_specification_dict.get("preconditions", ""))
            .all()
        )
        if existing:
            return existing[0]
        new_test_specification = TestSpecificationModel(
            title=test_specification_dict.get("title", ""),
            test_description=test_specification_dict.get("test_description", ""),
            expected_behavior=test_specification_dict.get("expected_behavior", ""),
            preconditions=test_specification_dict.get("preconditions", ""),
            created_by=self.user,
        )
        self.dbi.session.add(new_test_specification)
        self.dbi.session.commit()
        return new_test_specification

    def generate_api_test_cases(self, api_model, snippet: dict, test_cases: List[dict]):
        # ApiTestCases
        api_test_cases = []
        for test_case in test_cases:
            new_test_case = self._get_or_create_test_case(test_case_dict=test_case)
            new_api_test_case = ApiTestCaseModel(
                api=api_model,
                test_case=new_test_case,
                section=snippet["section"],
                offset=snippet["offset"],
                coverage=test_case["coverage"],
                created_by=self.user,
            )
            api_test_cases.append(new_api_test_case)
        self.dbi.session.add_all(api_test_cases)
        self.dbi.session.commit()
        return api_test_cases

    def _get_or_create_test_case(self, test_case_dict: dict) -> TestCaseModel:
        existing = (
            self.dbi.session.query(TestCaseModel)
            .filter(TestCaseModel.title == test_case_dict.get("title", ""))
            .filter(TestCaseModel.description == test_case_dict.get("description", ""))
            .filter(TestCaseModel.repository == test_case_dict.get("repository", ""))
            .filter(TestCaseModel.relative_path == test_case_dict.get("relative_path", ""))
            .all()
        )
        if existing:
            return existing[0]
        new_test_case = TestCaseModel(
            title=test_case_dict.get("title", ""),
            description=test_case_dict.get("description", ""),
            repository=test_case_dict.get("repository", ""),
            relative_path=test_case_dict.get("relative_path", ""),
            created_by=self.user,
        )
        self.dbi.session.add(new_test_case)
        self.dbi.session.commit()
        return new_test_case

    def generate(self) -> dict:
        """Traverse the traceability and
        - if the work item already exists in the db extract it from the db
        - else create a new work item in the db
        """
        user_files_path = os.path.join(USER_FILES_BASE_DIR, f"{self.user_id}")
        if not os.path.exists(user_files_path):
            os.makedirs(user_files_path, exist_ok=True)

        for api in self.traceability:
            logger.info(f"Api {api['api']} {api['library']} {api['library_version']}")

            # Check if the api already exists
            existing_apis = (
                self.dbi.session.query(ApiModel)
                .filter(ApiModel.api == api["api"])
                .filter(ApiModel.library == api["library"])
                .filter(ApiModel.library_version == api["library_version"])
                .all()
            )
            if existing_apis:
                logger.info(f" - Api {api['api']} {api['library']} {api['library_version']} already exists")
                api_model = existing_apis[0]
            else:
                logger.info(
                    f" - Api {api['api']} {api['library']} {api['library_version']}" "does not exist, creating new api"
                )

                api_model = ApiModel(
                    api=api["api"],
                    library=api["library"],
                    library_version=api["library_version"],
                    raw_specification_url=api["api_reference_document"],
                    category="",
                    checksum="",
                    implementation_file="",
                    implementation_file_from_row=0,
                    implementation_file_to_row=0,
                    tags="",
                    created_by=self.user,
                )
                self.dbi.session.add(api_model)
                self.dbi.session.commit()
                logger.info(f" - Api {api['api']} {api['library']} {api['library_version']}" "created")

            # Create a user file with the content of the reference document
            reference_document_filename = f"{api['api']}_{api['library']}_{api['library_version']}.txt"
            reference_document_filepath = os.path.join(user_files_path, reference_document_filename)

            with open(reference_document_filepath, "w") as f:
                f.write(api["api_reference_document"])

            for index, snippet in enumerate(api["snippets"]):
                logger.info(f"* Snippet {index}")

                # ApiJustifications
                generated_justifications = self.generate_api_justifications(
                    api_model=api_model, snippet=snippet, justifications=snippet["justifications"]
                )
                logger.info(f" - justifications: {len(snippet['justifications'])}")
                logger.info(f" -  Generated {len(generated_justifications)} api justifications")

                # ApiDocuments
                generated_documents = self.generate_api_documents(
                    api_model=api_model, snippet=snippet, documents=snippet["documents"]
                )
                logger.info(f" - documents: {len(snippet['documents'])}")
                logger.info(f" -  Generated {len(generated_documents)} api documents")

                # ApiSoftwareRequirements
                generated_software_requirements = self.generate_api_software_requirements(
                    api_model=api_model, snippet=snippet, software_requirements=snippet["software_requirements"]
                )
                logger.info(f" - software_requirements: {len(snippet['software_requirements'])}")
                logger.info(f" -  Generated {len(generated_software_requirements)} api software requirements")

                # ApiTestSpecifications
                generated_test_specifications = self.generate_api_test_specifications(
                    api_model=api_model, snippet=snippet, test_specifications=snippet["test_specifications"]
                )
                logger.info(f" - test_specifications: {len(snippet['test_specifications'])}")
                logger.info(f" -  Generated {len(generated_test_specifications)} api test specifications")

                # ApiTestCases
                generated_test_cases = self.generate_api_test_cases(
                    api_model=api_model, snippet=snippet, test_cases=snippet["test_cases"]
                )
                logger.info(f" - test_cases: {len(snippet['test_cases'])}")
                logger.info(f" -  Generated {len(generated_test_cases)} api test cases")

                self.dbi.session.commit()
                logger.info(
                    f" - Traceability scan completed for api {api['api']} {api['library']} {api['library_version']}"
                )

        logger.info(" - Traceability scan completed")
        self.dbi.session.commit()
        self.dbi.session.close()


class RepoScanner:
    """
    Utilities to clone a Git repository into a per-user temporary folder,
    checkout a target branch, strip the VCS metadata (.git), and inspect files.
    """

    files = []
    user_id = None

    def __init__(self, user_id: str, _config: dict = {}) -> None:
        """
        Initialize the scanner.

        If base_temp_dir is not provided, a directory under the system temp
        directory will be used: <tmp>/basil/repos
        """
        default_root = Path(tempfile.gettempdir()) / "basil" / "repos" / self._sanitize(user_id)
        self.base_temp_dir = default_root
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        self.user_id = user_id
        self.config = _config
        if not self.validate_config():
            logger.error(f"Invalid repository configuration: {self.config}")
            raise ValueError("Invalid repository configuration")

    def validate_config(self) -> bool:
        """
        Validate the configuration.
        """
        if not self.config.get("url", None):
            return False
        if not self.config.get("branch", None):
            return False
        return True

    def clone_to_user_temp(self) -> str:
        """
        Clone the repository at repo_url into the user's temporary folder and
        checkout the given branch. After cloning, remove the .git folder.

        Returns the absolute path to the cloned working directory.
        """
        self.target_dir = "/var/folders/6b/t6rm59dn6q1g3_4p5b2fv__40000gn/T/basil/repos/1/BASIL-main-9a7208"
        return self.target_dir
        user_root = self._get_user_root()
        user_root.mkdir(parents=True, exist_ok=True)

        url = self.config.get("url", "")
        branch = self.config.get("branch", "")
        target_dir = user_root / self._generate_repo_dir_name(url, branch)
        if target_dir.exists():
            # Avoid accidental reuse; create a unique directory instead
            target_dir = user_root / f"{target_dir.name}-{uuid.uuid4().hex[:8]}"

        # Perform a shallow clone of the target branch into target_dir
        self._git_clone(url=url, branch=branch, target_dir=target_dir)

        self.git_version = self._git_version(target_dir=target_dir)

        # Remove the .git directory to leave a clean working copy
        self._remove_git_dir(target_dir)

        logger.info(f"Cloned repository {url} to {target_dir}")
        self.target_dir = str(target_dir)
        return str(target_dir)

    def clear_user_temp(self) -> None:
        """Remove the entire temporary folder for the given user."""
        user_root = self._get_user_root()
        if user_root.exists():
            shutil.rmtree(user_root)

    def list_all_files(self, include_hidden: bool = False) -> List[str]:
        """
        Return a list of all file paths (relative to root_dir) contained within root_dir.
        Directories are not included.
        """
        root_path = Path(self.target_dir).resolve()
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
        self, include_hidden: bool = False, filename_pattern: str = "", folder_pattern: str = ""
    ) -> List[str]:
        """
        List all files in the given root directory.
        """
        if not self.files:
            files = self.list_all_files(include_hidden=include_hidden)
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
        return self.base_temp_dir

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
        value = str(value)
        safe = "".join(ch if ch.isalnum() or ch in "-._" else "-" for ch in value.strip())
        return safe.strip("-._") or "value"

    @staticmethod
    def _git_clone(url: str, branch: str, target_dir: Path) -> None:
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
            url,
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


class TextScanner:

    def __init__(self, text: str):
        self.text = text

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
        match_type: str,
        match_string: str,
        strip: bool,
        case_sensitive: bool,
        lstrip=False,
        rstrip=False,
    ) -> Callable[[str], bool]:
        """
        Build a predicate that checks a single line against the given condition.
        match_type: one of ["startswith", "endswith", "contains", "not_contains", "equal", "regex"]
        """
        if not case_sensitive:
            match_string_cmp = match_string.lower()
        else:
            match_string_cmp = match_string

        def apply_trim(s: str) -> str:
            # strip takes precedence (can be True or a string of characters)
            if isinstance(strip, str):
                return s.strip(strip)
            if strip:
                return s.strip()
            out = s
            # lstrip may be bool or a string of characters
            if lstrip:
                if isinstance(lstrip, str):
                    out = out.lstrip(lstrip)
                else:
                    out = out.lstrip()
            # rstrip may be bool or a string of characters
            if rstrip:
                if isinstance(rstrip, str):
                    out = out.rstrip(rstrip)
                else:
                    out = out.rstrip()
            return out

        def normalize(line: str) -> str:
            value = apply_trim(line)
            return value if case_sensitive else value.lower()

        if match_type == "startswith":
            return lambda line: normalize(line).startswith(match_string_cmp)
        if match_type == "not_startswith":
            return lambda line: not normalize(line).startswith(match_string_cmp)
        if match_type == "endswith":
            return lambda line: normalize(line).endswith(match_string_cmp)
        if match_type == "not_endswith":
            return lambda line: not normalize(line).endswith(match_string_cmp)
        if match_type == "contains":
            return lambda line: match_string_cmp in normalize(line)
        if match_type == "not_contains":
            return lambda line: match_string_cmp not in normalize(line)
        if match_type == "equal":
            return lambda line: normalize(line) == match_string_cmp
        if match_type == "not_equal":
            return lambda line: normalize(line) != match_string_cmp
        if match_type == "regex":
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(match_string, flags)
            except re.error as exc:
                raise ValueError(f"Invalid regular expression: {match_string}") from exc
            return lambda line: pattern.search(apply_trim(line)) is not None
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
        lstrip: bool,
        rstrip: bool,
        output_mode: str,
        skip_top_items: int,
        skip_bottom_items: int,
    ) -> List[dict]:
        """
        Generic scanner to reduce duplication across start__/end__/... helpers.
        Return a list of elements
        """

        ret = []
        if not text:
            return ret

        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type=match_type,
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )

        # If elements are not provided, scan the whole text
        if not elements:
            ret = self._collect_matches_for_lines(
                lines=lines,
                initial_index=0,
                check_line=check_line,
                output_mode=output_mode,
            )
            return ret

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
        ret = self._skip_items(elements=aggregated, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def start__lines_starting_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections starting at specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
            + index of starting line
            + text: portion of text starting from the identified line
        """
        logger.info(f"start__lines_starting_with: {json.dumps(elements, indent=4)}")
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="startswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def start__lines_not_starting_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections starting at specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
            + index of starting line
            + text: portion of text starting from the identified line
        """
        logger.info(f"start__lines_starting_with: {json.dumps(elements, indent=4)}")
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="not_startswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__at(self, text: str, end_at: int, elements: List[dict]) -> List[dict]:
        """
        Analyze text for sections ending at specific index.
        Returns a list of dictionaries with:
            + index of starting line
            + text: portion of text starting from the identified line
        """

        for el in elements:
            if end_at < el.get("index", 0) + len(el.get("text", "")):
                el["text"] = text[el.get("index", 0): end_at]
        return elements

    def end__at_line(self, text: str, end_at_line: int, elements: List[dict]) -> List[dict]:
        """
        Analyze text for sections ending at specific line.
        Returns a list of dictionaries with:
            + index of starting line
            + text: portion of text ending at the identified line
        """
        logger.info(f"end__at_line: {end_at_line}")
        for el in elements:
            if el.get("index", 0) <= end_at_line < el.get("index", 0) + len(el.get("text", "").splitlines()):
                el["text"] = "\n".join(text.splitlines()[el["index"]: end_at_line + 1])
        logger.info(f"elements: {elements}")
        return elements

    def end__lines_starting_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections ending at specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
            + index of starting line
            + text: portion of text ending at the identified line
        """

        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="startswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="to",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__lines_ending_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections ending with specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
            + index of starting line
            + text: portion of text ending with the identified line
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="endswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="to",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__lines_contains(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections ending at a line containing match_string.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="contains",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="to",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__lines_not_contains(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections ending at a line not containing match_string.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="not_contains",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="to",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__lines_equal(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections ending at a line equal to match_string.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="equal",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="to",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def end__lines_not_equal(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections ending at a line not equal to match_string.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="not_equal",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
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
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections starting at specific lines and extend elements to provide a new text
        starting from the identified line that is the one matching the condition with the closest index.
        - Extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
            + index of starting line
            + text: portion of text starting from top to the identified line
        """

        def text_to_elements(
            lines: List[str],
            match_string: str = "",
            strip: bool = False,
            case_sensitive: bool = False,
            lstrip: bool = False,
            rstrip: bool = False,
        ) -> List[dict]:
            check_line = self._make_line_checker(
                match_type="startswith",
                match_string=match_string,
                strip=strip,
                case_sensitive=case_sensitive,
                lstrip=lstrip,
                rstrip=rstrip,
            )
            return self._collect_matches_for_lines(
                lines=lines,
                initial_index=0,
                check_line=check_line,
                output_mode="from",
            )

        ret = []

        lines = text.splitlines()

        # No elements provided: use every non-empty line as a starting point
        closest_elements = text_to_elements(
            lines=lines,
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )

        # Elements provided: for each element pick candidate by closest index
        for el in elements:
            el_index = el.get("index", 0)
            new_element_closest_index = None
            new_element_closest_text = None
            for idx, closest_el in enumerate(closest_elements):
                closest_el_index = closest_el.get("index", 0)
                closest_el_text = closest_el.get("text", "")
                if direction == "up" and closest_el_index > el_index:
                    continue
                if direction == "down" and closest_el_index < el_index:
                    continue
                if new_element_closest_index is None or (
                    abs(closest_el_index - el_index) < abs(new_element_closest_index - el_index)
                ):
                    new_element_closest_index = closest_el_index
                    new_element_closest_text = closest_el_text

            if new_element_closest_index is not None:
                ret.append({"index": new_element_closest_index, "text": new_element_closest_text})

        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def closest__lines_not_starting_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Find closest lines not starting with match_string for each element.
        """
        if not text or not elements:
            return []
        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type="not_startswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )
        candidates = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )
        ret = []
        for el in elements:
            el_index = el.get("index", 0)
            best = None
            for c in candidates:
                ci = c.get("index", 0)
                if direction == "up" and ci > el_index:
                    continue
                if direction == "down" and ci < el_index:
                    continue
                if best is None or abs(ci - el_index) < abs(best.get("index", 0) - el_index):
                    best = c
            if best is not None:
                ret.append({"index": best.get("index", 0), "text": best.get("text", "")})
        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def closest__lines_ending_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Find closest lines ending with match_string for each element.
        """
        if not text or not elements:
            return []
        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type="endswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )
        candidates = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )
        ret = []
        for el in elements:
            el_index = el.get("index", 0)
            best = None
            for c in candidates:
                ci = c.get("index", 0)
                if direction == "up" and ci > el_index:
                    continue
                if direction == "down" and ci < el_index:
                    continue
                if best is None or abs(ci - el_index) < abs(best.get("index", 0) - el_index):
                    best = c
            if best is not None:
                ret.append({"index": best.get("index", 0), "text": best.get("text", "")})
        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def closest__lines_not_ending_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Find closest lines not ending with match_string for each element.
        """
        if not text or not elements:
            return []
        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type="not_endswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )
        candidates = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )
        ret = []
        for el in elements:
            el_index = el.get("index", 0)
            best = None
            for c in candidates:
                ci = c.get("index", 0)
                if direction == "up" and ci > el_index:
                    continue
                if direction == "down" and ci < el_index:
                    continue
                if best is None or abs(ci - el_index) < abs(best.get("index", 0) - el_index):
                    best = c
            if best is not None:
                ret.append({"index": best.get("index", 0), "text": best.get("text", "")})
        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def closest__lines_contains(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Find closest lines containing match_string for each element.
        """
        if not text or not elements:
            return []
        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type="contains",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )
        candidates = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )
        ret = []
        for el in elements:
            el_index = el.get("index", 0)
            best = None
            for c in candidates:
                ci = c.get("index", 0)
                if direction == "up" and ci > el_index:
                    continue
                if direction == "down" and ci < el_index:
                    continue
                if best is None or abs(ci - el_index) < abs(best.get("index", 0) - el_index):
                    best = c
            if best is not None:
                ret.append({"index": best.get("index", 0), "text": best.get("text", "")})
        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def closest__lines_not_contains(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Find closest lines not containing match_string for each element.
        """
        if not text or not elements:
            return []
        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type="not_contains",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )
        candidates = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )
        ret = []
        for el in elements:
            el_index = el.get("index", 0)
            best = None
            for c in candidates:
                ci = c.get("index", 0)
                if direction == "up" and ci > el_index:
                    continue
                if direction == "down" and ci < el_index:
                    continue
                if best is None or abs(ci - el_index) < abs(best.get("index", 0) - el_index):
                    best = c
            if best is not None:
                ret.append({"index": best.get("index", 0), "text": best.get("text", "")})
        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def closest__lines_equal(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Find closest lines equal to match_string for each element.
        """
        if not text or not elements:
            return []
        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type="equal",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )
        candidates = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )
        ret = []
        for el in elements:
            el_index = el.get("index", 0)
            best = None
            for c in candidates:
                ci = c.get("index", 0)
                if direction == "up" and ci > el_index:
                    continue
                if direction == "down" and ci < el_index:
                    continue
                if best is None or abs(ci - el_index) < abs(best.get("index", 0) - el_index):
                    best = c
            if best is not None:
                ret.append({"index": best.get("index", 0), "text": best.get("text", "")})
        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def closest__lines_not_equal(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        direction: str = "",
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Find closest lines not equal to match_string for each element.
        """
        if not text or not elements:
            return []
        lines = text.splitlines()
        check_line = self._make_line_checker(
            match_type="not_equal",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
        )
        candidates = self._collect_matches_for_lines(
            lines=lines,
            initial_index=0,
            check_line=check_line,
            output_mode="from",
        )
        ret = []
        for el in elements:
            el_index = el.get("index", 0)
            best = None
            for c in candidates:
                ci = c.get("index", 0)
                if direction == "up" and ci > el_index:
                    continue
                if direction == "down" and ci < el_index:
                    continue
                if best is None or abs(ci - el_index) < abs(best.get("index", 0) - el_index):
                    best = c
            if best is not None:
                ret.append({"index": best.get("index", 0), "text": best.get("text", "")})
        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

    def start__lines_ending_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections ending with specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
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
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def start__lines_not_ending_with(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections not ending with specific lines.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="not_endswith",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
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
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections containing specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
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
            lstrip=lstrip,
            rstrip=rstrip,
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
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections not containing specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
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
            lstrip=lstrip,
            rstrip=rstrip,
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
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections equal to specific lines.
        - If elements is empty, extract elements from text
        - If elements are provided, extract a new set of elements from the input elements
          Case sensitivity is controlled by the case_sensitive flag.
        Returns a list of dictionaries with:
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
            lstrip=lstrip,
            rstrip=rstrip,
            output_mode="from",
            skip_top_items=skip_top_items,
            skip_bottom_items=skip_bottom_items,
        )

    def start__lines_not_equal(
        self,
        text: str,
        elements: List[dict],
        match_string: str = "",
        strip: bool = False,
        case_sensitive: bool = False,
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections not equal to specific lines.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="not_equal",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
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
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections where a line matches the given regular expression and start from that line.
        Returns a list of elements {index, text}.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="regex",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
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
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections where a line matches the given regular expression and end at that line.
        Returns a list of elements {index, text}.
        """
        return self._scan_text_by_elements(
            text=text,
            elements=elements,
            match_type="regex",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
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
        lstrip: bool = False,
        rstrip: bool = False,
        skip_top_items: int = 0,
        skip_bottom_items: int = 0,
    ) -> List[dict]:
        """
        Analyze text for sections where a line matches the given regular expression and extend elements
        to provide a new text starting from the closest matching line index.
        Returns structure with 'text' and list of elements {index, text}.
        """
        ret = []

        if not text or not elements:
            return ret

        lines = text.splitlines()

        # Build candidate matches from entire text using regex
        check_line = self._make_line_checker(
            match_type="regex",
            match_string=match_string,
            strip=strip,
            case_sensitive=case_sensitive,
            lstrip=lstrip,
            rstrip=rstrip,
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
                ret.append({"index": new_element_closest_index, "text": new_element_closest_text})

        ret = self._skip_items(elements=ret, skip_top_items=skip_top_items, skip_bottom_items=skip_bottom_items)
        return ret

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

        ret = []

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
                    ret.append(tmp)
        return ret

    def split_elements(
        self,
        text: str,
        elements: List[dict],
        delimiter: str,
        strip: bool = False,
        lstrip=False,
        rstrip=False,
        keep_empty: bool = False,
    ) -> List[dict]:
        """
        Explode each element's text into multiple elements by splitting on delimiter.
        - delimiter: string separator
        - strip/lstrip/rstrip: whether to strip each resulting part
        - keep_empty: whether to keep empty parts after split/strip
        Index for each new element is computed as the original element index plus
        the number of lines before the part within the element text.
        """
        if not delimiter:
            return elements
        new_elements: List[dict] = []
        for el in elements:
            base_index = el.get("index", 0)
            element_text = el.get("text", "")
            parts = element_text.split(delimiter)
            if not parts:
                continue
            # Precompute cumulative line counts to derive starting index per part
            cumulative_prefix_lines = [0]
            running_prefix = ""
            for i, part in enumerate(parts[:-1]):
                running_prefix += part
                # account for inserted delimiter between parts (except before first part)
                running_prefix += delimiter
                cumulative_prefix_lines.append(len(running_prefix.splitlines()))
            # Last part prefix lines already represented
            for i, part in enumerate(parts):
                curr_text = part
                if strip:
                    curr_text = curr_text.strip()
                else:
                    if lstrip:
                        if isinstance(lstrip, str):
                            curr_text = curr_text.lstrip(lstrip)
                        else:
                            curr_text = curr_text.lstrip()
                    if rstrip:
                        if isinstance(rstrip, str):
                            curr_text = curr_text.rstrip(rstrip)
                        else:
                            curr_text = curr_text.rstrip()
                if not keep_empty and not curr_text:
                    continue
                new_elements.append(
                    {
                        "index": base_index + cumulative_prefix_lines[i],
                        "text": curr_text,
                    }
                )
        return new_elements


class FilesScanner:

    def __init__(self, files: List[str] = [], tmp_repo_path: str = ""):
        self.files = files
        self.tmp_repo_path = tmp_repo_path

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

        for curr_file in files:
            curr_file_content = self.get_file_content(filepath=os.path.join(self.tmp_repo_path, curr_file))
            if contains:
                for curr_str_match in contains:
                    if curr_str_match in curr_file_content:
                        ret.append(curr_file)
                        break
            if not_contains and curr_file in ret:
                for curr_str_match in not_contains:
                    if curr_str_match in curr_file_content:
                        ret.remove(curr_file)
                        break
        return ret

    @staticmethod
    def get_file_content(filepath: str, encoding: str = "utf-8") -> str:
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

    SNIPPET_FIELDS = [{"name": "section", "type": "str"}, {"name": "offset", "type": "int"}]

    JUSTIFICATION_FIELDS = [{"name": "description", "type": "str"}, {"name": "coverage", "type": "int"}]

    DOCUMENT_FIELDS = [
        {"name": "title", "type": "str"},
        {"name": "description", "type": "str"},
        {"name": "document_type", "type": "str"},
        {"name": "spdx_relation", "type": "str"},
        {"name": "url", "type": "str"},
        {"name": "coverage", "type": "int"},
    ]

    SOFTWARE_REQUIREMENT_FIELDS = [
        {"name": "title", "type": "str"},
        {"name": "description", "type": "str"},
        {"name": "coverage", "type": "int"},
    ]

    TEST_SPECIFICATION_FIELDS = [
        {"name": "title", "type": "str"},
        {"name": "preconditions", "type": "str"},
        {"name": "test_description", "type": "str"},
        {"name": "expected_behavior", "type": "str"},
        {"name": "coverage", "type": "int"},
    ]

    TEST_CASE_FIELDS = [
        {"name": "title", "type": "str"},
        {"name": "description", "type": "str"},
        {"name": "repository", "type": "str", "mandatory": False},
        {"name": "relative_path", "type": "str", "mandatory": False},
        {"name": "coverage", "type": "int"},
    ]

    def __init__(self, user_id: str, api: Optional[dict] = {}, scan_config: Optional[dict] = {}) -> None:
        self.api = api
        self.scan_config = scan_config
        self.user_id = user_id

    def _is_valid_repo_config(self, _config: dict) -> bool:
        mandatory_configs = ["repository"]
        for mandatory_config in mandatory_configs:
            if not _config.get(mandatory_config, None):
                logger.info(f"Scan configuration error: `{mandatory_config}` is not valid")
                logger.info(f" -> config: {_config}")
                return False
        return True

    def _is_valid_work_item_config(self, _config: dict, field_name: str) -> bool:
        """
        Validate the configuration of a work item
        """
        if not isinstance(_config.get(field_name, {}), dict):
            return False
        else:
            if _config.get(field_name, {}).get("value", None) is not None:
                logger.info(f"Configuration: value is into the configuration for: {field_name}")
                if isinstance(_config.get(field_name, {}).get("value", ""), str) or isinstance(
                    _config.get(field_name, {}).get("value", ""), int
                ):
                    return True
                return False
            else:
                logger.info(
                    f"Configuration: {_config.get(field_name, {})} value "
                    "is not into the configuration for: {field_name}"
                )
                mandatory_configs = ["start", "end"]
                for mandatory_config in mandatory_configs:
                    if not _config.get(field_name, {}).get(mandatory_config, None):
                        logger.info(f"Scan configuration error: `{field_name}` do not have `{mandatory_config}` key")
                        logger.info(f" -> config: {_config}")
                        return False
                return True
        return False

    def scan(self) -> dict:

        api = []
        if not self.scan_config.get("api", None):
            return ValueError("Scan configuration do not have `api` key")

        apis_config = self.scan_config.get("api", [])

        for curr_api_config in apis_config:

            # Create a ReposScanner
            if not self._is_valid_repo_config(curr_api_config):
                continue

            api_repository_config = curr_api_config.get("repository", {})
            api_repo_scanner = RepoScanner(user_id=self.user_id, _config=api_repository_config)
            api_repo_scanner.clone_to_user_temp()

            for idx, curr_api in enumerate(curr_api_config.get("name", [])):
                logger.info(f"Scan for api: {curr_api}")

                curr_api_config["api"] = curr_api
                api_reference_documents = self.search__get_files(
                    repo_scanner=api_repo_scanner,
                    _config=api_repository_config,
                    _magic_variables={"__api__": curr_api},
                )
                if api_reference_documents:
                    api_repository_url = api_repository_config.get("url", "")
                    api_repository_branch = api_repository_config.get("branch", "")
                    api_library = curr_api_config.get("library", "")
                    api_library_version = (
                        curr_api_config.get("library_version", "")
                        .replace("__ref__", api_repository_branch)
                        .replace("__branch__", api_repository_branch)
                    )

                    api_reference_document = api_reference_documents[0]

                    # Copy the api reference document to the user's files folder
                    api_reference_document_extension = api_reference_document.split(".")[-1]
                    user_file_name = f"{curr_api}_{api_repository_branch}.{api_reference_document_extension}"
                    api_user_files_path = os.path.join(USER_FILES_BASE_DIR, f"{self.user_id}", user_file_name)
                    shutil.copy(os.path.join(api_repo_scanner.target_dir, api_reference_document), api_user_files_path)

                    tmp_api = {
                        "api": curr_api,
                        "snippets": [],
                        "repository_url": api_repository_url,
                        "repository_branch": api_repository_branch,
                        "library": api_library,
                        "library_version": api_library_version,
                        "original_api_reference_document": api_reference_document,
                        "api_reference_document": api_user_files_path,
                    }
                    reference_document_content = FilesScanner.get_file_content(
                        filepath=os.path.join(api_user_files_path)
                    )
                    tmp_api["reference_document_content"] = reference_document_content
                    magic_variables = {
                        "__api__": tmp_api["api"],
                        "__library__": tmp_api["library"],
                        "__library_version__": tmp_api["library_version"],
                        "__api_reference_document__": tmp_api["api_reference_document"],
                        "__reference_document_content__": tmp_api["reference_document_content"],
                    }

                    logger.info(f"Copied api reference document to user's folder: {api_user_files_path}")
                    logger.info(f"Api reference document filename in user's folder: {user_file_name}")
                    logger.info(f"Api library: {api_library}")
                    logger.info(f"Api library version: {api_library_version}")
                    logger.info(f"Api original reference document file: {api_reference_document}")
                    logger.info(f"Api repository url: {api_repository_url}")
                    logger.info(f"Api repository branch: {api_repository_branch}")
                    logger.info(f"Api reference document extension: {api_reference_document_extension}")

                else:
                    logger.info(f"No api reference document found for api: {curr_api}")
                    continue

                # ------------------------------------------------------------
                # Get api reference document Snippets
                # ------------------------------------------------------------
                logger.info("Get api reference document Snippets")

                snippets_config = curr_api_config.get("snippets", {})
                if not snippets_config:
                    logger.info(f"No snippets configuration found for api: {curr_api}")
                    continue

                snippet_rules_config = snippets_config.get("rules", [])
                if not snippet_rules_config:
                    logger.info(f"No snippet rules configuration found for api: {curr_api}")
                    continue

                for snippet_rule_config in snippet_rules_config:
                    snippets = []

                    logger.info(f"Scan for snippet: {snippet_rule_config.get('name', '')}")

                    for snippet_field in self.SNIPPET_FIELDS:
                        valid_fields_config = True
                        if not self._is_valid_work_item_config(snippet_rule_config, snippet_field["name"]):
                            valid_fields_config = False
                            break

                    if not valid_fields_config:
                        continue

                    reference_document_snippets = self.search__snippets(
                        _config=snippet_rule_config,
                        _reference_document_content=reference_document_content,
                        _magic_variables=magic_variables,
                    )
                    if reference_document_snippets:
                        # reference_document_snippet = reference_document_snippets[0]
                        snippets += reference_document_snippets

                    # add nested work items keys to each snippet
                    for snippet in snippets:
                        snippet["justifications"] = []
                        snippet["documents"] = []
                        snippet["software_requirements"] = []
                        snippet["test_specifications"] = []
                        snippet["test_cases"] = []

                    # ------------------------------------------------------------
                    # Justifications
                    # ------------------------------------------------------------
                    logger.info("  - Justifications")

                    justifications_config = snippet_rule_config.get("justifications", {})
                    justifications = self.search__justifications(
                        _config=justifications_config,
                        _magic_variables=magic_variables,
                    )

                    if justifications:
                        for snippet in snippets:
                            snippet["justifications"] += justifications

                    logger.info(f"    -> Found: {len(snippet['justifications'])} justifications")

                    # ------------------------------------------------------------
                    # Documents
                    # ------------------------------------------------------------
                    logger.info("  - Documents")

                    documents_config = snippet_rule_config.get("documents", {})
                    documents = self.search__documents(
                        _config=documents_config,
                        _magic_variables=magic_variables,
                    )

                    if documents:
                        for snippet in snippets:
                            snippet["documents"] += documents

                    logger.info(f"    -> Found: {len(snippet['documents'])} documents")

                    # ------------------------------------------------------------
                    # Software Requirements
                    # ------------------------------------------------------------
                    logger.info("  - Software Requirements")

                    software_requirements_config = snippet_rule_config.get("software_requirements", {})
                    software_requirements = self.search__software_requirements(
                        _config=software_requirements_config,
                        _magic_variables=magic_variables,
                    )
                    if software_requirements:
                        for snippet in snippets:
                            snippet["software_requirements"] += software_requirements

                    logger.info(f"    -> Found: {len(snippet['software_requirements'])} software requirements")

                    # ------------------------------------------------------------
                    # Test Specifications
                    # ------------------------------------------------------------
                    logger.info("  - Test Specifications")

                    test_specifications_config = snippet_rule_config.get("test_specifications", {})
                    test_specifications = self.search__test_specifications(
                        _config=test_specifications_config,
                        _magic_variables=magic_variables,
                    )
                    if test_specifications:
                        for snippet in snippets:
                            snippet["test_specifications"] += test_specifications

                    logger.info(f"    -> Found: {len(snippet['test_specifications'])} test specifications")

                    # ------------------------------------------------------------
                    # Test Cases
                    # ------------------------------------------------------------
                    logger.info("  - Test Cases")

                    test_cases_config = snippet_rule_config.get("test_cases", {})
                    test_cases = self.search__test_cases(
                        _config=test_cases_config,
                        _magic_variables=magic_variables,
                    )
                    if test_cases:
                        for snippet in snippets:
                            snippet["test_cases"] += test_cases

                    logger.info(f"    -> Found: {len(snippet['test_cases'])} test cases")

                    if snippets:
                        tmp_api["snippets"] += snippets

                # ------------------------------------------------------------
                api.append(tmp_api)

            logger.info("Clear api repository scanner")
            # api_repo_scanner.clear_user_temp()
            del api_repo_scanner

        logger.info(f"Api: {json.dumps(api, indent=4)}")
        return api

    def search__get_files(self, repo_scanner: RepoScanner, _config: dict, _magic_variables: dict) -> List[str]:
        # Get api reference document

        filename_pattern = _config.get("filename_pattern", "")
        folder_pattern = _config.get("folder_pattern", "")

        for mk, mv in _magic_variables.items():
            filename_pattern = filename_pattern.replace(mk, mv)
            folder_pattern = folder_pattern.replace(mk, mv)

        files = repo_scanner.list_files(
            include_hidden=_config.get("hidden", False),
            filename_pattern=filename_pattern,
            folder_pattern=folder_pattern,
        )

        file_scanner = FilesScanner(files=files, tmp_repo_path=repo_scanner.target_dir)
        logger.info(f"Number of identified files: {len(files)}")

        filter_file_by_content_contains = _config.get("file_contains", [])
        filter_file_by_content_not_contains = _config.get("file_not_contains", [])
        filtered_files = file_scanner.filter_files_by_content(
            files=files, contains=filter_file_by_content_contains, not_contains=filter_file_by_content_not_contains
        )

        if filtered_files:
            logger.info(f"Number of files passing the content filter: {len(filtered_files)}")
        return filtered_files

    def search__extract_sections(self, _config: dict, text: str, elements: List[dict]) -> List[dict]:
        """
        Extract sections text
        """

        def _normalize_trim_value(v):
            """
            Normalize lstrip/rstrip/strip config values:
            - True -> True (default whitespace)
            - ""   -> True (explicit default whitespace)
            - str  -> the provided character set
            - list/tuple of strings -> concatenated character set
            - falsy/None -> False (disabled)
            """
            if v is True:
                return True
            if isinstance(v, str):
                return True if v == "" else v
            if isinstance(v, (list, tuple)):
                chars = "".join([c for c in v if isinstance(c, str) and c])
                return chars if chars else False
            return bool(v)

        mandatory_configs = ["start", "end"]
        for mandatory_config in mandatory_configs:
            if not _config.get(mandatory_config, None):
                logger.info(f"Scan configuration error: `{mandatory_config}` is not valid into {_config}")
                return []

        text_scanner = TextScanner(text=text)

        # Extract sections using start definition
        strip = _normalize_trim_value(_config.get("start").get("strip", False))
        lstrip_flag = _normalize_trim_value(_config.get("start").get("lstrip", False))
        rstrip_flag = _normalize_trim_value(_config.get("start").get("rstrip", False))
        case_sensitive = _config.get("start").get("case_sensitive", False)
        skip_top_items = _config.get("start").get("skip_top_items", 0)
        skip_bottom_items = _config.get("start").get("skip_bottom_items", 0)
        start_cfg = _config.get("start") or {}
        end_cfg = _config.get("end") or {}
        # Defaults for end are inherited from start unless explicitly overridden
        strip_end = _normalize_trim_value(end_cfg.get("strip", strip))
        lstrip_end = _normalize_trim_value(end_cfg.get("lstrip", lstrip_flag))
        rstrip_end = _normalize_trim_value(end_cfg.get("rstrip", rstrip_flag))

        if _config.get("start").get("at", None) is not None:
            start_at = _config.get("start").get("at")
            if start_at == "__start__":
                start_at = 0
            if isinstance(start_at, int):
                elements = [{"index": start_at, "text": text[start_at:]}]
        if not elements and _config.get("start").get("line", None) is not None:
            start_at_line = _config.get("start").get("line")
            if start_at_line == "__start__":
                start_at_line = 0
            if isinstance(start_at_line, int):
                elements = [{"index": start_at_line, "text": "\n".join(text.splitlines()[start_at_line:])}]
        if not elements:
            if _config.get("start").get("line_starting_with", None):
                elements = text_scanner.start__lines_starting_with(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_starting_with", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_not_starting_with", None):
                elements = text_scanner.start__lines_not_starting_with(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_not_starting_with", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_ending_with", None):
                elements = text_scanner.start__lines_ending_with(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_ending_with", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_not_ending_with", None):
                elements = text_scanner.start__lines_not_ending_with(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_not_ending_with", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_contains", None):
                elements = text_scanner.start__lines_containing(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_contains", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_not_contains", None):
                elements = text_scanner.start__lines_not_containing(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_not_contains", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_equal", None):
                elements = text_scanner.start__lines_equal(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_equal", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_not_equal", None):
                elements = text_scanner.start__lines_not_equal(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_not_equal", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("line_regex", None):
                elements = text_scanner.start__lines_regex(
                    text=text,
                    elements=elements,
                    match_string=start_cfg.get("line_regex", ""),
                    strip=strip,
                    lstrip=lstrip_flag,
                    rstrip=rstrip_flag,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
            if _config.get("start").get("extend", None) is not None:
                if _config.get("start").get("extend").get("count", None) is not None:
                    if _config.get("start").get("extend").get("direction", None) is not None:
                        extend_direction = _config.get("start").get("extend").get("direction")
                        extend_count = _config.get("start").get("extend").get("count")
                        elements = text_scanner._extend_content_of_elements(
                            direction=extend_direction,
                            count=extend_count,
                            text=text,
                            elements=elements,
                        )
            if _config.get("start").get("closest", None) is not None:
                closest_dir = (start_cfg.get("closest", {}) or {}).get("direction", "")
                if _config.get("start").get("closest").get("line_starting_with", None) is not None:
                    elements = text_scanner.closest__lines_starting_with(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_starting_with", ""),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )
                if _config.get("start").get("closest").get("line_not_starting_with", None) is not None:
                    elements = text_scanner.closest__lines_not_starting_with(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_not_starting_with", ""),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )
                if _config.get("start").get("closest").get("line_ending_with", None):
                    elements = text_scanner.closest__lines_ending_with(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_ending_with", "").rstrip("\n"),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )
                if _config.get("start").get("closest").get("line_not_ending_with", None):
                    elements = text_scanner.closest__lines_not_ending_with(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_not_ending_with", "").rstrip("\n"),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )
                if _config.get("start").get("closest").get("line_contains", None):
                    elements = text_scanner.closest__lines_contains(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_contains", ""),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )
                if _config.get("start").get("closest").get("line_not_contains", None):
                    elements = text_scanner.closest__lines_not_contains(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_not_contains", ""),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )

                if _config.get("start").get("closest").get("line_equal", None):
                    elements = text_scanner.closest__lines_equal(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_equal", ""),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )

                if _config.get("start").get("closest").get("line_not_equal", None):
                    elements = text_scanner.closest__lines_not_equal(
                        text=text,
                        elements=elements,
                        match_string=start_cfg.get("closest", {}).get("line_equal", ""),
                        strip=strip,
                        lstrip=lstrip_flag,
                        rstrip=rstrip_flag,
                        direction=closest_dir,
                        case_sensitive=case_sensitive,
                        skip_top_items=skip_top_items,
                        skip_bottom_items=skip_bottom_items,
                    )

        if elements:
            skip_end = False
            # Extract sections using end definition
            if _config.get("end").get("at", None) is not None:
                end_at = _config.get("end").get("at")
                if end_at == "__end__":
                    end_at = len(text)
                if isinstance(end_at, int):
                    elements = text_scanner.end__at(text=text, end_at=end_at, elements=elements)
                    skip_end = True

            if not skip_end and _config.get("end").get("line", None):
                end_line = _config.get("end").get("line")
                if end_line == "__end__":
                    end_line = max(0, len(text.splitlines()) - 1)
                if isinstance(end_line, int):
                    elements = text_scanner.end__at_line(text=text, end_at_line=end_line, elements=elements)
                    skip_end = True

            if not skip_end and _config.get("end").get("line_starting_with", None):
                elements = text_scanner.end__lines_starting_with(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_starting_with", ""),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_not_starting_with", None):
                elements = text_scanner.end__lines_not_starting_with(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_not_starting_with", ""),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_ending_with", None):
                elements = text_scanner.end__lines_ending_with(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_ending_with", "").rstrip("\n"),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_not_ending_with", None):
                elements = text_scanner.end__lines_not_ending_with(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_not_ending_with", "").rstrip("\n"),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_contains", None):
                elements = text_scanner.end__lines_contains(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_contains", ""),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_not_contains", None):
                elements = text_scanner.end__lines_not_contains(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_not_contains", ""),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_equal", None):
                elements = text_scanner.end__lines_equal(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_equal", ""),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_not_equal", None):
                elements = text_scanner.end__lines_not_equal(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_not_equal", ""),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )
                skip_end = True

            if not skip_end and _config.get("end").get("line_regex", None):
                elements = text_scanner.end__lines_regex(
                    text=text,
                    elements=elements,
                    match_string=end_cfg.get("line_regex", ""),
                    strip=strip_end,
                    lstrip=lstrip_end,
                    rstrip=rstrip_end,
                    case_sensitive=case_sensitive,
                    skip_top_items=skip_top_items,
                    skip_bottom_items=skip_bottom_items,
                )

        # Optionally split resulting elements into multiple sections
        if elements and _config.get("split", None):
            split_cfg = _config.get("split") or {}
            delimiter = (
                split_cfg.get("delimiter")
                or split_cfg.get("by")
                or split_cfg.get("value")
                or split_cfg.get("separator")
            )
            split_strip = _normalize_trim_value(split_cfg.get("strip", False)) if "strip" in split_cfg else False
            split_lstrip = _normalize_trim_value(split_cfg.get("lstrip", False)) if "lstrip" in split_cfg else False
            split_rstrip = _normalize_trim_value(split_cfg.get("rstrip", False)) if "rstrip" in split_cfg else False
            split_keep_empty = split_cfg.get("keep_empty", False)
            if delimiter:
                # If elements accidentally wrapped in a dict of shape {"text":..., "elements":[...]},
                # unwrap, split, and return the plain list for consistency with the rest of the pipeline.
                if isinstance(elements, list):
                    elements = text_scanner.split_elements(
                        text=text,
                        elements=elements,
                        delimiter=delimiter,
                        strip=split_strip,
                        lstrip=split_lstrip,
                        rstrip=split_rstrip,
                        keep_empty=split_keep_empty,
                    )
                else:
                    elements = text_scanner.split_elements(
                        text=text,
                        elements=elements,
                        delimiter=delimiter,
                        strip=split_strip,
                        lstrip=split_lstrip,
                        rstrip=split_rstrip,
                        keep_empty=split_keep_empty,
                    )

        # Field-level final trimming on resulting element texts, e.g. rstrip: ";"
        if elements:
            field_strip = _normalize_trim_value(_config.get("strip", False)) if "strip" in _config else False
            field_lstrip = _normalize_trim_value(_config.get("lstrip", False)) if "lstrip" in _config else False
            field_rstrip = _normalize_trim_value(_config.get("rstrip", False)) if "rstrip" in _config else False
            if field_strip or field_lstrip or field_rstrip:
                for el in elements:
                    curr = el.get("text", "")
                    if field_strip:
                        if isinstance(field_strip, str):
                            curr = curr.strip(field_strip)
                        else:
                            curr = curr.strip()
                    else:
                        if field_lstrip:
                            if isinstance(field_lstrip, str):
                                curr = curr.lstrip(field_lstrip)
                            else:
                                curr = curr.lstrip()
                        if field_rstrip:
                            if isinstance(field_rstrip, str):
                                curr = curr.rstrip(field_rstrip)
                            else:
                                curr = curr.rstrip()
                    el["text"] = curr

        return elements

    def _get_field_value(self, _config: dict, field_name: str, field_type: str, text: str, _magic_variables: dict):
        """
        Get the value of a field from the configuration
        Apply magic variables to the field value
        Apply transforms to the field value
        """
        field_config = _config.get(field_name, {})
        if not isinstance(field_config, dict):
            raise ValueError(f"Configuration error: Field value is not a dictionary: {field_name}")

        if field_config.get("value", None) is not None:
            field_value = field_config.get("value", "")
            if isinstance(field_value, str):
                if field_type == "str":
                    # Apply magic variables to string values
                    for mk, mv in _magic_variables.items():
                        try:
                            field_value = field_value.replace(mk, str(mv))
                        except Exception:
                            # Be tolerant to non-string replacers
                            field_value = field_value.replace(mk, str(mv))
                    return field_value
                if field_type == "int":
                    # keep template variables as is
                    if field_value.startswith("__") and field_value.endswith("__"):
                        for mk, mv in _magic_variables.items():
                            field_value = field_value.replace(mk, mv)
                        return field_value
                    return int(field_value)
                return None
            if isinstance(field_value, int):
                if field_type == "int":
                    if str(field_value).startswith("__") and str(field_value).endswith("__"):
                        for mk, mv in _magic_variables.items():
                            field_value = field_value.replace(mk, mv)
                        return field_value
                    return field_value
                if field_type == "str":
                    return str(field_value)
                return None
        else:
            # Only treat as extraction config if both 'start' and 'end' are provided
            # To avoid conflict with test_case repository field
            if field_config.get("start", None) is not None and field_config.get("end", None) is not None:
                ret = self.search__extract_sections(_config=field_config, text=text, elements=[])

                # NOTE: Do not apply magic variables to the extracted text

                # Apply transforms to the extracted text
                if field_config.get("transform", None) is not None:
                    ret = [self._apply_transforms(r, field_config.get("transform", []), field_type) for r in ret]

                return ret

            return None
        return None

    @staticmethod
    def _to_camel_case(s: str) -> str:
        """
        Convert string to lowerCamelCase.
        """
        parts = re.split(r"[^A-Za-z0-9]+", s)
        parts = [p for p in parts if p]
        if not parts:
            return ""
        first = parts[0].lower()
        rest = [p[:1].upper() + p[1:].lower() if p else "" for p in parts[1:]]
        return first + "".join(rest)

    def _apply_transforms(self, value, transforms: list, field_type: str):
        """
        Apply a sequence of transforms to a string or to each string inside a list/dict element.
        Supported operations:
          - uppercase
          - lowercase
          - camelcase
          - strip
          - suffix (requires 'value')
          - prefix (requires 'value')
          - replace (requires 'what' and 'with')
          - regex_sub (requires 'what' and 'with'; optional flags: i/m/s or booleans ignorecase/multiline/dotall)
        """

        def apply_one(v: str, t: dict) -> str:
            how = (t.get("how", "") or "").lower()
            if how == "uppercase":
                return v.upper()
            if how == "lowercase":
                return v.lower()
            if how == "camelcase":
                return self._to_camel_case(v)
            if how == "strip":
                return v.strip()
            if how == "suffix":
                return v + str(t.get("value", ""))
            if how == "prefix":
                return str(t.get("value", "")) + v
            if how == "replace":
                what = str(t.get("what", ""))
                with_ = str(t.get("with", ""))
                return v.replace(what, with_)
            if how == "regex_sub":
                # 'what' is preferred; 'pattern' remains supported for backward compatibility
                pattern = str(t.get("what", t.get("pattern", "")))
                with_ = str(t.get("with", ""))
                flags_spec = t.get("flags", "")
                re_flags = 0
                # Support string flags like "im" or "is"
                if isinstance(flags_spec, str):
                    fs = flags_spec.lower()
                    if "i" in fs:
                        re_flags |= re.IGNORECASE
                    if "m" in fs:
                        re_flags |= re.MULTILINE
                    if "s" in fs:
                        re_flags |= re.DOTALL
                # Also support explicit booleans
                if t.get("ignorecase", False):
                    re_flags |= re.IGNORECASE
                if t.get("multiline", False):
                    re_flags |= re.MULTILINE
                if t.get("dotall", False):
                    re_flags |= re.DOTALL
                try:
                    return re.sub(pattern, with_, v, flags=re_flags)
                except re.error as exc:
                    raise ValueError(f"Invalid regular expression in regex_sub: {pattern}") from exc
            return v

        def apply_all(v: str) -> str:
            out = v
            for t in transforms:
                out = apply_one(out, t or {})
            return out

        # Strings
        if isinstance(value, str):
            return apply_all(value)
        # Lists of strings or dicts with 'text'
        if isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, str):
                    new_list.append(apply_all(item))
                elif isinstance(item, dict) and isinstance(item.get("text", ""), str):
                    new_item = dict(item)
                    new_item["text"] = apply_all(new_item["text"])
                    new_list.append(new_item)
                else:
                    new_list.append(item)
            return new_list
        # Dict with 'text'
        if isinstance(value, dict) and isinstance(value.get("text", ""), str):
            new_value = dict(value)
            new_value["text"] = apply_all(new_value["text"])
            return new_value
        # Other types unchanged
        return value

    @staticmethod
    def _combine_fields_to_work_items(field_specs: List[dict], values_by_field: dict) -> List[dict]:
        """
        Generic combiner for any kind of work item fields.
        Rules:
        - If there are no list fields, return a single work item.
        - If there is exactly one list field, broadcast scalar fields to its length.
        - If there are multiple list fields, all list lengths must match; otherwise return [].
        """
        field_names = [f["name"] for f in field_specs]
        list_field_names = [n for n in field_names if isinstance(values_by_field.get(n), list)]

        if not list_field_names:
            return [dict(values_by_field)]

        if len(list_field_names) == 1:
            list_name = list_field_names[0]
            n = len(values_by_field.get(list_name, []))
            items: List[dict] = []
            for i in range(n):
                item = {}
                for name in field_names:
                    v = values_by_field.get(name)
                    if isinstance(v, list):
                        item[name] = v[i] if i < len(v) else None
                    else:
                        item[name] = v
                items.append(item)
            return items

        lengths = [len(values_by_field.get(n, [])) for n in list_field_names]
        if len(set(lengths)) != 1:
            logger.info("Scan configuration error: list fields have different lengths")
            for n in list_field_names:
                logger.info(f"found {n}: {len(values_by_field.get(n, []))}")
            return []

        n = lengths[0]
        items: List[dict] = []
        for i in range(n):
            item = {}
            for name in field_names:
                v = values_by_field.get(name)
                item[name] = v[i] if isinstance(v, list) else v
            items.append(item)
        return items

    def search__snippets(self, _config: dict, _reference_document_content: str, _magic_variables: dict) -> List[dict]:
        """
        Search snippets from api reference document
        Need to extract sections from files
        """

        snippets_elements = []

        values_by_field = {}
        for snippet_field in self.SNIPPET_FIELDS:
            values_by_field[snippet_field["name"]] = self._get_field_value(
                _config=_config,
                field_name=snippet_field["name"],
                field_type=snippet_field["type"],
                text=_reference_document_content,
                _magic_variables=_magic_variables,
            )
        snippets_elements = ArtifactsScanner._combine_fields_to_work_items(
            field_specs=self.SNIPPET_FIELDS, values_by_field=values_by_field
        )

        # logger.info(f"Snippet elements: {snippets_elements}")
        snippets = []
        for snippet_element in snippets_elements:
            if isinstance(snippet_element.get("section", {}), dict):
                snippets.append(
                    {
                        "section": snippet_element.get("section", {}).get("text", ""),
                        "__offset__": snippet_element.get("section", {}).get("index", 99999),
                        "offset": snippet_element.get("offset", "__offset__"),
                    }
                )
            else:
                snippets.append(
                    {
                        "section": snippet_element.get("section", ""),
                        "__offset__": _reference_document_content.find(snippet_element.get("section", "")),
                        "offset": snippet_element.get("offset", "__offset__"),
                    }
                )

        # replace template variables in snippets
        for snippet in snippets:
            if snippet.get("offset", None) is not None:
                if snippet.get("offset") == "__offset__":
                    snippet["offset"] = snippet.get("__offset__", 99999)

        logger.info(f"Snippets: {len(snippets)}")
        return snippets

    def format_new_item_value(self, item: dict, work_item_types: dict, field_name: str) -> str:
        """In case of dict, we are extracting sections from text, so we need to get the text value
        and format it based on the expected output"""

        # logger.info(f"format_new_item: {item}")
        if item.get(field_name, None) is None:
            raise ValueError(f"Field {field_name} is not found in item {item}")

        if isinstance(item.get(field_name), dict):
            if [x for x in work_item_types if x.get("name") == field_name][0].get("type") == "str":
                return item.get(field_name).get("text", "")
            elif [x for x in work_item_types if x.get("name") == field_name][0].get("type") == "int":
                return int(item.get(field_name).get("text", ""))
            else:
                raise ValueError(f"Unsupported field type for {field_name}: {type(work_item_types.get(field_name))}")
        else:
            # For constant string values, allow late substitution of magic variables
            value = item.get(field_name)
            if isinstance(value, str):
                # Perform magic variable replacement now, so variables set during enumeration are applied
                # Note: We do not mutate the original value stored in the item
                try:
                    for mk, mv in list(getattr(self, "_ArtifactsScanner__magic_vars_for_format", {}).items()):
                        value = value.replace(mk, str(mv))
                except Exception:
                    # Be tolerant to unexpected issues during replacement
                    pass
            return value

    def search__justifications(self, _config: dict, _magic_variables: dict) -> List[dict]:
        """
        Search justifications from api reference document snippet
        Need to extract sections from files
        """

        def extract_justification_values(rule_config: dict, file_content: str, _magic_variables: dict):
            justifications_elements = []

            values_by_field = {}
            for justification_field in self.JUSTIFICATION_FIELDS:
                values_by_field[justification_field["name"]] = self._get_field_value(
                    _config=rule_config,
                    field_name=justification_field["name"],
                    field_type=justification_field["type"],
                    text=file_content,
                    _magic_variables=_magic_variables,
                )
            # Apply rule-level top/bottom skipping uniformly to all list fields
            wl_skip_top = rule_config.get("skip_top_items", 0)
            wl_skip_bottom = rule_config.get("skip_bottom_items", 0)
            if (isinstance(wl_skip_top, int) and wl_skip_top > 0) or (
                isinstance(wl_skip_bottom, int) and wl_skip_bottom > 0
            ):
                _ts_tmp = TextScanner(text="")
                for _k, _v in list(values_by_field.items()):
                    if isinstance(_v, list):
                        if _v and isinstance(_v[0], dict):
                            values_by_field[_k] = _ts_tmp._skip_items(
                                elements=_v,
                                skip_top_items=int(wl_skip_top) if isinstance(wl_skip_top, int) else 0,
                                skip_bottom_items=int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0,
                            )
                        else:
                            _start = int(wl_skip_top) if isinstance(wl_skip_top, int) else 0
                            _end_trim = int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0
                            values_by_field[_k] = _v[_start: len(_v) - _end_trim if _end_trim > 0 else None]
            justifications_elements = ArtifactsScanner._combine_fields_to_work_items(
                field_specs=self.JUSTIFICATION_FIELDS, values_by_field=values_by_field
            )

            justifications = []
            for justification_element in justifications_elements:

                new_item_description = self.format_new_item_value(
                    item=justification_element, work_item_types=self.JUSTIFICATION_FIELDS, field_name="description"
                )

                new_item_coverage = self.format_new_item_value(
                    item=justification_element, work_item_types=self.JUSTIFICATION_FIELDS, field_name="coverage"
                )

                justifications.append(
                    {
                        "description": new_item_description,
                        "coverage": new_item_coverage,
                    }
                )

            return justifications

        # ------------------------------------------------------------
        ret = []
        for rule_config in _config.get("rules", []):
            logger.info(f"  - Justification Rule: {rule_config.get('name', '')}")
            repository_config = rule_config.get("repository", None)

            if not repository_config:
                logger.info(f"  - Justification Rule: {rule_config} do not have `repository` key")
                # extract work item in case of constant values

                # Remove file related magic variables
                _magic_variables.pop("__file__", None)
                _magic_variables.pop("__file_relative_path__", None)
                _magic_variables.pop("__file_content__", None)

                justifications = extract_justification_values(
                    rule_config=rule_config, file_content="", _magic_variables=_magic_variables
                )
                if justifications:
                    ret += justifications
                continue

            repo_scanner = RepoScanner(user_id=self.user_id, _config=repository_config)
            repo_scanner.clone_to_user_temp()

            justification_files = self.search__get_files(
                repo_scanner=repo_scanner, _config=repository_config, _magic_variables=_magic_variables
            )
            if justification_files:
                for justification_file in justification_files:
                    justification_file_content = FilesScanner.get_file_content(
                        filepath=os.path.join(repo_scanner.target_dir, justification_file)
                    )

                    # Update magic variables with current file information
                    _magic_variables["__file__"] = justification_file
                    _magic_variables["__file_relative_path__"] = justification_file.replace(
                        repo_scanner.target_dir, ""
                    ).lstrip("/")
                    _magic_variables["__file_content__"] = justification_file_content

                    justifications = extract_justification_values(
                        rule_config=rule_config,
                        file_content=justification_file_content,
                        _magic_variables=_magic_variables,
                    )

                    if justifications:
                        ret += justifications
        return ret

    def search__documents(self, _config: dict, _magic_variables: dict) -> List[dict]:
        """
        Search documents from api reference document snippet
        Need to extract sections from files
        """

        def extract_documents_values(rule_config: dict, file_content: str, _magic_variables: dict):
            documents_elements = []

            values_by_field = {}
            for document_field in self.DOCUMENT_FIELDS:
                values_by_field[document_field["name"]] = self._get_field_value(
                    _config=rule_config,
                    field_name=document_field["name"],
                    field_type=document_field["type"],
                    text=file_content,
                    _magic_variables=_magic_variables,
                )
            # Apply rule-level top/bottom skipping uniformly to all list fields
            wl_skip_top = rule_config.get("skip_top_items", 0)
            wl_skip_bottom = rule_config.get("skip_bottom_items", 0)
            if (isinstance(wl_skip_top, int) and wl_skip_top > 0) or (
                isinstance(wl_skip_bottom, int) and wl_skip_bottom > 0
            ):
                _ts_tmp = TextScanner(text="")
                for _k, _v in list(values_by_field.items()):
                    if isinstance(_v, list):
                        if _v and isinstance(_v[0], dict):
                            values_by_field[_k] = _ts_tmp._skip_items(
                                elements=_v,
                                skip_top_items=int(wl_skip_top) if isinstance(wl_skip_top, int) else 0,
                                skip_bottom_items=int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0,
                            )
                        else:
                            _start = int(wl_skip_top) if isinstance(wl_skip_top, int) else 0
                            _end_trim = int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0
                            values_by_field[_k] = _v[_start: len(_v) - _end_trim if _end_trim > 0 else None]
            documents_elements = ArtifactsScanner._combine_fields_to_work_items(
                field_specs=self.DOCUMENT_FIELDS, values_by_field=values_by_field
            )

            documents = []
            for document_element in documents_elements:
                new_item_title = self.format_new_item_value(
                    item=document_element, work_item_types=self.DOCUMENT_FIELDS, field_name="title"
                )

                new_item_description = self.format_new_item_value(
                    item=document_element, work_item_types=self.DOCUMENT_FIELDS, field_name="description"
                )

                new_item_document_type = self.format_new_item_value(
                    item=document_element, work_item_types=self.DOCUMENT_FIELDS, field_name="document_type"
                )

                new_item_spdx_relation = self.format_new_item_value(
                    item=document_element, work_item_types=self.DOCUMENT_FIELDS, field_name="spdx_relation"
                )

                new_item_url = self.format_new_item_value(
                    item=document_element, work_item_types=self.DOCUMENT_FIELDS, field_name="url"
                )

                new_item_coverage = self.format_new_item_value(
                    item=document_element, work_item_types=self.DOCUMENT_FIELDS, field_name="coverage"
                )

                documents.append(
                    {
                        "title": new_item_title,
                        "description": new_item_description,
                        "document_type": new_item_document_type,
                        "spdx_relation": new_item_spdx_relation,
                        "url": new_item_url,
                        "coverage": new_item_coverage,
                        "documents": [],
                    }
                )
            return documents

        # ------------------------------------------------------------
        ret = []
        for rule_config in _config.get("rules", []):
            logger.info(f"  - Document Rule: {rule_config.get('name', '')}")
            repository_config = rule_config.get("repository", None)

            # Precompute nested documents (if any) once per rule to attach to each produced document
            nested_documents_config = rule_config.get("documents", {})
            nested_documents = []
            if isinstance(nested_documents_config, dict) and nested_documents_config.get("rules"):
                nested_documents = (
                    self.search__documents(_config=nested_documents_config, _magic_variables=_magic_variables) or []
                )

            if not repository_config:
                logger.info(f"  - Document Rule: {rule_config} do not have `repository` key")
                # extract work item in case of constant values

                # Remove file related magic variables
                _magic_variables.pop("__file__", None)
                _magic_variables.pop("__file_relative_path__", None)
                _magic_variables.pop("__file_content__", None)

                documents = extract_documents_values(
                    rule_config=rule_config, file_content="", _magic_variables=_magic_variables
                )
                if documents and nested_documents:
                    for d in documents:
                        d.setdefault("documents", [])
                        d["documents"] += nested_documents
                if documents:
                    ret += documents
                continue

            repo_scanner = RepoScanner(user_id=self.user_id, _config=repository_config)
            repo_scanner.clone_to_user_temp()

            document_files = self.search__get_files(
                repo_scanner=repo_scanner, _config=repository_config, _magic_variables=_magic_variables
            )
            if document_files:
                for document_file in document_files:
                    document_file_content = FilesScanner.get_file_content(
                        filepath=os.path.join(repo_scanner.target_dir, document_file)
                    )

                    # Update magic variables with current file information
                    _magic_variables["__file__"] = document_file
                    _magic_variables["__file_relative_path__"] = document_file.replace(
                        repo_scanner.target_dir, ""
                    ).lstrip("/")
                    _magic_variables["__file_content__"] = document_file_content

                    documents = extract_documents_values(
                        rule_config=rule_config, file_content=document_file_content, _magic_variables=_magic_variables
                    )

                    if documents and nested_documents:
                        for d in documents:
                            d.setdefault("documents", [])
                            d["documents"] += nested_documents

                    if documents:
                        ret += documents
        return ret

    def search__software_requirements(self, _config: dict, _magic_variables: dict) -> List[dict]:
        """
        Search software requirements from api reference document snippet
        Need to extract sections from files
        """

        def extract_software_requirements_values(rule_config: dict, file_content: str, _magic_variables: dict):
            software_requirements_elements = []

            values_by_field = {}
            for software_requirement_field in self.SOFTWARE_REQUIREMENT_FIELDS:
                values_by_field[software_requirement_field["name"]] = self._get_field_value(
                    _config=rule_config,
                    field_name=software_requirement_field["name"],
                    field_type=software_requirement_field["type"],
                    text=file_content,
                    _magic_variables=_magic_variables,
                )
            # Apply rule-level top/bottom skipping uniformly to all list fields
            wl_skip_top = rule_config.get("skip_top_items", 0)
            wl_skip_bottom = rule_config.get("skip_bottom_items", 0)
            if (isinstance(wl_skip_top, int) and wl_skip_top > 0) or (
                isinstance(wl_skip_bottom, int) and wl_skip_bottom > 0
            ):
                _ts_tmp = TextScanner(text="")
                for _k, _v in list(values_by_field.items()):
                    if isinstance(_v, list):
                        if _v and isinstance(_v[0], dict):
                            values_by_field[_k] = _ts_tmp._skip_items(
                                elements=_v,
                                skip_top_items=int(wl_skip_top) if isinstance(wl_skip_top, int) else 0,
                                skip_bottom_items=int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0,
                            )
                        else:
                            _start = int(wl_skip_top) if isinstance(wl_skip_top, int) else 0
                            _end_trim = int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0
                            values_by_field[_k] = _v[_start: len(_v) - _end_trim if _end_trim > 0 else None]
            software_requirements_elements = ArtifactsScanner._combine_fields_to_work_items(
                field_specs=self.SOFTWARE_REQUIREMENT_FIELDS, values_by_field=values_by_field
            )

            software_requirements = []
            for index, software_requirement_element in enumerate(software_requirements_elements):

                _magic_variables["__software_requirement_index__"] = index
                # Expose current magic variables for late substitution during formatting
                try:
                    self._ArtifactsScanner__magic_vars_for_format = dict(_magic_variables)
                except Exception:
                    self._ArtifactsScanner__magic_vars_for_format = {}

                new_item_title = self.format_new_item_value(
                    item=software_requirement_element,
                    work_item_types=self.SOFTWARE_REQUIREMENT_FIELDS,
                    field_name="title",
                )

                new_item_description = self.format_new_item_value(
                    item=software_requirement_element,
                    work_item_types=self.SOFTWARE_REQUIREMENT_FIELDS,
                    field_name="description",
                )

                new_item_coverage = self.format_new_item_value(
                    item=software_requirement_element,
                    work_item_types=self.SOFTWARE_REQUIREMENT_FIELDS,
                    field_name="coverage",
                )

                software_requirements.append(
                    {
                        "title": new_item_title,
                        "description": new_item_description,
                        "coverage": new_item_coverage,
                        "software_requirements": [],
                        "test_specifications": [],
                        "test_cases": [],
                    }
                )
            return software_requirements

        # ------------------------------------------------------------
        ret = []
        for rule_config in _config.get("rules", []):
            logger.info(f"  - Software Requirement Rule: {rule_config.get('name', '')}")
            repository_config = rule_config.get("repository", None)

            # Nested configs
            nested_sw_reqs_config = rule_config.get("software_requirements", {})
            nested_test_specs_config = rule_config.get("test_specifications", {})
            nested_test_cases_config = rule_config.get("test_cases", {})

            if not repository_config:
                logger.info(f"  - Software Requirement Rule: {rule_config} do not have `repository` key")
                # extract work item in case of constant values

                # Remove file related magic variables
                _magic_variables.pop("__file__", None)
                _magic_variables.pop("__file_relative_path__", None)
                _magic_variables.pop("__file_content__", None)

                software_requirements = extract_software_requirements_values(
                    rule_config=rule_config, file_content="", _magic_variables=_magic_variables
                )
                # Compute nested using current (non-file) magic variables
                nested_sw_reqs = []
                if isinstance(nested_sw_reqs_config, dict) and nested_sw_reqs_config.get("rules"):
                    nested_sw_reqs = (
                        self.search__software_requirements(
                            _config=nested_sw_reqs_config, _magic_variables=_magic_variables
                        )
                        or []
                    )
                nested_test_specs = []
                if isinstance(nested_test_specs_config, dict) and nested_test_specs_config.get("rules"):
                    nested_test_specs = (
                        self.search__test_specifications(
                            _config=nested_test_specs_config, _magic_variables=_magic_variables
                        )
                        or []
                    )
                nested_test_cases = []
                if isinstance(nested_test_cases_config, dict) and nested_test_cases_config.get("rules"):
                    nested_test_cases = (
                        self.search__test_cases(_config=nested_test_cases_config, _magic_variables=_magic_variables)
                        or []
                    )
                if software_requirements and nested_sw_reqs:
                    for s in software_requirements:
                        s.setdefault("software_requirements", [])
                        s["software_requirements"] += nested_sw_reqs
                if software_requirements and nested_test_specs:
                    for s in software_requirements:
                        s.setdefault("test_specifications", [])
                        s["test_specifications"] += nested_test_specs
                if software_requirements and nested_test_cases:
                    for s in software_requirements:
                        s.setdefault("test_cases", [])
                        s["test_cases"] += nested_test_cases
                if software_requirements:
                    ret += software_requirements
                logger.info(" ---> here")
                continue

            repo_scanner = RepoScanner(user_id=self.user_id, _config=repository_config)
            repo_scanner.clone_to_user_temp()

            software_requirements_files = self.search__get_files(
                repo_scanner=repo_scanner, _config=repository_config, _magic_variables=_magic_variables
            )
            if software_requirements_files:
                for software_requirements_file in software_requirements_files:
                    logger.info(f"  - Software Requirements File: {software_requirements_file}")
                    software_requirements_file_content = FilesScanner.get_file_content(
                        filepath=os.path.join(repo_scanner.target_dir, software_requirements_file)
                    )

                    # Update magic variables with current file information
                    _magic_variables["__file__"] = software_requirements_file
                    _magic_variables["__file_relative_path__"] = software_requirements_file.replace(
                        repo_scanner.target_dir, ""
                    ).lstrip("/")
                    _magic_variables["__file_content__"] = software_requirements_file_content

                    # Compute nested using current file-level magic variables
                    nested_sw_reqs = []
                    if isinstance(nested_sw_reqs_config, dict) and nested_sw_reqs_config.get("rules"):
                        nested_sw_reqs = (
                            self.search__software_requirements(
                                _config=nested_sw_reqs_config, _magic_variables=_magic_variables
                            )
                            or []
                        )
                    nested_test_specs = []
                    if isinstance(nested_test_specs_config, dict) and nested_test_specs_config.get("rules"):
                        nested_test_specs = (
                            self.search__test_specifications(
                                _config=nested_test_specs_config, _magic_variables=_magic_variables
                            )
                            or []
                        )
                    nested_test_cases = []
                    if isinstance(nested_test_cases_config, dict) and nested_test_cases_config.get("rules"):
                        nested_test_cases = (
                            self.search__test_cases(
                                _config=nested_test_cases_config, _magic_variables=_magic_variables
                            )
                            or []
                        )

                    software_requirements = extract_software_requirements_values(
                        rule_config=rule_config,
                        file_content=software_requirements_file_content,
                        _magic_variables=_magic_variables,
                    )

                    logger.info(f"  - Software Requirements: {software_requirements}")

                    if software_requirements and nested_sw_reqs:
                        for s in software_requirements:
                            s.setdefault("software_requirements", [])
                            s["software_requirements"] += nested_sw_reqs
                    if software_requirements and nested_test_specs:
                        for s in software_requirements:
                            s.setdefault("test_specifications", [])
                            s["test_specifications"] += nested_test_specs
                    if software_requirements and nested_test_cases:
                        for s in software_requirements:
                            s.setdefault("test_cases", [])
                            s["test_cases"] += nested_test_cases

                    if software_requirements:
                        ret += software_requirements
            else:
                logger.info("No software requirements files found")
        return ret

    def search__test_specifications(self, _config: dict, _magic_variables: dict) -> List[dict]:
        """
        Search test specifications from api reference document snippet
        Need to extract sections from files
        """

        def extract_test_specifications_values(rule_config: dict, file_content: str, _magic_variables: dict):
            test_specifications_elements = []

            values_by_field = {}
            for test_specification_field in self.TEST_SPECIFICATION_FIELDS:
                values_by_field[test_specification_field["name"]] = self._get_field_value(
                    _config=rule_config,
                    field_name=test_specification_field["name"],
                    field_type=test_specification_field["type"],
                    text=file_content,
                    _magic_variables=_magic_variables,
                )
            # Apply rule-level top/bottom skipping uniformly to all list fields
            wl_skip_top = rule_config.get("skip_top_items", 0)
            wl_skip_bottom = rule_config.get("skip_bottom_items", 0)
            if (isinstance(wl_skip_top, int) and wl_skip_top > 0) or (
                isinstance(wl_skip_bottom, int) and wl_skip_bottom > 0
            ):
                _ts_tmp = TextScanner(text="")
                for _k, _v in list(values_by_field.items()):
                    if isinstance(_v, list):
                        if _v and isinstance(_v[0], dict):
                            values_by_field[_k] = _ts_tmp._skip_items(
                                elements=_v,
                                skip_top_items=int(wl_skip_top) if isinstance(wl_skip_top, int) else 0,
                                skip_bottom_items=int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0,
                            )
                        else:
                            _start = int(wl_skip_top) if isinstance(wl_skip_top, int) else 0
                            _end_trim = int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0
                            values_by_field[_k] = _v[_start: len(_v) - _end_trim if _end_trim > 0 else None]
            test_specifications_elements = ArtifactsScanner._combine_fields_to_work_items(
                field_specs=self.TEST_SPECIFICATION_FIELDS, values_by_field=values_by_field
            )

            test_specifications = []
            for test_specification_element in test_specifications_elements:

                new_item_title = self.format_new_item_value(
                    item=test_specification_element, work_item_types=self.TEST_SPECIFICATION_FIELDS, field_name="title"
                )

                new_item_description = self.format_new_item_value(
                    item=test_specification_element,
                    work_item_types=self.TEST_SPECIFICATION_FIELDS,
                    field_name="test_description",
                )

                new_item_expected_behavior = self.format_new_item_value(
                    item=test_specification_element,
                    work_item_types=self.TEST_SPECIFICATION_FIELDS,
                    field_name="expected_behavior",
                )

                new_item_preconditions = self.format_new_item_value(
                    item=test_specification_element,
                    work_item_types=self.TEST_SPECIFICATION_FIELDS,
                    field_name="preconditions",
                )

                new_item_coverage = self.format_new_item_value(
                    item=test_specification_element,
                    work_item_types=self.TEST_SPECIFICATION_FIELDS,
                    field_name="coverage",
                )

                test_specifications.append(
                    {
                        "title": new_item_title,
                        "test_description": new_item_description,
                        "expected_behavior": new_item_expected_behavior,
                        "preconditions": new_item_preconditions,
                        "coverage": new_item_coverage,
                    }
                )
            return test_specifications

        # ------------------------------------------------------------
        ret = []
        for rule_config in _config.get("rules", []):
            logger.info(f"  - Test Specification Rule: {rule_config.get('name', '')}")
            repository_config = rule_config.get("repository", None)

            if not repository_config:
                logger.info(f"  - Test Specification Rule: {rule_config} do not have `repository` key")
                # extract work item in case of constant values

                # Remove file related magic variables
                _magic_variables.pop("__file__", None)
                _magic_variables.pop("__file_relative_path__", None)
                _magic_variables.pop("__file_content__", None)

                test_specifications = extract_test_specifications_values(
                    rule_config=rule_config, file_content="", _magic_variables=_magic_variables
                )
                if test_specifications:
                    ret += test_specifications
                continue

            repo_scanner = RepoScanner(user_id=self.user_id, _config=repository_config)
            repo_scanner.clone_to_user_temp()

            test_specifications_files = self.search__get_files(
                repo_scanner=repo_scanner, _config=repository_config, _magic_variables=_magic_variables
            )
            if test_specifications_files:
                for test_specifications_file in test_specifications_files:
                    test_specifications_file_content = FilesScanner.get_file_content(
                        filepath=os.path.join(repo_scanner.target_dir, test_specifications_file)
                    )

                    # Update magic variables with current file information
                    _magic_variables["__file__"] = test_specifications_file
                    _magic_variables["__file_relative_path__"] = test_specifications_file.replace(
                        repo_scanner.target_dir, ""
                    ).lstrip("/")
                    _magic_variables["__file_content__"] = test_specifications_file_content

                    test_specifications = extract_test_specifications_values(
                        rule_config=rule_config,
                        file_content=test_specifications_file_content,
                        _magic_variables=_magic_variables,
                    )

                    if test_specifications:
                        ret += test_specifications
        return ret

    def search__test_cases(self, _config: dict, _magic_variables: dict) -> List[dict]:
        """
        Search test cases from api reference document snippet
        Need to extract sections from files
        """

        def extract_test_cases_values(
            rule_config: dict,
            repository_config: dict,
            file_relative_path: str,
            file_content: str,
            _magic_variables: dict,
        ):
            test_cases_elements = []

            values_by_field = {}
            for test_case_field in self.TEST_CASE_FIELDS:
                values_by_field[test_case_field["name"]] = self._get_field_value(
                    _config=rule_config,
                    field_name=test_case_field["name"],
                    field_type=test_case_field["type"],
                    text=file_content,
                    _magic_variables=_magic_variables,
                )
            # Apply rule-level top/bottom skipping uniformly to all list fields
            wl_skip_top = rule_config.get("skip_top_items", 0)
            wl_skip_bottom = rule_config.get("skip_bottom_items", 0)
            if (isinstance(wl_skip_top, int) and wl_skip_top > 0) or (
                isinstance(wl_skip_bottom, int) and wl_skip_bottom > 0
            ):
                _ts_tmp = TextScanner(text="")
                for _k, _v in list(values_by_field.items()):
                    if isinstance(_v, list):
                        if _v and isinstance(_v[0], dict):
                            values_by_field[_k] = _ts_tmp._skip_items(
                                elements=_v,
                                skip_top_items=int(wl_skip_top) if isinstance(wl_skip_top, int) else 0,
                                skip_bottom_items=int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0,
                            )
                        else:
                            _start = int(wl_skip_top) if isinstance(wl_skip_top, int) else 0
                            _end_trim = int(wl_skip_bottom) if isinstance(wl_skip_bottom, int) else 0
                            values_by_field[_k] = _v[_start: len(_v) - _end_trim if _end_trim > 0 else None]
            test_cases_elements = ArtifactsScanner._combine_fields_to_work_items(
                field_specs=self.TEST_CASE_FIELDS, values_by_field=values_by_field
            )

            test_cases = []
            for test_case_element in test_cases_elements:

                new_item_title = self.format_new_item_value(
                    item=test_case_element, work_item_types=self.TEST_CASE_FIELDS, field_name="title"
                )

                new_item_description = self.format_new_item_value(
                    item=test_case_element, work_item_types=self.TEST_CASE_FIELDS, field_name="description"
                )

                new_item_coverage = self.format_new_item_value(
                    item=test_case_element, work_item_types=self.TEST_CASE_FIELDS, field_name="coverage"
                )

                test_cases.append(
                    {
                        "title": new_item_title,
                        "description": new_item_description,
                        "repository": repository_config.get("url", ""),
                        "relative_path": file_relative_path,
                        "coverage": new_item_coverage,
                    }
                )
            return test_cases

        # ------------------------------------------------------------
        ret = []
        for rule_config in _config.get("rules", []):
            logger.info(f"  - Test Case Rule: {rule_config.get('name', '')}")
            repository_config = rule_config.get("repository", None)

            if not repository_config:
                # Mandatory for Test Cases
                logger.info(f"  - Test Case Rule: {rule_config} do not have `repository` key")
                continue

            repo_scanner = RepoScanner(user_id=self.user_id, _config=repository_config)
            repo_scanner.clone_to_user_temp()

            test_cases_files = self.search__get_files(
                repo_scanner=repo_scanner, _config=repository_config, _magic_variables=_magic_variables
            )
            if test_cases_files:
                for test_cases_file in test_cases_files:
                    test_cases_file_content = FilesScanner.get_file_content(
                        filepath=os.path.join(repo_scanner.target_dir, test_cases_file)
                    )

                    # Update magic variables with current file information
                    _magic_variables["__file__"] = test_cases_file
                    _magic_variables["__file_relative_path__"] = test_cases_file.replace(
                        repo_scanner.target_dir, ""
                    ).lstrip("/")
                    _magic_variables["__file_content__"] = test_cases_file_content

                    test_cases = extract_test_cases_values(
                        rule_config=rule_config,
                        repository_config=repository_config,
                        file_relative_path=test_cases_file.replace(repo_scanner.target_dir, "").lstrip("/"),
                        file_content=test_cases_file_content,
                        _magic_variables=_magic_variables,
                    )

                    if test_cases:
                        ret += test_cases
        return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Artifacts Repo Scanner")
    parser.add_argument("--userid", type=int, required=True, help="User ID (e.g., --userid 323)")
    parser.add_argument(
        "--logfile", type=str, required=False, help="Log file name (e.g., --logfile 20251115_120000.log)"
    )
    args = parser.parse_args()

    # Scan user configuration file
    user_config_path = os.path.join(USER_FILES_BASE_DIR, f"{args.userid}.config")
    if not os.path.exists(user_config_path):
        os.makedirs(os.path.dirname(user_config_path), exist_ok=True)

    scan_config_path = os.path.join(user_config_path, "config.yaml")

    with open(scan_config_path, "r") as f:
        scan_config = yaml.safe_load(f) or {}

    # Update the logger to write to a file under USER_FILES_BASE_DIR
    # Use timestamp as name of the log file
    if not args.logfile:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logfile = os.path.join(user_config_path, f"{args.userid}_{timestamp}.log")
    else:
        logfile = os.path.join(user_config_path, args.logfile)

    logger.handlers = []
    logger.addHandler(logging.FileHandler(logfile))
    logger.setLevel(logging.INFO)

    scanner = ArtifactsScanner(user_id=args.userid, api="test", scan_config=scan_config)
    traceability = scanner.scan()
    generator = TraceabilityGenerator(traceability=traceability, user_id=args.userid, logfile=logfile)
    generator.generate()
