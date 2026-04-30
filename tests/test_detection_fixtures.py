from __future__ import annotations

import nodes


def test_detection_fixture_blocks_cross_contamination(load_prompt_fixture):
    prompt = load_prompt_fixture("detection_cross_contamination.json")

    assert nodes._find_active_names(prompt, "1") == {
        "ACTIVE_UNET": "qwen-image-edit-2509-Q8_0.gguf",
        "ACTIVE_CLIP": "umt5xxl-fp16.gguf",
    }


def test_detection_fixture_resolves_get_set_bridges(load_prompt_fixture):
    prompt = load_prompt_fixture("detection_get_set_bridge.json")

    assert nodes._find_active_names(prompt, "1") == {
        "ACTIVE_UNET": "z_image-Q5_K_S.gguf",
        "ACTIVE_CLIP": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
    }


def test_detection_fixture_respects_switch_selection(load_prompt_fixture):
    prompt = load_prompt_fixture("detection_switch_branch.json")

    assert nodes._find_active_names(prompt, "1") == {
        "ACTIVE_UNET": "z_image-Q5_K_S.gguf",
        "ACTIVE_CLIP": "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf",
    }


def test_detection_fixture_supports_widget_only_loaders(load_prompt_fixture):
    prompt = load_prompt_fixture("detection_widget_only_loader.json")

    assert nodes._find_active_names(prompt, "1") == {
        "ACTIVE_UNET": "zImageTurboGGUF_q80.gguf",
        "ACTIVE_CLIP": "huihui-qwen3-4b-abliterated-v2-q8_0.gguf",
    }


def test_detection_fixture_supports_checkpoint_loaders(load_prompt_fixture):
    prompt = load_prompt_fixture("detection_checkpoint_loader.json")

    assert nodes._find_active_names(prompt, "1") == {
        "ACTIVE_UNET": "sd15/juggernaut_reborn.safetensors",
        "ACTIVE_CLIP": "sd15/juggernaut_reborn.safetensors",
    }


def test_detection_fixture_supports_checkpoint_widget_object_values(load_prompt_fixture):
    prompt = load_prompt_fixture("detection_checkpoint_widget_object.json")

    assert nodes._find_active_names(prompt, "1") == {
        "ACTIVE_UNET": "SDXL/Anubis XL_v1.safetensors",
        "ACTIVE_CLIP": "SDXL/Anubis XL_v1.safetensors",
    }


def test_detection_fixture_traverses_lora_passthrough_nodes(load_prompt_fixture):
    prompt = load_prompt_fixture("detection_lora_passthrough.json")

    assert nodes._find_active_names(prompt, "1") == {
        "ACTIVE_UNET": "Flux/flux-2-klein-9b-Q5_K_M.gguf",
        "ACTIVE_CLIP": "Goekdeniz-Guelmez_Josiefied-Qwen3-8B-abliterated-v1-Q4_K_M.gguf",
    }
