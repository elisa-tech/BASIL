"""Traceability Graphviz map generated alongside SPDX JSON-LD export."""

import re

from spdx_manager import (
    GRAPH_CONTAINER_KINDS,
    GRAPH_NODE_COLORS,
    SPDXFile,
    SPDXManager,
    SPDXRelationship,
    SPDXSnippet,
    SpdxRelationshipType,
    graph_node_kind,
    graphviz_node_id,
    is_graph_container,
)


def _file(spdx_id, name="item"):
    return SPDXFile(spdx_id=spdx_id, name=name, comment="", creation_info=None)


def _snippet(spdx_id, from_file=None, comment=""):
    return SPDXSnippet(
        spdx_id=spdx_id,
        from_file=from_file,
        name="snippet",
        comment=comment,
        creation_info=None,
    )


def _rel(from_element, to, relationship_type):
    targets = to if isinstance(to, list) else [to]
    return SPDXRelationship(
        from_element=from_element,
        to=targets,
        relationship_type=relationship_type,
    )


def _manager_with_sbom(items):
    manager = object.__new__(SPDXManager)
    manager.sbom = items
    return manager


def _write_dot(manager, tmp_path, stem, monkeypatch):
    monkeypatch.setattr("spdx_manager.Digraph.render", lambda *args, **kwargs: None)
    output = tmp_path / stem
    manager.generate_diagraph(output)
    dot_path = tmp_path / f"{stem}.dot"
    assert dot_path.is_file(), f"Expected {dot_path}"
    return dot_path.read_text()


def _edge_labels(dot_source):
    """Return {(src, dst): label} for visible (non-legend) edges."""
    edges = {}
    legend_nodes = set(GRAPH_NODE_COLORS)
    for match in re.finditer(
        r'"?([\w.-]+)"?\s*->\s*"?([\w.-]+)"?\s*\[label="?([^"\]]+)"?\]',
        dot_source,
    ):
        src, dst, label = match.group(1), match.group(2), match.group(3)
        if src in legend_nodes and dst in legend_nodes:
            continue
        edges[(src, dst)] = label
    return edges


def test_graph_node_kind_from_spdx_id_not_comment():
    snippet = _snippet(
        "spdx:snippet:api:1:0",
        comment="Snippet of api Foo reference document",
    )
    assert graph_node_kind(snippet) == "snippet"
    assert not is_graph_container(snippet)

    ref_doc = _file("spdx:file:basil:api:reference-document:1")
    ref_doc.comment = "BASIL Reference Document for Software Component Foo"
    assert graph_node_kind(ref_doc) == "reference_document"
    assert is_graph_container(ref_doc)

    api = _file("spdx:file:basil:api:9")
    assert graph_node_kind(api) == "software_component"
    assert is_graph_container(api)

    library = _file("spdx:file:basil:library:mylib")
    assert graph_node_kind(library) == "library"

    assert graph_node_kind(_file("spdx:file:basil:software-requirement:1")) == "software_requirement"
    assert graph_node_kind(_file("spdx:file:basil:test-specification:1")) == "test_specification"
    assert graph_node_kind(_file("spdx:file:basil:test-case:1")) == "test_case"
    assert graph_node_kind(_file("spdx:file:basil:document:1")) == "document"
    assert graph_node_kind(_file("spdx:file:basil:justification:1")) == "justification"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3")) == "test_run"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3:bug:1")) == "bug"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3:fix:1")) == "fix"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3:artifact:1")) == "artifact"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3")) not in GRAPH_CONTAINER_KINDS


def test_diagraph_uses_jsonld_basename(tmp_path, monkeypatch):
    library = _file("spdx:file:basil:library:lib")
    api = _file("spdx:file:basil:api:1")
    manager = _manager_with_sbom(
        [_rel(library, api, SpdxRelationshipType.CONTAINS)]
    )
    _write_dot(manager, tmp_path, "my_export", monkeypatch)
    assert (tmp_path / "my_export.dot").is_file()
    assert not (tmp_path / "latest.dot").exists()


def test_diagraph_combines_parallel_relationship_types_on_one_edge(tmp_path, monkeypatch):
    library = _file("spdx:file:basil:library:lib")
    api = _file("spdx:file:basil:api:1")
    manager = _manager_with_sbom(
        [
            _rel(library, api, SpdxRelationshipType.CONTAINS),
            _rel(library, api, SpdxRelationshipType.HAS_INPUT),
            _rel(library, api, SpdxRelationshipType.HAS_SPECIFICATION),
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    lib_id = graphviz_node_id(library.spdx_id)
    api_id = graphviz_node_id(api.spdx_id)
    edges = _edge_labels(dot)
    pair_edges = [(src, dst) for src, dst in edges if src == lib_id and dst == api_id]
    assert len(pair_edges) == 1
    assert edges[(lib_id, api_id)] == "contains,hasInput,hasSpecification"


def test_diagraph_includes_snippet_relationships(tmp_path, monkeypatch):
    api = _file("spdx:file:basil:api:1")
    ref_doc = _file("spdx:file:basil:api:reference-document:1")
    snippet = _snippet("spdx:snippet:api:1:0", from_file=ref_doc)
    requirement = _file("spdx:file:basil:software-requirement:2")
    manager = _manager_with_sbom(
        [
            _rel(api, snippet, SpdxRelationshipType.CONTAINS),
            _rel(snippet, requirement, SpdxRelationshipType.HAS_REQUIREMENT),
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    api_id = graphviz_node_id(api.spdx_id)
    snippet_id = graphviz_node_id(snippet.spdx_id)
    api_snippet = f"{api_id}__{snippet_id}"
    req_id = graphviz_node_id(requirement.spdx_id)
    snippet_req = f"{api_snippet}__{req_id}"
    ref_id = graphviz_node_id(ref_doc.spdx_id)
    edges = _edge_labels(dot)
    assert edges[(api_id, api_snippet)] == "contains"
    assert edges[(api_snippet, snippet_req)] == "hasRequirement"
    assert edges[(ref_id, api_snippet)] == "contains"
    assert f'fillcolor={GRAPH_NODE_COLORS["snippet"]}' in dot or "fillcolor=yellow" in dot
    assert f'fillcolor={GRAPH_NODE_COLORS["reference_document"]}' in dot


def test_diagraph_reuses_test_run_instance_for_api_has_test(tmp_path, monkeypatch):
    api = _file("spdx:file:basil:api:1")
    test_case = _file("spdx:file:basil:test-case:8")
    test_run = _file("spdx:file:basil:test-run:9")
    manager = _manager_with_sbom(
        [
            _rel(api, test_case, SpdxRelationshipType.HAS_TEST_CASE),
            _rel(test_case, test_run, SpdxRelationshipType.GENERATES),
            _rel(test_case, test_run, SpdxRelationshipType.HAS_TEST),
            _rel(test_case, test_run, SpdxRelationshipType.HAS_OUTPUT),
            _rel(api, test_run, SpdxRelationshipType.HAS_TEST),
            _rel(test_run, api, SpdxRelationshipType.TESTED_ON),
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    api_id = graphviz_node_id(api.spdx_id)
    tc_label = graphviz_node_id(test_case.spdx_id)
    tr_label = graphviz_node_id(test_run.spdx_id)
    tc_instance = f"{api_id}__{tc_label}"
    tr_instance = f"{tc_instance}__{tr_label}"
    duplicate_tr = f"{api_id}__{tr_label}"
    edges = _edge_labels(dot)
    assert edges[(tc_instance, tr_instance)] == "generates,hasTest,hasOutput"
    assert (tc_instance, tr_instance) in edges
    assert edges[(api_id, tr_instance)] == "hasTest"
    assert (api_id, duplicate_tr) not in edges
    assert edges[(tr_instance, api_id)] == "testedOn"
    tc_tr_labels = [label for (src, dst), label in edges.items() if src == tc_instance and dst == tr_instance]
    assert tc_tr_labels == ["generates,hasTest,hasOutput"]


def test_diagraph_duplicates_work_item_under_each_parent(tmp_path, monkeypatch):
    api = _file("spdx:file:basil:api:1")
    sr = _file("spdx:file:basil:software-requirement:2")
    test_case = _file("spdx:file:basil:test-case:8")
    manager = _manager_with_sbom(
        [
            _rel(api, sr, SpdxRelationshipType.HAS_REQUIREMENT),
            _rel(sr, test_case, SpdxRelationshipType.HAS_TEST_CASE),
            _rel(api, test_case, SpdxRelationshipType.HAS_TEST_CASE),
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    api_id = graphviz_node_id(api.spdx_id)
    sr_label = graphviz_node_id(sr.spdx_id)
    tc_label = graphviz_node_id(test_case.spdx_id)
    sr_instance = f"{api_id}__{sr_label}"
    tc_under_sr = f"{sr_instance}__{tc_label}"
    tc_under_api = f"{api_id}__{tc_label}"
    edges = _edge_labels(dot)
    assert (sr_instance, tc_under_sr) in edges
    assert (api_id, tc_under_api) in edges
    assert tc_under_sr != tc_under_api


def test_diagraph_attaches_test_run_outputs_to_mapped_instance(tmp_path, monkeypatch):
    """SBOM emits TR → bug/artifact before TC → TR; map must not orphan the run."""
    api = _file("spdx:file:basil:api:1")
    test_case = _file("spdx:file:basil:test-case:8")
    test_run = _file("spdx:file:basil:test-run:9")
    artifact = _file("spdx:file:basil:test-run:9:artifact:1")
    bug = _file("spdx:file:basil:test-run:9:bug:1")
    manager = _manager_with_sbom(
        [
            _rel(api, test_case, SpdxRelationshipType.HAS_TEST_CASE),
            _rel(test_run, bug, SpdxRelationshipType.HAS_OUTPUT),
            _rel(test_run, artifact, SpdxRelationshipType.HAS_OUTPUT),
            _rel(test_run, artifact, SpdxRelationshipType.HAS_EVIDENCE),
            _rel(test_case, test_run, SpdxRelationshipType.GENERATES),
            _rel(api, test_run, SpdxRelationshipType.HAS_TEST),
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    api_id = graphviz_node_id(api.spdx_id)
    tc_label = graphviz_node_id(test_case.spdx_id)
    tr_label = graphviz_node_id(test_run.spdx_id)
    bug_label = graphviz_node_id(bug.spdx_id)
    artifact_label = graphviz_node_id(artifact.spdx_id)
    tr_instance = f"{api_id}__{tc_label}__{tr_label}"
    orphan_tr = tr_label
    edges = _edge_labels(dot)
    assert (f"{api_id}__{tc_label}", tr_instance) in edges
    assert edges[(tr_instance, f"{tr_instance}__{bug_label}")] == "hasOutput"
    assert edges[(tr_instance, f"{tr_instance}__{artifact_label}")] == "hasOutput,hasEvidence"
    assert orphan_tr not in {src for src, _ in edges}
