from __future__ import annotations

from datetime import datetime

import numpy as np
import pytest

import nodes


def test_strip_known_extension_removes_only_supported_suffix():
    assert nodes._strip_known_extension("model.safetensors") == "model"
    assert nodes._strip_known_extension("encoder.gguf") == "encoder"
    assert nodes._strip_known_extension("notes.txt") == "notes.txt"


def test_humanize_display_name_normalizes_known_model_alias_and_quant():
    value = nodes._humanize_display_name("flux-2-klein-9b-Q5_K_M.gguf", kind="model")
    assert value == "FLUX.2 Klein 9B [5K-M]"


def test_render_date_format_supports_single_letter_tokens():
    now = datetime(2026, 4, 22, 21, 7, 5)
    rendered = nodes._render_date_format("yyyy-M-d_h-m-s", now)
    assert rendered == "2026-4-22_21-7-5"


def test_render_path_template_resolves_variables_and_widget_placeholders():
    now = datetime(2026, 4, 22, 21, 22, 5)
    variables = {
        "TOP_FOLDER": "portraits",
        "MODEL_NAME": "FLUX.2 Klein 9B [5K-M]",
        "TEXT_ENCODER_NAME": "Lockout Qwen3 4B zimage V2 [Her][Q8]",
        "FILENAME": "2026-04-22_21-22-05",
    }
    prompt = {
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 42,
            },
            "title": "KSampler",
        }
    }

    rendered = nodes._render_path_template(
        "%TOP_FOLDER%/%MODEL_NAME%/%KSampler.seed%/%FILENAME%",
        variables,
        now,
        prompt,
    )

    assert rendered == "portraits/FLUX.2 Klein 9B [5K-M]/42/2026-04-22_21-22-05"


def test_render_path_template_rejects_unknown_variables():
    with pytest.raises(ValueError, match=r"Unknown path template variables: MODLE_NAME \(did you mean MODEL_NAME\?\)"):
        nodes._render_path_template(
            "%MODLE_NAME%",
            {"MODEL_NAME": "model"},
            datetime(2026, 4, 22, 21, 22, 5),
            {},
        )


def test_render_path_template_reports_unknown_node_with_known_candidates():
    with pytest.raises(ValueError, match=r"Unknown template node reference 'KSampler' in placeholder '%KSampler.seed%'"):
        nodes._render_path_template(
            "%KSampler.seed%",
            {},
            datetime(2026, 4, 22, 21, 22, 5),
            {
                "10": {
                    "class_type": "SamplerCustom",
                    "inputs": {
                        "seed": 42,
                    },
                    "title": "Sampler Custom",
                }
            },
        )


def test_render_path_template_reports_ambiguous_node_matches():
    prompt = {
        "10": {
            "class_type": "KSampler",
            "inputs": {"seed": 42},
            "title": "Shared Name",
        },
        "11": {
            "class_type": "KSamplerAdvanced",
            "inputs": {"seed": 99},
            "title": "Shared Name",
        },
    }

    with pytest.raises(ValueError, match=r"Ambiguous template node reference 'Shared Name'.*Use a unique title, Node name for S&R, or node id"):
        nodes._render_path_template(
            "%Shared Name.seed%",
            {},
            datetime(2026, 4, 22, 21, 22, 5),
            prompt,
        )


def test_render_path_template_reports_unknown_widget_with_suggestions():
    prompt = {
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 42,
                "steps": 20,
            },
            "title": "KSampler",
        }
    }

    with pytest.raises(ValueError, match=r"Unknown widget reference 'sead'.*Close matches: seed.*Available widget inputs: seed, steps"):
        nodes._render_path_template(
            "%KSampler.sead%",
            {"MODEL_NAME": "model"},
            datetime(2026, 4, 22, 21, 22, 5),
            prompt,
        )


def test_find_active_names_picks_nearest_unet_and_clip_loaders():
    prompt = {
        "1": {
            "class_type": "SaveImageClean",
            "inputs": {
                "images": ["2", 0],
            },
        },
        "2": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["3", 0],
                "clip": ["4", 0],
            },
        },
        "3": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "flux-2-klein-9b-Q5_K_M.gguf",
            },
        },
        "4": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {
                "clip_name": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
            },
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "flux-2-klein-9b-Q5_K_M.gguf",
        "ACTIVE_CLIP": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
    }


def test_resolve_target_path_increments_existing_files(workspace_tmp_path):
    saver = nodes.SaveImageClean()

    existing = workspace_tmp_path / "example.png"
    existing.write_bytes(b"first")

    target = saver._resolve_target_path(
        output_root=workspace_tmp_path,
        relative_path=existing.relative_to(workspace_tmp_path),
        collision_mode="increment",
    )

    assert target == workspace_tmp_path / "example-2.png"


def test_resolve_target_path_errors_when_requested(workspace_tmp_path):
    saver = nodes.SaveImageClean()

    existing = workspace_tmp_path / "example.png"
    existing.write_bytes(b"first")

    with pytest.raises(FileExistsError):
        saver._resolve_target_path(
            output_root=workspace_tmp_path,
            relative_path=existing.relative_to(workspace_tmp_path),
            collision_mode="error",
        )


def test_render_path_template_rejects_linked_or_unsupported_widget_values():
    prompt = {
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "seed": ["20", 0],
            },
            "title": "KSampler",
        }
    }

    with pytest.raises(ValueError, match=r"Template reference 'KSampler.seed' from placeholder '%KSampler.seed%' points to a linked or unsupported value"):
        nodes._render_path_template(
            "%KSampler.seed%",
            {},
            datetime(2026, 4, 22, 21, 22, 5),
            prompt,
        )


class DummyImage:
    def __init__(self, array):
        self._array = array

    def cpu(self):
        return self

    def numpy(self):
        return self._array


def test_save_images_includes_detection_summary_in_ui_text(workspace_tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    image = DummyImage(np.zeros((2, 2, 3), dtype=np.float32))
    prompt = {
        "1": {
            "class_type": "SaveImageClean",
            "inputs": {
                "images": ["2", 0],
            },
        },
        "2": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["3", 0],
                "clip": ["4", 0],
            },
        },
        "3": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "flux-2-klein-9b-Q5_K_M.gguf",
            },
        },
        "4": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {
                "clip_name": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
            },
        },
    }

    result = saver.save_images(
        images=[image],
        path_template=nodes.SaveImageClean.DEFAULT_TEMPLATE,
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Exact",
        detection_info="Summary",
        prompt=prompt,
        unique_id="1",
    )

    assert result["ui"]["text"][0].endswith(".png") is False
    assert "Detection Summary" in result["ui"]["text"]
    assert any("Model detection: workflow loader -> flux-2-klein-9b-Q5_K_M" in line for line in result["ui"]["text"])
    assert any("Model output: Friendly -> FLUX.2 Klein 9B [5K-M]" in line for line in result["ui"]["text"])
    assert any(
        "Text encoder output: Exact -> Lockout-Qwen3-4b-zimage-hereticV2-q8" in line
        for line in result["ui"]["text"]
    )


def test_save_images_verbose_detection_reports_custom_fallback(workspace_tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    image = DummyImage(np.zeros((2, 2, 3), dtype=np.float32))

    result = saver.save_images(
        images=[image],
        path_template=nodes.SaveImageClean.DEFAULT_TEMPLATE,
        collision_mode="increment",
        model_source="Custom",
        clip_source="Friendly",
        detection_info="Verbose",
        model_folder="my-model.safetensors",
        clip_folder="my-clip.gguf",
        prompt={"1": {"class_type": "SaveImageClean", "inputs": {}}},
        unique_id="1",
    )

    assert any("Model detection: custom fallback -> my-model" in line for line in result["ui"]["text"])
    assert any("Text encoder detection: custom fallback -> my-clip" in line for line in result["ui"]["text"])
    assert any("Model variants:" in line for line in result["ui"]["text"])
    assert any("Text encoder variants:" in line for line in result["ui"]["text"])
