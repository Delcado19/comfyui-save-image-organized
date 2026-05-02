from __future__ import annotations

import json

from tools.validate_local_workflows import (
    DetectionRow,
    _summary,
    scan_workflows,
    workflow_to_prompt,
)


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


def _ui_workflow_without_reachable_loader():
    return {
        "nodes": [
            {
                "id": 1,
                "type": "SaveImageClean",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 12}],
            },
            {
                "id": 2,
                "type": "LoadImage",
                "inputs": [
                    {"name": "image", "type": "COMBO", "widget": {"name": "image"}},
                ],
                "widgets_values": ["input.png"],
            },
        ],
        "links": [
            [12, 2, 0, 1, 0, "IMAGE"],
        ],
    }


def _ui_workflow_with_image_only_postprocess():
    return {
        "nodes": [
            {
                "id": 1,
                "type": "SaveImageClean",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 12}],
            },
            {
                "id": 2,
                "type": "FastFilmGrain",
                "inputs": [{"name": "image", "type": "IMAGE", "link": 11}],
            },
            {
                "id": 3,
                "type": "LoadImage",
                "inputs": [
                    {"name": "image", "type": "COMBO", "widget": {"name": "image"}},
                ],
                "widgets_values": ["input.png"],
            },
        ],
        "links": [
            [11, 3, 0, 2, 0, "IMAGE"],
            [12, 2, 0, 1, 0, "IMAGE"],
        ],
    }


def _ui_workflow_with_upscale_model_only():
    return {
        "nodes": [
            {
                "id": 1,
                "type": "SaveImageClean",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 12}],
            },
            {
                "id": 2,
                "type": "Upscale by Factor with Model (WLSH)",
                "inputs": [
                    {"name": "image", "type": "IMAGE", "link": 10},
                    {"name": "upscale_model", "type": "UPSCALE_MODEL", "link": 11},
                ],
            },
            {
                "id": 3,
                "type": "LoadImage",
                "inputs": [
                    {"name": "image", "type": "COMBO", "widget": {"name": "image"}},
                ],
                "widgets_values": ["input.png"],
            },
            {
                "id": 4,
                "type": "UpscaleModelLoader",
                "inputs": [
                    {"name": "model_name", "type": "COMBO", "widget": {"name": "model_name"}},
                ],
                "widgets_values": ["upscaler.pth"],
            },
        ],
        "links": [
            [10, 3, 0, 2, 0, "IMAGE"],
            [11, 4, 0, 2, 1, "UPSCALE_MODEL"],
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
    assert rows[0].reason == "detected"
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
    assert rows[0].reason == "detected"
    assert rows[0].model == "SDXL/Anubis XL_v1.safetensors"
    assert rows[0].text_encoder == "SDXL/Anubis XL_v1.safetensors"


def test_scan_workflows_explains_missing_loader_branch(workspace_tmp_path):
    (workspace_tmp_path / "workflow.json").write_text(
        json.dumps(_ui_workflow_without_reachable_loader()),
        encoding="utf-8",
    )

    rows, errors = scan_workflows(workspace_tmp_path)

    assert errors == []
    assert len(rows) == 1
    assert rows[0].status == "MISS"
    assert rows[0].reason == "no model/text encoder loader reachable"
    assert rows[0].model == ""
    assert rows[0].text_encoder == ""


def test_scan_workflows_treats_image_only_postprocess_as_expected_miss(workspace_tmp_path):
    (workspace_tmp_path / "workflow.json").write_text(
        json.dumps(_ui_workflow_with_image_only_postprocess()),
        encoding="utf-8",
    )

    rows, errors = scan_workflows(workspace_tmp_path)

    assert errors == []
    assert len(rows) == 1
    assert rows[0].status == "MISS"
    assert rows[0].reason == "no model/text encoder loader reachable"


def test_scan_workflows_does_not_treat_upscale_model_as_generation_model(workspace_tmp_path):
    (workspace_tmp_path / "workflow.json").write_text(
        json.dumps(_ui_workflow_with_upscale_model_only()),
        encoding="utf-8",
    )

    rows, errors = scan_workflows(workspace_tmp_path)

    assert errors == []
    assert len(rows) == 1
    assert rows[0].status == "MISS"
    assert rows[0].reason == "no model/text encoder loader reachable"


def test_summary_counts_unresolved_loader_names():
    rows = [
        DetectionRow(
            workflow="ok.json",
            save_id="1",
            model="model.safetensors",
            text_encoder="clip.safetensors",
            reason="detected",
        ),
        DetectionRow(
            workflow="expected-miss.json",
            save_id="2",
            model="",
            text_encoder="",
            reason="no model/text encoder loader reachable",
        ),
        DetectionRow(
            workflow="broken-loader.json",
            save_id="3",
            model="",
            text_encoder="clip.safetensors",
            reason="model loader reachable but no name resolved",
        ),
    ]

    assert _summary(rows, []) == {
        "save_nodes": 3,
        "ok": 1,
        "partial": 1,
        "miss": 1,
        "unresolved": 1,
        "errors": 0,
    }
