"""Export and compare knowledge graph extractions across different LLM models.

Usage via CLI:
    uv run python main.py export-model gpt-4o       # Snapshot current graph tagged by model
    uv run python main.py compare-models             # Compare all model snapshots
    uv run python main.py compare-models --a gpt-4o_20260322_120000.json --b gpt-4.1-mini_20260322_130000.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from neo4j import Driver

_SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "model_snapshots"

# Entity types extracted by the LLM (not CSV-loaded)
_LLM_ENTITY_LABELS = ["RiskFactor", "Product", "Executive", "FinancialMetric"]

# All entity labels including CSV-loaded ones
_ALL_ENTITY_LABELS = ["Company", *_LLM_ENTITY_LABELS, "AssetManager"]

# Relationship types from the extraction schema
_SCHEMA_RELS = [
    "FACES_RISK", "OFFERS", "HAS_EXECUTIVE", "REPORTS",
    "COMPETES_WITH", "PARTNERS_WITH",
]


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_snapshot(driver: Driver, model_name: str) -> Path:
    """Export the current graph state to a JSON snapshot file tagged by model.

    Captures entity counts, relationship counts, all extracted entities
    with properties, and all schema relationships.
    """
    _SNAPSHOTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = model_name.replace("/", "_").replace(" ", "_")
    snapshot_path = _SNAPSHOTS_DIR / f"{safe_name}_{timestamp}.json"

    snapshot: dict = {
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "entity_counts": {},
        "relationship_counts": {},
        "entities": {},
        "relationships": [],
    }

    # Entity counts
    for label in _ALL_ENTITY_LABELS + ["Chunk", "Document"]:
        rows, _, _ = driver.execute_query(
            f"MATCH (n:{label}) RETURN count(n) AS count"
        )
        snapshot["entity_counts"][label] = rows[0]["count"]

    # Relationship counts
    for rel_type in _SCHEMA_RELS:
        rows, _, _ = driver.execute_query(
            f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count"
        )
        snapshot["relationship_counts"][rel_type] = rows[0]["count"]

    # Export all LLM-extracted entities with properties
    for label in _LLM_ENTITY_LABELS:
        rows, _, _ = driver.execute_query(
            f"MATCH (n:{label}) WHERE n.name IS NOT NULL "
            f"RETURN properties(n) AS props ORDER BY n.name"
        )
        snapshot["entities"][label] = [_clean_props(r["props"]) for r in rows]

    # Export Company entities
    rows, _, _ = driver.execute_query(
        "MATCH (c:Company) WHERE c.name IS NOT NULL "
        "RETURN properties(c) AS props ORDER BY c.name"
    )
    snapshot["entities"]["Company"] = [_clean_props(r["props"]) for r in rows]

    # Export all schema relationships
    rows, _, _ = driver.execute_query("""
        MATCH (source)-[r]->(target)
        WHERE type(r) IN $rel_types
          AND source.name IS NOT NULL
          AND target.name IS NOT NULL
        RETURN source.name AS source, type(r) AS rel_type,
               target.name AS target
        ORDER BY type(r), source.name, target.name
    """, rel_types=_SCHEMA_RELS)
    snapshot["relationships"] = [
        {"source": r["source"], "type": r["rel_type"], "target": r["target"]}
        for r in rows
    ]

    with open(snapshot_path, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    # Print summary
    total_entities = sum(
        snapshot["entity_counts"].get(label, 0) for label in _ALL_ENTITY_LABELS
    )
    total_rels = sum(snapshot["relationship_counts"].values())
    print(f"\nSnapshot exported: {snapshot_path.name}")
    print(f"  Model: {model_name}")
    print(f"  Total entities: {total_entities}")
    print(f"  Total relationships: {total_rels}")
    for label in _ALL_ENTITY_LABELS:
        count = snapshot["entity_counts"].get(label, 0)
        if count:
            print(f"    {label}: {count}")

    return snapshot_path


def _clean_props(props: dict) -> dict:
    """Remove embedding vectors and internal properties for readable snapshots."""
    return {
        k: v for k, v in props.items()
        if not k.startswith("__") and k != "embedding" and not isinstance(v, list)
    }


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------


def compare_snapshots(path_a: Path, path_b: Path) -> None:
    """Compare two model snapshot files and print a detailed diff."""
    with open(path_a) as f:
        snap_a = json.load(f)
    with open(path_b) as f:
        snap_b = json.load(f)

    model_a = snap_a["model"]
    model_b = snap_b["model"]
    w = 70

    print(f"\n{'=' * w}")
    print(f"  Model Comparison: {model_a} vs {model_b}")
    print(f"{'=' * w}")

    # --- Entity count comparison ---
    print(f"\n  Entity Counts:")
    print(f"  {'Label':<20} {model_a:>12} {model_b:>12} {'Delta':>10}")
    print(f"  {'-' * 56}")
    for label in _ALL_ENTITY_LABELS:
        count_a = snap_a["entity_counts"].get(label, 0)
        count_b = snap_b["entity_counts"].get(label, 0)
        delta = count_b - count_a
        sign = f"+{delta}" if delta > 0 else str(delta)
        flag = " *" if delta != 0 else ""
        print(f"  {label:<20} {count_a:>12} {count_b:>12} {sign:>10}{flag}")

    # --- Relationship count comparison ---
    print(f"\n  Relationship Counts:")
    print(f"  {'Type':<20} {model_a:>12} {model_b:>12} {'Delta':>10}")
    print(f"  {'-' * 56}")
    total_a = total_b = 0
    for rel_type in _SCHEMA_RELS:
        count_a = snap_a["relationship_counts"].get(rel_type, 0)
        count_b = snap_b["relationship_counts"].get(rel_type, 0)
        total_a += count_a
        total_b += count_b
        delta = count_b - count_a
        sign = f"+{delta}" if delta > 0 else str(delta)
        flag = " *" if delta != 0 else ""
        print(f"  {rel_type:<20} {count_a:>12} {count_b:>12} {sign:>10}{flag}")
    print(f"  {'-' * 56}")
    total_delta = total_b - total_a
    total_sign = f"+{total_delta}" if total_delta > 0 else str(total_delta)
    print(f"  {'TOTAL':<20} {total_a:>12} {total_b:>12} {total_sign:>10}")

    # --- Entity name diffs per type ---
    for label in _LLM_ENTITY_LABELS:
        entities_a = snap_a.get("entities", {}).get(label, [])
        entities_b = snap_b.get("entities", {}).get(label, [])
        names_a = {e.get("name", "") for e in entities_a}
        names_b = {e.get("name", "") for e in entities_b}
        only_a = sorted(names_a - names_b)
        only_b = sorted(names_b - names_a)
        common = names_a & names_b

        print(f"\n  {label}:")
        print(f"    Common: {len(common)}  |  Only {model_a}: {len(only_a)}  |  Only {model_b}: {len(only_b)}")

        if only_a:
            print(f"    Removed ({model_a} only):")
            for name in only_a[:20]:
                print(f"      - {name}")
            if len(only_a) > 20:
                print(f"      ... and {len(only_a) - 20} more")

        if only_b:
            print(f"    Added ({model_b} only):")
            for name in only_b[:20]:
                print(f"      + {name}")
            if len(only_b) > 20:
                print(f"      ... and {len(only_b) - 20} more")

        # For entities with descriptions (RiskFactor, Executive), compare detail
        if label == "RiskFactor" and common:
            _compare_descriptions(entities_a, entities_b, common, model_a, model_b)

    # --- Relationship diffs ---
    def _rel_key(r):
        return (r["type"], r.get("source") or "", r.get("target") or "")

    rels_a = {_rel_key(r) for r in snap_a.get("relationships", [])}
    rels_b = {_rel_key(r) for r in snap_b.get("relationships", [])}
    common_rels = rels_a & rels_b
    only_rels_a = sorted(rels_a - rels_b)
    only_rels_b = sorted(rels_b - rels_a)

    print(f"\n  Relationship Differences:")
    print(f"    Common: {len(common_rels)}  |  Only {model_a}: {len(only_rels_a)}  |  Only {model_b}: {len(only_rels_b)}")
    if only_rels_a:
        print(f"    Removed ({model_a} only, sample):")
        for rel_type, src, tgt in only_rels_a[:10]:
            print(f"      - ({src})-[{rel_type}]->({tgt})")
        if len(only_rels_a) > 10:
            print(f"      ... and {len(only_rels_a) - 10} more")
    if only_rels_b:
        print(f"    Added ({model_b} only, sample):")
        for rel_type, src, tgt in only_rels_b[:10]:
            print(f"      + ({src})-[{rel_type}]->({tgt})")
        if len(only_rels_b) > 10:
            print(f"      ... and {len(only_rels_b) - 10} more")

    print(f"\n{'=' * w}\n")


def _compare_descriptions(
    entities_a: list[dict],
    entities_b: list[dict],
    common_names: set[str],
    model_a: str,
    model_b: str,
) -> None:
    """Compare description lengths for entities present in both snapshots."""
    lookup_a = {e["name"]: e for e in entities_a if e.get("name") in common_names}
    lookup_b = {e["name"]: e for e in entities_b if e.get("name") in common_names}

    longer_b = shorter_b = same = 0
    for name in common_names:
        desc_a = lookup_a.get(name, {}).get("description", "")
        desc_b = lookup_b.get(name, {}).get("description", "")
        len_a = len(desc_a) if desc_a else 0
        len_b = len(desc_b) if desc_b else 0
        if len_b > len_a:
            longer_b += 1
        elif len_b < len_a:
            shorter_b += 1
        else:
            same += 1

    if longer_b or shorter_b:
        print(f"    Description lengths ({len(common_names)} shared):")
        print(f"      {model_b} longer: {longer_b}  |  {model_a} longer: {shorter_b}  |  Same: {same}")


# ---------------------------------------------------------------------------
# List snapshots
# ---------------------------------------------------------------------------


def list_snapshots() -> list[Path]:
    """List available model snapshot files."""
    if not _SNAPSHOTS_DIR.exists():
        return []
    return sorted(_SNAPSHOTS_DIR.glob("*.json"))


def find_snapshots_for_model(model_name: str) -> list[Path]:
    """Find snapshots matching a model name prefix."""
    safe_name = model_name.replace("/", "_").replace(" ", "_")
    if not _SNAPSHOTS_DIR.exists():
        return []
    return sorted(_SNAPSHOTS_DIR.glob(f"{safe_name}_*.json"))
