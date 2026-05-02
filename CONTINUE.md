# Continue

## Purpose

Maintainer handoff for the current working state of `comfyui-save-image-organized`.
This file is for continuation context, not end-user documentation.

## Current State

- The repository is published to the Comfy Registry as `save-image-organized` under publisher `delcado`.
- The current registry version is `0.5.3`.
- `v0.5.3` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI plus the `Publish to Comfy Registry` workflow.
- `v0.5.3` publishes the workflow migration helper, expected no-loader workflow regression coverage, conservative `Friendly Clean` audit coverage, and loader-distance diagnostics for Detection Info/helper payloads.
- The latest full release gate passed with `H:\ComfyUI-Easy-Install\python_embeded\python.exe tools\check_release_ready.py --tag v0.5.3 --github --workflows --fail-on-unresolved-detection`.
- The latest verified GitHub Actions release runs are `25248828655` for CI and `25248828645` for `Publish to Comfy Registry`, both successful.
- The latest verified GitHub Actions CI run for `main` is `25251347108` for commit `53b60b7` (`Refine registry icon artwork`), successful.
- The local live ComfyUI custom-node install at `H:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\comfyui-save-image-organized` has been refreshed from `v0.5.0` to current `main`; installed `nodes.py` imports successfully and exposes `SaveImageClean` as `Save Image Organized`.
- `v0.5.2` is published to the Comfy Registry and verified by passing GitHub Actions CI plus the `Publish to Comfy Registry` workflow.
- `v0.5.2` keeps the Inkscape-authored Comfy Registry icon design and updates only SVG metadata for the registry asset.
- `v0.5.1` adds the dedicated Comfy Registry icon asset and `Icon` metadata in `pyproject.toml`.
- `v0.5.0` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions runs.
- `main` includes post-`v0.5.0` documentation updates for Registry installation and the GitHub Actions publishing workflow.
- `main` includes post-`v0.4.0` maintainer updates for handoff status, repository Git policy, workflow validation diagnostics, stricter release gates, full workflow release scans, and the optional `Friendly Clean` name sources.
- `CHANGELOG.md` has a `0.5.0` section dated `2026-05-01` for the `AGENTS.md` policy, unnamed Reroute input validation fix, workflow-validation reason reporting, stricter unresolved-detection release gate, full workflow release scans, and `Friendly Clean` name sources.
- `CHANGELOG.md` has a `0.4.0` section dated `2026-05-01` for maintainer workflow-validation tooling, release-readiness tooling, loader-source labels in detection summaries, and sampler-setting convenience variables.
- GitHub Actions CI now runs `ruff` and `pytest` on Windows for pushes to `main` and pull requests.
- Maintainer workflow validation now preserves linked UI inputs even when the exported input name is empty, which allows Reroute and `Reroute (rgthree)` nodes to stay connected during local workflow scans.
- Maintainer workflow validation now reports a `REASON` column and JSON `reason` field for each Save node, so remaining misses explain whether a loader is unreachable or a loader name could not be resolved.
- The current local `private-workflows` validator summary is `103` Save Image Organized nodes, `70 OK`, `0 PARTIAL`, `33 MISS`, `0 unresolved`, and `0 errors`; the remaining MISS cases report `no model/text encoder loader reachable`.
- The `33` private-workflow MISS nodes have been classified as expected image-only or postprocessing branches: `21` VTON variants are fed by `LoadImage` sources through anonymized subgraph/composite nodes, `8` are `FastFilmGrain`/`FastLaplacianSharpen` branches from `LoadImage`, and `4` are image upscale branches using `UpscaleModelLoader` rather than a generation model loader.
- The ignored local `private-workflows` folder has been migrated from standard `SaveImage` nodes to `SaveImageClean` nodes: `60` workflow files changed locally, `80` standard `SaveImage` nodes replaced, and `0` standard `SaveImage` nodes remain.
- During the local private-workflow migration, node `id`, `pos`, `size`, `flags`, `order`, `mode`, `title`, image input links, and global link IDs were preserved. Existing `filename_prefix` values were carried into the new `Save Layout` as `<old prefix>/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%`.
- One pre-existing private workflow link-table inconsistency remains outside Save nodes: `private-workflows/VTON/Codex/Flux2 klein 9b Virtual Try-On 6.0.2 (Codex).json` has link `176` targeting input slot `0` on `List of strings [Crystools]`, while the node stores that link on `string_2`.
- The release-readiness checker now has `--fail-on-unresolved-detection`, which is stricter than the default workflow scan but does not fail on expected no-loader Save branches.
- Release-readiness workflow checks now scan all workflows by default; use `--workflow-limit <n>` only for explicit sampling during development.
- The repo currently exposes two nodes:
  - `Save Image Organized`
  - `Strip Model Extension`
- The shipped save flow is now centered around:
  - `Top Folder`
  - `Model Name`
  - `Text Encoder Name`
  - `Filename`
- The visible node rename to `Save Image Organized` is already implemented in code and reflected in docs.
- Maintainer workflow validation is available via `python tools/validate_local_workflows.py`.
- Maintainer workflow migration is available via `python tools/migrate_save_image_nodes.py`; it dry-runs by default, writes only with `--write`, and can fail verification with `--verify-no-standard`.
- Release readiness checks are available via `python tools/check_release_ready.py`.
- Detection summaries and helper snapshots include upstream loader node labels and upstream link distance when detection comes from the workflow.
- Save templates support sampler-setting convenience variables: `%STEPS%`, `%CFG%`, `%SAMPLER%`, `%SCHEDULER%`, and `%DENOISE%`.
- `Model Name` and `Text Encoder Name` now offer `Friendly Clean` in addition to `Friendly`, `Exact`, and `Custom`; it removes known releaser or publisher prefixes while preserving the existing `Friendly` and `Exact` behavior.
- A local `private-workflows` Friendly Clean audit found only the already-covered packager prefixes `Goekdeniz-Guelmez`, `Goekdeniz_Guelmez`, and `mradermacher`; no new prefix stripping rule was added. Regression tests preserve creator/producer-style prefixes such as `Huihui` and `Lockout`.
- Registry publishing is configured in `pyproject.toml` and automated by `.github/workflows/publish_action.yml` with the `REGISTRY_ACCESS_TOKEN` repository secret.
- Registry icon metadata points at `assets/registry-icon.svg`; keep it square and within the Comfy Registry icon requirements.

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

## Released In v0.3.0

The following items are the core of the `v0.3.0` release:

- clearer template error messages for unknown variables, bad `%node.widget%` references, ambiguous node matches, and unsupported widget values
- optional `Detection Info` runtime output with `Off`, `Summary`, and `Verbose` modes
- workflow loader detection fixes for:
  - cross-contaminating generic loader fields
  - `GetNode`/`SetNode` bridge traversal
  - active `ComfySwitchNode` branch selection
  - widget-only loader values from exported workflows
- broader regression coverage for save behavior, collision handling, checkpoint fallback, diffusion-model loader variants, postprocessing-only save branches, and PNG prompt metadata preservation
- public synthetic detection fixtures for:
  - checkpoint loaders
  - bridge nodes
  - switch branches
  - widget-only loaders
  - LoRA pass-through paths
- helper-preview improvements that warn about unknown placeholders, show `%node.widget%` placeholders clearly before execution, and switch to the last real resolved path after a successful run
- convenience template variables:
  - `%WIDTH%`
  - `%HEIGHT%`
  - `%SEED%`
  - `%BATCH_INDEX%`
  - `%BATCH_SIZE%`
- `Export Workflow Metadata` toggle that matches normal ComfyUI `Save Image` PNG metadata behavior
- explicit `Primary only` design decision for multi-loader cases:
  - detection resolves to one active model name and one active text-encoder name
  - combined multi-loader names are intentionally not generated by default

## Released In v0.3.1

The following item is the core of the `v0.3.1` release:

- checkpoint loader names are detected from widget-only custom loaders that store the selected file in an object value such as `{content: "..."}`

## Released In v0.4.0

The following items are the core of the `v0.4.0` release:

- maintainer workflow validator for scanning local ComfyUI workflow JSON files and reporting `Save Image Organized` model/text-encoder detection results
- release-readiness checker for local validation plus optional tag, GitHub release, and Actions checks
- detection summaries and helper snapshots include the upstream workflow loader node label when a model or text encoder name is detected
- save templates support sampler-setting convenience variables:
  - `%STEPS%`
  - `%CFG%`
  - `%SAMPLER%`
  - `%SCHEDULER%`
  - `%DENOISE%`

## Released In v0.5.0

The following items are the core of the `v0.5.0` release:

- repository `AGENTS.md` policy for autonomous Git operations, release checks, and CI verification
- maintainer workflow validation follows unnamed Reroute inputs and reports a `REASON` column plus JSON `reason` field
- release-readiness checks can fail on unresolved reachable-loader detection problems while allowing expected no-loader Save branches
- release-readiness workflow checks scan all workflows by default, with `--workflow-limit` kept for explicit sampling
- `Friendly Clean` model and text-encoder name sources remove known releaser or publisher prefixes while preserving `Friendly`, `Exact`, and raw detection behavior

## Released In v0.5.1

The following items are the core of the `v0.5.1` release:

- dedicated square Comfy Registry icon asset
- `Icon` metadata in `pyproject.toml`
- Comfy Registry installation and publishing documentation updates

## Released In v0.5.2

The following items are the core of the `v0.5.2` release:

- preserved the Inkscape-authored Comfy Registry icon design
- updated SVG title, description, ARIA labeling, and document-name metadata for the registry icon asset

## Released In v0.5.3

The following items are the core of the `v0.5.3` release:

- maintainer helper for dry-run verification and in-place migration from standard ComfyUI `SaveImage` workflow nodes to `SaveImageClean`
- regression coverage for expected image-only private workflow MISS branches, including postprocessing and upscale-model-only save paths
- regression coverage that keeps `Friendly Clean` conservative: known packager prefixes are removed while creator or producer prefixes remain intact
- detection diagnostics now include the selected loader node's upstream link distance in UI text and structured helper payloads

## Known Gaps

- The latest checkpoint widget-object fix is covered by automated regression tests and an installation-level runtime check against the local ComfyUI custom-node copy.
- The automated test suite is still modest, but it now covers core helper behavior, multi-image save execution, PNG metadata preservation, checkpoint fallback, diffusion-model loader variants, bridge/switch traversal, widget-only loaders, postprocessing-only save branches, and prompt references via `Node name for S&R` or node id.
- Validation is still mostly runtime validation inside the node; the current regression harness covers template parsing, loader detection, collision handling, detection-info UI text, convenience variables, basic save/metadata behavior, migration tooling, and expected image-only workflow MISS branches. The ignored `private-workflows` folder provides a larger local workflow corpus, but it is not public test coverage and should not replace tracked regression fixtures.
- Frontend preview logic is clearer than before, now warns about unknown placeholders, and can reflect the last real resolved path after execution, but it still relies on sample values before the first workflow run.
- Compatibility has been expanded for loader naming patterns, bridge nodes, and switch nodes, but third-party custom-node ecosystems remain the most likely place for future edge cases.
- Some save or preview nodes in real workflows legitimately resolve to empty detection because their current branch only contains input-image, postprocessing, or utility nodes and no sampler/loader path. That behavior is expected and should not be treated as a detection bug by itself.
- Multi-loader cases currently collapse to one best active match rather than a combined display. That is intentional for path stability and shorter save names, but it should stay documented so users do not expect all CLIP/model names to appear.

## Next Priorities

1. Keep watching `Friendly Clean` prefix rules against new real filenames, but add new stripping rules only when the prefix is clearly a packager label rather than a creator or producer.
2. Keep `private-workflows` as a local migration and detection regression corpus, especially mixed GGUF/safetensors workflows and future custom-node branches.
3. Keep `CHANGELOG.md` and `pyproject.toml` versions aligned before each registry release.
4. Extend `tools/migrate_save_image_nodes.py` only when future exported workflow formats require additional compatibility handling.

## Deferred Ideas

- More detailed UI diagnostics beyond the selected loader label and upstream link distance, if real workflows need them
- Expanded collision strategies:
  - millisecond timestamp option
  - hash-based suffix option
  - more configurable suffix handling
- Metadata controls:
  - toggle PNG metadata writing
  - optional prompt-only metadata mode
  - clearer handling for extra PNG info
- Small text filters for templates:
  - `lower`
  - `upper`
  - `slug`
- Optional additional export formats such as JPEG or WebP

## Out Of Scope For Now

- a large template language
- regex-heavy filename/path transformation features
- too many export modes or save options
- major UI expansion that makes the node harder to scan

## Manual Test Checklist

- Verify default save layout produces `%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%`.
- Verify `Friendly`, `Friendly Clean`, `Exact`, and `Custom` selection for both model and text encoder.
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
- For ignored `private-workflows`, verify standard `SaveImage` node count stays `0` after migrations and rerun `tools/validate_local_workflows.py private-workflows --json`.
- For repeat migrations, run `tools/migrate_save_image_nodes.py private-workflows --verify-no-standard` after any `--write` pass.

## Release Checklist

- `v0.3.1` was tagged and published on GitHub.
- `CHANGELOG.md` has a `0.3.1` section dated `2026-04-30`.
- GitHub Actions CI passed for the release commit.
- `v0.4.0` was tagged and published on GitHub.
- `CHANGELOG.md` has a `0.4.0` section dated `2026-05-01`.
- Local release readiness checks passed with `pytest`, `ruff`, Python compile, frontend syntax check, and workflow validation.
- GitHub Actions CI passed for the `v0.4.0` release commit.
- `v0.5.0` is prepared with a `CHANGELOG.md` section dated `2026-05-01`.
- `v0.5.0` was published to the Comfy Registry as `save-image-organized`.
- For the final release gate, use `tools/check_release_ready.py --tag <tag> --github --workflows --fail-on-unresolved-detection`.
- `v0.3.0` was tagged and published on GitHub.
- `CHANGELOG.md` has a `0.3.0` section dated `2026-04-30`.
- GitHub Actions CI passed for the `v0.3.0` release commit.
- For the next release, keep a full manual workflow pass in ComfyUI with at least:
  - checkpoint-based workflow
  - UNET loader workflow
  - GGUF text encoder workflow
- Confirm `README.md`, `docs/USAGE.md`, and Info-tab docs still match the actual UI labels.
- Use `tools/check_release_ready.py --tag <tag> --github --workflows --fail-on-unresolved-detection` as the final release gate.
- Verify `Publish to Comfy Registry` succeeds after pushing a `pyproject.toml` version change.
- `v0.5.2` was published to the Comfy Registry after bumping `pyproject.toml` to avoid republishing the existing `0.5.1` node version.
- GitHub Actions CI and `Publish to Comfy Registry` passed for commit `0d7ce96`.

## Notes

- `CONTINUE.md` is intentionally tracked and part of the shared maintainer handoff.
