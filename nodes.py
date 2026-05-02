from __future__ import annotations

import json
import re
from collections import deque
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
from typing import Any

import folder_paths
import numpy as np
from PIL import Image, PngImagePlugin

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
VARIABLE_TOKEN_RE = re.compile(r"%([A-Z0-9_]+)((?::[a-z]+)*)%")
SEARCH_REPLACE_TOKEN_RE = re.compile(r"%([^%./\\]+)\.([^%./\\:]+)((?::[a-z]+)*)%")
UNKNOWN_TOKEN_RE = re.compile(r"%([^%]+)%")
DATE_FORMAT_TOKEN_RE = re.compile(r"yyyy|yy|hh|h|MM|M|dd|d|mm|m|ss|s")
STRFTIME_DIRECTIVE_RE = re.compile(r"%(?:[%YymdHMSf]|[A-Za-z])")
IDENTIFIER_RE = re.compile(r"[^a-z0-9]+")
SLUG_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")
DISPLAY_DOT_RE = re.compile(r"(?<!\d)\.|\.(?!\d)")
LEADING_TAG_RE = re.compile(r"^(?:[A-Z0-9]{2,8}[_-]+)(.+)$")
KNOWN_RELEASER_PREFIX_RE = re.compile(
    r"(?i)^(?:goekdeniz[-_]?guelmez|mradermacher)\s*(?:[-_]+\s*|\s+-\s+)(?P<name>.+)$"
)
SPACED_RELEASER_PREFIX_RE = re.compile(r"^\s*[^\\/]{2,40}\s+-\s+(?P<name>.+)$")
SCALED_FP8_SUFFIX_RE = re.compile(
    r"(?i)^(?P<base>.*?)(?:[ ._-]+)?FP8[ ._-]*(?P<format>E4M3FN|E5M2)[ ._-]*SCALED$"
)
QUANT_SUFFIX_RE = re.compile(
    r"(?i)^(?P<base>.*?)(?:[ ._-]+)?(?P<quant>"
    r"Q\d+_K_[MS]|Q\d+_K|Q\d+_0|Q\d+|IQ\d+_[A-Z]+|FP8_e4m3fn|FP8_e5m2|BF16|FP16|F16|FP32"
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
TEMPLATE_FILTERS = ("lower", "upper", "slug")
KNOWN_IMAGE_MODEL_DISPLAY_ALIASES = (
    ("flux2klein9b", "FLUX.2 Klein 9B"),
    ("flux2klein4b", "FLUX.2 Klein 4B"),
    ("flux2dev", "FLUX.2 Dev"),
    ("flux1kontextdev", "FLUX.1 Kontext Dev"),
    ("flux1filldev", "FLUX.1 Fill Dev"),
    ("flux1schnell", "FLUX.1 Schnell"),
    ("flux1dev", "FLUX.1 Dev"),
    ("hidreame11", "HiDream E1.1"),
    ("hidreame1", "HiDream E1"),
    ("hidreami1full", "HiDream I1 Full"),
    ("hidreami1fast", "HiDream I1 Fast"),
    ("hidreami1dev", "HiDream I1 Dev"),
    ("hidreami1", "HiDream I1"),
    ("qwenimageedit2511", "Qwen Image Edit 2511"),
    ("qwenimageedit2509", "Qwen Image Edit 2509"),
    ("qwenimageedit", "Qwen Image Edit"),
    ("qwenimage", "Qwen Image"),
    ("ovisimage7b", "Ovis Image"),
    ("ovisimage", "Ovis Image"),
    ("newbieimageexp01", "NewBie Image Exp0.1"),
    ("omnigen2", "OmniGen2"),
    ("ernieimageturbo", "ERNIE Image Turbo"),
    ("ernieimage", "ERNIE Image"),
    ("zimageturbo", "Z-Image Turbo"),
    ("zit", "Z-Image Turbo"),
    ("zimage", "Z-Image"),
    ("stablediffusion15", "Stable Diffusion 1.5"),
    ("sd15", "Stable Diffusion 1.5"),
)
KNOWN_TEXT_ENCODER_DISPLAY_ALIASES = (
    ("qwen34b", "Qwen3 4B"),
    ("qwen25vl", "Qwen2.5 VL"),
    ("qwen257b", "Qwen2.5 7B"),
    ("clipl", "CLIP-L"),
    ("clipg", "CLIP-G"),
    ("t5xxl", "T5 XXL"),
    ("oldt5xxl", "Old T5 XXL"),
    ("t5base", "T5 Base"),
    ("mt5xl", "mT5 XL"),
    ("umt5xxl", "UMT5 XXL"),
    ("gemma22b", "Gemma 2 2B"),
    ("llama", "Llama"),
    ("bert", "BERT"),
)
DISPLAY_WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\d|[^A-Za-z0-9]|$)|[A-Z]?[a-z]+|\d+(?:\.\d+)?")

UNET_DETECTION_EXACT_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name")
UNET_DETECTION_PREFIX_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name")
UNET_EXTRACTION_EXACT_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name")
UNET_EXTRACTION_PREFIX_KEYS = ("unet_name", "diffusion_model_name", "diffusion_name")

CLIP_DETECTION_EXACT_KEYS = ("clip_name", "text_encoder_name", "text_encoder", "encoder_name")
CLIP_DETECTION_PREFIX_KEYS = ("clip_name", "text_encoder_name", "encoder_name")
CLIP_EXTRACTION_EXACT_KEYS = ("clip_name", "text_encoder_name", "text_encoder", "encoder_name")
CLIP_EXTRACTION_PREFIX_KEYS = ("clip_name", "text_encoder_name", "encoder_name")

CHECKPOINT_DETECTION_EXACT_KEYS = ("ckpt_name", "checkpoint_name", "model_name", "name")
CHECKPOINT_DETECTION_PREFIX_KEYS = ("ckpt_name", "checkpoint_name")

MODEL_SOURCE_LABEL_TO_KEY = {
    "Friendly": "FRIENDLY_MODEL_NAME",
    "Friendly Clean": "CLEAN_FRIENDLY_MODEL_NAME",
    "Exact": "EXACT_MODEL_NAME",
    "Custom": "CUSTOM",
}
CLIP_SOURCE_LABEL_TO_KEY = {
    "Friendly": "FRIENDLY_TEXT_ENCODER_NAME",
    "Friendly Clean": "CLEAN_FRIENDLY_TEXT_ENCODER_NAME",
    "Exact": "EXACT_TEXT_ENCODER_NAME",
    "Custom": "CUSTOM",
}
MODEL_SOURCE_OPTIONS = list(MODEL_SOURCE_LABEL_TO_KEY.keys())
CLIP_SOURCE_OPTIONS = list(CLIP_SOURCE_LABEL_TO_KEY.keys())
DETECTION_INFO_OPTIONS = ["Off", "Summary", "Verbose"]
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
        "Q3_K_M": "[3K-M]",
        "Q3_K_S": "[3K-S]",
        "Q4_K_M": "[4K-M]",
        "Q4_K_S": "[4K-S]",
        "Q5_K_M": "[5K-M]",
        "Q5_K_S": "[5K-S]",
        "Q6_K": "[6K]",
        "Q8_0": "[Q8]",
        "Q8": "[Q8]",
        "FP8_E4M3FN": "[FP8-E4M3FN]",
        "FP8_E5M2": "[FP8-E5M2]",
        "FP32": "[FP32]",
        "BF16": "[BF16]",
        "FP16": "[FP16]",
        "F16": "[FP16]",
    }
    if normalized in exact_map:
        return exact_map[normalized]

    match = re.fullmatch(r"IQ(\d+)_([A-Z]+)", normalized)
    if match:
        return f"[IQ{match.group(1)}-{match.group(2)}]"

    zero_quant = re.fullmatch(r"Q(\d+)_0", normalized)
    if zero_quant:
        return f"[Q{zero_quant.group(1)}]"

    plain_quant = re.fullmatch(r"Q(\d+)", normalized)
    if plain_quant:
        return f"[Q{plain_quant.group(1)}]"

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


def _normalize_display_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().casefold())


def _iter_display_words(value: str) -> list[tuple[int, int, str]]:
    return [(match.start(), match.end(), match.group(0)) for match in DISPLAY_WORD_RE.finditer(value or "")]


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


def _humanize_display_name_generic(value: str, quant_display: str = "") -> str:
    base_value = DISPLAY_DOT_RE.sub(" ", value or "")
    base_value = base_value.replace("_", " ").replace("-", " ")
    base_parts = [part for part in re.sub(r"\s+", " ", base_value).strip().split(" ") if part]
    plain_parts = []
    version_parts = []
    tag_parts = []
    for part in base_parts:
        lowered = part.lower()
        if lowered in DISPLAY_DROP_WORDS:
            continue

        quant_part = _format_quant_display(part)
        if quant_part:
            tag_parts.append(quant_part)
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


def _match_known_display_aliases(
    value: str,
    aliases: tuple[tuple[str, str], ...],
    quant_display: str = "",
) -> str | None:
    words = _iter_display_words(value)
    if not words:
        return None

    normalized_words = [_normalize_display_identifier(word) for _, _, word in words]
    best_match: tuple[int, int, int, str] | None = None

    for start_index in range(len(normalized_words)):
        compact = ""
        for end_index in range(start_index, len(normalized_words)):
            compact += normalized_words[end_index]
            for alias, display in aliases:
                if compact != alias:
                    continue
                candidate = (len(alias), start_index, end_index, display)
                if best_match is None or candidate > best_match:
                    best_match = candidate

    if best_match is None:
        return None

    _, start_index, end_index, display = best_match
    prefix_raw = (value or "")[: words[start_index][0]]
    suffix_raw = (value or "")[words[end_index][1] :]

    parts = []
    if prefix_raw.strip():
        prefix_display = _humanize_display_name_generic(prefix_raw)
        if prefix_display != "unnamed":
            parts.append(prefix_display)

    parts.append(display)

    if suffix_raw.strip():
        suffix_display = _humanize_display_name_generic(suffix_raw)
        if suffix_display != "unnamed":
            parts.append(suffix_display)

    base_value = _join_display_parts(parts) or display
    if quant_display:
        return _join_display_parts([base_value, quant_display])
    return base_value


def _humanize_display_name(value: str, *, kind: str = "generic") -> str:
    base_value = _basename_without_known_extension(value or "")
    extra_parts: list[str] = []

    scaled_fp8_match = SCALED_FP8_SUFFIX_RE.match(base_value)
    if scaled_fp8_match:
        base_value = scaled_fp8_match.group("base").rstrip(" ._-")
        extra_parts.append("Scaled")
        quant_display = f"[FP8-{scaled_fp8_match.group('format').upper()}]"
    else:
        quant_display = ""
        match = QUANT_SUFFIX_RE.match(base_value)
        if match:
            base_value = match.group("base").rstrip(" ._-")
            quant_display = _format_quant_display(match.group("quant")) or f"[{match.group('quant').upper()}]"

    aliases: tuple[tuple[str, str], ...] | None = None
    if kind == "model":
        aliases = KNOWN_IMAGE_MODEL_DISPLAY_ALIASES
    elif kind == "text_encoder":
        aliases = KNOWN_TEXT_ENCODER_DISPLAY_ALIASES

    if aliases:
        known_display = _match_known_display_aliases(base_value, aliases)
        if known_display:
            return _join_display_parts([known_display, *extra_parts, quant_display])

    tag_match = LEADING_TAG_RE.match(base_value)
    if tag_match:
        base_value = tag_match.group(1)

    if aliases:
        known_display = _match_known_display_aliases(base_value, aliases)
        if known_display:
            return _join_display_parts([known_display, *extra_parts, quant_display])

    base_display = _humanize_display_name_generic(base_value)
    return _join_display_parts([base_display, *extra_parts, quant_display])


def _strip_releaser_prefix(value: str) -> str:
    base_value = _basename_without_known_extension(value)
    known_match = KNOWN_RELEASER_PREFIX_RE.match(base_value)
    if known_match:
        return known_match.group("name").strip()

    spaced_match = SPACED_RELEASER_PREFIX_RE.match(base_value)
    if spaced_match:
        return spaced_match.group("name").strip()

    return value


def _humanize_clean_display_name(value: str, *, kind: str = "generic") -> str:
    return _humanize_display_name(_strip_releaser_prefix(value), kind=kind)


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


def _coerce_bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return None


def _extract_bridge_labels(node: dict[str, Any]) -> list[str]:
    labels = []
    seen = set()

    def add_candidate(value: Any):
        if not isinstance(value, str):
            return

        cleaned = value.strip()
        if not cleaned:
            return

        for prefix in ("get_", "set_"):
            if cleaned.casefold().startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                break

        normalized = _normalize_identifier(cleaned)
        if not normalized or normalized in seen:
            return

        seen.add(normalized)
        labels.append(cleaned)

    inputs = node.get("inputs", {})
    if isinstance(inputs, dict):
        for value in inputs.values():
            add_candidate(value)

    add_candidate(node.get("title"))
    add_candidate(node.get("name"))

    for container_key in ("_meta", "meta", "properties", "extra"):
        container = node.get(container_key)
        if not isinstance(container, dict):
            continue

        for key in ("title", "name", "previousName", "previous_name"):
            add_candidate(container.get(key))

    return labels


def _iter_getnode_bridge_parents(prompt: Any, node: dict[str, Any]) -> list[str]:
    if not isinstance(prompt, dict):
        return []

    class_name = _normalize_identifier(str(node.get("class_type", "")))
    if class_name != "getnode":
        return []

    target_labels = {_normalize_identifier(label) for label in _extract_bridge_labels(node)}
    if not target_labels:
        return []

    parent_ids = []
    seen = set()

    for candidate_id, candidate in prompt.items():
        if not isinstance(candidate, dict):
            continue

        candidate_class = _normalize_identifier(str(candidate.get("class_type", "")))
        if candidate_class != "setnode":
            continue

        candidate_labels = {_normalize_identifier(label) for label in _extract_bridge_labels(candidate)}
        if not target_labels.intersection(candidate_labels):
            continue

        candidate_inputs = candidate.get("inputs", {})
        if not isinstance(candidate_inputs, dict):
            continue

        for value in candidate_inputs.values():
            parent_id = _extract_connected_node_id(value)
            if parent_id is not None and parent_id not in seen:
                seen.add(parent_id)
                parent_ids.append(parent_id)

    return parent_ids


def _iter_selected_parent_ids(node: dict[str, Any]) -> list[str] | None:
    inputs = node.get("inputs", {})
    if not isinstance(inputs, dict):
        return None

    class_name = _normalize_identifier(str(node.get("class_type", "")))
    if class_name != "comfyswitchnode":
        return None

    switch_value = _coerce_bool_value(inputs.get("switch"))
    if switch_value is None:
        return None

    selected_input_name = "on_true" if switch_value else "on_false"
    parent_id = _extract_connected_node_id(inputs.get(selected_input_name))
    if parent_id is None:
        return []
    return [parent_id]


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

        selected_parent_ids = _iter_selected_parent_ids(node)
        input_values = (
            []
            if selected_parent_ids is not None
            else node.get("inputs", {}).values() if isinstance(node.get("inputs", {}), dict) else []
        )

        for parent_id in selected_parent_ids or ():
            queue.append((parent_id, distance + 1))

        for input_value in input_values:
            parent_id = _extract_connected_node_id(input_value)
            if parent_id is not None:
                queue.append((parent_id, distance + 1))

        for parent_id in _iter_getnode_bridge_parents(prompt, node):
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


def _extract_widget_string_inputs(
    node: dict[str, Any],
    *,
    exact: tuple[str, ...],
    prefix: tuple[str, ...] = (),
) -> list[str]:
    widgets_values = node.get("widgets_values")
    if not isinstance(widgets_values, list) or not widgets_values:
        return []

    class_name = _normalize_identifier(str(node.get("class_type", "")))
    exact_normalized = {_normalize_identifier(item) for item in exact}
    prefix_normalized = tuple(_normalize_identifier(item) for item in prefix)

    def wants_any(*names: str) -> bool:
        return any(
            _normalize_identifier(name) in exact_normalized
            or any(_normalize_identifier(name).startswith(item) for item in prefix_normalized)
            for name in names
        )

    if wants_any("unet_name", "diffusion_model_name", "diffusion_name") and (
        "unetloader" in class_name or "diffusionmodelloader" in class_name or "loaddiffusionmodel" in class_name
    ):
        candidate = widgets_values[0]
    elif wants_any("clip_name", "text_encoder_name", "text_encoder", "encoder_name") and (
        "cliploader" in class_name or "textencoderloader" in class_name
    ):
        candidate = widgets_values[0]
    elif wants_any("ckpt_name", "checkpoint_name", "model_name", "name") and (
        "checkpointloader" in class_name or "ckptloader" in class_name
    ):
        candidate = widgets_values[0]
    else:
        return []

    if isinstance(candidate, str):
        cleaned = candidate.strip()
        return [cleaned] if cleaned else []
    if isinstance(candidate, dict):
        for key in ("content", "value", "text", "name", "filename"):
            value = candidate.get(key)
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    return [cleaned]
    return []


def _extract_string_inputs_from_node(
    node: dict[str, Any],
    *,
    exact: tuple[str, ...],
    prefix: tuple[str, ...] = (),
) -> list[str]:
    inputs = node.get("inputs", {})
    values = _extract_string_inputs(inputs if isinstance(inputs, dict) else {}, exact=exact, prefix=prefix)
    if values:
        return values
    return _extract_widget_string_inputs(node, exact=exact, prefix=prefix)


def _extract_scalar_inputs(inputs: dict[str, Any], *, exact: tuple[str, ...], prefix: tuple[str, ...] = ()) -> list[str]:
    values = []
    exact_normalized = {_normalize_identifier(item) for item in exact}
    prefix_normalized = tuple(_normalize_identifier(item) for item in prefix)

    for key, value in inputs.items():
        key_normalized = _normalize_identifier(key)
        if key_normalized not in exact_normalized and not any(
            key_normalized.startswith(item) for item in prefix_normalized
        ):
            continue

        coerced = _coerce_template_value(value)
        if coerced is not None:
            values.append(coerced)

    return values


def _matches_loader_inputs(inputs: dict[str, Any], *, exact: tuple[str, ...], prefix: tuple[str, ...] = ()) -> bool:
    return bool(_extract_string_inputs(inputs, exact=exact, prefix=prefix))


def _find_upstream_scalar_input(
    prompt: Any,
    unique_id: Any,
    *,
    exact: tuple[str, ...],
    prefix: tuple[str, ...] = (),
) -> str:
    best_match: tuple[int, int, str] | None = None

    for _, node, distance in _walk_prompt_upstream(prompt, unique_id):
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue

        values = _extract_scalar_inputs(inputs, exact=exact, prefix=prefix)
        for value_index, value in enumerate(values):
            candidate = (distance, value_index, value)
            if best_match is None or candidate < best_match:
                best_match = candidate

    return best_match[2] if best_match else ""


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


def _parse_template_filters(filter_text: str, placeholder: str) -> list[str]:
    filters = [item for item in (filter_text or "").split(":") if item]
    unknown = [item for item in filters if item not in TEMPLATE_FILTERS]
    if unknown:
        raise ValueError(
            f"Unknown template filter '{unknown[0]}' in placeholder '{placeholder}'. "
            f"Supported filters: {', '.join(TEMPLATE_FILTERS)}."
        )
    return filters


def _slugify_template_value(value: str) -> str:
    slug = SLUG_SEPARATOR_RE.sub("-", (value or "").casefold()).strip("-")
    return slug or "unnamed"


def _apply_template_filters(value: str, filters: list[str]) -> str:
    rendered = value
    for filter_name in filters:
        if filter_name == "lower":
            rendered = rendered.lower()
        elif filter_name == "upper":
            rendered = rendered.upper()
        elif filter_name == "slug":
            rendered = _slugify_template_value(rendered)
    return rendered


def _format_preview_list(values: list[str], *, limit: int = 5) -> str:
    items = [value for value in values if value]
    if not items:
        return ""
    preview = items[:limit]
    suffix = " ..." if len(items) > limit else ""
    return ", ".join(preview) + suffix


def _format_match_label(node_id: str, node: dict[str, Any]) -> str:
    names = _collect_prompt_names(node_id, node)
    preferred = next((name for name in names if name != node_id), node_id)
    return f"{preferred} (node id {node_id})"


def _find_prompt_node(prompt: Any, node_name: str, placeholder: str | None = None) -> tuple[str, dict[str, Any]]:
    matches = []
    target = node_name.strip().casefold()
    all_candidates: list[tuple[str, dict[str, Any], list[str]]] = []

    for node_id, node in _iter_prompt_nodes(prompt):
        candidate_names = _collect_prompt_names(node_id, node)
        all_candidates.append((node_id, node, candidate_names))
        if any(name.casefold() == target for name in candidate_names):
            matches.append((node_id, node))

    if not matches:
        known_names = []
        for node_id, node, candidate_names in all_candidates:
            preferred = next((name for name in candidate_names if name != node_id), node_id)
            label = f"{preferred} (node id {node_id})"
            if label not in known_names:
                known_names.append(label)

        available = (
            f" Known nodes include: {_format_preview_list(known_names)}."
            if known_names
            else ""
        )
        context = f" in placeholder '{placeholder}'" if placeholder else ""
        raise ValueError(f"Unknown template node reference '{node_name}'{context}.{available}")

    if len(matches) > 1:
        joined = _format_preview_list([_format_match_label(node_id, node) for node_id, node in matches])
        context = f" in placeholder '{placeholder}'" if placeholder else ""
        raise ValueError(
            f"Ambiguous template node reference '{node_name}'{context}. "
            f"Matched multiple nodes: {joined}. Use a unique title, Node name for S&R, or node id."
        )

    return matches[0]


def _resolve_prompt_input_value(
    prompt: Any,
    node_name: str,
    widget_name: str,
    *,
    placeholder: str | None = None,
    filters: list[str] | None = None,
) -> str:
    node_id, node = _find_prompt_node(prompt, node_name, placeholder=placeholder)
    inputs = node.get("inputs", {})
    if not isinstance(inputs, dict):
        context = f" for placeholder '{placeholder}'" if placeholder else ""
        raise ValueError(f"Node '{node_name}' (node id {node_id}) does not expose widget inputs{context}.")

    value = inputs.get(widget_name)
    if value is None:
        matching_keys = [
            key
            for key in inputs
            if isinstance(key, str) and key.casefold() == widget_name.strip().casefold()
        ]
        if len(matching_keys) != 1:
            available_widgets = [key for key in inputs if isinstance(key, str)]
            suggestions = get_close_matches(widget_name, available_widgets, n=3, cutoff=0.6)
            suggestion_text = f" Close matches: {', '.join(suggestions)}." if suggestions else ""
            available_text = (
                f" Available widget inputs: {_format_preview_list(sorted(available_widgets), limit=8)}."
                if available_widgets
                else ""
            )
            raise ValueError(
                f"Unknown widget reference '{widget_name}' on node '{node_name}' (node id {node_id})."
                f"{suggestion_text}{available_text}"
            )
        value = inputs[matching_keys[0]]

    coerced = _coerce_template_value(value)
    if coerced is not None:
        return _apply_template_filters(coerced, filters or [])

    raise ValueError(
        f"Template reference '{node_name}.{widget_name}'"
        f"{f' from placeholder {placeholder!r}' if placeholder else ''} "
        "points to a linked or unsupported value. "
        "Only string, int, float, and bool widget inputs can be used."
    )


def _find_active_name_details(prompt: Any, unique_id: Any) -> dict[str, Any]:
    best_unet: tuple[int, int, int, str, str, str] | None = None
    best_clip: tuple[int, int, int, str, str, str] | None = None

    for node_id, node, distance in _walk_prompt_upstream(prompt, unique_id):
        class_type = str(node.get("class_type", ""))
        inputs = node.get("inputs", {})
        unet_priority = _get_unet_loader_priority(class_type, inputs)
        clip_priority = _get_clip_loader_priority(class_type, inputs)
        checkpoint_priority = _get_checkpoint_loader_priority(class_type, inputs)
        loader_label = _format_match_label(node_id, node)

        if unet_priority is not None or checkpoint_priority is not None:
            unet_values = _extract_string_inputs_from_node(
                node,
                exact=UNET_EXTRACTION_EXACT_KEYS if unet_priority is not None else CHECKPOINT_DETECTION_EXACT_KEYS,
                prefix=UNET_EXTRACTION_PREFIX_KEYS if unet_priority is not None else CHECKPOINT_DETECTION_PREFIX_KEYS,
            )
            priority = unet_priority if unet_priority is not None else checkpoint_priority
            for value_index, value in enumerate(unet_values):
                candidate = (priority, distance, value_index, value.casefold(), value, loader_label)
                if best_unet is None or candidate < best_unet:
                    best_unet = candidate

        if clip_priority is not None or checkpoint_priority is not None:
            clip_values = _extract_string_inputs_from_node(
                node,
                exact=CLIP_EXTRACTION_EXACT_KEYS if clip_priority is not None else CHECKPOINT_DETECTION_EXACT_KEYS,
                prefix=CLIP_EXTRACTION_PREFIX_KEYS if clip_priority is not None else CHECKPOINT_DETECTION_PREFIX_KEYS,
            )
            priority = clip_priority if clip_priority is not None else checkpoint_priority
            for value_index, value in enumerate(clip_values):
                candidate = (priority, distance, value_index, value.casefold(), value, loader_label)
                if best_clip is None or candidate < best_clip:
                    best_clip = candidate

    return {
        "ACTIVE_UNET": best_unet[4] if best_unet else "",
        "ACTIVE_CLIP": best_clip[4] if best_clip else "",
        "ACTIVE_UNET_SOURCE": best_unet[5] if best_unet else "",
        "ACTIVE_CLIP_SOURCE": best_clip[5] if best_clip else "",
        "ACTIVE_UNET_DISTANCE": best_unet[1] if best_unet else None,
        "ACTIVE_CLIP_DISTANCE": best_clip[1] if best_clip else None,
    }


def _find_active_names(prompt: Any, unique_id: Any) -> dict[str, str]:
    details = _find_active_name_details(prompt, unique_id)
    return {
        "ACTIVE_UNET": details["ACTIVE_UNET"],
        "ACTIVE_CLIP": details["ACTIVE_CLIP"],
    }


def _format_detection_loader_source(label: str, distance: int | None) -> str:
    if not label:
        return ""
    if not isinstance(distance, int):
        return label

    link_label = "upstream link" if distance == 1 else "upstream links"
    return f"{label}, {distance} {link_label}"


def _render_path_template(template: str, variables: dict[str, str], now: datetime, prompt: Any) -> str:
    def replace_date(match: re.Match[str]) -> str:
        return _render_date_format(match.group(1), now)

    rendered = DATE_TOKEN_RE.sub(replace_date, template or "")
    rendered = _replace_strftime_tokens(rendered, now)
    def replace_prompt_value(match: re.Match[str]) -> str:
        placeholder = match.group(0)
        return _resolve_prompt_input_value(
            prompt,
            match.group(1),
            match.group(2),
            placeholder=placeholder,
            filters=_parse_template_filters(match.group(3), placeholder),
        )

    rendered = SEARCH_REPLACE_TOKEN_RE.sub(replace_prompt_value, rendered)

    unknown_tokens = sorted(
        {
            match.group(1)
            for match in VARIABLE_TOKEN_RE.finditer(rendered)
            if match.group(1) not in variables
        }
    )
    if unknown_tokens:
        known_variables = sorted(variables)
        details = []
        for token in unknown_tokens:
            suggestions = get_close_matches(token, known_variables, n=2, cutoff=0.6)
            if suggestions:
                details.append(f"{token} (did you mean {', '.join(suggestions)}?)")
            else:
                details.append(token)
        raise ValueError(
            "Unknown path template variables: "
            + ", ".join(details)
            + ". Known variables: "
            + ", ".join(known_variables)
        )

    def replace_variable(match: re.Match[str]) -> str:
        placeholder = match.group(0)
        value = variables[match.group(1)]
        filters = _parse_template_filters(match.group(2), placeholder)
        return _apply_template_filters(value, filters)

    rendered = VARIABLE_TOKEN_RE.sub(replace_variable, rendered)

    remaining_tokens = sorted({match.group(1) for match in UNKNOWN_TOKEN_RE.finditer(rendered)})
    if remaining_tokens:
        raise ValueError(
            "Unknown path template placeholders: "
            + ", ".join(remaining_tokens)
            + ". Supported forms are %VARIABLE%, %VARIABLE:filter%, %node.widget%, "
            "%node.widget:filter%, %date:...%, and %strftime:...%."
        )

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

    DEFAULT_TEMPLATE = "%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%"
    DESCRIPTION = (
        "Save images into a clean, readable folder structure.\n\n"
        "Quick start:\n"
        "- Leave the default Save Layout alone for the simplest setup\n"
        "- Change Model Name, Text Encoder Name, or Filename only if you want different output\n"
        "- Leave Export Workflow Metadata on if you want PNG metadata like ComfyUI Save Image\n"
        "- Clear Save Layout only if you want the built-in folder order instead of a custom layout\n\n"
        "Default result example:\n"
        "portraits/FLUX.2 Klein 9B [5K-M]/Lockout Qwen3 4B zimage V2 [Her][Q8]/2026-04-22_15-30-10.png\n\n"
        "For multi-image batches, %BATCH% automatically adds _1-of-4, _2-of-4, and so on.\n\n"
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
                            "Text Encoder Name / Filename plus an automatic batch suffix for multi-image saves. "
                            "Clear it only if you want the built-in order."
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
                "detection_info": (
                    DETECTION_INFO_OPTIONS,
                    {
                        "default": "Off",
                        "tooltip": (
                            "Optional runtime detection summary in the node output text. "
                            "Use Summary or Verbose when you want to see which model and text "
                            "encoder names were detected and selected."
                        ),
                    },
                ),
                "export_workflow_metadata": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": (
                            "Store prompt and workflow metadata in the PNG, like ComfyUI's normal "
                            "Save Image node. Turn this off when you want clean PNG files without "
                            "embedded workflow data."
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

    def _build_metadata(
        self,
        *,
        export_workflow_metadata: bool,
        prompt: Any = None,
        extra_pnginfo: Any = None,
    ) -> PngImagePlugin.PngInfo | None:
        if not export_workflow_metadata:
            return None

        metadata = PngImagePlugin.PngInfo()

        if prompt is not None:
            metadata.add_text("prompt", json.dumps(prompt))

        if extra_pnginfo is not None:
            if isinstance(extra_pnginfo, dict):
                for key, value in extra_pnginfo.items():
                    metadata.add_text(str(key), json.dumps(value))
            else:
                metadata.add_text("extra_pnginfo", json.dumps(extra_pnginfo))

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
        image_width: int | None,
        image_height: int | None,
        batch_index: int,
        batch_size: int,
        now: datetime,
    ) -> tuple[dict[str, str], dict[str, str]]:
        active_names = _find_active_name_details(prompt=prompt, unique_id=unique_id)
        seed_value = _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("seed", "noise_seed"),
            prefix=("seed", "noise_seed"),
        )
        steps_value = _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("steps",),
        )
        cfg_value = _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("cfg",),
        )
        sampler_value = _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("sampler_name", "sampler"),
        )
        scheduler_value = _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("scheduler",),
        )
        denoise_value = _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("denoise",),
        )
        width_value = str(image_width) if image_width is not None else _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("width",),
        )
        height_value = str(image_height) if image_height is not None else _find_upstream_scalar_input(
            prompt,
            unique_id,
            exact=("height",),
        )

        manual_model = _strip_known_extension(model_folder)
        manual_clip = _strip_known_extension(clip_folder)
        raw_active_unet = active_names["ACTIVE_UNET"] or manual_model or "model"
        raw_active_clip = active_names["ACTIVE_CLIP"] or manual_clip or "text-encoder"
        active_unet = _basename_without_known_extension(raw_active_unet) or manual_model or "model"
        active_clip = _basename_without_known_extension(raw_active_clip) or manual_clip or "text-encoder"

        variables = {
            "EXACT_MODEL_NAME": active_unet,
            "EXACT_TEXT_ENCODER_NAME": active_clip,
            "FRIENDLY_MODEL_NAME": _humanize_display_name(raw_active_unet, kind="model"),
            "FRIENDLY_TEXT_ENCODER_NAME": _humanize_display_name(raw_active_clip, kind="text_encoder"),
            "CLEAN_FRIENDLY_MODEL_NAME": _humanize_clean_display_name(raw_active_unet, kind="model"),
            "CLEAN_FRIENDLY_TEXT_ENCODER_NAME": _humanize_clean_display_name(raw_active_clip, kind="text_encoder"),
            "CUSTOM_MODEL_NAME": manual_model or "",
            "CUSTOM_TEXT_ENCODER_NAME": manual_clip or "",
            "WIDTH": width_value or "0",
            "HEIGHT": height_value or "0",
            "SEED": seed_value or "",
            "STEPS": steps_value or "",
            "CFG": cfg_value or "",
            "SAMPLER": sampler_value or "",
            "SCHEDULER": scheduler_value or "",
            "DENOISE": denoise_value or "",
            "BATCH": f"_{batch_index}-of-{batch_size}" if batch_size > 1 else "",
            "BATCH_INDEX": str(batch_index),
            "BATCH_SIZE": str(batch_size),
            "TOP_FOLDER": _sanitize_path_component(subfolder) if subfolder.strip() else "",
            "FILENAME": _render_filename_value(filename_datetime or DEFAULT_FILENAME_PATTERN, now),
        }
        variables["MODEL_NAME"] = _resolve_selected_variable(model_source, variables, kind="model")
        variables["TEXT_ENCODER_NAME"] = _resolve_selected_variable(clip_source, variables, kind="clip")

        detection_state = {
            "RAW_ACTIVE_MODEL_NAME": active_names["ACTIVE_UNET"] or "",
            "RAW_ACTIVE_TEXT_ENCODER_NAME": active_names["ACTIVE_CLIP"] or "",
            "DETECTED_MODEL_NAME": active_unet if active_names["ACTIVE_UNET"] else "",
            "DETECTED_TEXT_ENCODER_NAME": active_clip if active_names["ACTIVE_CLIP"] else "",
            "MODEL_DETECTION_SOURCE": (
                "workflow" if active_names["ACTIVE_UNET"] else "custom_fallback" if manual_model else "default_placeholder"
            ),
            "TEXT_ENCODER_DETECTION_SOURCE": (
                "workflow" if active_names["ACTIVE_CLIP"] else "custom_fallback" if manual_clip else "default_placeholder"
            ),
            "MODEL_DETECTION_LABEL": active_names["ACTIVE_UNET_SOURCE"] if active_names["ACTIVE_UNET"] else "",
            "TEXT_ENCODER_DETECTION_LABEL": active_names["ACTIVE_CLIP_SOURCE"] if active_names["ACTIVE_CLIP"] else "",
            "MODEL_DETECTION_DISTANCE": active_names["ACTIVE_UNET_DISTANCE"] if active_names["ACTIVE_UNET"] else None,
            "TEXT_ENCODER_DETECTION_DISTANCE": active_names["ACTIVE_CLIP_DISTANCE"]
            if active_names["ACTIVE_CLIP"]
            else None,
            "MANUAL_MODEL_NAME": manual_model,
            "MANUAL_TEXT_ENCODER_NAME": manual_clip,
            "SELECTED_MODEL_SOURCE": model_source,
            "SELECTED_TEXT_ENCODER_SOURCE": clip_source,
            "SELECTED_MODEL_NAME": variables["MODEL_NAME"],
            "SELECTED_TEXT_ENCODER_NAME": variables["TEXT_ENCODER_NAME"],
            "EXACT_MODEL_NAME": variables["EXACT_MODEL_NAME"],
            "EXACT_TEXT_ENCODER_NAME": variables["EXACT_TEXT_ENCODER_NAME"],
            "FRIENDLY_MODEL_NAME": variables["FRIENDLY_MODEL_NAME"],
            "FRIENDLY_TEXT_ENCODER_NAME": variables["FRIENDLY_TEXT_ENCODER_NAME"],
            "CLEAN_FRIENDLY_MODEL_NAME": variables["CLEAN_FRIENDLY_MODEL_NAME"],
            "CLEAN_FRIENDLY_TEXT_ENCODER_NAME": variables["CLEAN_FRIENDLY_TEXT_ENCODER_NAME"],
            "CUSTOM_MODEL_NAME": variables["CUSTOM_MODEL_NAME"],
            "CUSTOM_TEXT_ENCODER_NAME": variables["CUSTOM_TEXT_ENCODER_NAME"],
            "WIDTH": variables["WIDTH"],
            "HEIGHT": variables["HEIGHT"],
            "SEED": variables["SEED"],
            "STEPS": variables["STEPS"],
            "CFG": variables["CFG"],
            "SAMPLER": variables["SAMPLER"],
            "SCHEDULER": variables["SCHEDULER"],
            "DENOISE": variables["DENOISE"],
            "BATCH": variables["BATCH"],
            "BATCH_INDEX": variables["BATCH_INDEX"],
            "BATCH_SIZE": variables["BATCH_SIZE"],
        }

        return variables, detection_state

    def _build_detection_info_lines(self, detection_info: str, detection_state: dict[str, Any]) -> list[str]:
        if detection_info == "Off":
            return []

        def format_detection_line(
            kind_label: str,
            detection_source: str,
            detected_value: str,
            manual_value: str,
            detection_label: str,
            detection_distance: int | None,
        ) -> str:
            if detection_source == "workflow":
                source_detail = _format_detection_loader_source(detection_label, detection_distance)
                source_suffix = f" (from {source_detail})" if source_detail else ""
                return f"{kind_label} detection: workflow loader -> {detected_value}{source_suffix}"
            if detection_source == "custom_fallback":
                return f"{kind_label} detection: custom fallback -> {manual_value}"
            return f"{kind_label} detection: no workflow loader found on this save branch, using default placeholder"

        lines = [
            "Detection Summary",
            format_detection_line(
                "Model",
                detection_state["MODEL_DETECTION_SOURCE"],
                detection_state["DETECTED_MODEL_NAME"],
                detection_state["MANUAL_MODEL_NAME"],
                detection_state["MODEL_DETECTION_LABEL"],
                detection_state["MODEL_DETECTION_DISTANCE"],
            ),
            (
                f"Model output: {detection_state['SELECTED_MODEL_SOURCE']} -> "
                f"{detection_state['SELECTED_MODEL_NAME']}"
            ),
            format_detection_line(
                "Text encoder",
                detection_state["TEXT_ENCODER_DETECTION_SOURCE"],
                detection_state["DETECTED_TEXT_ENCODER_NAME"],
                detection_state["MANUAL_TEXT_ENCODER_NAME"],
                detection_state["TEXT_ENCODER_DETECTION_LABEL"],
                detection_state["TEXT_ENCODER_DETECTION_DISTANCE"],
            ),
            (
                f"Text encoder output: {detection_state['SELECTED_TEXT_ENCODER_SOURCE']} -> "
                f"{detection_state['SELECTED_TEXT_ENCODER_NAME']}"
            ),
        ]

        if detection_info == "Verbose":
            lines.extend(
                [
                    (
                        "Model variants: "
                        f"Friendly={detection_state['FRIENDLY_MODEL_NAME']} | "
                        f"Friendly Clean={detection_state['CLEAN_FRIENDLY_MODEL_NAME']} | "
                        f"Exact={detection_state['EXACT_MODEL_NAME']} | "
                        f"Custom={detection_state['CUSTOM_MODEL_NAME'] or '(empty)'}"
                    ),
                    (
                        "Text encoder variants: "
                        f"Friendly={detection_state['FRIENDLY_TEXT_ENCODER_NAME']} | "
                        f"Friendly Clean={detection_state['CLEAN_FRIENDLY_TEXT_ENCODER_NAME']} | "
                        f"Exact={detection_state['EXACT_TEXT_ENCODER_NAME']} | "
                        f"Custom={detection_state['CUSTOM_TEXT_ENCODER_NAME'] or '(empty)'}"
                    ),
                ]
            )

        return lines

    def _build_detection_ui_payload(
        self,
        *,
        preview: str,
        detection_state: dict[str, Any],
        detection_lines: list[str],
    ) -> dict[str, Any]:
        return {
            "preview": preview,
            "detection_lines": list(detection_lines),
            "model_detection_source": detection_state["MODEL_DETECTION_SOURCE"],
            "text_encoder_detection_source": detection_state["TEXT_ENCODER_DETECTION_SOURCE"],
            "model_detection_label": detection_state["MODEL_DETECTION_LABEL"],
            "text_encoder_detection_label": detection_state["TEXT_ENCODER_DETECTION_LABEL"],
            "model_detection_distance": detection_state["MODEL_DETECTION_DISTANCE"],
            "text_encoder_detection_distance": detection_state["TEXT_ENCODER_DETECTION_DISTANCE"],
            "detected_model_name": detection_state["DETECTED_MODEL_NAME"],
            "detected_text_encoder_name": detection_state["DETECTED_TEXT_ENCODER_NAME"],
            "selected_model_source": detection_state["SELECTED_MODEL_SOURCE"],
            "selected_text_encoder_source": detection_state["SELECTED_TEXT_ENCODER_SOURCE"],
            "selected_model_name": detection_state["SELECTED_MODEL_NAME"],
            "selected_text_encoder_name": detection_state["SELECTED_TEXT_ENCODER_NAME"],
            "exact_model_name": detection_state["EXACT_MODEL_NAME"],
            "exact_text_encoder_name": detection_state["EXACT_TEXT_ENCODER_NAME"],
            "friendly_model_name": detection_state["FRIENDLY_MODEL_NAME"],
            "friendly_text_encoder_name": detection_state["FRIENDLY_TEXT_ENCODER_NAME"],
            "clean_friendly_model_name": detection_state["CLEAN_FRIENDLY_MODEL_NAME"],
            "clean_friendly_text_encoder_name": detection_state["CLEAN_FRIENDLY_TEXT_ENCODER_NAME"],
            "custom_model_name": detection_state["CUSTOM_MODEL_NAME"],
            "custom_text_encoder_name": detection_state["CUSTOM_TEXT_ENCODER_NAME"],
            "width": detection_state["WIDTH"],
            "height": detection_state["HEIGHT"],
            "seed": detection_state["SEED"],
            "steps": detection_state["STEPS"],
            "cfg": detection_state["CFG"],
            "sampler": detection_state["SAMPLER"],
            "scheduler": detection_state["SCHEDULER"],
            "denoise": detection_state["DENOISE"],
            "batch": detection_state["BATCH"],
            "batch_index": detection_state["BATCH_INDEX"],
            "batch_size": detection_state["BATCH_SIZE"],
        }

    def _resolve_relative_output_path(
        self,
        *,
        model_folder: str,
        clip_folder: str,
        filename_datetime: str,
        subfolder: str,
        model_source: str,
        clip_source: str,
        detection_info: str,
        image_width: int | None,
        image_height: int | None,
        batch_index: int,
        batch_size: int,
        path_template: str,
        prompt: Any,
        unique_id: Any,
    ) -> tuple[Path, str, list[str], dict[str, str]]:
        now = datetime.now()
        variables, detection_state = self._build_template_variables(
            prompt=prompt,
            unique_id=unique_id,
            model_folder=model_folder,
            clip_folder=clip_folder,
            filename_datetime=filename_datetime,
            subfolder=subfolder,
            model_source=model_source,
            clip_source=clip_source,
            image_width=image_width,
            image_height=image_height,
            batch_index=batch_index,
            batch_size=batch_size,
            now=now,
        )
        detection_lines = self._build_detection_info_lines(detection_info, detection_state)

        if path_template and path_template.strip():
            rendered = _render_path_template(path_template.strip(), variables, now, prompt)
            relative_path = _normalize_template_file_path(rendered)
            return relative_path, rendered, detection_lines, detection_state

        clean_model = _sanitize_path_component(variables["MODEL_NAME"])
        clean_clip = _sanitize_path_component(variables["TEXT_ENCODER_NAME"])
        clean_subfolder = _sanitize_path_component(subfolder) if subfolder.strip() else ""
        base_name = f"{variables['FILENAME']}{variables['BATCH']}"

        relative_path = Path(clean_model) / clean_clip / f"{base_name}.png"
        if clean_subfolder:
            relative_path = Path(clean_subfolder) / relative_path
        preview = str(relative_path.with_suffix(""))
        return relative_path, preview, detection_lines, detection_state

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
        detection_info: str,
        export_workflow_metadata: bool,
        subfolder: str = "",
        model_folder: str = "",
        clip_folder: str = "",
        filename_datetime: str = DEFAULT_FILENAME_PATTERN,
        prompt: Any = None,
        extra_pnginfo: Any = None,
        unique_id: Any = None,
    ):
        output_root = Path(self.output_dir)
        metadata = self._build_metadata(
            export_workflow_metadata=export_workflow_metadata,
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
        saved = []
        preview = ""
        detection_lines: list[str] = []
        detection_ui_payload: dict[str, Any] | None = None
        batch_size = len(images)
        for batch_index, image in enumerate(images, start=1):
            array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
            image_height, image_width = array.shape[:2]
            relative_path, current_preview, current_detection_lines, current_detection_state = self._resolve_relative_output_path(
                model_folder=model_folder,
                clip_folder=clip_folder,
                filename_datetime=filename_datetime,
                subfolder=subfolder,
                model_source=model_source,
                clip_source=clip_source,
                detection_info=detection_info,
                image_width=image_width,
                image_height=image_height,
                batch_index=batch_index,
                batch_size=batch_size,
                path_template=path_template,
                prompt=prompt,
                unique_id=unique_id,
            )
            if not preview:
                preview = current_preview
                detection_lines = current_detection_lines
                detection_ui_payload = self._build_detection_ui_payload(
                    preview=current_preview,
                    detection_state=current_detection_state,
                    detection_lines=current_detection_lines,
                )

            target_path = self._resolve_target_path(
                output_root=output_root,
                relative_path=relative_path,
                collision_mode=collision_mode,
            )

            pil_image = Image.fromarray(array)
            pil_image.save(target_path, pnginfo=metadata, compress_level=self.compress_level)

            saved.append(
                {
                    "filename": target_path.name,
                    "subfolder": str(target_path.parent.relative_to(output_root)) if target_path.parent != output_root else "",
                    "type": self.type,
                }
            )

        ui = {"images": saved, "text": [preview, *detection_lines]}
        if detection_ui_payload is not None:
            ui["save_image_clean"] = [detection_ui_payload]
        return {"ui": ui}


NODE_CLASS_MAPPINGS = {
    "StripModelExtension": StripModelExtension,
    "SaveImageClean": SaveImageClean,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StripModelExtension": "Strip Model Extension",
    "SaveImageClean": "Save Image Organized",
}
