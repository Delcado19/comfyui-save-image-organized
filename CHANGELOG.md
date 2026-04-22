# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- ComfyUI-style `%node.widget%` placeholders in `path_template`
- best-effort resolution against node title, custom `Node name for S&R`, class name, and node id
- in-node descriptions and field tooltips for `Save Image Clean` and `Strip Model Extension`
- markdown node documentation for the ComfyUI `Info` tab via `WEB_DIRECTORY/docs`
- dropdown-based `model_source` and `clip_source` selection with matching custom value fields
- new `%MODEL_DISPLAY%`, `%CLIP_DISPLAY%`, `%MODEL_SELECTED%`, and `%CLIP_SELECTED%` template variables

### Changed

- `%date:...%` formatting now stays aligned with the documented ComfyUI-style tokens, including single-letter tokens such as `M`, `d`, `h`, `m`, and `s`
- `%strftime:...%` now supports a small documented subset: `%Y`, `%y`, `%m`, `%d`, `%H`, `%M`, `%S`, `%f`, and `%%`
- active names now use the basename instead of the full model path, and display variables render recognized quant suffixes in a compact readable form such as `[4K-M]` or `[8F]`
- active loader detection now recognizes more UNET, text encoder, and checkpoint loader naming patterns, including common custom-node variants such as diffusion-model loaders and GGUF-style loaders

## [0.1.0] - 2026-04-21

### Added

- initial Git repository structure
- `Save Image Clean` node with legacy and template-based save modes
- automatic upstream detection for active UNET and CLIP loader names
- template variables for model, clip and date-based output paths
- `Strip Model Extension` utility node
- repository documentation for installation, usage and contribution workflow
