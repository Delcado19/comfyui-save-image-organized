# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.5.3] - 2026-05-02

### Added

- maintainer helper for dry-run verification and in-place migration from standard ComfyUI `SaveImage` workflow nodes to `SaveImageClean`
- regression coverage for expected image-only private workflow MISS branches, including postprocessing and upscale-model-only save paths
- regression coverage that keeps `Friendly Clean` conservative: known packager prefixes are removed while creator or producer prefixes remain intact
- detection diagnostics now include the selected loader node's upstream link distance in UI text and structured helper payloads

## [0.5.2] - 2026-05-02

### Changed

- Updated the Comfy Registry icon source metadata while preserving the existing Inkscape-authored design

## [0.5.1] - 2026-05-01

### Added

- Comfy Registry icon metadata and a dedicated square registry icon asset
- documentation for Comfy Registry installation and the GitHub Actions publishing workflow

## [0.5.0] - 2026-05-01

### Added

- repository `AGENTS.md` policy for Git operations, release checks, and CI verification
- maintainer workflow validation now reports a `reason` for each Save node in table and JSON output
- release-readiness checks can fail only on unresolved reachable-loader detection problems while allowing expected no-loader save branches
- release-readiness workflow checks now scan all workflows by default, with `--workflow-limit` kept for explicit sampling
- `Friendly Clean` model and text-encoder name sources that keep Friendly formatting while removing known releaser or publisher prefixes

### Fixed

- maintainer workflow validation now follows UI workflow links through unnamed Reroute inputs

## [0.4.0] - 2026-05-01

### Added

- maintainer workflow validator for scanning local ComfyUI workflow JSON files and reporting `Save Image Organized` model/text-encoder detection results
- detection summaries and helper snapshots now include the upstream workflow loader node label when a model or text encoder name is detected
- maintainer release-readiness checker for local validation plus optional tag, GitHub release, and Actions checks
- convenience template variables for upstream sampler settings: `%STEPS%`, `%CFG%`, `%SAMPLER%`, `%SCHEDULER%`, and `%DENOISE%`

## [0.3.1] - 2026-04-30

### Fixed

- detect checkpoint loader names from widget-only custom loaders that store the selected file in an object value such as `{content: "..."}`

## [0.3.0] - 2026-04-30

### Added

- optional `Detection Info` runtime output with `Off`, `Summary`, and `Verbose` modes for model and text encoder resolution
- convenience template variables `%WIDTH%`, `%HEIGHT%`, `%SEED%`, `%BATCH_INDEX%`, and `%BATCH_SIZE%`
- optional `Export Workflow Metadata` switch for matching normal ComfyUI PNG metadata export or disabling it entirely
- persistent helper detection snapshots, including `Fresh Detection` and `Last Detection Snapshot` states
- public synthetic workflow fixtures for checkpoint loaders, bridge nodes, switch branches, widget-only loaders, and LoRA pass-through paths
- GitHub Actions CI on Windows with `ruff` and `pytest`
- isolated `uv`-based local `pytest` setup for repo maintenance
- regression coverage for template errors, save output, collision handling, PNG metadata, loader detection, detection-info output, helper state, and convenience variables
- troubleshooting documentation for common detection and helper-preview states

### Changed

- path template errors now report clearer guidance for unknown variables, unknown `%node.widget%` node references, ambiguous node matches, unknown widget names, and linked or unsupported widget values
- the in-node helper preview now warns about unknown placeholders, shows `%node.widget%` values as `{node.widget}` before execution, and makes it clearer that detected names are sample values until the workflow runs
- after execution, the helper preview now switches to the last real resolved save path and can show the latest detection details
- PNG metadata export now matches ComfyUI's normal `Save Image` behavior by JSON-encoding prompt and workflow data
- loader detection now avoids cross-contaminating generic fields, follows `GetNode`/`SetNode` bridge paths, respects active `ComfySwitchNode` branches, and supports widget-only loader values from exported workflows
- multi-loader cases are documented and maintained as `Primary only`, resolving to one active model name and one active text-encoder name for stable output paths

### Fixed

- the UI label for workflow metadata export now matches the backend behavior
- preserve the user's manually resized node height when the helper preview refreshes, so the image preview area no longer collapses back to the minimum size

## [0.2.0] - 2026-04-23

### Added

- ComfyUI-style `%node.widget%` placeholders in `Save Image Organized`
- best-effort resolution against node title, custom `Node name for S&R`, class name, and node id
- in-node descriptions and field tooltips for `Save Image Organized` and `Strip Model Extension`
- markdown node documentation for the ComfyUI `Info` tab via `WEB_DIRECTORY/docs`
- in-node helper panel for `Save Image Organized`

### Changed

- `%date:...%` formatting now follows the documented ComfyUI-style tokens, including single-letter tokens such as `M`, `d`, `h`, `m`, and `s`
- `%strftime:...%` now supports the documented subset `%Y`, `%y`, `%m`, `%d`, `%H`, `%M`, `%S`, `%f`, and `%%`
- active names now use the basename instead of the full model path, and friendly text encoder names keep compatibility markers such as `zimage`, move versions ahead of bracket tags, and render `Q8`-style quant suffixes as a final bracket tag such as `[Q8]`
- active loader detection now recognizes more UNET, text encoder, and checkpoint loader naming patterns, including common custom-node variants such as diffusion-model loaders and GGUF-style loaders
- the visible node name is now `Save Image Organized`
- `Save Image Organized` is built around a clean `Top Folder / Model Name / Text Encoder / Filename` model
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
- `Save Image Organized` node with legacy and template-based save modes
- automatic upstream detection for active UNET and CLIP loader names
- template variables for model, clip and date-based output paths
- `Strip Model Extension` utility node
- repository documentation for installation, usage and contribution workflow
