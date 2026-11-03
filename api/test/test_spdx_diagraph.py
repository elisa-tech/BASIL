"""Traceability Graphviz map generated alongside SPDX JSON-LD export."""

import datetime
import json
import re
from pathlib import Path
from types import SimpleNamespace

from spdx_manager import (
    GRAPH_CONTAINER_KINDS,
    GRAPH_NODE_COLORS,
    SPDXAnnotation,
    SPDXCreationInfo,
    SPDXFile,
    SPDXManager,
    SPDXRelationship,
    SPDXSnippet,
    SpdxRelationshipType,
    graph_node_kind,
    graphviz_node_id,
    is_basil_comment_annotation,
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
    assert graph_node_kind(_file("spdx:file:basil:test-run-config:4")) == "test_run_config"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3:bug:1")) == "bug"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3:fix:1")) == "fix"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3:artifact:1")) == "artifact"
    assert graph_node_kind(_file("spdx:file:basil:test-run:3")) not in GRAPH_CONTAINER_KINDS


def _comment_annotation(subject, comment_id=11, text="please clarify coverage"):
    return SPDXAnnotation(
        spdx_id=f"spdx:annotation:basil:comment:{comment_id}",
        name=f"BASIL comment {comment_id}",
        subject=subject,
        object={"kind": "comment", "comment": text},
        creation_info=SimpleNamespace(spdx_id="_:creation_info_comment"),
        annotation_type="review",
    )


def test_graph_node_kind_for_comment_annotation():
    requirement = _file("spdx:file:basil:software-requirement:2")
    annotation = _comment_annotation(requirement)
    assert is_basil_comment_annotation(annotation)
    assert graph_node_kind(annotation) == "comment"
    assert graph_node_kind(requirement) == "software_requirement"


def test_diagraph_includes_work_item_comments(tmp_path, monkeypatch):
    api = _file("spdx:file:basil:api:1")
    requirement = _file("spdx:file:basil:software-requirement:2")
    annotation = _comment_annotation(requirement, text="please clarify coverage")
    manager = _manager_with_sbom(
        [
            _rel(api, requirement, SpdxRelationshipType.HAS_REQUIREMENT),
            annotation,
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    api_id = graphviz_node_id(api.spdx_id)
    req_label = graphviz_node_id(requirement.spdx_id)
    comment_label = graphviz_node_id(annotation.spdx_id)
    req_instance = f"{api_id}__{req_label}"
    comment_instance = f"{req_instance}__{comment_label}"
    edges = _edge_labels(dot)
    assert edges[(req_instance, comment_instance)] == "comment"
    assert "please clarify coverage" in dot
    assert f'fillcolor={GRAPH_NODE_COLORS["comment"]}' in dot or "fillcolor=pink" in dot


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
            _rel(api, ref_doc, SpdxRelationshipType.HAS_DOCUMENTATION),
            _rel(ref_doc, snippet, SpdxRelationshipType.CONTAINS),
            _rel(snippet, requirement, SpdxRelationshipType.HAS_REQUIREMENT),
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    api_id = graphviz_node_id(api.spdx_id)
    snippet_id = graphviz_node_id(snippet.spdx_id)
    req_id = graphviz_node_id(requirement.spdx_id)
    ref_id = graphviz_node_id(ref_doc.spdx_id)
    ref_snippet = f"{ref_id}__{snippet_id}"
    snippet_req = f"{ref_snippet}__{req_id}"
    edges = _edge_labels(dot)
    assert edges[(api_id, ref_id)] == "hasDocumentation"
    assert edges[(ref_id, ref_snippet)] == "contains"
    assert edges[(ref_snippet, snippet_req)] == "hasRequirement"
    assert not any(src == api_id and dst.endswith(snippet_id) for src, dst in edges)
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


def test_diagraph_links_shared_test_run_config_without_forking_runs(tmp_path, monkeypatch):
    """configures is Configuration → Test Run and must reuse the mapped run.

    The relationship is emitted before Test Case → Test Run, matching export
    order. One configuration node points at each already placed run.
    """
    api = _file("spdx:file:basil:api:1")
    test_case = _file("spdx:file:basil:test-case:8")
    test_run = _file("spdx:file:basil:test-run:9")
    other_run = _file("spdx:file:basil:test-run:10")
    bug = _file("spdx:file:basil:test-run:9:bug:1")
    config = _file("spdx:file:basil:test-run-config:4", name="CI config")
    manager = _manager_with_sbom(
        [
            _rel(api, test_case, SpdxRelationshipType.HAS_TEST_CASE),
            _rel(config, test_run, SpdxRelationshipType.CONFIGURES),
            _rel(config, other_run, SpdxRelationshipType.CONFIGURES),
            _rel(test_run, bug, SpdxRelationshipType.HAS_OUTPUT),
            _rel(test_case, [test_run, other_run], SpdxRelationshipType.GENERATES),
        ]
    )
    dot = _write_dot(manager, tmp_path, "map", monkeypatch)
    api_id = graphviz_node_id(api.spdx_id)
    tc_label = graphviz_node_id(test_case.spdx_id)
    tr_label = graphviz_node_id(test_run.spdx_id)
    other_label = graphviz_node_id(other_run.spdx_id)
    bug_label = graphviz_node_id(bug.spdx_id)
    config_id = graphviz_node_id(config.spdx_id)
    tc_instance = f"{api_id}__{tc_label}"
    tr_instance = f"{tc_instance}__{tr_label}"
    other_instance = f"{tc_instance}__{other_label}"
    edges = _edge_labels(dot)
    assert edges[(config_id, tr_instance)] == "configures"
    assert edges[(config_id, other_instance)] == "configures"
    assert edges[(tr_instance, f"{tr_instance}__{bug_label}")] == "hasOutput"
    assert (config_id, f"{config_id}__{tr_label}") not in edges
    assert f"{tr_instance}__{config_id}" not in dot
    assert "Test Run Configuration" in dot
    assert f'fillcolor={GRAPH_NODE_COLORS["test_run_config"]}' in dot or "fillcolor=gold" in dot


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


def _manager_for_export():
    manager = object.__new__(SPDXManager)
    manager.sbom = []
    manager.tool = None
    manager.sbom_creation_info = SPDXCreationInfo(
        spdx_id="_:sbom_creation_info",
        created_by=[],
        created_using=[],
        created=datetime.datetime(2026, 1, 2, 3, 4, 5),
    )
    return manager


class _FakeTestRunConfig:
    __tablename__ = "test_run_configs"
    id = 4
    title = "CI config"
    plugin = "tmt"
    created_at = datetime.datetime(2026, 1, 2, 3, 4, 5)
    created_by = SimpleNamespace(id=7, username="ut_user")

    def as_dict(self, full_data=False):
        data = {
            "id": self.id,
            "plugin": self.plugin,
            "plugin_preset": "",
            "plugin_vars": "VAR=1",
            "title": self.title,
            "git_repo_ref": "main",
            "context_vars": "",
            "ssh_key": None,
            "environment_vars": "",
            "provision_type": "container",
            "provision_guest": "",
            "provision_guest_port": "",
            "created_by": self.created_by.username,
        }
        if full_data:
            stamp = self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            data["created_at"] = stamp
            data["updated_at"] = stamp
        return data


def test_export_writes_shared_test_run_configuration(tmp_path, monkeypatch):
    """One configuration File configures every Test Run in jsonld, dot, and png."""
    rendered = {}

    def fake_render(self, filename="", cleanup=True, **kwargs):
        rendered["png"] = f"{filename}.png"
        Path(rendered["png"]).write_bytes(b"\x89PNG\r\n")

    monkeypatch.setattr("spdx_manager.Digraph.render", fake_render)

    manager = _manager_for_export()
    creation = manager.sbom_creation_info
    api = SPDXFile(
        spdx_id="spdx:file:basil:api:1",
        name="component",
        comment="",
        creation_info=creation,
    )
    test_case = SPDXFile(
        spdx_id="spdx:file:basil:test-case:8",
        name="case",
        comment="",
        creation_info=creation,
    )
    test_run = SPDXFile(
        spdx_id="spdx:file:basil:test-run:9",
        name="run-9",
        comment="",
        creation_info=creation,
    )
    other_run = SPDXFile(
        spdx_id="spdx:file:basil:test-run:10",
        name="run-10",
        comment="",
        creation_info=creation,
    )
    manager.add_to_sbom(api)
    manager.add_to_sbom(test_case)
    manager.add_to_sbom(test_run)
    manager.add_to_sbom(other_run)
    manager.addRelationship(
        from_element=api,
        to=[test_case],
        relationship_type=SpdxRelationshipType.HAS_TEST_CASE,
    )
    manager.addRelationship(
        from_element=test_case,
        to=[test_run, other_run],
        relationship_type=SpdxRelationshipType.GENERATES,
    )
    config = _FakeTestRunConfig()
    first = manager.addTestRunConfiguration(test_run_config=config, spdx_tr=test_run)
    second = manager.addTestRunConfiguration(test_run_config=config, spdx_tr=other_run)
    assert first is second
    assert first.purpose == "configuration"

    config_files = [
        item for item in manager.sbom if getattr(item, "spdx_id", "") == first.spdx_id
    ]
    assert len(config_files) == 1
    relationships = [item for item in manager.sbom if isinstance(item, SPDXRelationship)]
    configures = [
        item for item in relationships if item.relationship_type == SpdxRelationshipType.CONFIGURES
    ]
    assert len(configures) == 2
    assert [target.spdx_id for item in configures for target in item.to] == [
        test_run.spdx_id,
        other_run.spdx_id,
    ]

    filepath = tmp_path / "library.jsonld"
    manager.export(str(filepath))
    document = json.loads(filepath.read_text())
    graph = document["@graph"]
    exported_configs = [
        element
        for element in graph
        if element.get("spdxId") == first.spdx_id
    ]
    assert len(exported_configs) == 1
    assert exported_configs[0]["software_primaryPurpose"] == "configuration"
    assert exported_configs[0]["externalIdentifier"][0]["identifier"] == "basil:test_run_configs:4"
    annotation = next(
        element
        for element in graph
        if element.get("spdxId") == "spdx:annotation:basil:test-run-config:4"
    )
    statement = json.loads(annotation["statement"])
    assert statement["plugin"] == "tmt"
    assert statement["git_repo_ref"] == "main"
    assert statement["plugin_vars"] == "VAR=1"
    assert "title" not in statement
    exported_rels = [
        element
        for element in graph
        if element.get("type") == "Relationship" and element.get("relationshipType") == "configures"
    ]
    assert len(exported_rels) == 2
    assert {element["from"] for element in exported_rels} == {first.spdx_id}
    assert {element["to"][0] for element in exported_rels} == {test_run.spdx_id, other_run.spdx_id}

    dot_source = (tmp_path / "library.dot").read_text()
    config_node = graphviz_node_id(first.spdx_id)
    edges = _edge_labels(dot_source)
    api_node = graphviz_node_id(api.spdx_id)
    tc_instance = f"{api_node}__{graphviz_node_id(test_case.spdx_id)}"
    for run in (test_run, other_run):
        run_instance = f"{tc_instance}__{graphviz_node_id(run.spdx_id)}"
        assert edges[(config_node, run_instance)] == "configures"
    assert rendered["png"] == str(tmp_path / "library.png")
    assert (tmp_path / "library.png").is_file()


def test_add_relationship_appends_without_merging():
    """addRelationship always appends a new Relationship.

    Callers that already pass multiple targets (library → APIs, Test Case → Test Runs)
    get a 1-to-many Relationship. Repeated calls with the same (from, type) stay separate.
    """
    ref_doc = _file("spdx:file:basil:api:reference-document:1")
    snippet_one = _snippet("spdx:snippet:api:1:1", from_file=ref_doc)
    snippet_two = _snippet("spdx:snippet:api:1:2", from_file=ref_doc)
    manager = _manager_with_sbom([])
    manager.sbom_creation_info = SimpleNamespace(spdx_id="_:sbom_creation_info")

    manager.addRelationship(
        from_element=ref_doc, to=[snippet_one], relationship_type=SpdxRelationshipType.CONTAINS
    )
    manager.addRelationship(
        from_element=ref_doc, to=[snippet_two], relationship_type=SpdxRelationshipType.CONTAINS
    )
    manager.addRelationship(
        from_element=ref_doc,
        to=[snippet_one, snippet_two],
        relationship_type=SpdxRelationshipType.HAS_OUTPUT,
        completeness_percentage=-1,
    )

    relationships = [item for item in manager.sbom if isinstance(item, SPDXRelationship)]
    assert len(relationships) == 3
    assert relationships[0].spdx_id == "spdx:relationship:1"
    assert [target.spdx_id for target in relationships[0].to] == [snippet_one.spdx_id]
    assert relationships[0].completeness == "incomplete"
    assert relationships[1].spdx_id == "spdx:relationship:2"
    assert [target.spdx_id for target in relationships[1].to] == [snippet_two.spdx_id]
    assert relationships[2].spdx_id == "spdx:relationship:3"
    assert [target.spdx_id for target in relationships[2].to] == [
        snippet_one.spdx_id,
        snippet_two.spdx_id,
    ]
    assert relationships[2].completeness == "noAssertion"
