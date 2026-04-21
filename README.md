# ComfyUI Clean Save Nodes

## Purpose

This custom node package extends ComfyUI with clean, minimal, and workflow-oriented image saving.

The focus is on:

- clear folder structure (`Model / CLIP`)
- short, consistent filenames
- automatic detection of active loader names
- template-based output paths
- preservation of prompt and PNG metadata

---

## Included Nodes

- `Save Image Clean`
- `Strip Model Extension`

---

## Quick Start

1. Place the repository in `ComfyUI/custom_nodes/comfyui-clean-save-nodes`.
2. Install the dependencies from `requirements.txt` in the Python environment used by ComfyUI.
3. Restart ComfyUI.
4. Use `Save Image Clean` in your workflow.

Additional documentation:

- [Installation](docs/INSTALLATION.md)
- [Usage](docs/USAGE.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---

## Save Image Clean

`Save Image Clean` now supports two modes:

- legacy mode via `model_folder`, `clip_folder`, `subfolder`, and `filename_datetime`
- template mode via `path_template`

If `path_template` is empty, the node continues to use legacy mode. This keeps existing workflows compatible.

### Legacy Mode

Legacy mode saves using this structure:

```text
<output_root>/<subfolder>/<model_folder>/<clip_folder>/<filename_datetime>.png
```

`filename_datetime` uses Python `strftime`.

Example:

```text
%Y-%m-%d_%H-%M
```

### Template Mode

If `path_template` is set, the target path is built from a template.

Recommended starting value:

```text
%ACTIVE_UNET%/%ACTIVE_CLIP%/%date:yyyy-MM-dd_hh-mm%
```

Example result:

```text
jibMixZIT_v10/Huihui-Qwen3-4B-abliterated-v2.Q8_0/2026-04-21_14-37.png
```

### Supported Template Variables

- `%ACTIVE_UNET%`
- `%ACTIVE_CLIP%`
- `%MODEL_SHORT%`
- `%CLIP_SHORT%`
- `%MODEL_FOLDER%`
- `%CLIP_FOLDER%`
- `%SUBFOLDER%`

### Supported Date Placeholders

Template mode supports ComfyUI-style date segments:

```text
%date:yyyy-MM-dd_hh-mm%
```

The following tokens are currently supported:

- `yyyy`
- `yy`
- `MM`
- `dd`
- `HH`
- `hh`
- `mm`
- `ss`

Note:
`hh` and `HH` currently both produce 24-hour output.

### Automatic Loader Detection

In template mode, the node attempts to detect the active name by traversing the ComfyUI `prompt` graph upstream from the current save node.

The detection currently prioritizes:

- UNET loaders via classes whose names contain `UnetLoader`
- CLIP loaders via classes whose names contain `ClipLoader`
- checkpoint loaders as a fallback via classes whose names contain `CheckpointLoader`

If detection is not possible, the node falls back to the manually provided `model_folder` and `clip_folder` values.

### Shorter Name Variants

`%MODEL_SHORT%` and `%CLIP_SHORT%` remove known model extensions and also trim prefixes in patterns like:

```text
mradermacher - Huihui-Qwen3-4B-abliterated-v2.Q8_0.gguf
```

to:

```text
Huihui-Qwen3-4B-abliterated-v2.Q8_0
```

### Path and Name Sanitization

The following extensions are removed automatically:

- `.safetensors`
- `.gguf`
- `.ckpt`
- `.pt`
- `.pth`
- `.bin`
- `.onnx`

Invalid Windows path characters are also replaced so paths and filenames remain stable.

### Collision Handling

Supported modes:

- `increment`
- `overwrite`
- `error`
- `seconds`

Example for `increment`:

```text
2026-04-21_14-30.png
2026-04-21_14-30-2.png
```

### Metadata

When saving, the node writes existing ComfyUI data into the PNG file:

- `prompt`
- contents of `extra_pnginfo`

### UI Preview

After execution, the node returns a UI text value containing the resolved relative target path.

This is a runtime preview after template resolution, not a permanent live preview inside the node before execution.

---

## Strip Model Extension

This utility node removes exactly one known model file extension from the end of a string.

Example:

```text
my-model.safetensors -> my-model
```

---

## What Is Still Not Implemented

The current version covers the core feature set, but not everything from the original wishlist.

Not yet implemented:

- a true live preview directly inside the node before execution
- broader detection for exotic or project-specific loader types
- freely configurable string manipulation inside templates
- more advanced shortening rules beyond the current prefix removal

---

## Design Principles

- folders = structure (`Model / CLIP`)
- filename = clear and short
- metadata = preserved completely
- behavior = explicit instead of implicit

---

## Summary

The node now supports both the previous manual save workflow and an automatic template-based workflow.

If you use `path_template`, you can combine model, clip, and time information directly in the target path without manually rebuilding the path for each workflow.
