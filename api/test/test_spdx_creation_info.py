"""Reuse SPDX CreationInfo objects that serialize to the same payload."""

from datetime import datetime, timezone
from types import SimpleNamespace

from spdx_manager import BASIL_TOOL_URL, SPDXCreationInfo, SPDXManager, SPDXPerson, SPDXTool


def _creation_info_manager(export_created=None):
    """Minimal SPDXManager with a Tool and sbom CreationInfo already in the graph."""
    manager = SPDXManager.__new__(SPDXManager)
    manager.sbom = []
    created = export_created or datetime(2026, 9, 18, 15, 0, 0, tzinfo=timezone.utc)
    exporter = SPDXPerson(spdx_id="spdx:person:basil:user:1", name="exporter", creation_info=None)
    tool = SPDXTool(spdx_id=BASIL_TOOL_URL, name="BASIL", creation_info=None)
    sbom_creation_info = SPDXCreationInfo(
        spdx_id="_:sbom_creation_info",
        created_by=[exporter],
        created_using=[tool],
        created=created,
    )
    exporter.creation_info = sbom_creation_info
    tool.creation_info = sbom_creation_info
    manager.sbom_creation_info = sbom_creation_info
    manager.tool = tool
    manager.add_to_sbom(sbom_creation_info)
    manager.add_to_sbom(exporter)
    manager.add_to_sbom(tool)
    return manager


def test_get_creation_info_reuses_identical_payload():
    """Items that share created time, author, and tool reuse one CreationInfo."""
    manager = _creation_info_manager()
    user = SimpleNamespace(id=4, username="alice")
    created = datetime(2026, 9, 8, 12, 14, 49, tzinfo=timezone.utc)

    first, _ = manager.getCreationInfoAndPerson(
        item_id="spdx:file:basil:api:1", created_at=created, created_by=user
    )
    second, _ = manager.getCreationInfoAndPerson(
        item_id="spdx:snippet:api:1:1", created_at=created, created_by=user
    )

    assert first is second
    creation_infos = [item for item in manager.sbom if isinstance(item, SPDXCreationInfo)]
    assert len(creation_infos) == 2  # sbom CreationInfo plus one reused work-item CreationInfo
    assert first.spdx_id == "_:creation_info_spdx:file:basil:api:1"


def test_get_creation_info_reuses_payload_when_created_seconds_match():
    """Serialized created timestamps are second-precision, so sub-second diffs reuse."""
    manager = _creation_info_manager()
    user = SimpleNamespace(id=4, username="alice")
    first, _ = manager.getCreationInfoAndPerson(
        item_id="a",
        created_at=datetime(2026, 9, 8, 12, 14, 49, 123000, tzinfo=timezone.utc),
        created_by=user,
    )
    second, _ = manager.getCreationInfoAndPerson(
        item_id="b",
        created_at=datetime(2026, 9, 8, 12, 14, 49, 987000, tzinfo=timezone.utc),
        created_by=user,
    )
    assert first is second
    assert len([item for item in manager.sbom if isinstance(item, SPDXCreationInfo)]) == 2


def test_get_creation_info_creates_new_when_created_or_author_differs():
    """Different created timestamps or authors must not share CreationInfo."""
    manager = _creation_info_manager()
    alice = SimpleNamespace(id=4, username="alice")
    bob = SimpleNamespace(id=5, username="bob")
    t1 = datetime(2026, 9, 8, 12, 14, 49, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 8, 12, 14, 50, tzinfo=timezone.utc)

    same_author_t1, _ = manager.getCreationInfoAndPerson(item_id="a", created_at=t1, created_by=alice)
    same_author_t2, _ = manager.getCreationInfoAndPerson(item_id="b", created_at=t2, created_by=alice)
    other_author_t1, _ = manager.getCreationInfoAndPerson(item_id="c", created_at=t1, created_by=bob)

    assert same_author_t1 is not same_author_t2
    assert same_author_t1 is not other_author_t1
    assert same_author_t2 is not other_author_t1
    creation_infos = [item for item in manager.sbom if isinstance(item, SPDXCreationInfo)]
    assert len(creation_infos) == 4  # sbom CreationInfo plus three distinct work-item payloads


def test_get_creation_info_reuses_sbom_creation_info_when_payload_matches():
    """Work items created at export time by the exporter share the SBOM CreationInfo."""
    export_created = datetime(2026, 9, 18, 15, 0, 0, tzinfo=timezone.utc)
    manager = _creation_info_manager(export_created=export_created)
    exporter = SimpleNamespace(id=1, username="exporter")

    reused, _ = manager.getCreationInfoAndPerson(
        item_id="spdx:file:basil:api:1", created_at=export_created, created_by=exporter
    )
    assert reused is manager.sbom_creation_info
    assert len([item for item in manager.sbom if isinstance(item, SPDXCreationInfo)]) == 1
