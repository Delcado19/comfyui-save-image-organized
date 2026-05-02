from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_WORKFLOW_ROOT = Path("private-workflows")
STANDARD_NODE_TYPE = "SaveImage"
ORGANIZED_NODE_TYPE = "SaveImageClean"
DEFAULT_FILENAME_PATTERN = "%date:yyyy-MM-dd_hh-mm-ss%"
PATH_SUFFIX = "%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%"
ORGANIZED_AUX_ID = "Delcado19/comfyui-save-image-organized"


@dataclass
class WorkflowMigration:
    workflow: str
    standard_nodes: int
    organized_nodes: int
    migrated_nodes: int
    changed: bool


def _iter_json_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.json") if path.is_file() and not path.name.startswith("."))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _dump_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _image_link(node: dict[str, Any]) -> Any:
    inputs = node.get("inputs")
    if not isinstance(inputs, list):
        return None

    for input_def in inputs:
        if isinstance(input_def, dict) and input_def.get("name") == "images":
            return input_def.get("link")
    for input_def in inputs:
        if isinstance(input_def, dict) and input_def.get("type") == "IMAGE":
            return input_def.get("link")
    return None


def _filename_prefix_from_ui(node: dict[str, Any]) -> str:
    values = node.get("widgets_values")
    if isinstance(values, list) and values:
        return str(values[0])
    if isinstance(values, dict):
        return str(values.get("filename_prefix", ""))
    return ""


def _path_template_from_prefix(prefix: str) -> str:
    normalized = prefix.strip().strip("/\\")
    if not normalized:
        return PATH_SUFFIX
    return f"{normalized}/{PATH_SUFFIX}"


def _organized_inputs(image_link: Any) -> list[dict[str, Any]]:
    return [
        {"localized_name": "images", "name": "images", "type": "IMAGE", "link": image_link},
        {
            "localized_name": "path_template",
            "name": "path_template",
            "type": "STRING",
            "widget": {"name": "path_template"},
            "link": None,
        },
        {
            "localized_name": "model_source",
            "name": "model_source",
            "type": "COMBO",
            "widget": {"name": "model_source"},
            "link": None,
        },
        {
            "localized_name": "clip_source",
            "name": "clip_source",
            "type": "COMBO",
            "widget": {"name": "clip_source"},
            "link": None,
        },
        {
            "localized_name": "filename_datetime",
            "name": "filename_datetime",
            "type": "STRING",
            "widget": {"name": "filename_datetime"},
            "link": None,
        },
        {
            "localized_name": "collision_mode",
            "name": "collision_mode",
            "type": "COMBO",
            "widget": {"name": "collision_mode"},
            "link": None,
        },
        {
            "localized_name": "detection_info",
            "name": "detection_info",
            "type": "COMBO",
            "widget": {"name": "detection_info"},
            "link": None,
        },
        {
            "localized_name": "export_workflow_metadata",
            "name": "export_workflow_metadata",
            "type": "BOOLEAN",
            "widget": {"name": "export_workflow_metadata"},
            "link": None,
        },
        {
            "localized_name": "subfolder",
            "name": "subfolder",
            "shape": 7,
            "type": "STRING",
            "widget": {"name": "subfolder"},
            "link": None,
        },
        {
            "localized_name": "model_folder",
            "name": "model_folder",
            "shape": 7,
            "type": "STRING",
            "widget": {"name": "model_folder"},
            "link": None,
        },
        {
            "localized_name": "clip_folder",
            "name": "clip_folder",
            "shape": 7,
            "type": "STRING",
            "widget": {"name": "clip_folder"},
            "link": None,
        },
    ]


def _organized_widgets(path_template: str) -> list[Any]:
    return [
        "",
        path_template,
        "Friendly",
        "Friendly",
        "",
        DEFAULT_FILENAME_PATTERN,
        "increment",
        "Off",
        True,
        "",
        "",
        "",
        "",
    ]


def _organized_properties(old_properties: Any, *, version: str | None) -> dict[str, Any]:
    properties = dict(old_properties) if isinstance(old_properties, dict) else {}
    properties.pop("cnr_id", None)
    properties.pop("models", None)
    properties["Node name for S&R"] = ORGANIZED_NODE_TYPE
    properties["aux_id"] = ORGANIZED_AUX_ID
    if version:
        properties["ver"] = version
    return properties


def _migrate_ui_node(node: dict[str, Any], *, version: str | None) -> None:
    path_template = _path_template_from_prefix(_filename_prefix_from_ui(node))
    node["type"] = ORGANIZED_NODE_TYPE
    node["inputs"] = _organized_inputs(_image_link(node))
    node["outputs"] = []
    node["properties"] = _organized_properties(node.get("properties"), version=version)
    node["widgets_values"] = _organized_widgets(path_template)


def _iter_node_lists(data: Any) -> list[list[Any]]:
    node_lists: list[list[Any]] = []
    if isinstance(data, dict):
        nodes = data.get("nodes")
        if isinstance(nodes, list):
            node_lists.append(nodes)
        for value in data.values():
            node_lists.extend(_iter_node_lists(value))
    elif isinstance(data, list):
        for item in data:
            node_lists.extend(_iter_node_lists(item))
    return node_lists


def _migrate_ui_workflow(data: Any, *, write: bool, version: str | None) -> tuple[int, int, int]:
    standard_nodes = 0
    organized_nodes = 0
    migrated_nodes = 0

    for nodes in _iter_node_lists(data):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = node.get("type")
            if node_type == ORGANIZED_NODE_TYPE:
                organized_nodes += 1
            elif node_type == STANDARD_NODE_TYPE:
                if write:
                    _migrate_ui_node(node, version=version)
                    migrated_nodes += 1
                    organized_nodes += 1
                else:
                    standard_nodes += 1

    return standard_nodes, organized_nodes, migrated_nodes


def _looks_like_api_prompt(data: Any) -> bool:
    return isinstance(data, dict) and all(
        isinstance(node, dict) and "class_type" in node for node in data.values()
    )


def _migrate_api_prompt(data: dict[str, Any], *, write: bool) -> tuple[int, int, int]:
    standard_nodes = 0
    organized_nodes = 0
    migrated_nodes = 0

    for node in data.values():
        if not isinstance(node, dict):
            continue
        class_type = node.get("class_type")
        if class_type == ORGANIZED_NODE_TYPE:
            organized_nodes += 1
        elif class_type == STANDARD_NODE_TYPE:
            if write:
                inputs = node.get("inputs")
                if not isinstance(inputs, dict):
                    inputs = {}
                filename_prefix = str(inputs.get("filename_prefix", ""))
                node["class_type"] = ORGANIZED_NODE_TYPE
                node["inputs"] = {
                    "images": inputs.get("images"),
                    "path_template": _path_template_from_prefix(filename_prefix),
                    "model_source": "Friendly",
                    "clip_source": "Friendly",
                    "filename_datetime": DEFAULT_FILENAME_PATTERN,
                    "collision_mode": "increment",
                    "detection_info": "Off",
                    "export_workflow_metadata": True,
                    "subfolder": "",
                    "model_folder": "",
                    "clip_folder": "",
                }
                migrated_nodes += 1
                organized_nodes += 1
            else:
                standard_nodes += 1

    return standard_nodes, organized_nodes, migrated_nodes


def migrate_workflow(path: Path, root: Path, *, write: bool, version: str | None) -> WorkflowMigration:
    data = _read_json(path)
    if _looks_like_api_prompt(data):
        standard_nodes, organized_nodes, migrated_nodes = _migrate_api_prompt(data, write=write)
    else:
        standard_nodes, organized_nodes, migrated_nodes = _migrate_ui_workflow(
            data,
            write=write,
            version=version,
        )

    changed = write and migrated_nodes > 0
    if changed:
        _dump_json(path, data)

    return WorkflowMigration(
        workflow=str(path.relative_to(root)),
        standard_nodes=standard_nodes,
        organized_nodes=organized_nodes,
        migrated_nodes=migrated_nodes,
        changed=changed,
    )


def scan_workflows(root: Path, *, write: bool = False, version: str | None = None) -> list[WorkflowMigration]:
    return [migrate_workflow(path, root, write=write, version=version) for path in _iter_json_files(root)]


def _summary(rows: list[WorkflowMigration]) -> dict[str, int]:
    return {
        "workflow_files": len(rows),
        "files_with_standard_nodes": sum(1 for row in rows if row.standard_nodes),
        "standard_nodes": sum(row.standard_nodes for row in rows),
        "organized_nodes": sum(row.organized_nodes for row in rows),
        "migrated_nodes": sum(row.migrated_nodes for row in rows),
        "changed_files": sum(1 for row in rows if row.changed),
    }


def _print_table(rows: list[WorkflowMigration]) -> None:
    relevant = [row for row in rows if row.standard_nodes or row.organized_nodes or row.changed]
    if not relevant:
        print("No SaveImage or SaveImageClean nodes found.")
        return

    header = f"{'STANDARD':>8} {'ORGANIZED':>9} {'MIGRATED':>8} {'CHANGED':>7} WORKFLOW"
    print(header)
    print("-" * len(header))
    for row in relevant:
        changed = "yes" if row.changed else "no"
        print(
            f"{row.standard_nodes:>8} {row.organized_nodes:>9} "
            f"{row.migrated_nodes:>8} {changed:>7} {row.workflow}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate standard ComfyUI SaveImage workflow nodes to Save Image Organized."
    )
    parser.add_argument(
        "workflow_root",
        nargs="?",
        type=Path,
        default=DEFAULT_WORKFLOW_ROOT,
        help=f"Workflow folder to scan. Default: {DEFAULT_WORKFLOW_ROOT}",
    )
    parser.add_argument("--write", action="store_true", help="Rewrite workflow files in place.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--verify-no-standard",
        action="store_true",
        help="Exit non-zero if any standard SaveImage nodes remain.",
    )
    parser.add_argument(
        "--node-version",
        default=None,
        help="Optional version/hash metadata to write into migrated UI node properties.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.workflow_root.resolve()
    if not root.exists():
        print(f"Workflow root does not exist: {root}", file=sys.stderr)
        return 2

    rows = scan_workflows(root, write=args.write, version=args.node_version)
    summary = _summary(rows)
    if args.json:
        print(
            json.dumps(
                {
                    "workflow_root": str(root),
                    "write": args.write,
                    "summary": summary,
                    "rows": [row.__dict__ for row in rows],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        _print_table(rows)
        print(f"\nSummary: {summary}")

    if args.verify_no_standard and summary["standard_nodes"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
