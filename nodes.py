from __future__ import annotations

import re
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, PngImagePlugin

import folder_paths


COMMON_EXTENSIONS = (
    ".safetensors",
    ".gguf",
    ".ckpt",
    ".pt",
    ".pth",
    ".bin",
    ".onnx",
)

WINDOWS_RESERVED_CHARS = '<>:"/\\|?*'
PATH_SPLIT_RE = re.compile(r"[\\/]+")
DATE_TOKEN_RE = re.compile(r"%date:([^%]+)%")
VARIABLE_TOKEN_RE = re.compile(r"%([A-Z0-9_]+)%")
SEARCH_REPLACE_TOKEN_RE = re.compile(r"%([^%./\\]+)\.([^%./\\]+)%")
UNKNOWN_TOKEN_RE = re.compile(r"%([^%]+)%")
DATE_FORMAT_TOKEN_RE = re.compile(r"yyyy|yy|hh|h|MM|M|dd|d|mm|m|ss|s")
STRFTIME_DIRECTIVE_RE = re.compile(r"%(?:[%YymdHMSf]|[A-Za-z])")
IDENTIFIER_RE = re.compile(r"[^a-z0-9]+")
DISPLAY_DOT_RE = re.compile(r"(?<!\d)\.|\.(?!\d)")
LEADING_TAG_RE = re.compile(r"^(?:[A-Z0-9]{2,8}[_-]+)(.+)$")
QUANT_SUFFIX_RE = re.compile(
    r"(?i)^(?P<base>.*?)(?:[ ._-]+)?(?P<quant>"
    r"Q\d+_K_[MS]|Q\d+_K|Q\d+_0|Q\d+|IQ\d+_[A-Z]+|FP8_e4m3fn|FP8_e5m2|BF16|F16"
    r")$"
)
DISPLAY_TAG_ABBREVIATIONS = {
    "abliterated": "[Ablt]",
    "instruct": "[Inst]",
    "heretic": "[Her]",
    "uncensored": "[Unc]",
    "decensored": "[Dec]",
    "thinking": "[Think]",
    "reasoning": "[Rsn]",
    "coder": "[Cod]",
    "creative": "[Crtv]",
    "roleplay": "[RP]",
    "roleplaying": "[RP]",
    "vision": "[Vis]",
    "preview": "[Prev]",
    "turbo": "[Tbo]",
}
DISPLAY_DROP_WORDS = {"gguf", "gptq", "awq"}

UNET_DETECTION_EXACT_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name")
UNET_DETECTION_PREFIX_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name")
UNET_EXTRACTION_EXACT_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name", "model_name", "ckpt_name", "name")
UNET_EXTRACTION_PREFIX_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name")

CLIP_DETECTION_EXACT_KEYS = ("clip_name", "text_encoder_name", "text_encoder", "encoder_name")
CLIP_DETECTION_PREFIX_KEYS = ("clip_name", "text_encoder_name", "encoder_name")
CLIP_EXTRACTION_EXACT_KEYS = ("clip_name", "text_encoder_name", "text_encoder", "encoder_name", "model_name", "ckpt_name", "name")
CLIP_EXTRACTION_PREFIX_KEYS = ("clip_name", "text_encoder_name", "encoder_name")

CHECKPOINT_DETECTION_EXACT_KEYS = ("ckpt_name", "checkpoint_name", "model_name", "name")
CHECKPOINT_DETECTION_PREFIX_KEYS = ("ckpt_name", "checkpoint_name")

MODEL_SOURCE_LABEL_TO_KEY = {
    "Friendly": "FRIENDLY_MODEL_NAME",
    "Exact": "EXACT_MODEL_NAME",
    "Custom": "CUSTOM",
}
CLIP_SOURCE_LABEL_TO_KEY = {
    "Friendly": "FRIENDLY_TEXT_ENCODER_NAME",
    "Exact": "EXACT_TEXT_ENCODER_NAME",
    "Custom": "CUSTOM",
}
MODEL_SOURCE_OPTIONS = list(MODEL_SOURCE_LABEL_TO_KEY.keys())
CLIP_SOURCE_OPTIONS = list(CLIP_SOURCE_LABEL_TO_KEY.keys())
DEFAULT_FILENAME_PATTERN = "%date:yyyy-MM-dd_hh-mm-ss%"


def _sanitize_path_component(value: str) -> str:
    """Keep names readable while making them safe for Windows folders/files."""
    value = (value or "").strip()
    for ch in WINDOWS_RESERVED_CHARS:
        value = value.replace(ch, "-")
    value = value.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    while "  " in value:
        value = value.replace("  ", " ")
    value = value.rstrip(" .")
    if value in {".", ".."}:
        return "unnamed"
    return value or "unnamed"


def _sanitize_relative_path(value: str) -> Path:
    parts = []
    for raw_part in PATH_SPLIT_RE.split((value or "").strip()):
        if not raw_part or not raw_part.strip():
            continue
        cleaned = _sanitize_path_component(raw_part)
        if cleaned:
            parts.append(cleaned)
    if not parts:
        return Path("unnamed")
    return Path(*parts)


def _strip_known_extension(value: str) -> str:
    value = (value or "").strip()
    lower = value.lower()
    for ext in COMMON_EXTENSIONS:
        if lower.endswith(ext):
            return value[: -len(ext)]
    return value


def _basename_without_known_extension(value: str) -> str:
    stripped = _strip_known_extension(value)
    parts = [part for part in PATH_SPLIT_RE.split((stripped or "").strip()) if part]
    return parts[-1] if parts else stripped


def _shorten_model_name(value: str) -> str:
    value = _strip_known_extension(value)
    if " - " in value:
        value = value.split(" - ")[-1].strip()
    return value.strip() or "unnamed"


def _format_quant_display(value: str) -> str | None:
    normalized = value.upper()

    exact_map = {
        "Q4_K_M": "[4K-M]",
        "Q4_K_S": "[4K-S]",
        "Q5_K_M": "[5K-M]",
        "Q5_K_S": "[5K-S]",
        "Q6_K": "[6K]",
        "Q8_0": "[q8]",
        "Q8": "[q8]",
        "FP8_E4M3FN": "[FP8-E4M3FN]",
        "FP8_E5M2": "[FP8-E5M2]",
        "BF16": "[BF16]",
        "F16": "[FP16]",
    }
    if normalized in exact_map:
        return exact_map[normalized]

    match = re.fullmatch(r"IQ(\d+)_([A-Z]+)", normalized)
    if match:
        return f"[IQ{match.group(1)}-{match.group(2)}]"

    plain_quant = re.fullmatch(r"Q(\d+)", normalized)
    if plain_quant:
        return f"[q{plain_quant.group(1)}]"

    return None


def _join_display_parts(parts: list[str]) -> str:
    result = ""
    for part in parts:
        if not part:
            continue
        if not result:
            result = part
            continue
        if result.endswith("]") and part.startswith("["):
            result += part
        else:
            result += f" {part}"
    return result.strip()


def _normalize_version_token(value: str) -> str | None:
    match = re.fullmatch(r"(?i)v(\d+(?:\.\d+)*)", value.strip())
    if not match:
        return None
    return f"V{match.group(1)}"


def _extract_tag_and_version(value: str) -> tuple[str | None, str | None]:
    lowered = value.lower()
    for word in sorted(DISPLAY_TAG_ABBREVIATIONS, key=len, reverse=True):
        if lowered == word:
            return DISPLAY_TAG_ABBREVIATIONS[word], None

        if not lowered.startswith(word):
            continue

        version = _normalize_version_token(value[len(word) :])
        if version:
            return DISPLAY_TAG_ABBREVIATIONS[word], version

    return None, None


def _humanize_display_name(value: str) -> str:
    base_value = _basename_without_known_extension(value or "")
    match = QUANT_SUFFIX_RE.match(base_value)

    quant_display = ""
    if match:
        base_value = match.group("base").rstrip(" ._-")
        quant_display = _format_quant_display(match.group("quant")) or f"[{match.group('quant').upper()}]"

    tag_match = LEADING_TAG_RE.match(base_value)
    if tag_match:
        base_value = tag_match.group(1)

    base_value = DISPLAY_DOT_RE.sub(" ", base_value)
    base_value = base_value.replace("_", " ").replace("-", " ")
    base_parts = [part for part in re.sub(r"\s+", " ", base_value).strip().split(" ") if part]
    plain_parts = []
    version_parts = []
    tag_parts = []
    for part in base_parts:
        lowered = part.lower()
        if lowered in DISPLAY_DROP_WORDS:
            continue

        version = _normalize_version_token(part)
        if version:
            version_parts.append(version)
            continue

        tag, attached_version = _extract_tag_and_version(part)
        if tag:
            if attached_version:
                version_parts.append(attached_version)
            tag_parts.append(tag)
            continue

        plain_parts.append(part)

    base_value = _join_display_parts(plain_parts + version_parts + tag_parts) or "unnamed"

    if quant_display:
        return _join_display_parts([base_value, quant_display])
    return base_value


def _normalize_template_file_path(value: str) -> Path:
    relative_path = _sanitize_relative_path(value)
    if relative_path.suffix.lower() == ".png":
        relative_path = relative_path.with_suffix("")
    return relative_path.with_suffix(".png")


def _render_date_format(value: str, now: datetime) -> str:
    token_values = {
        "yyyy": f"{now.year:04d}",
        "yy": f"{now.year % 100:02d}",
        "MM": f"{now.month:02d}",
        "M": str(now.month),
        "dd": f"{now.day:02d}",
        "d": str(now.day),
        "hh": f"{now.hour:02d}",
        "h": str(now.hour),
        "mm": f"{now.minute:02d}",
        "m": str(now.minute),
        "ss": f"{now.second:02d}",
        "s": str(now.second),
    }
    return DATE_FORMAT_TOKEN_RE.sub(lambda match: token_values[match.group(0)], value)


def _render_strftime_format(value: str, now: datetime) -> str:
    allowed_directives = {"%Y", "%y", "%m", "%d", "%H", "%M", "%S", "%f", "%%"}
    unsupported = sorted(
        {
            match.group(0)
            for match in STRFTIME_DIRECTIVE_RE.finditer(value)
            if match.group(0) not in allowed_directives
        }
    )
    if unsupported:
        raise ValueError(
            "Unsupported strftime directives in path template: "
            + ", ".join(unsupported)
            + ". Supported directives are %Y, %y, %m, %d, %H, %M, %S, %f, and %%."
        )

    return now.strftime(value)


def _replace_strftime_tokens(template: str, now: datetime) -> str:
    marker = "%strftime:"
    result = []
    index = 0

    while True:
        start = template.find(marker, index)
        if start == -1:
            result.append(template[index:])
            return "".join(result)

        result.append(template[index:start])
        cursor = start + len(marker)

        while cursor < len(template):
            if template[cursor] != "%":
                cursor += 1
                continue

            if cursor + 1 >= len(template):
                format_value = template[start + len(marker) : cursor]
                result.append(_render_strftime_format(format_value, now))
                index = cursor + 1
                break

            if template[cursor + 1] == "%" or template[cursor + 1].isalpha():
                cursor += 2
                continue

            format_value = template[start + len(marker) : cursor]
            result.append(_render_strftime_format(format_value, now))
            index = cursor
            break
        else:
            raise ValueError("Unterminated %strftime:...% placeholder in path template.")


def _resolve_selected_variable(source: str, variables: dict[str, str], *, kind: str) -> str:
    if kind == "model":
        source_key = MODEL_SOURCE_LABEL_TO_KEY.get(source, "FRIENDLY_MODEL_NAME")
        custom_key = "CUSTOM_MODEL_NAME"
        default_key = "FRIENDLY_MODEL_NAME"
    else:
        source_key = CLIP_SOURCE_LABEL_TO_KEY.get(source, "FRIENDLY_TEXT_ENCODER_NAME")
        custom_key = "CUSTOM_TEXT_ENCODER_NAME"
        default_key = "FRIENDLY_TEXT_ENCODER_NAME"

    if source_key == "CUSTOM":
        return variables.get(custom_key, "") or "unnamed"

    return variables.get(source_key, variables.get(default_key, "unnamed")) or "unnamed"


def _normalize_identifier(value: str) -> str:
    return IDENTIFIER_RE.sub("", (value or "").strip().casefold())


def _extract_connected_node_id(value: Any) -> str | None:
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and isinstance(value[0], (str, int))
        and isinstance(value[1], int)
    ):
        return str(value[0])
    return None


def _walk_prompt_upstream(prompt: Any, start_node_id: Any):
    if not isinstance(prompt, dict):
        return

    queue = deque()
    visited = set()
    queue.append((str(start_node_id), 0))

    while queue:
        node_id, distance = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)

        node = prompt.get(node_id)
        if not isinstance(node, dict):
            continue

        yield node_id, node, distance

        for input_value in node.get("inputs", {}).values():
            parent_id = _extract_connected_node_id(input_value)
            if parent_id is not None:
                queue.append((parent_id, distance + 1))


def _extract_string_inputs(inputs: dict[str, Any], *, exact: tuple[str, ...], prefix: tuple[str, ...] = ()) -> list[str]:
    values = []
    seen = set()
    exact_normalized = {_normalize_identifier(item) for item in exact}
    prefix_normalized = tuple(_normalize_identifier(item) for item in prefix)

    for key, value in inputs.items():
        if not isinstance(value, str):
            continue

        key_normalized = _normalize_identifier(key)
        if key_normalized not in exact_normalized and not any(
            key_normalized.startswith(item) for item in prefix_normalized
        ):
            continue

        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            values.append(cleaned)
            seen.add(cleaned)

    return values


def _matches_loader_inputs(inputs: dict[str, Any], *, exact: tuple[str, ...], prefix: tuple[str, ...] = ()) -> bool:
    return bool(_extract_string_inputs(inputs, exact=exact, prefix=prefix))


def _get_unet_loader_priority(class_type: str, inputs: dict[str, Any]) -> int | None:
    class_name = _normalize_identifier(class_type)
    if "unetloader" in class_name:
        return 0
    if "diffusionmodelloader" in class_name or "loaddiffusionmodel" in class_name:
        return 1
    if (
        "loader" in class_name
        and ("unet" in class_name or "diffusion" in class_name or "model" in class_name)
        and _matches_loader_inputs(
            inputs,
            exact=UNET_DETECTION_EXACT_KEYS,
            prefix=UNET_DETECTION_PREFIX_KEYS,
        )
    ):
        return 2
    return None


def _get_clip_loader_priority(class_type: str, inputs: dict[str, Any]) -> int | None:
    class_name = _normalize_identifier(class_type)
    if "cliploader" in class_name:
        return 0
    if "textencoderloader" in class_name:
        return 1
    if (
        "loader" in class_name
        and ("clip" in class_name or "textencoder" in class_name or "encoder" in class_name)
        and _matches_loader_inputs(
            inputs,
            exact=CLIP_DETECTION_EXACT_KEYS,
            prefix=CLIP_DETECTION_PREFIX_KEYS,
        )
    ):
        return 2
    return None


def _get_checkpoint_loader_priority(class_type: str, inputs: dict[str, Any]) -> int | None:
    class_name = _normalize_identifier(class_type)
    if "checkpointloader" in class_name or "ckptloader" in class_name:
        return 10
    if (
        "loader" in class_name
        and ("checkpoint" in class_name or "ckpt" in class_name)
        and _matches_loader_inputs(
            inputs,
            exact=CHECKPOINT_DETECTION_EXACT_KEYS,
            prefix=CHECKPOINT_DETECTION_PREFIX_KEYS,
        )
    ):
        return 11
    return None


def _iter_prompt_nodes(prompt: Any):
    if not isinstance(prompt, dict):
        return

    for node_id, node in prompt.items():
        if isinstance(node, dict):
            yield str(node_id), node


def _collect_prompt_names(node_id: str, node: dict[str, Any]) -> list[str]:
    candidates = []

    def add_candidate(value: Any):
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)

    add_candidate(node_id)
    add_candidate(node.get("class_type"))
    add_candidate(node.get("title"))
    add_candidate(node.get("name"))

    for container_key in ("_meta", "meta", "properties", "extra"):
        container = node.get(container_key)
        if not isinstance(container, dict):
            continue

        for key in (
            "title",
            "name",
            "Node name for S&R",
            "node name for s&r",
            "node_name_for_s&r",
            "search_and_replace",
            "search_replace_name",
            "s&r_name",
            "sr_name",
        ):
            add_candidate(container.get(key))

    return candidates


def _coerce_template_value(value: Any) -> str | None:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return None


def _find_prompt_node(prompt: Any, node_name: str) -> tuple[str, dict[str, Any]]:
    matches = []
    target = node_name.strip().casefold()

    for node_id, node in _iter_prompt_nodes(prompt):
        candidate_names = _collect_prompt_names(node_id, node)
        if any(name.casefold() == target for name in candidate_names):
            matches.append((node_id, node))

    if not matches:
        raise ValueError(f"Unknown template node reference: {node_name}")

    if len(matches) > 1:
        joined = ", ".join(node_id for node_id, _ in matches[:5])
        raise ValueError(
            f"Ambiguous template node reference '{node_name}' matched multiple nodes: {joined}"
        )

    return matches[0]


def _resolve_prompt_input_value(prompt: Any, node_name: str, widget_name: str) -> str:
    node_id, node = _find_prompt_node(prompt, node_name)
    inputs = node.get("inputs", {})
    if not isinstance(inputs, dict):
        raise ValueError(f"Node '{node_name}' does not expose widget inputs in the prompt.")

    value = inputs.get(widget_name)
    if value is None:
        matching_keys = [
            key
            for key in inputs
            if isinstance(key, str) and key.casefold() == widget_name.strip().casefold()
        ]
        if len(matching_keys) != 1:
            raise ValueError(
                f"Unknown widget reference '{widget_name}' on node '{node_name}' (node id {node_id})."
            )
        value = inputs[matching_keys[0]]

    coerced = _coerce_template_value(value)
    if coerced is not None:
        return coerced

    raise ValueError(
        f"Template reference '{node_name}.{widget_name}' points to a linked or unsupported value."
    )


def _find_active_names(prompt: Any, unique_id: Any) -> dict[str, str]:
    best_unet: tuple[int, int, int, str, str] | None = None
    best_clip: tuple[int, int, int, str, str] | None = None

    for _, node, distance in _walk_prompt_upstream(prompt, unique_id):
        class_type = str(node.get("class_type", ""))
        inputs = node.get("inputs", {})
        unet_priority = _get_unet_loader_priority(class_type, inputs)
        clip_priority = _get_clip_loader_priority(class_type, inputs)
        checkpoint_priority = _get_checkpoint_loader_priority(class_type, inputs)

        if unet_priority is not None or checkpoint_priority is not None:
            unet_values = _extract_string_inputs(
                inputs,
                exact=UNET_EXTRACTION_EXACT_KEYS if unet_priority is not None else CHECKPOINT_DETECTION_EXACT_KEYS,
                prefix=UNET_EXTRACTION_PREFIX_KEYS if unet_priority is not None else CHECKPOINT_DETECTION_PREFIX_KEYS,
            )
            priority = unet_priority if unet_priority is not None else checkpoint_priority
            for value_index, value in enumerate(unet_values):
                candidate = (priority, distance, value_index, value.casefold(), value)
                if best_unet is None or candidate < best_unet:
                    best_unet = candidate

        if clip_priority is not None or checkpoint_priority is not None:
            clip_values = _extract_string_inputs(
                inputs,
                exact=CLIP_EXTRACTION_EXACT_KEYS if clip_priority is not None else CHECKPOINT_DETECTION_EXACT_KEYS,
                prefix=CLIP_EXTRACTION_PREFIX_KEYS if clip_priority is not None else CHECKPOINT_DETECTION_PREFIX_KEYS,
            )
            priority = clip_priority if clip_priority is not None else checkpoint_priority
            for value_index, value in enumerate(clip_values):
                candidate = (priority, distance, value_index, value.casefold(), value)
                if best_clip is None or candidate < best_clip:
                    best_clip = candidate

    return {
        "ACTIVE_UNET": best_unet[4] if best_unet else "",
        "ACTIVE_CLIP": best_clip[4] if best_clip else "",
    }


def _render_path_template(template: str, variables: dict[str, str], now: datetime, prompt: Any) -> str:
    def replace_date(match: re.Match[str]) -> str:
        return _render_date_format(match.group(1), now)

    rendered = DATE_TOKEN_RE.sub(replace_date, template or "")
    rendered = _replace_strftime_tokens(rendered, now)
    rendered = SEARCH_REPLACE_TOKEN_RE.sub(
        lambda match: _resolve_prompt_input_value(prompt, match.group(1), match.group(2)),
        rendered,
    )

    unknown_tokens = sorted(
        {
            match.group(1)
            for match in VARIABLE_TOKEN_RE.finditer(rendered)
            if match.group(1) not in variables
        }
    )
    if unknown_tokens:
        raise ValueError(f"Unknown path template variables: {', '.join(unknown_tokens)}")

    rendered = VARIABLE_TOKEN_RE.sub(lambda match: variables[match.group(1)], rendered)

    remaining_tokens = sorted({match.group(1) for match in UNKNOWN_TOKEN_RE.finditer(rendered)})
    if remaining_tokens:
        raise ValueError(f"Unknown path template placeholders: {', '.join(remaining_tokens)}")

    return rendered


def _render_filename_value(pattern: str, now: datetime) -> str:
    rendered = DATE_TOKEN_RE.sub(lambda match: _render_date_format(match.group(1), now), pattern or "")
    rendered = _replace_strftime_tokens(rendered, now)
    return _sanitize_path_component(rendered)


class StripModelExtension:
    """Remove only the final known model extension from a loader/model name string."""

    DESCRIPTION = (
        "Removes one known model file extension from the end of a string. "
        "Useful when you want a clean folder or filename from values such as "
        "'model.safetensors' or 'model.gguf'."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "Text to clean. Removes one known model file extension from the end, "
                            "for example '.safetensors' or '.gguf'."
                        ),
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("clean_text",)
    OUTPUT_TOOLTIPS = ("The input text with one known model file extension removed.",)
    FUNCTION = "run"
    CATEGORY = "utils/filename"

    def run(self, text: str):
        return (_strip_known_extension(text),)


class SaveImageClean:
    """Save images into a readable folder layout with template support."""

    DEFAULT_TEMPLATE = "%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%"
    DESCRIPTION = (
        "Save images into a clean, readable folder structure.\n\n"
        "Quick start:\n"
        "- Leave the default Save Layout alone for the simplest setup\n"
        "- Change Model Name, Text Encoder Name, or Filename only if you want different output\n"
        "- Clear Save Layout only if you want the built-in folder order instead of a custom layout\n\n"
        "Default result example:\n"
        "portraits/flux 2 klein 9b [5K-M]/Lockout Qwen3 4b V2 [Her][q8]/2026-04-22_15-30-10.png\n\n"
        "Open the Info tab for copy-paste templates, variable explanations, and beginner examples."
    )
    SEARCH_ALIASES = [
        "save image",
        "save png",
        "template save",
        "clean save",
        "filename template",
        "output path",
    ]

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "path_template": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": cls.DEFAULT_TEMPLATE,
                        "tooltip": (
                            "Main save layout. The default layout is Top Folder / Model Name / "
                            "Text Encoder Name / Filename. Clear it only if you want the built-in order."
                        ),
                    },
                ),
                "model_source": (
                    MODEL_SOURCE_OPTIONS,
                    {
                        "default": "Friendly",
                        "tooltip": (
                            "Choose how the model name should look. "
                            "Friendly is the easiest option for most people."
                        ),
                    },
                ),
                "clip_source": (
                    CLIP_SOURCE_OPTIONS,
                    {
                        "default": "Friendly",
                        "tooltip": (
                            "Choose how the text encoder name should look. "
                            "Friendly is the easiest option for most people."
                        ),
                    },
                ),
                "filename_datetime": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": DEFAULT_FILENAME_PATTERN,
                        "tooltip": (
                            "Filename pattern. The default is year-month-day_hour-minute-second. "
                            "Supports plain text, %date:...%, and the small %strftime:...% subset."
                        ),
                    },
                ),
                "collision_mode": (
                    ["increment", "overwrite", "error", "seconds"],
                    {
                        "default": "increment",
                        "tooltip": (
                            "What to do if the file already exists. "
                            "Increment is the safest default."
                        ),
                    },
                ),
            },
            "optional": {
                "subfolder": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "Optional extra top folder, such as portraits or test-renders."
                        ),
                    },
                ),
                "model_folder": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "Custom model name. Used directly in Custom mode, and also as a "
                            "fallback if auto-detection fails."
                        ),
                    },
                ),
                "clip_folder": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "Custom text encoder name. Used directly in Custom mode, and also as "
                            "a fallback if auto-detection fails."
                        ),
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image/save"

    def _build_metadata(self, prompt: Any = None, extra_pnginfo: Any = None) -> PngImagePlugin.PngInfo:
        metadata = PngImagePlugin.PngInfo()

        if prompt is not None:
            metadata.add_text("prompt", str(prompt))

        if extra_pnginfo is not None:
            if isinstance(extra_pnginfo, dict):
                for key, value in extra_pnginfo.items():
                    metadata.add_text(str(key), str(value))
            else:
                metadata.add_text("extra_pnginfo", str(extra_pnginfo))

        return metadata

    def _build_template_variables(
        self,
        *,
        prompt: Any,
        unique_id: Any,
        model_folder: str,
        clip_folder: str,
        filename_datetime: str,
        subfolder: str,
        model_source: str,
        clip_source: str,
        now: datetime,
    ) -> dict[str, str]:
        active_names = _find_active_names(prompt=prompt, unique_id=unique_id)

        manual_model = _strip_known_extension(model_folder)
        manual_clip = _strip_known_extension(clip_folder)
        raw_active_unet = active_names["ACTIVE_UNET"] or manual_model or "model"
        raw_active_clip = active_names["ACTIVE_CLIP"] or manual_clip or "text-encoder"
        active_unet = _basename_without_known_extension(raw_active_unet) or manual_model or "model"
        active_clip = _basename_without_known_extension(raw_active_clip) or manual_clip or "text-encoder"

        variables = {
            "EXACT_MODEL_NAME": active_unet,
            "EXACT_TEXT_ENCODER_NAME": active_clip,
            "FRIENDLY_MODEL_NAME": _humanize_display_name(raw_active_unet),
            "FRIENDLY_TEXT_ENCODER_NAME": _humanize_display_name(raw_active_clip),
            "CUSTOM_MODEL_NAME": manual_model or "",
            "CUSTOM_TEXT_ENCODER_NAME": manual_clip or "",
            "TOP_FOLDER": _sanitize_path_component(subfolder) if subfolder.strip() else "",
            "FILENAME": _render_filename_value(filename_datetime or DEFAULT_FILENAME_PATTERN, now),
        }
        variables["MODEL_NAME"] = _resolve_selected_variable(model_source, variables, kind="model")
        variables["TEXT_ENCODER_NAME"] = _resolve_selected_variable(clip_source, variables, kind="clip")

        return variables

    def _resolve_relative_output_path(
        self,
        *,
        model_folder: str,
        clip_folder: str,
        filename_datetime: str,
        subfolder: str,
        model_source: str,
        clip_source: str,
        path_template: str,
        prompt: Any,
        unique_id: Any,
    ) -> tuple[Path, str]:
        now = datetime.now()
        variables = self._build_template_variables(
            prompt=prompt,
            unique_id=unique_id,
            model_folder=model_folder,
            clip_folder=clip_folder,
            filename_datetime=filename_datetime,
            subfolder=subfolder,
            model_source=model_source,
            clip_source=clip_source,
            now=now,
        )

        if path_template and path_template.strip():
            rendered = _render_path_template(path_template.strip(), variables, now, prompt)
            relative_path = _normalize_template_file_path(rendered)
            return relative_path, rendered

        clean_model = _sanitize_path_component(variables["MODEL_NAME"])
        clean_clip = _sanitize_path_component(variables["TEXT_ENCODER_NAME"])
        clean_subfolder = _sanitize_path_component(subfolder) if subfolder.strip() else ""
        base_name = variables["FILENAME"]

        relative_path = Path(clean_model) / clean_clip / f"{base_name}.png"
        if clean_subfolder:
            relative_path = Path(clean_subfolder) / relative_path
        preview = str(relative_path.with_suffix(""))
        return relative_path, preview

    def _resolve_target_path(
        self,
        *,
        output_root: Path,
        relative_path: Path,
        collision_mode: str,
    ) -> Path:
        candidate = output_root / relative_path
        candidate.parent.mkdir(parents=True, exist_ok=True)

        if collision_mode == "overwrite":
            return candidate
        if not candidate.exists():
            return candidate
        if collision_mode == "error":
            raise FileExistsError(f"Target file already exists: {candidate}")
        if collision_mode == "seconds":
            second_name = _sanitize_path_component(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            candidate = candidate.with_name(f"{second_name}.png")
            if not candidate.exists():
                return candidate

        stem = candidate.stem
        for index in range(2, 10000):
            numbered = candidate.with_name(f"{stem}-{index}.png")
            if not numbered.exists():
                return numbered

        raise RuntimeError("Could not create a unique filename after many attempts.")

    def save_images(
        self,
        images,
        path_template: str,
        collision_mode: str,
        model_source: str,
        clip_source: str,
        subfolder: str = "",
        model_folder: str = "",
        clip_folder: str = "",
        filename_datetime: str = DEFAULT_FILENAME_PATTERN,
        prompt: Any = None,
        extra_pnginfo: Any = None,
        unique_id: Any = None,
    ):
        output_root = Path(self.output_dir)
        metadata = self._build_metadata(prompt=prompt, extra_pnginfo=extra_pnginfo)
        relative_path, preview = self._resolve_relative_output_path(
            model_folder=model_folder,
            clip_folder=clip_folder,
            filename_datetime=filename_datetime,
            subfolder=subfolder,
            model_source=model_source,
            clip_source=clip_source,
            path_template=path_template,
            prompt=prompt,
            unique_id=unique_id,
        )

        saved = []
        for image in images:
            target_path = self._resolve_target_path(
                output_root=output_root,
                relative_path=relative_path,
                collision_mode=collision_mode,
            )

            array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
            pil_image = Image.fromarray(array)
            pil_image.save(target_path, pnginfo=metadata, compress_level=self.compress_level)

            saved.append(
                {
                    "filename": target_path.name,
                    "subfolder": str(target_path.parent.relative_to(output_root)) if target_path.parent != output_root else "",
                    "type": self.type,
                }
            )

        return {"ui": {"images": saved, "text": [preview]}}


NODE_CLASS_MAPPINGS = {
    "StripModelExtension": StripModelExtension,
    "SaveImageClean": SaveImageClean,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StripModelExtension": "Strip Model Extension",
    "SaveImageClean": "Save Image Clean",
}
