# Continue

## Purpose

Maintainer handoff for the current working state of `comfyui-save-image-organized`.
This file is for continuation context, not end-user documentation.

## Current State

- Branch status was clean on `main` on 2026-04-23.
- The next visible project version should be `v0.2.0`.
- The repo currently exposes two nodes:
  - `Save Image Organized`
  - `Strip Model Extension`
- The shipped save flow is now centered around:
  - `Top Folder`
  - `Model Name`
  - `Text Encoder Name`
  - `Filename`
- The visible node rename to `Save Image Organized` is already implemented in code and reflected in docs.

## Released In v0.2.0

The following items are the core of the `v0.2.0` release:

- `%node.widget%` placeholders for path templates
- best-effort node lookup by title, custom `Node name for S&R`, class name, and node id
- inline descriptions and tooltips for both nodes
- markdown docs for the ComfyUI `Info` tab via `WEB_DIRECTORY/docs`
- in-node helper panel with live example output
- ComfyUI-style `%date:...%` token support including single-letter tokens
- restricted `%strftime:...%` support
- broader loader detection for UNET, text encoder, and checkpoint loader variants
- basename-based active name handling instead of full paths
- improved friendly naming for common image models, text encoders, versions, tags, and quant suffixes
- simplified main template variables:
  - `%TOP_FOLDER%`
  - `%MODEL_NAME%`
  - `%TEXT_ENCODER_NAME%`
  - `%FILENAME%`
- direct and fallback use of custom model/text encoder names
- removal of the old `Output Root` concept

## Known Gaps

- The automated test suite is still small, but it now covers core helper behavior, multi-image save execution, and PNG metadata preservation.
- Validation is still mostly runtime validation inside the node; the current regression harness covers template parsing, loader detection, collision handling, detection-info UI text, and basic save/metadata behavior, but not broader real-world prompt fixtures or format variations.
- Frontend preview logic is clearer than before and now warns about unknown placeholders, but it still uses sample names before first workflow execution and does not yet reflect real post-run detection details inside the helper panel itself.
- Compatibility has been expanded for loader naming patterns, but this area is still the most likely place for future edge cases from third-party custom nodes.

## Next Priorities

1. Expand regression coverage across representative prompt payloads from common ComfyUI ecosystems.
2. Decide whether detection summary details should also surface in the in-node helper panel after execution, not only in the output text.
3. Extend save tests toward additional collision modes and more than one loader-family prompt shape per workflow style.
4. Consider direct convenience variables such as `%WIDTH%`, `%HEIGHT%`, `%SEED%`, and `%BATCH_INDEX%`.
5. Keep `CHANGELOG.md` moving from the fresh `Unreleased` section after the `v0.2.0` tag.

## v0.2.0 Roadmap

### Must Have

- Better template error UX:
  - unknown variables should name the exact token
  - invalid `%node.widget%` references should identify the missing node or widget
  - ambiguous node matches should explain why resolution failed
  - unsupported `%strftime:...%` directives should stay explicit and user-facing
- Detection transparency:
  - optional debug/info output for which model loader was detected
  - optional debug/info output for which text encoder source was detected
  - visible note when the node falls back to custom names
- Automated tests for core behavior:
  - friendly/exact/custom naming
  - loader detection
  - path template rendering
  - `%date:...%` and `%strftime:...%`
  - collision modes
- More informative preview behavior:
  - make it clearer when the preview uses sample values
  - surface invalid template tokens earlier
  - keep the preview close to the final resolved save path

### Should Have

- Direct convenience variables for common workflow values:
  - `%WIDTH%`
  - `%HEIGHT%`
  - `%SEED%`
  - `%BATCH_INDEX%`
- Expanded collision strategies:
  - millisecond timestamp option
  - hash-based suffix option
  - more configurable suffix handling
- Metadata controls:
  - toggle PNG metadata writing
  - optional prompt-only metadata mode
  - clearer handling for extra PNG info

### Nice To Have

- Small text filters for templates:
  - `lower`
  - `upper`
  - `slug`
- Optional additional export formats such as JPEG or WebP
- Small UI diagnostics such as which loader path produced the active names

### Not A v0.2.0 Priority

- a large template language
- regex-heavy filename/path transformation features
- too many export modes or save options
- major UI expansion that makes the node harder to scan

## Manual Test Checklist

- Verify default save layout produces `%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%`.
- Verify `Friendly`, `Exact`, and `Custom` selection for both model and text encoder.
- Verify custom names are used as fallback when detection fails.
- Verify `%date:...%` tokens render correctly for both multi-letter and single-letter tokens.
- Verify supported `%strftime:...%` directives render and unsupported directives fail clearly.
- Verify `%node.widget%` placeholders resolve from real workflow nodes.
- Verify ambiguous or unknown `%node.widget%` references fail with clear errors.
- Verify collision modes:
  - `increment`
  - `overwrite`
  - `error`
  - `seconds`
- Verify PNG prompt metadata is preserved in saved files.
- Verify the frontend helper panel updates when relevant widgets change.

## Release Checklist

- Review and trim the `Unreleased` section in `CHANGELOG.md`.
- Decide release version for the current feature set.
- Run a full manual workflow pass in ComfyUI with at least:
  - checkpoint-based workflow
  - UNET loader workflow
  - GGUF text encoder workflow
- Confirm `README.md`, `docs/USAGE.md`, and Info-tab docs still match the actual UI labels.
- Create release commit and tag.

## Notes

- `CONTINUE.md` is intentionally tracked and part of the shared maintainer handoff.
