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


def _shorten_model_name(value: str) -> str:
    value = _strip_known_extension(value)
    if " - " in value:
        value = value.split(" - ")[-1].strip()
    return value.strip() or "unnamed"


def _normalize_template_file_path(value: str) -> Path:
    relative_path = _sanitize_relative_path(value)
    if relative_path.suffix.lower() == ".png":
        relative_path = relative_path.with_suffix("")
    return relative_path.with_suffix(".png")


def _to_python_datetime_format(value: str) -> str:
    converted = value
    for source, target in (
        ("yyyy", "%Y"),
        ("yy", "%y"),
        ("MM", "%m"),
        ("dd", "%d"),
        ("HH", "%H"),
        ("hh", "%H"),
        ("mm", "%M"),
        ("ss", "%S"),
    ):
        converted = converted.replace(source, target)
    return converted


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

    for key, value in inputs.items():
        if not isinstance(value, str):
            continue

        key_lower = key.lower()
        if key_lower not in exact and not any(key_lower.startswith(item) for item in prefix):
            continue

        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            values.append(cleaned)
            seen.add(cleaned)

    return values


def _find_active_names(prompt: Any, unique_id: Any) -> dict[str, str]:
    best_unet: tuple[int, int, str] | None = None
    best_clip: tuple[int, int, str] | None = None

    for _, node, distance in _walk_prompt_upstream(prompt, unique_id):
        class_type = str(node.get("class_type", ""))
        inputs = node.get("inputs", {})
        class_name = class_type.lower()

        is_unet_loader = "unetloader" in class_name
        is_clip_loader = "cliploader" in class_name
        is_checkpoint_loader = "checkpointloader" in class_name

        if is_unet_loader or is_checkpoint_loader:
            unet_values = _extract_string_inputs(
                inputs,
                exact=("unet_name", "model_name", "ckpt_name", "name"),
                prefix=("unet_name",),
            )
            for value in unet_values:
                candidate = (0 if is_unet_loader else 1, distance, value)
                if best_unet is None or candidate < best_unet:
                    best_unet = candidate

        if is_clip_loader or is_checkpoint_loader:
            clip_values = _extract_string_inputs(
                inputs,
                exact=("clip_name", "model_name", "ckpt_name", "name"),
                prefix=("clip_name",),
            )
            for value in clip_values:
                candidate = (0 if is_clip_loader else 1, distance, value)
                if best_clip is None or candidate < best_clip:
                    best_clip = candidate

    return {
        "ACTIVE_UNET": best_unet[2] if best_unet else "",
        "ACTIVE_CLIP": best_clip[2] if best_clip else "",
    }


def _render_path_template(template: str, variables: dict[str, str], now: datetime) -> str:
    def replace_date(match: re.Match[str]) -> str:
        python_format = _to_python_datetime_format(match.group(1))
        return now.strftime(python_format)

    rendered = DATE_TOKEN_RE.sub(replace_date, template or "")

    unknown_tokens = sorted(
        {
            match.group(1)
            for match in VARIABLE_TOKEN_RE.finditer(rendered)
            if match.group(1) not in variables
        }
    )
    if unknown_tokens:
        raise ValueError(f"Unknown path template variables: {', '.join(unknown_tokens)}")

    return VARIABLE_TOKEN_RE.sub(lambda match: variables[match.group(1)], rendered)


class StripModelExtension:
    """Remove only the final known model extension from a loader/model name string."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("clean_text",)
    FUNCTION = "run"
    CATEGORY = "utils/filename"

    def run(self, text: str):
        return (_strip_known_extension(text),)


class SaveImageClean:
    """Save images using either an explicit template or the legacy folder fields."""

    DEFAULT_TEMPLATE = "%ACTIVE_UNET%/%ACTIVE_CLIP%/%date:yyyy-MM-dd_hh-mm%"

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
                "model_folder": ("STRING", {"multiline": False, "default": "model"}),
                "clip_folder": ("STRING", {"multiline": False, "default": "clip"}),
                "filename_datetime": (
                    "STRING",
                    {"multiline": False, "default": "%Y-%m-%d_%H-%M"},
                ),
                "collision_mode": (
                    ["increment", "overwrite", "error", "seconds"],
                    {"default": "increment"},
                ),
                "subfolder": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                "base_output_folder": ("STRING", {"multiline": False, "default": ""}),
                "path_template": ("STRING", {"multiline": False, "default": ""}),
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

    def _resolve_output_root(self, base_output_folder: str | None) -> Path:
        if base_output_folder and base_output_folder.strip():
            return Path(base_output_folder.strip())
        return Path(self.output_dir)

    def _build_template_variables(
        self,
        *,
        prompt: Any,
        unique_id: Any,
        model_folder: str,
        clip_folder: str,
        subfolder: str,
    ) -> dict[str, str]:
        active_names = _find_active_names(prompt=prompt, unique_id=unique_id)

        manual_model = _strip_known_extension(model_folder)
        manual_clip = _strip_known_extension(clip_folder)
        active_unet = _strip_known_extension(active_names["ACTIVE_UNET"] or manual_model or "model")
        active_clip = _strip_known_extension(active_names["ACTIVE_CLIP"] or manual_clip or "clip")

        return {
            "ACTIVE_UNET": active_unet,
            "ACTIVE_CLIP": active_clip,
            "MODEL_SHORT": _shorten_model_name(active_unet),
            "CLIP_SHORT": _shorten_model_name(active_clip),
            "MODEL_FOLDER": manual_model or active_unet,
            "CLIP_FOLDER": manual_clip or active_clip,
            "SUBFOLDER": _sanitize_path_component(subfolder) if subfolder.strip() else "",
        }

    def _resolve_relative_output_path(
        self,
        *,
        model_folder: str,
        clip_folder: str,
        filename_datetime: str,
        subfolder: str,
        path_template: str,
        prompt: Any,
        unique_id: Any,
    ) -> tuple[Path, str]:
        now = datetime.now()

        if path_template and path_template.strip():
            variables = self._build_template_variables(
                prompt=prompt,
                unique_id=unique_id,
                model_folder=model_folder,
                clip_folder=clip_folder,
                subfolder=subfolder,
            )
            rendered = _render_path_template(path_template.strip(), variables, now)
            relative_path = _normalize_template_file_path(rendered)
            return relative_path, rendered

        clean_model = _sanitize_path_component(_strip_known_extension(model_folder))
        clean_clip = _sanitize_path_component(_strip_known_extension(clip_folder))
        clean_subfolder = _sanitize_path_component(subfolder) if subfolder.strip() else ""
        base_name = _sanitize_path_component(now.strftime(filename_datetime))

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
        model_folder: str,
        clip_folder: str,
        filename_datetime: str,
        collision_mode: str,
        subfolder: str,
        base_output_folder: str = "",
        path_template: str = "",
        prompt: Any = None,
        extra_pnginfo: Any = None,
        unique_id: Any = None,
    ):
        output_root = self._resolve_output_root(base_output_folder)
        metadata = self._build_metadata(prompt=prompt, extra_pnginfo=extra_pnginfo)
        relative_path, preview = self._resolve_relative_output_path(
            model_folder=model_folder,
            clip_folder=clip_folder,
            filename_datetime=filename_datetime,
            subfolder=subfolder,
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
