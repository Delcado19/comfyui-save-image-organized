from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pytest
from PIL import Image

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


def test_find_active_names_falls_back_to_checkpoint_loader_values():
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
                "clip": ["3", 1],
            },
        },
        "3": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "sdxl-checkpoint-v1.safetensors",
            },
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "sdxl-checkpoint-v1.safetensors",
        "ACTIVE_CLIP": "sdxl-checkpoint-v1.safetensors",
    }


def test_find_active_names_detects_diffusion_model_loader_variants():
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
            "class_type": "LoadDiffusionModelGGUF",
            "inputs": {
                "diffusion_model_name": "qwen-image-edit-2509-Q8_0.gguf",
            },
        },
        "4": {
            "class_type": "TextEncoderLoader",
            "inputs": {
                "text_encoder_name": "umt5xxl-fp16.gguf",
            },
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "qwen-image-edit-2509-Q8_0.gguf",
        "ACTIVE_CLIP": "umt5xxl-fp16.gguf",
    }


def test_find_active_names_ignores_cross_contaminating_generic_loader_fields():
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
            "class_type": "LoadDiffusionModelGGUF",
            "inputs": {
                "name": "umt5xxl-fp16.gguf",
                "diffusion_model_name": "qwen-image-edit-2509-Q8_0.gguf",
            },
        },
        "4": {
            "class_type": "TextEncoderLoader",
            "inputs": {
                "model_name": "qwen-image-edit-2509-Q8_0.gguf",
                "text_encoder_name": "umt5xxl-fp16.gguf",
            },
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "qwen-image-edit-2509-Q8_0.gguf",
        "ACTIVE_CLIP": "umt5xxl-fp16.gguf",
    }


def test_find_active_names_resolves_getnode_setnode_bridges():
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
            "class_type": "GetNode",
            "title": "Get_MODEL",
            "inputs": {},
        },
        "4": {
            "class_type": "GetNode",
            "title": "Get_CLIP",
            "inputs": {},
        },
        "5": {
            "class_type": "SetNode",
            "title": "Set_MODEL",
            "inputs": {
                "MODEL": ["6", 0],
            },
        },
        "6": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {
                "unet_name": "z_image-Q5_K_S.gguf",
            },
        },
        "7": {
            "class_type": "SetNode",
            "title": "Set_CLIP",
            "inputs": {
                "CLIP": ["8", 0],
            },
        },
        "8": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {
                "clip_name": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
            },
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "z_image-Q5_K_S.gguf",
        "ACTIVE_CLIP": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
    }


def test_find_active_names_respects_comfyswitchnode_selected_branch():
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
                "clip": ["8", 0],
            },
        },
        "3": {
            "class_type": "ComfySwitchNode",
            "inputs": {
                "on_false": ["4", 0],
                "on_true": ["5", 0],
                "switch": False,
            },
        },
        "4": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {
                "unet_name": "z_image-Q5_K_S.gguf",
            },
        },
        "5": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "jibMixZIT_v10.safetensors",
            },
        },
        "8": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {
                "clip_name": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
            },
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "z_image-Q5_K_S.gguf",
        "ACTIVE_CLIP": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
    }


def test_find_active_names_supports_widget_only_loader_values():
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
            "class_type": "UnetLoaderGGUF",
            "inputs": {},
            "widgets_values": ["zImageTurboGGUF_q80.gguf"],
        },
        "4": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {},
            "widgets_values": ["huihui-qwen3-4b-abliterated-v2-q8_0.gguf", "lumina2"],
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "zImageTurboGGUF_q80.gguf",
        "ACTIVE_CLIP": "huihui-qwen3-4b-abliterated-v2-q8_0.gguf",
    }


def test_find_active_names_returns_empty_for_postprocess_only_save_branch():
    prompt = {
        "1": {
            "class_type": "SaveImageClean",
            "inputs": {
                "images": ["2", 0],
            },
        },
        "2": {
            "class_type": "ImageScaleToTotalPixels",
            "inputs": {
                "image": ["3", 0],
            },
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {},
        },
    }

    active_names = nodes._find_active_names(prompt, "1")

    assert active_names == {
        "ACTIVE_UNET": "",
        "ACTIVE_CLIP": "",
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


def test_resolve_target_path_overwrites_when_requested(workspace_tmp_path):
    saver = nodes.SaveImageClean()

    existing = workspace_tmp_path / "example.png"
    existing.write_bytes(b"first")

    target = saver._resolve_target_path(
        output_root=workspace_tmp_path,
        relative_path=existing.relative_to(workspace_tmp_path),
        collision_mode="overwrite",
    )

    assert target == existing


def test_resolve_target_path_uses_seconds_name_when_requested(workspace_tmp_path, monkeypatch):
    saver = nodes.SaveImageClean()

    existing = workspace_tmp_path / "example.png"
    existing.write_bytes(b"first")

    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 4, 22, 21, 22, 5)

    monkeypatch.setattr(nodes, "datetime", FixedDateTime)

    target = saver._resolve_target_path(
        output_root=workspace_tmp_path,
        relative_path=existing.relative_to(workspace_tmp_path),
        collision_mode="seconds",
    )

    assert target == workspace_tmp_path / "2026-04-22_21-22-05.png"


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


def test_render_path_template_resolves_node_name_for_search_and_replace():
    prompt = {
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 31415,
            },
            "_meta": {
                "Node name for S&R": "Sampler Alias",
            },
        }
    }

    rendered = nodes._render_path_template(
        "%Sampler Alias.seed%",
        {},
        datetime(2026, 4, 22, 21, 22, 5),
        prompt,
    )

    assert rendered == "31415"


def test_render_path_template_resolves_direct_node_id_references():
    prompt = {
        "42": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 777,
            },
        }
    }

    rendered = nodes._render_path_template(
        "%42.seed%",
        {},
        datetime(2026, 4, 22, 21, 22, 5),
        prompt,
    )

    assert rendered == "777"


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
        export_workflow_metadata=True,
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
        export_workflow_metadata=True,
        model_folder="my-model.safetensors",
        clip_folder="my-clip.gguf",
        prompt={"1": {"class_type": "SaveImageClean", "inputs": {}}},
        unique_id="1",
    )

    assert any("Model detection: custom fallback -> my-model" in line for line in result["ui"]["text"])
    assert any("Text encoder detection: custom fallback -> my-clip" in line for line in result["ui"]["text"])
    assert any("Model variants:" in line for line in result["ui"]["text"])
    assert any("Text encoder variants:" in line for line in result["ui"]["text"])


def test_save_images_verbose_detection_reports_missing_loader_on_current_branch(workspace_tmp_path):
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
            "class_type": "ImageScaleToTotalPixels",
            "inputs": {
                "image": ["3", 0],
            },
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {},
        },
    }

    result = saver.save_images(
        images=[image],
        path_template=nodes.SaveImageClean.DEFAULT_TEMPLATE,
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Verbose",
        export_workflow_metadata=True,
        prompt=prompt,
        unique_id="1",
    )

    assert any(
        "Model detection: no workflow loader found on this save branch, using default placeholder" in line
        for line in result["ui"]["text"]
    )
    assert any(
        "Text encoder detection: no workflow loader found on this save branch, using default placeholder" in line
        for line in result["ui"]["text"]
    )
    assert any("Model output: Friendly -> model" in line for line in result["ui"]["text"])
    assert any("Text encoder output: Friendly -> text encoder" in line for line in result["ui"]["text"])


def test_save_images_includes_structured_detection_snapshot_in_ui(workspace_tmp_path):
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
                "seed": 321,
            },
        },
        "3": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "Flux\\flux-2-klein-9b-Q5_K_M.gguf",
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
        detection_info="Off",
        export_workflow_metadata=True,
        prompt=prompt,
        unique_id="1",
    )

    payload = result["ui"]["save_image_clean"][0]
    assert payload["model_detection_source"] == "workflow"
    assert payload["text_encoder_detection_source"] == "workflow"
    assert payload["model_detection_label"] == "UNETLoader (node id 3)"
    assert payload["text_encoder_detection_label"] == "CLIPLoaderGGUF (node id 4)"
    assert payload["detected_model_name"] == "flux-2-klein-9b-Q5_K_M"
    assert payload["detected_text_encoder_name"] == "Lockout-Qwen3-4b-zimage-hereticV2-q8"
    assert payload["selected_model_source"] == "Friendly"
    assert payload["selected_text_encoder_source"] == "Exact"
    assert payload["selected_model_name"] == "FLUX.2 Klein 9B [5K-M]"
    assert payload["selected_text_encoder_name"] == "Lockout-Qwen3-4b-zimage-hereticV2-q8"
    assert payload["seed"] == "321"
    assert payload["width"] == "2"
    assert payload["height"] == "2"
    assert payload["detection_lines"] == []


def test_save_images_increments_across_multiple_images_and_creates_files(workspace_tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    images = [
        DummyImage(np.zeros((2, 2, 3), dtype=np.float32)),
        DummyImage(np.ones((2, 2, 3), dtype=np.float32)),
    ]

    result = saver.save_images(
        images=images,
        path_template="%TOP_FOLDER%/%FILENAME%",
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Off",
        export_workflow_metadata=True,
        subfolder="batch-tests",
        filename_datetime="sample-output",
        prompt={"1": {"class_type": "SaveImageClean", "inputs": {}}},
        unique_id="1",
    )

    saved_images = result["ui"]["images"]
    assert [item["filename"] for item in saved_images] == ["sample-output.png", "sample-output-2.png"]
    assert all(item["subfolder"] == "batch-tests" for item in saved_images)

    first_file = workspace_tmp_path / "batch-tests" / "sample-output.png"
    second_file = workspace_tmp_path / "batch-tests" / "sample-output-2.png"
    assert first_file.exists()
    assert second_file.exists()


def test_save_images_preserves_prompt_and_extra_png_metadata(workspace_tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    image = DummyImage(np.zeros((2, 2, 3), dtype=np.float32))
    prompt = {"workflow": "metadata-check"}
    extra_pnginfo = {
        "seed": 1234,
        "sampler": "euler",
    }

    result = saver.save_images(
        images=[image],
        path_template="%TOP_FOLDER%/%FILENAME%",
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Off",
        export_workflow_metadata=True,
        subfolder="metadata-tests",
        filename_datetime="meta-output",
        prompt=prompt,
        extra_pnginfo=extra_pnginfo,
        unique_id="1",
    )

    saved_file = workspace_tmp_path / "metadata-tests" / result["ui"]["images"][0]["filename"]
    with Image.open(saved_file) as png:
        assert png.info["prompt"] == json.dumps(prompt)
        assert png.info["seed"] == json.dumps(extra_pnginfo["seed"])
        assert png.info["sampler"] == json.dumps(extra_pnginfo["sampler"])


def test_save_images_can_disable_workflow_metadata_export(workspace_tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    image = DummyImage(np.zeros((2, 2, 3), dtype=np.float32))

    result = saver.save_images(
        images=[image],
        path_template="%TOP_FOLDER%/%FILENAME%",
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Off",
        export_workflow_metadata=False,
        subfolder="metadata-tests",
        filename_datetime="meta-off",
        prompt={"workflow": "disabled"},
        extra_pnginfo={"seed": 1234, "workflow": {"nodes": 1}},
        unique_id="1",
    )

    saved_file = workspace_tmp_path / "metadata-tests" / result["ui"]["images"][0]["filename"]
    with Image.open(saved_file) as png:
        assert "prompt" not in png.info
        assert "seed" not in png.info
        assert "workflow" not in png.info


def test_save_images_supports_convenience_variables(workspace_tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    images = [
        DummyImage(np.zeros((3, 4, 3), dtype=np.float32)),
        DummyImage(np.zeros((3, 4, 3), dtype=np.float32)),
    ]
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
                "seed": 321,
                "steps": 30,
                "cfg": 4.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 0.75,
            },
        },
    }

    result = saver.save_images(
        images=images,
        path_template=(
            "%WIDTH%x%HEIGHT%/%SEED%/%STEPS%steps-cfg%CFG%/"
            "%SAMPLER%-%SCHEDULER%-d%DENOISE%/%BATCH_INDEX%-of-%BATCH_SIZE%"
        ),
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Off",
        export_workflow_metadata=True,
        prompt=prompt,
        unique_id="1",
    )

    saved_images = result["ui"]["images"]
    assert [item["filename"] for item in saved_images] == ["1-of-2.png", "2-of-2.png"]
    expected_subfolder = r"4x3\321\30steps-cfg4.5\dpmpp_2m-karras-d0.75"
    assert [item["subfolder"] for item in saved_images] == [expected_subfolder, expected_subfolder]
    assert (
        workspace_tmp_path / "4x3" / "321" / "30steps-cfg4.5" / "dpmpp_2m-karras-d0.75" / "1-of-2.png"
    ).exists()
    assert (
        workspace_tmp_path / "4x3" / "321" / "30steps-cfg4.5" / "dpmpp_2m-karras-d0.75" / "2-of-2.png"
    ).exists()

    payload = result["ui"]["save_image_clean"][0]
    assert payload["seed"] == "321"
    assert payload["steps"] == "30"
    assert payload["cfg"] == "4.5"
    assert payload["sampler"] == "dpmpp_2m"
    assert payload["scheduler"] == "karras"
    assert payload["denoise"] == "0.75"
