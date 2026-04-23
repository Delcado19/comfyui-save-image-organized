# Continue

## Purpose

Maintainer handoff for the current working state of `comfyui-save-image-organized`.
This file is for continuation context, not end-user documentation.

## Current State

- Branch status was clean on `main` on 2026-04-23.
- The repo currently exposes two nodes:
  - `Save Image Organized`
  - `Strip Model Extension`
- The shipped save flow is now centered around:
  - `Top Folder`
  - `Model Name`
  - `Text Encoder Name`
  - `Filename`
- The visible node rename to `Save Image Organized` is already implemented in code and reflected in docs.

## Implemented But Unreleased

The following items are present in code and documented in the `Unreleased` section of `CHANGELOG.md`:

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

- No automated test suite is present yet.
- No release tag exists yet for the current post-`0.1.0` work.
- Validation is mostly runtime validation inside the node; there is no dedicated regression harness for template parsing or loader detection.
- Frontend preview logic uses sample names before first workflow execution, so preview correctness is illustrative until a real prompt runs.
- Compatibility has been expanded for loader naming patterns, but this area is still the most likely place for future edge cases from third-party custom nodes.

## Next Priorities

1. Add targeted tests for path template rendering, date token handling, collision modes, and friendly-name normalization.
2. Add regression coverage for loader detection across representative prompt payloads from common ComfyUI ecosystems.
3. Decide whether `CONTINUE.md` is intended to stay local-only or become part of the tracked maintainer docs.
4. Cut a release after changelog cleanup and a short manual validation pass.

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

- `CONTINUE.md` is not excluded by the current `.gitignore`.
- That means it will be included in the remote repository if you add and commit it.
- If this file should stay local-only, add `CONTINUE.md` to `.gitignore` or `.git/info/exclude`.
