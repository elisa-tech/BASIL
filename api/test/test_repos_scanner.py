import pytest

from repos_scanner import RepoScanner

TEST_TEXT = "A\n\n  B\nC"

# ------------------------------------------------------------
# start__lines_starting_with
# ------------------------------------------------------------


def test_start__lines_starting_with_empty_elements_defaults():
    scanner = RepoScanner()
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="  b")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_starting_with_empty_elements_strip_true():
    scanner = RepoScanner()
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="B", strip=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_starting_with_empty_elements_case_sensitive_true():
    scanner = RepoScanner()
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="  B", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_starting_with_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = RepoScanner()
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=elements, match_string="C")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_starting_with_empty_elements_defaults_no_match():
    scanner = RepoScanner()
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="B")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == []


# ------------------------------------------------------------
# start__lines_ending_with
# ------------------------------------------------------------
def test_start__lines_ending_with_empty_elements_defaults():
    scanner = RepoScanner()
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="C")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_ending_with_empty_elements_strip_true():
    scanner = RepoScanner()
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="b", strip=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_ending_with_empty_elements_case_sensitive_true():
    scanner = RepoScanner()
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="B", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_ending_with_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = RepoScanner()
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=elements, match_string="B")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_ending_with_empty_elements_defaults_no_match():
    scanner = RepoScanner()
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="Z", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == []


# ------------------------------------------------------------
# start__lines_containing
# ------------------------------------------------------------


def test_start__lines_containing_empty_elements_defaults():
    scanner = RepoScanner()
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=[], match_string="b")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_containing_empty_elements_case_sensitive_true():
    scanner = RepoScanner()
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=[], match_string="B", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        }
    ]


def test_start__lines_containing_not_empty_elements():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = RepoScanner()
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=elements, match_string="b")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_containing_empty_elements_no_match():
    scanner = RepoScanner()
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=[], match_string="Z", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == []


# ------------------------------------------------------------
# start__lines_not_containing
# ------------------------------------------------------------


def test_start__lines_not_containing_empty_elements_defaults():
    scanner = RepoScanner()
    result = scanner.start__lines_not_containing(text=TEST_TEXT, elements=[], match_string="b")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 0,
            "text": "A\n\n  B\nC",
        },
        {
            "index": 1,
            "text": "\n  B\nC",
        },
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_not_containing_empty_elements_case_sensitive_true():
    scanner = RepoScanner()
    result = scanner.start__lines_not_containing(text=TEST_TEXT, elements=[], match_string="B", case_sensitive=True)

    f = open("result.txt", "w")
    f.write(f"{result}")
    f.close()

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 0,
            "text": "A\n\n  B\nC",
        },
        {
            "index": 1,
            "text": "\n  B\nC",
        },
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_not_containing_not_empty_elements():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = RepoScanner()
    result = scanner.start__lines_not_containing(text=TEST_TEXT, elements=elements, match_string="b")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 3,
            "text": "C",
        },
    ]


# ------------------------------------------------------------
# start__lines_equal
# ------------------------------------------------------------
def test_start__lines_equal_empty_elements_defaults():
    scanner = RepoScanner()
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="C")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_equal_empty_elements_strip_true():
    scanner = RepoScanner()
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="b", strip=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_equal_empty_elements_case_sensitive_true():
    scanner = RepoScanner()
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="  B", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_equal_not_empty_elements():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = RepoScanner()
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=elements, match_string="  B")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_equal_empty_elements_no_match():
    scanner = RepoScanner()
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="Z", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == []


# ------------------------------------------------------------
# _remove_empty_lines
# ------------------------------------------------------------
def test_remove_empty_lines():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 1, "text": "\n  B\nC"}, {"index": 3, "text": "C"}]
    scanner = RepoScanner()
    result = scanner._remove_empty_lines(elements=elements)

    assert result == [{"index": 0, "text": "A\n  B\nC"}, {"index": 1, "text": "  B\nC"}, {"index": 3, "text": "C"}]


# ------------------------------------------------------------
# _extend_content_of_elements
# ------------------------------------------------------------
def test_extend_content_of_elements_up():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = RepoScanner()
    result = scanner._extend_content_of_elements(direction="up", count=1, text=TEST_TEXT, elements=elements)

    assert result == [
        {"index": 0, "text": "A\n\n  B\nC"},
        {"index": 1, "text": "\n  B\nC"},
        {"index": 2, "text": "  B\nC"},
    ]


# ------------------------------------------------------------
# closest__lines_starting_with
# ------------------------------------------------------------
def test_closest__lines_starting_with_empty_elements_defaults():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = RepoScanner()
    result = scanner.closest__lines_starting_with(text=TEST_TEXT, elements=elements, match_string="a")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 0,
            "text": TEST_TEXT,
        },
    ]


def test_closest__lines_starting_with_empty_elements_defaults_2():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = RepoScanner()
    result = scanner.closest__lines_starting_with(text=TEST_TEXT, elements=elements, match_string="  b")
    f = open("closest__lines_starting_with.txt", "a")
    f.write(f"result: {result}\n")
    f.close()
    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_closest__lines_starting_with_empty_elements_defaults_3():
    text = "A\nA\nA\n  B\nB\nC"
    elements = [{"index": 2, "text": "A\n  B\nC"}, {"index": 3, "text": "  B"}, {"index": 5, "text": "C"}]
    scanner = RepoScanner()
    result = scanner.closest__lines_starting_with(text=text, elements=elements, match_string="a")
    f = open("closest__lines_starting_with.txt", "a")
    f.write(f"result: {result}\n")
    f.close()
    assert "text" in result and result["text"] == text
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "A\n  B\nB\nC",
        },
    ]


# ------------------------------------------------------------
# start__lines_regex
# ------------------------------------------------------------
def test_start__lines_regex_empty_elements_defaults():
    scanner = RepoScanner()
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^\s*b")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_regex_empty_elements_case_sensitive_true():
    scanner = RepoScanner()
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^\s*B", case_sensitive=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_regex_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = RepoScanner()
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^C$")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_regex_empty_elements_defaults_no_match():
    scanner = RepoScanner()
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^Z$")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == []


# ------------------------------------------------------------
# end__lines_regex
# ------------------------------------------------------------
def test_end__lines_regex_empty_elements_defaults():
    scanner = RepoScanner()
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^C$")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 0,
            "text": "A\n\n  B",
        },
    ]


def test_end__lines_regex_empty_elements_strip_true():
    scanner = RepoScanner()
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^b$", strip=True)

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 0,
            "text": "A\n",
        },
    ]


def test_end__lines_regex_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = RepoScanner()
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^C$")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B",
        },
    ]


def test_end__lines_regex_empty_elements_defaults_no_match():
    scanner = RepoScanner()
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^Z$")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == []


# ------------------------------------------------------------
# closest__lines_regex
# ------------------------------------------------------------
def test_closest__lines_regex_empty_elements_defaults():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = RepoScanner()
    result = scanner.closest__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^[a]")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 0,
            "text": TEST_TEXT,
        },
    ]


def test_closest__lines_regex_empty_elements_defaults_2():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = RepoScanner()
    result = scanner.closest__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^\s+b")

    assert "text" in result and result["text"] == TEST_TEXT
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_closest__lines_regex_multiple_matches():
    text = "A\nA\nA\n  B\nB\nC"
    elements = [{"index": 2, "text": "A\n  B\nC"}, {"index": 3, "text": "  B"}, {"index": 5, "text": "C"}]
    scanner = RepoScanner()
    result = scanner.closest__lines_regex(text=text, elements=elements, match_string=r"^[a]")

    assert "text" in result and result["text"] == text
    assert "elements" in result and isinstance(result["elements"], list)
    assert result["elements"] == [
        {
            "index": 2,
            "text": "A\n  B\nB\nC",
        },
    ]


# ------------------------------------------------------------
# list_files
# ------------------------------------------------------------
def test_list_files():
    scanner = RepoScanner()
    result = scanner.list_files(root_dir=".", include_hidden=False, filename_pattern="*.py", folder_pattern="")
    assert "api/test/test_repos_scanner.py" in result

    result = scanner.list_files(root_dir=".", include_hidden=False, filename_pattern="*.py", folder_pattern="api")
    assert "api/test/test_repos_scanner.py" in result

    result = scanner.list_files(
        root_dir=".", include_hidden=False, filename_pattern="test_repos_scanner.py", folder_pattern=""
    )
    assert result == ["api/test/test_repos_scanner.py"]
