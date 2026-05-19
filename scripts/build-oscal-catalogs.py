#!/usr/bin/env python3
"""Expand compact control-source YAML files into OSCAL Catalog Model JSON.

Source files live at `gaps/catalogs/v1/controls/sources/*.yml`.
Outputs live at `gaps/catalogs/v1/controls/*.json`.

Idempotent: re-running produces byte-identical output for unchanged sources
because all UUIDs are derived deterministically via UUIDv5 from a stable
namespace plus control id.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "gaps" / "catalogs" / "v1" / "controls" / "sources"
OUTPUT_DIR = ROOT / "gaps" / "catalogs" / "v1" / "controls"
NAMESPACE_UUID = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
OSCAL_VERSION = "1.1.2"

sys.dont_write_bytecode = True


def load_yaml(path: Path) -> Any:
    result = subprocess.run(
        [
            "ruby",
            "-ryaml",
            "-rjson",
            "-e",
            "print YAML.load_file(ARGV[0]).to_json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"failed to load {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def stable_uuid(seed: str, key: str) -> str:
    return str(uuid.uuid5(NAMESPACE_UUID, f"{seed}:{key}"))


def build_catalog(source: dict[str, Any]) -> dict[str, Any]:
    seed = source["catalogUuidSeed"]
    catalog_uuid = stable_uuid(seed, "catalog")
    groups: list[dict[str, Any]] = []
    for group in source["groups"]:
        controls = []
        for control in group["controls"]:
            controls.append({
                "id": control["id"],
                "title": control["title"],
            })
        groups.append({
            "id": group["id"],
            "title": group["title"],
            "controls": controls,
        })
    return {
        "catalog": {
            "uuid": catalog_uuid,
            "metadata": {
                "title": source["catalogTitle"],
                "version": source["catalogVersion"],
                "oscal-version": OSCAL_VERSION,
            },
            "groups": groups,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if regenerated JSON differs from committed JSON.",
    )
    args = parser.parse_args()
    sources = sorted(SOURCES_DIR.glob("*.yml"))
    if not sources:
        print("no sources found", file=sys.stderr)
        return 1
    differ = False
    for source_path in sources:
        source = load_yaml(source_path)
        catalog = build_catalog(source)
        output_path = OUTPUT_DIR / (source_path.stem + ".json")
        rendered = json.dumps(catalog, indent=2, sort_keys=False) + "\n"
        if args.check:
            if not output_path.exists():
                print(f"MISSING: {output_path}", file=sys.stderr)
                differ = True
                continue
            if output_path.read_text(encoding="utf-8") != rendered:
                print(f"DIFFER: {output_path}", file=sys.stderr)
                differ = True
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"wrote {output_path}")
    return 1 if differ else 0


if __name__ == "__main__":
    raise SystemExit(main())
