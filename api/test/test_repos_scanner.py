from repos_scanner import RepoScanner, TextScanner, ArtifactsScanner

TEST_TEXT = "A\n\n  B\nC"

# ------------------------------------------------------------
# start__lines_starting_with
# ------------------------------------------------------------


def test_start__lines_starting_with_empty_elements_defaults():
    scanner = TextScanner(text="")
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="  b")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_starting_with_empty_elements_strip_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="B", strip=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_starting_with_empty_elements_case_sensitive_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="  B", case_sensitive=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_starting_with_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = TextScanner(text="")
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=elements, match_string="C")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_starting_with_empty_elements_defaults_no_match():
    scanner = TextScanner(text="")
    result = scanner.start__lines_starting_with(text=TEST_TEXT, elements=[], match_string="B")

    assert isinstance(result, list)
    assert result == []


# ------------------------------------------------------------
# start__lines_ending_with
# ------------------------------------------------------------
def test_start__lines_ending_with_empty_elements_defaults():
    scanner = TextScanner(text="")
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="C")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_ending_with_empty_elements_strip_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="b", strip=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_ending_with_empty_elements_case_sensitive_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="B", case_sensitive=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_ending_with_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = TextScanner(text="")
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=elements, match_string="B")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_ending_with_empty_elements_defaults_no_match():
    scanner = TextScanner(text="")
    result = scanner.start__lines_ending_with(text=TEST_TEXT, elements=[], match_string="Z", case_sensitive=True)

    assert isinstance(result, list)
    assert result == []


# ------------------------------------------------------------
# start__lines_containing
# ------------------------------------------------------------


def test_start__lines_containing_empty_elements_defaults():
    scanner = TextScanner(text="")
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=[], match_string="b")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_containing_empty_elements_case_sensitive_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=[], match_string="B", case_sensitive=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        }
    ]


def test_start__lines_containing_not_empty_elements():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = TextScanner(text="")
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=elements, match_string="b")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_containing_empty_elements_no_match():
    scanner = TextScanner(text="")
    result = scanner.start__lines_containing(text=TEST_TEXT, elements=[], match_string="Z", case_sensitive=True)

    assert isinstance(result, list)
    assert result == []


# ------------------------------------------------------------
# start__lines_not_containing
# ------------------------------------------------------------


def test_start__lines_not_containing_empty_elements_defaults():
    scanner = TextScanner(text="")
    result = scanner.start__lines_not_containing(text=TEST_TEXT, elements=[], match_string="b")

    assert isinstance(result, list)
    assert result == [
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
    scanner = TextScanner(text="")
    result = scanner.start__lines_not_containing(text=TEST_TEXT, elements=[], match_string="B", case_sensitive=True)

    assert isinstance(result, list)
    assert result == [
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
    scanner = TextScanner(text="")
    result = scanner.start__lines_not_containing(text=TEST_TEXT, elements=elements, match_string="b")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 3,
            "text": "C",
        },
    ]


# ------------------------------------------------------------
# start__lines_equal
# ------------------------------------------------------------
def test_start__lines_equal_empty_elements_defaults():
    scanner = TextScanner(text="")
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="C")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_equal_empty_elements_strip_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="b", strip=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_equal_empty_elements_case_sensitive_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="  B", case_sensitive=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_equal_not_empty_elements():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = TextScanner(text="")
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=elements, match_string="  B")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_equal_empty_elements_no_match():
    scanner = TextScanner(text="")
    result = scanner.start__lines_equal(text=TEST_TEXT, elements=[], match_string="Z", case_sensitive=True)

    assert isinstance(result, list)
    assert result == []


# ------------------------------------------------------------
# _extend_content_of_elements
# ------------------------------------------------------------
def test_extend_content_of_elements_up():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = TextScanner(text="")
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
    scanner = TextScanner(text="")
    result = scanner.closest__lines_starting_with(text=TEST_TEXT, elements=elements, match_string="a")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 0,
            "text": TEST_TEXT,
        },
    ]


def test_closest__lines_starting_with_empty_elements_defaults_2():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = TextScanner(text="")
    result = scanner.closest__lines_starting_with(text=TEST_TEXT, elements=elements, match_string="  b")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_closest__lines_starting_with_empty_elements_defaults_3():
    text = "A\nA\nA\n  B\nB\nC"
    elements = [{"index": 2, "text": "A\n  B\nC"}, {"index": 3, "text": "  B"}, {"index": 5, "text": "C"}]
    scanner = TextScanner(text="")
    result = scanner.closest__lines_starting_with(text=text, elements=elements, match_string="a")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "A\n  B\nB\nC",
        },
    ]


# ------------------------------------------------------------
# start__lines_regex
# ------------------------------------------------------------
def test_start__lines_regex_empty_elements_defaults():
    scanner = TextScanner(text="")
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^\s*b")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_regex_empty_elements_case_sensitive_true():
    scanner = TextScanner(text="")
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^\s*B", case_sensitive=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_start__lines_regex_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = TextScanner(text="")
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^C$")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 3,
            "text": "C",
        },
    ]


def test_start__lines_regex_empty_elements_defaults_no_match():
    scanner = TextScanner(text="")
    result = scanner.start__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^Z$")

    assert isinstance(result, list)
    assert result == []


# ------------------------------------------------------------
# end__lines_regex
# ------------------------------------------------------------
def test_end__lines_regex_empty_elements_defaults():
    scanner = TextScanner(text="")
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^C$")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 0,
            "text": "A\n\n  B",
        },
    ]


def test_end__lines_regex_empty_elements_strip_true():
    scanner = TextScanner(text="")
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^b$", strip=True)

    assert isinstance(result, list)
    assert result == [
        {
            "index": 0,
            "text": "A\n",
        },
    ]


def test_end__lines_regex_not_empty_elements_defaults():
    elements = [{"index": 2, "text": "  B\nC"}]
    scanner = TextScanner(text="")
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^C$")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B",
        },
    ]


def test_end__lines_regex_empty_elements_defaults_no_match():
    scanner = TextScanner(text="")
    result = scanner.end__lines_regex(text=TEST_TEXT, elements=[], match_string=r"^Z$")

    assert isinstance(result, list)
    assert result == []


# ------------------------------------------------------------
# closest__lines_regex
# ------------------------------------------------------------
def test_closest__lines_regex_empty_elements_defaults():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = TextScanner(text="")
    result = scanner.closest__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^[a]")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 0,
            "text": TEST_TEXT,
        },
    ]


def test_closest__lines_regex_empty_elements_defaults_2():
    elements = [{"index": 0, "text": "A\n\n  B\nC"}, {"index": 2, "text": "  B\nC"}, {"index": 3, "text": "C"}]
    scanner = TextScanner(text="")
    result = scanner.closest__lines_regex(text=TEST_TEXT, elements=elements, match_string=r"^\s+b")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "  B\nC",
        },
    ]


def test_closest__lines_regex_multiple_matches():
    text = "A\nA\nA\n  B\nB\nC"
    elements = [{"index": 2, "text": "A\n  B\nC"}, {"index": 3, "text": "  B"}, {"index": 5, "text": "C"}]
    scanner = TextScanner(text="")
    result = scanner.closest__lines_regex(text=text, elements=elements, match_string=r"^[a]")

    assert isinstance(result, list)
    assert result == [
        {
            "index": 2,
            "text": "A\n  B\nB\nC",
        },
    ]


# ------------------------------------------------------------
# list_files
# ------------------------------------------------------------
def test_list_files():
    repo_config = {
        "url": "https://github.com/elisa-tech/BASIL.git",
        "branch": "main",
    }
    scanner = RepoScanner(user_id="test", _config=repo_config)
    scanner.clone_to_user_temp()
    result = scanner.list_files(include_hidden=False, filename_pattern="*.py", folder_pattern="")
    assert len([x.endswith("api/api.py") for x in result]) > 0

    result = scanner.list_files(include_hidden=False, filename_pattern="*.py", folder_pattern="api")
    assert len([x.endswith("api/api.py") for x in result]) > 0

    result = scanner.list_files(include_hidden=False, filename_pattern="api.py", folder_pattern="api")
    assert result[0].endswith("api/api.py")


# ------------------------------------------------------------
# _apply_filters_to_elements (ArtifactsScanner)
# ------------------------------------------------------------
def test_apply_filters_contains():
    elements = [{"text": "alpha"}, {"text": "beta"}, {"text": "gamma"}]
    filter_cfg = {"contains": ["et"]}
    out = ArtifactsScanner._apply_filters_to_elements(elements, filter_cfg)
    assert out == [{"text": "beta"}]


def test_apply_filters_not_contains():
    elements = [{"text": "Alpha"}, {"text": "Beta"}, {"text": "Gamma"}]
    filter_cfg = {"not_contains": ["beta"]}  # case-insensitive default
    out = ArtifactsScanner._apply_filters_to_elements(elements, filter_cfg)
    assert out == [{"text": "Alpha"}, {"text": "Gamma"}]


def test_apply_filters_regex():
    elements = [{"text": "keep-123"}, {"text": "drop"}, {"text": "KEEP-999"}]
    filter_cfg = {"regex": [r"^keep-\d+"]}  # case-insensitive default
    out = ArtifactsScanner._apply_filters_to_elements(elements, filter_cfg)
    assert out == [{"text": "keep-123"}, {"text": "KEEP-999"}]


def test_apply_filters_combined():
    elements = [{"text": "ticket: ABC-1"}, {"text": "ticket: XYZ-2"}, {"text": "note: ABC-3"}]
    filter_cfg = {
        "contains": ["ticket:"],           # must contain "ticket:"
        "not_contains": ["xyz"],           # drop ones containing "xyz"
        "regex": [r"\bABC-\d+\b"],         # must match ABC-n
    }
    out = ArtifactsScanner._apply_filters_to_elements(elements, filter_cfg)
    assert out == [{"text": "ticket: ABC-1"}]


def test_get_field_value_filter_integration():
    """
    After sections are extracted (start/end), filter must apply before transforms.
    """
    scanner = ArtifactsScanner(user_id="u")
    text = "\n".join(
        [
            "START",
            "keeP this line 1",
            "END",
            "START",
            "remove this line 2",
            "END",
        ]
    )
    config = {
        "section": {
            "start": {"line_equal": "START", "strip": True},
            "end": {"line_equal": "END", "strip": True},
            "filter": {"contains": ["keep", "1"], "case_sensitive": False},
            "transform": [{"how": "uppercase"}],
        }
    }
    ret = scanner._get_field_value(
        _config=config, field_name="section", field_type="str", text=text, _magic_variables={}
    )
    # Expect only the first section to remain after filtering
    assert isinstance(ret, list)
    assert len(ret) == 1
    assert "KEEP THIS LINE 1" in ret[0].get("text", "")


def test_closest_integration():
    """
    """
    scanner = ArtifactsScanner(user_id="u")
    text = "\n".join(
        [
            "START",
            "remove this line 1",
            "END",
            "START",
            "target line 2",
            "END",
            "START",
            "another line to remove 3",
            "END",
        ]
    )
    config = {
        "section": {
            "start": {
                "line_contains": "target",
                "strip": True,
                "closest": {
                    "line_starting_with": "START",
                    "direction": "up"
                }
            },
            "end": {"line_equal": "END", "strip": True},
            "transform": [
                {"how": "uppercase"},
                {"how": "replace", "what": "START\n", "with": ""}
            ],
        }
    }
    ret = scanner._get_field_value(
        _config=config, field_name="section", field_type="str", text=text, _magic_variables={}
    )
    # Expect only the first section to remain after filtering
    assert isinstance(ret, list)
    assert len(ret) == 1
    assert "TARGET LINE 2" in ret[0].get("text", "")
