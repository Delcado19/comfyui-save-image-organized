from __future__ import annotations

import argparse
import json
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW_ROOT = Path(r"H:\ComfyUI-Easy-Install\ComfyUI\user\default\workflows")


@dataclass
class DetectionRow:
    workflow: str
    save_id: str
    model: str
    text_encoder: str
    reason: str

    @property
    def status(self) -> str:
        if self.model and self.text_encoder:
            return "OK"
        if self.model or self.text_encoder:
            return "PARTIAL"
        return "MISS"


def _detection_reason(prompt: Any, save_id: str, active_names: dict[str, str], nodes_module: Any) -> str:
    model = active_names["ACTIVE_UNET"]
    text_encoder = active_names["ACTIVE_CLIP"]
    if model and text_encoder:
        return "detected"

    has_model_loader = False
    has_text_encoder_loader = False
    for _, node, _ in nodes_module._walk_prompt_upstream(prompt, save_id):
        class_type = str(node.get("class_type", ""))
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            inputs = {}

        has_model_loader = has_model_loader or nodes_module._get_unet_loader_priority(
            class_type,
            inputs,
        ) is not None
        has_text_encoder_loader = has_text_encoder_loader or nodes_module._get_clip_loader_priority(
            class_type,
            inputs,
        ) is not None
        checkpoint_loader_priority = nodes_module._get_checkpoint_loader_priority(class_type, inputs)
        if checkpoint_loader_priority is not None:
            has_model_loader = True
            has_text_encoder_loader = True

    if not has_model_loader and not has_text_encoder_loader:
        return "no model/text encoder loader reachable"
    if not model and not has_model_loader:
        return "no model loader reachable"
    if not text_encoder and not has_text_encoder_loader:
        return "no text encoder loader reachable"
    if not model:
        return "model loader reachable but no name resolved"
    if not text_encoder:
        return "text encoder loader reachable but no name resolved"
    return "detected"


def _ensure_repo_imports() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    if "folder_paths" not in sys.modules:
        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_output_directory = lambda: str(REPO_ROOT / "output")
        sys.modules["folder_paths"] = folder_paths


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _link_sources(links: Any) -> dict[Any, list[Any]]:
    sources: dict[Any, list[Any]] = {}
    if not isinstance(links, list):
        return sources

    for link in links:
        if isinstance(link, list) and len(link) >= 4:
            link_id, source_id, source_slot = link[:3]
            sources[link_id] = [str(source_id), int(source_slot)]
        elif isinstance(link, dict):
            link_id = link.get("id")
            source_id = link.get("origin_id")
            source_slot = link.get("origin_slot")
            if link_id is not None and source_id is not None and source_slot is not None:
                sources[link_id] = [str(source_id), int(source_slot)]
    return sources


def _widget_values_by_name(node: dict[str, Any]) -> dict[str, Any]:
    values = node.get("widgets_values") or []
    if isinstance(values, dict):
        return values
    if not isinstance(values, list):
        return {}

    result: dict[str, Any] = {}
    value_index = 0
    for input_def in node.get("inputs") or []:
        if not isinstance(input_def, dict):
            continue
        widget = input_def.get("widget")
        widget_name = widget.get("name") if isinstance(widget, dict) else None
        if widget_name and value_index < len(values):
            result[widget_name] = values[value_index]
            value_index += 1
    return result


def _node_title(node: dict[str, Any]) -> str | None:
    title = node.get("title")
    if isinstance(title, str) and title:
        return title

    properties = node.get("properties")
    if isinstance(properties, dict):
        search_name = properties.get("Node name for S&R")
        if isinstance(search_name, str) and search_name:
            return search_name
    return None


def _ui_workflow_to_prompt(workflow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = _link_sources(workflow.get("links"))
    prompt: dict[str, dict[str, Any]] = {}

    for node in workflow.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id"))
        inputs = _widget_values_by_name(node)

        for input_index, input_def in enumerate(node.get("inputs") or []):
            if not isinstance(input_def, dict):
                continue
            input_name = input_def.get("name")
            link_id = input_def.get("link")
            if link_id in sources:
                if not isinstance(input_name, str) or not input_name:
                    input_name = f"__linked_input_{input_index}"
                inputs[input_name] = sources[link_id]

        prompt_node: dict[str, Any] = {
            "class_type": node.get("type", ""),
            "inputs": inputs,
            "widgets_values": node.get("widgets_values") or [],
        }
        title = _node_title(node)
        if title:
            prompt_node["_meta"] = {"title": title}
        prompt[node_id] = prompt_node

    return prompt


def _looks_like_api_prompt(data: Any) -> bool:
    return isinstance(data, dict) and all(
        isinstance(node, dict) and "class_type" in node for node in data.values()
    )


def workflow_to_prompt(data: Any) -> dict[str, dict[str, Any]]:
    if _looks_like_api_prompt(data):
        return data
    if isinstance(data, dict) and isinstance(data.get("nodes"), list):
        return _ui_workflow_to_prompt(data)
    raise ValueError("unsupported JSON workflow format")


def _iter_json_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.json") if path.is_file() and not path.name.startswith("."))


def _find_save_ids(prompt: dict[str, dict[str, Any]]) -> list[str]:
    return [
        node_id
        for node_id, node in prompt.items()
        if isinstance(node, dict) and node.get("class_type") == "SaveImageClean"
    ]


def scan_workflows(workflow_root: Path, *, limit: int | None = None) -> tuple[list[DetectionRow], list[str]]:
    _ensure_repo_imports()
    import nodes  # noqa: PLC0415

    rows: list[DetectionRow] = []
    errors: list[str] = []

    for path in _iter_json_files(workflow_root):
        try:
            prompt = workflow_to_prompt(_read_json(path))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        save_ids = _find_save_ids(prompt)
        if not save_ids:
            continue

        for save_id in save_ids:
            try:
                active_names = nodes._find_active_names(prompt, save_id)
            except Exception as exc:  # pragma: no cover - defensive maintainer tool boundary
                errors.append(f"{path} SaveImageClean {save_id}: {exc}")
                continue

            rows.append(
                DetectionRow(
                    workflow=str(path.relative_to(workflow_root)),
                    save_id=save_id,
                    model=active_names["ACTIVE_UNET"],
                    text_encoder=active_names["ACTIVE_CLIP"],
                    reason=_detection_reason(prompt, save_id, active_names, nodes),
                )
            )
            if limit is not None and len(rows) >= limit:
                return rows, errors

    return rows, errors


def _print_table(rows: list[DetectionRow], errors: list[str]) -> None:
    if not rows:
        print("No SaveImageClean nodes found.")
    else:
        header = f"{'STATUS':8} {'SAVE':>5} {'REASON':38} {'WORKFLOW':60} MODEL / TEXT ENCODER"
        print(header)
        print("-" * len(header))
        for row in rows:
            names = f"{row.model or '<none>'} / {row.text_encoder or '<none>'}"
            print(f"{row.status:8} {row.save_id:>5} {row.reason:38} {row.workflow[:60]:60} {names}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")


def _summary(rows: list[DetectionRow], errors: list[str]) -> dict[str, int]:
    return {
        "save_nodes": len(rows),
        "ok": sum(1 for row in rows if row.status == "OK"),
        "partial": sum(1 for row in rows if row.status == "PARTIAL"),
        "miss": sum(1 for row in rows if row.status == "MISS"),
        "errors": len(errors),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan local ComfyUI workflow JSON files and report Save Image Organized detection."
    )
    parser.add_argument(
        "workflow_root",
        nargs="?",
        type=Path,
        default=DEFAULT_WORKFLOW_ROOT,
        help=f"Workflow folder to scan. Default: {DEFAULT_WORKFLOW_ROOT}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after this many SaveImageClean nodes.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--fail-on-miss",
        action="store_true",
        help="Exit non-zero if any SaveImageClean node has no model or text encoder detection.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workflow_root = args.workflow_root.resolve()
    if not workflow_root.exists():
        print(f"Workflow root does not exist: {workflow_root}", file=sys.stderr)
        return 2

    rows, errors = scan_workflows(workflow_root, limit=args.limit)
    summary = _summary(rows, errors)

    if args.json:
        print(
            json.dumps(
                {
                    "workflow_root": str(workflow_root),
                    "summary": summary,
                    "rows": [row.__dict__ | {"status": row.status} for row in rows],
                    "errors": errors,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        _print_table(rows, errors)
        print(f"\nSummary: {summary}")

    if errors:
        return 1
    if args.fail_on_miss and (summary["partial"] or summary["miss"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
