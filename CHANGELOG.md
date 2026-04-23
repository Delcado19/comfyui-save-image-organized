# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- ComfyUI-style `%node.widget%` placeholders in `Save Image Clean`
- best-effort resolution against node title, custom `Node name for S&R`, class name, and node id
- in-node descriptions and field tooltips for `Save Image Clean` and `Strip Model Extension`
- markdown node documentation for the ComfyUI `Info` tab via `WEB_DIRECTORY/docs`
- in-node helper panel for `Save Image Clean`

### Changed

- `%date:...%` formatting now follows the documented ComfyUI-style tokens, including single-letter tokens such as `M`, `d`, `h`, `m`, and `s`
- `%strftime:...%` now supports the documented subset `%Y`, `%y`, `%m`, `%d`, `%H`, `%M`, `%S`, `%f`, and `%%`
- active names now use the basename instead of the full model path, and friendly text encoder names keep compatibility markers such as `zimage`, move versions ahead of bracket tags, and render `Q8`-style quant suffixes as a final bracket tag such as `[Q8]`
- active loader detection now recognizes more UNET, text encoder, and checkpoint loader naming patterns, including common custom-node variants such as diffusion-model loaders and GGUF-style loaders
- `Save Image Clean` was rebuilt around a clean `Top Folder / Model Name / Text Encoder / Filename` model
- `Save Layout` now defaults to `%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%`
- `Filename` is now a first-class field with the default `%date:yyyy-MM-dd_hh-mm-ss%`
- the visible dropdown choices are now only `Friendly`, `Exact`, and `Custom`
- `Custom Model Name` and `Custom Text Encoder Name` are now used directly in `Custom` mode and automatically as fallback if detection fails
- the template variable names now match the visible UI language: `%TOP_FOLDER%`, `%MODEL_NAME%`, `%TEXT_ENCODER_NAME%`, and `%FILENAME%`
- friendly names now shorten common descriptor words such as `abliterated`, `instruct`, `heretic`, and `uncensored` into bracket tags like `[Ablt]`, `[Inst]`, `[Her]`, and `[Unc]`
- friendly model names now normalize known image-model families such as `FLUX.2 Klein 9B`, `Qwen Image Edit 2511`, `Z-Image Turbo`, and `ERNIE Image`
- `Output Root` was removed to keep the node focused on ComfyUI's normal output folder
- the node help and markdown docs were rewritten around the new naming scheme and simpler default flow

## [0.1.0] - 2026-04-21

### Added

- initial Git repository structure
- `Save Image Clean` node with legacy and template-based save modes
- automatic upstream detection for active UNET and CLIP loader names
- template variables for model, clip and date-based output paths
- `Strip Model Extension` utility node
- repository documentation for installation, usage and contribution workflow
