from __future__ import annotations

import json

from tools.validate_local_workflows import scan_workflows, workflow_to_prompt


def _ui_workflow():
    return {
        "nodes": [
            {
                "id": 1,
                "type": "SaveImageClean",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 12}],
            },
            {
                "id": 2,
                "type": "KSampler",
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 10},
                    {"name": "clip", "type": "CLIP", "link": 11},
                ],
            },
            {
                "id": 3,
                "type": "CheckpointLoader|pysssss",
                "inputs": [
                    {"name": "ckpt_name", "type": "COMBO", "widget": {"name": "ckpt_name"}}
                ],
                "widgets_values": [
                    {"content": "SDXL/Anubis XL_v1.safetensors", "image": None},
                    "[none]",
                ],
            },
        ],
        "links": [
            [10, 3, 0, 2, 0, "MODEL"],
            [11, 3, 1, 2, 1, "CLIP"],
            [12, 2, 0, 1, 0, "IMAGE"],
        ],
    }


def _ui_workflow_with_unnamed_reroute():
    return {
        "nodes": [
            {
                "id": 1,
                "type": "SaveImageClean",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 12}],
            },
            {
                "id": 2,
                "type": "KSampler",
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 10},
                    {"name": "clip", "type": "CLIP", "link": 11},
                ],
            },
            {
                "id": 3,
                "type": "CheckpointLoaderSimple",
                "inputs": [
                    {"name": "ckpt_name", "type": "COMBO", "widget": {"name": "ckpt_name"}}
                ],
                "widgets_values": ["SDXL/Anubis XL_v1.safetensors"],
            },
            {
                "id": 4,
                "type": "Reroute",
                "inputs": [{"name": "", "type": "*", "link": 13}],
                "outputs": [{"name": "", "type": "MODEL", "links": [10]}],
            },
        ],
        "links": [
            [13, 3, 0, 4, 0, "MODEL"],
            [10, 4, 0, 2, 0, "MODEL"],
            [11, 3, 1, 2, 1, "CLIP"],
            [12, 2, 0, 1, 0, "IMAGE"],
        ],
    }


def test_workflow_to_prompt_converts_ui_links_and_widgets():
    prompt = workflow_to_prompt(_ui_workflow())

    assert prompt["1"]["inputs"]["images"] == ["2", 0]
    assert prompt["2"]["inputs"]["model"] == ["3", 0]
    assert prompt["2"]["inputs"]["clip"] == ["3", 1]
    assert prompt["3"]["inputs"]["ckpt_name"] == {
        "content": "SDXL/Anubis XL_v1.safetensors",
        "image": None,
    }


def test_workflow_to_prompt_preserves_unnamed_linked_inputs():
    prompt = workflow_to_prompt(_ui_workflow_with_unnamed_reroute())

    assert prompt["4"]["inputs"]["__linked_input_0"] == ["3", 0]


def test_scan_workflows_detects_saved_ui_workflow(workspace_tmp_path):
    (workspace_tmp_path / "workflow.json").write_text(json.dumps(_ui_workflow()), encoding="utf-8")

    rows, errors = scan_workflows(workspace_tmp_path)

    assert errors == []
    assert len(rows) == 1
    assert rows[0].status == "OK"
    assert rows[0].model == "SDXL/Anubis XL_v1.safetensors"
    assert rows[0].text_encoder == "SDXL/Anubis XL_v1.safetensors"


def test_scan_workflows_follows_unnamed_reroute_inputs(workspace_tmp_path):
    (workspace_tmp_path / "workflow.json").write_text(
        json.dumps(_ui_workflow_with_unnamed_reroute()),
        encoding="utf-8",
    )

    rows, errors = scan_workflows(workspace_tmp_path)

    assert errors == []
    assert len(rows) == 1
    assert rows[0].status == "OK"
    assert rows[0].model == "SDXL/Anubis XL_v1.safetensors"
    assert rows[0].text_encoder == "SDXL/Anubis XL_v1.safetensors"
