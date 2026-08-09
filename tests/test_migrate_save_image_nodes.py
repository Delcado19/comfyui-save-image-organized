from __future__ import annotations

import json

import nodes
from tools.migrate_save_image_nodes import (
    DEFAULT_FILENAME_PATTERN,
    ORGANIZED_AUX_ID,
    ORGANIZED_NODE_TYPE,
    _organized_widgets,
    migrate_workflow,
    scan_workflows,
)


def test_organized_widgets_stays_aligned_with_input_types():
    # Regression guard: _organized_widgets is a plain positional list that must
    # match SaveImageClean.INPUT_TYPES()'s required-then-optional widget count
    # exactly, or ComfyUI's positional widgets_values restore silently shifts
    # every value into the wrong widget's slot. This is the check that would
    # have caught the original misalignment.
    input_types = nodes.SaveImageClean.INPUT_TYPES()
    widget_names = [name for name in input_types["required"] if name != "images"]
    widget_names += list(input_types["optional"])

    assert len(_organized_widgets("some/path")) == len(widget_names)


def _ui_workflow():
    return {
        "nodes": [
            {
                "id": 1,
                "type": "SaveImage",
                "pos": [100, 200],
                "size": [320, 260],
                "flags": {"collapsed": False},
                "order": 7,
                "mode": 0,
                "inputs": [{"name": "images", "type": "IMAGE", "link": 12}],
                "outputs": [],
                "title": "Final save",
                "properties": {
                    "cnr_id": "comfy-core",
                    "ver": "0.3.76",
                    "Node name for S&R": "SaveImage",
                },
                "widgets_values": ["renders/test"],
            },
            {
                "id": 2,
                "type": "PreviewImage",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 13}],
                "widgets_values": [],
            },
        ],
        "links": [
            [12, 99, 0, 1, 0, "IMAGE"],
            [13, 99, 0, 2, 0, "IMAGE"],
        ],
    }


def test_scan_workflows_dry_run_reports_standard_nodes_without_writing(workspace_tmp_path):
    workflow_path = workspace_tmp_path / "workflow.json"
    original = _ui_workflow()
    workflow_path.write_text(json.dumps(original), encoding="utf-8")

    rows = scan_workflows(workspace_tmp_path)

    assert len(rows) == 1
    assert rows[0].standard_nodes == 1
    assert rows[0].organized_nodes == 0
    assert rows[0].migrated_nodes == 0
    assert rows[0].changed is False
    assert json.loads(workflow_path.read_text(encoding="utf-8")) == original


def test_migrate_workflow_preserves_ui_geometry_and_links(workspace_tmp_path):
    workflow_path = workspace_tmp_path / "workflow.json"
    workflow_path.write_text(json.dumps(_ui_workflow()), encoding="utf-8")

    row = migrate_workflow(workflow_path, workspace_tmp_path, write=True, version="test-version")
    migrated = json.loads(workflow_path.read_text(encoding="utf-8"))
    save_node = migrated["nodes"][0]

    assert row.standard_nodes == 0
    assert row.migrated_nodes == 1
    assert row.changed is True
    assert save_node["id"] == 1
    assert save_node["type"] == ORGANIZED_NODE_TYPE
    assert save_node["pos"] == [100, 200]
    assert save_node["size"] == [320, 260]
    assert save_node["flags"] == {"collapsed": False}
    assert save_node["order"] == 7
    assert save_node["mode"] == 0
    assert save_node["title"] == "Final save"
    assert save_node["inputs"][0] == {
        "localized_name": "images",
        "name": "images",
        "type": "IMAGE",
        "link": 12,
    }
    # Left empty rather than guessed at: ComfyUI's frontend adds any output
    # sockets missing from a saved workflow by reconciling against the live
    # node definition on load.
    assert save_node["outputs"] == []
    assert migrated["links"] == [
        [12, 99, 0, 1, 0, "IMAGE"],
        [13, 99, 0, 2, 0, "IMAGE"],
    ]
    # Must stay positionally aligned with SaveImageClean.INPUT_TYPES()'s
    # required-then-optional widget order: path_template, model_source,
    # clip_source, filename_datetime, collision_mode, detection_info,
    # export_workflow_metadata, subfolder, model_folder, clip_folder,
    # image_format, image_quality, loader_priority.
    assert save_node["widgets_values"] == [
        "renders/test/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%",
        "Friendly",
        "Friendly",
        DEFAULT_FILENAME_PATTERN,
        "increment",
        "Off",
        True,
        "",
        "",
        "",
        "PNG",
        95,
        "Nearest",
    ]
    assert save_node["properties"]["Node name for S&R"] == ORGANIZED_NODE_TYPE
    assert save_node["properties"]["aux_id"] == ORGANIZED_AUX_ID
    assert save_node["properties"]["ver"] == "test-version"
    assert "cnr_id" not in save_node["properties"]


def test_migrate_workflow_leaves_existing_organized_nodes_unchanged(workspace_tmp_path):
    workflow = _ui_workflow()
    workflow["nodes"][0]["type"] = ORGANIZED_NODE_TYPE
    workflow["nodes"][0]["widgets_values"] = ["existing"]
    workflow_path = workspace_tmp_path / "workflow.json"
    workflow_path.write_text(json.dumps(workflow), encoding="utf-8")

    row = migrate_workflow(workflow_path, workspace_tmp_path, write=True, version="test-version")
    migrated = json.loads(workflow_path.read_text(encoding="utf-8"))

    assert row.standard_nodes == 0
    assert row.organized_nodes == 1
    assert row.migrated_nodes == 0
    assert row.changed is False
    assert migrated == workflow


def test_migrate_workflow_updates_api_prompt_inputs(workspace_tmp_path):
    prompt = {
        "1": {
            "class_type": "SaveImage",
            "inputs": {"images": ["2", 0], "filename_prefix": "ComfyUI"},
        }
    }
    workflow_path = workspace_tmp_path / "prompt.json"
    workflow_path.write_text(json.dumps(prompt), encoding="utf-8")

    row = migrate_workflow(workflow_path, workspace_tmp_path, write=True, version=None)
    migrated = json.loads(workflow_path.read_text(encoding="utf-8"))

    assert row.standard_nodes == 0
    assert row.migrated_nodes == 1
    assert migrated["1"] == {
        "class_type": ORGANIZED_NODE_TYPE,
        "inputs": {
            "images": ["2", 0],
            "path_template": "ComfyUI/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%",
            "model_source": "Friendly",
            "clip_source": "Friendly",
            "filename_datetime": DEFAULT_FILENAME_PATTERN,
            "collision_mode": "increment",
            "detection_info": "Off",
            "export_workflow_metadata": True,
            "subfolder": "",
            "model_folder": "",
            "clip_folder": "",
        },
    }
