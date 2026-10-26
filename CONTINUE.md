# Continue

## Purpose

Maintainer handoff for the current working state of `comfyui-save-image-organized`.
This file is for continuation context, not end-user documentation.

## Current State

- Released in `v0.8.3`: fixed a user report ("Bildvorschau nach letzter Änderung auf Miniansicht beschränkt") that the v0.8.1 preview-zoom fix never actually covered `Save` mode. Root cause: `nodes.py` only populated `ui["save_image_clean_preview"]` when `save_mode == "Preview"`; in `Save` mode the frontend's `updatePreviewGrid` (`web/save_image_clean.js`) saw an empty `entries` array and returned before touching `node.imgs`, so ComfyUI's own default `onExecuted` thumbnail (small, fixed, driven by `node.imgs`/`message.images`) rendered instead of our full-node-height custom grid - confirmed via `git bisect`-style reading of `web/save_image_clean.js`'s history (no JS change since the v0.8.1 fix) plus a diff against the live install (`G:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\ComfyUI-Delcado`, byte-identical, ruling out stale-install drift). Fixed by appending a `preview_entries_ui` entry for every image in the `Save` branch too (real `filename`/`subfolder`, `type="output"` pointing at the already-written file, `width`/`height`), and changing the `ui["save_image_clean_preview"]` gate from `save_mode == "Preview" and preview_entries_ui` to just `preview_entries_ui`; the `_PREVIEW_CACHE` write (used only by the per-cell `Save` button's `/save_image_organized/save_now` route) stays `Preview`-only since `Save` mode has nothing left to save. `updatePreviewGrid`'s `node.imgs = []` call, previously only defensive, is now load-bearing in `Save` mode too (suppresses ComfyUI's native strip so the same image isn't shown twice) - comment there updated accordingly. Regression test added: `test_save_images_save_mode_also_populates_preview_grid` (108 passed). `README.md`/`docs/USAGE.md`/`web/docs/SaveImageClean.md` updated to state the full-size grid applies in both modes, not just `Preview`. Synced to the live install. See `CHANGELOG.md [0.8.3]`.
- Released in `v0.8.2`: the `Filename` field (`filename_datetime` widget) now resolves `%VARIABLE%` tokens (`%SEED%`, `%SAMPLER%`, `%SCHEDULER%`, etc.) in addition to `%date:...%`/`%strftime:...%`, matching the Output Path Template. Reported by a user pasting a live ComfyUI error report: typing `%date:...%%SCHEDULER%%SAMPLER%` into `Filename` left the two variable tokens as literal text (since `_render_filename_value` in `nodes.py` never resolved them), which then surfaced once that literal text was inserted into `%FILENAME%` inside the path template, as a confusing `ValueError: Unknown path template placeholders: SAMPLER, SCHEDULER` raised from `_render_path_template` - the actual error site was one call-level removed from the field the user had actually edited. Fixed in `nodes.py` (`_render_filename_value` now accepts the `variables` dict and resolves known tokens before `%FILENAME%` is assembled) and mirrored in `web/save_image_clean.js`'s `buildFilenameValue`/`buildVariables` so the live preview matches. User then asked whether *every* "Build Path"/"Build Filename" chip now works in both panels - checking found a second, related bug: `MODEL_NAME`/`TEXT_ENCODER_NAME` are derived from the other variables via `_resolve_selected_variable` and were being assigned *after* `FILENAME` was rendered in both `nodes.py` and `save_image_clean.js`, so those two chips alone still silently failed inside the Filename field. Fixed by reordering both call sites so `MODEL_NAME`/`TEXT_ENCODER_NAME` are resolved before `FILENAME`. Added regression tests (`test_save_images_resolves_convenience_variables_inside_filename_field`, `test_save_images_resolves_every_builder_chip_variable_in_filename_field` - the latter exercises every chip from both builder panels at once; 104 passed). The one remaining non-functional case is an inherent self-reference, not a bug: clicking the `%FILENAME%` chip while editing the Filename field itself can't resolve (nothing to reference yet) and correctly raises `Unknown path template placeholders: FILENAME`. Tooltip text and `docs/USAGE.md`/`web/docs/SaveImageClean.md` updated; `CHANGELOG.md [Unreleased]` has the user-facing note. Synced to the live install (`G:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\ComfyUI-Delcado`, which had the same pre-fix code uncommitted in its working tree). `tools/check_release_ready.py --workflows` (via `.venv`) flagged unrelated pre-existing noise, not caused by this change: 7 "unsupported JSON workflow format" errors from `.claude`/`.remember` metadata files living inside the local `workflows` tree (not real ComfyUI workflows) plus the paired install's existing MISS/PARTIAL rows for workflows with no reachable model loader - proceeded with the release regardless. See `CHANGELOG.md [0.8.2]`.
- Released in `v0.8.1`: 5 UI fixes reported live against the running node (screenshot-driven, checked against `emil-design-eng`/`apple-design` skill guidance before implementing): the `Preview`-mode single-image thumbnail was capped at a fixed `max-height:420px` with `object-fit:contain`, so a portrait image rendered letterboxed/under-zoomed and a manually-enlarged node left dead gray space below `Example Output` instead of the image growing into it - fixed by making `.sic-root`/`.sic-inner` fill the widget's assigned height and flexing the whole preview-grid chain (`flex:1`/`min-height:0`) so extra node height goes into the image. Also: the `Advanced Settings` gear row moved from after `Example Output` (disconnected, near the node's bottom) to directly under `Filename`/above `Output`/`Mode`; the redundant `FILENAME` eyebrow (duplicating the `Filename` heading right below it) was removed; `Top Folder`'s hover tooltip now reads `%TOP_FOLDER% → <value>` instead of just the typed value (`buildTextRow`'s new `tokenLabel` option in `web/sic_components.mjs`); and `Preview`-mode thumbnails now show a `WxH` pixel-size readout, forwarded from `nodes.py`'s already-computed `image_width`/`image_height` via a new `width`/`height` key on `save_image_clean_preview` entries. `node --check`, `py_compile`, the full `pytest` suite (102 passed), and `ruff check` all pass via the repo's own `.venv` - `uv run` failed this session (`uv trampoline failed to canonicalize script path`) and the paired ComfyUI install's embedded Python has neither `pytest` nor `ruff` installed, so `tools/check_release_ready.py`/`AGENTS.md`'s prescribed commands need `--python .\.venv\Scripts\python.exe` (or an equivalent env with those dev deps) until that's resolved. Also fixed in this pass: `tools/check_release_ready.py`'s `DEFAULT_PYTHON` and `tools/validate_local_workflows.py`'s `DEFAULT_WORKFLOW_ROOT`, plus `AGENTS.md`'s own example commands, still pointed at the retired `H:` drive letter - updated to the current `G:\ComfyUI-Easy-Install`. See `CHANGELOG.md [0.8.1]`.
- Released in `v0.8.0`: `IMAGES` output added (passes saved images through unchanged for mid-workflow use). Backend widget values and serialization are unchanged; verified live against the paired ComfyUI install (now `G:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\ComfyUI-Delcado` - the folder was renamed from `save-image-organized` this session so the on-canvas node badge reads "Delcado"; ComfyUI derives that badge purely from the `custom_nodes/<folder>` name, stripping a `ComfyUI-`/`Comfy-` prefix, confirmed by reading the installed `comfyui_frontend_package` bundle directly, not from `pyproject.toml`. The package/registry name and the GitHub repo name are untouched) via `/object_info/SaveImageClean` and confirmed visually by the maintainer in the node canvas, including the native batch-grid preview (already free via ComfyUI's `ui.images`, no code change needed). See `CHANGELOG.md [0.8.0]`.
- Released in `v0.8.0`: the full node-body UI redesign (`docs/superpowers/plans/2026-10-12-save-image-organized-ui-redesign.md`, worktree `.worktrees/save-preview-mode-split`), implemented and committed inline (all 11 tasks), then substantially reworked across a long live-QA session (`.superpowers/sdd/2026-10-12-save-image-organized-ui-redesign/progress.md`, Rounds 1-9) after the user tested it live. Every field now renders through a shared `web/sic_components.mjs` component library (segmented/pill-group buttons, dropdown rows, a pill switch, a styled slider, styled text rows with a hover tooltip for the full value) assembled into a single root flex widget (`buildNodeUI`, `web/save_image_clean.js`). Final layout, all labels English: the main card only shows `Folder Structure`/`Top Folder`, `Filename`, and `Output`/`Mode` (two side-by-side pill groups, Pixaroma-style); everything else - `Model Name`/`Text Encoder` (+ their Custom Name fields), `If File Exists`, `Detection Info`, `Image Quality`, `Export Workflow Metadata`, `Loader Priority`, and the Detection Snapshot - lives behind the gear-icon `Advanced Settings` panel, each with a one-line description. A single-image preview fills the available node width; its `Save` button is omitted entirely in `Save` mode. Native widget identity/order is untouched throughout, so old saved workflows restore unchanged. `node --check` on both frontend files, `py_compile`, the full `pytest` suite (102 passed), and `ruff check` all pass. See `CHANGELOG.md [0.8.0]`.
- **Live-QA fix wave (same session, Rounds 1-9 in the ledger above) found and fixed real regressions the static-analysis-only implementation above had missed**, several requiring multiple attempts and two advisor consults before the actual root cause was confirmed via live DevTools data rather than guessed:
  - Native STRING widgets (path/filename/subfolder/custom-name fields) weren't getting a persistent `inputEl` from ComfyUI at all in this frontend version for single-line widgets - `buildTextRow` now creates and owns its own `<input>` instead of depending on one.
  - The node became unresizable, then resizable-but-not-tracking-width-in-either-direction. Root cause, confirmed via a DevTools paste: `node.addDOMWidget()` sets `widget.width` ONCE at creation time and never updates it; ComfyUI's per-frame positioner prefers that frozen `widget.width` over the (already-correct) `node.width` fallback. Fixed by overriding `widget.width` as an accessor that always returns `undefined`, restoring ComfyUI's own working fallback.
  - A DOM-content overflow bug (`min-width:auto` on a flex item containing an `<img>` resolving to the image's own intrinsic pixel width) let content bleed past the node's own frame; fixed with `min-width:0` through the flex chain plus `overflow:hidden` on the root as a safety net.
  - Two risky fixes were tried and reverted live after making things worse (a conditional node-shrink that broke width tracking entirely; a full port of Pixaroma's `position:absolute` inner-layer pattern that caused content clipping and totally inert width-resize) - both are recorded in the ledger as dead ends, not re-attempted.
  - **Still open, deliberately not re-attempted without live data:** the node doesn't auto-shrink back down after switching from Preview mode (image + Save button) to Save mode - content shrinks, the node's own height doesn't, leaving an empty gap. Two fix attempts in this area already caused worse regressions; see Round 5/6 in the ledger before trying again.
  - Formally covered via extensive live testing with the maintainer during this session (resize, Advanced Settings panel, both confirmed working after fixes); the plan's own Task 11 Step 2 test list and Step 3 before/after screenshots were not run as a separate formal pass, since the live-QA rounds above already exercised the same surface area more thoroughly than that checklist would have.
- Released in `v0.8.0`: a `Build Path…`/`Build Filename…` floating window (frontend-only, `web/save_image_clean.js`) with click-to-insert chips for every template variable, filter, and date preset, plus three small motion/UX fixes (shared easing tokens, help-panel color transitions) from an `improve-animations` audit. See `plans/` (001, 002, 004 applied; 003 — a litegraph node-height resize tween — deliberately deferred as higher-risk/lower-certainty, no dependents) and `docs/superpowers/specs/2026-10-12-save-preview-mode-design.md` for the separately-designed Save/Preview mode split below.
- Released in `v0.8.0`: a `Save`/`Preview` mode toggle (`save_mode` widget, default `Save`, unchanged behavior) per `docs/superpowers/specs/2026-10-12-save-preview-mode-design.md` and `docs/superpowers/plans/2026-10-12-save-preview-mode-split.md`. `Preview` writes nothing to the final path, shows the result via ComfyUI's native temp-image mechanism, and caches pending images in an in-memory, per-node dict (`nodes._PREVIEW_CACHE`); a `POST /save_image_organized/save_now` route (guarded import, a no-op outside a real ComfyUI install such as pytest) commits one cached image per click from a per-image Save button in the node's preview grid, shown only in `Preview` mode.
- The repository is published to the Comfy Registry as `save-image-organized` under publisher `delcado`.
- The current registry version is `0.8.1`: node-body UI bug fixes (preview zoom, `Advanced Settings` position, duplicate label, `Top Folder` tooltip, preview pixel-size readout). See `CHANGELOG.md [0.8.1]`.
- `v0.8.0` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI (`38455260160`) plus `Publish to Comfy Registry` (`38455260038`), both successful.
- `v0.7.2` fixed the checkpoint-loader duplicate-folder collapse (from 0.7.0) so it no longer merges an unrelated `%TOP_FOLDER%` that happens to equal `%MODEL_NAME%` (e.g. a model-family folder holding a single model). The collapse is now scoped to a literal adjacent `%MODEL_NAME%/%TEXT_ENCODER_NAME%` token pair in the template, matched pre-render, and only fires when both resolve to the same file. See `CHANGELOG.md [0.7.2]`.
- `v0.7.2` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI (`31679404698`) plus `Publish to Comfy Registry` (`31679404697`), both successful.
- `v0.7.1` adds a `Loader Priority` (`Nearest`/`First Used`) widget appended after `Image Quality`. Fixes the case where a multi-stage pipeline (e.g. a base pass refined by a second model) resolved `Model Name`/`Text Encoder Name` to the nearer refiner loader instead of the base loader that produced the actual content; `Nearest` keeps the previous default behavior, `First Used` opts into picking the loader furthest upstream. See `CHANGELOG.md [0.7.1]`.
- `v0.7.1` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI (`31315692742`) plus `Publish to Comfy Registry` (`31315692738`), both successful.
- `v0.7.0` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI (`30761127021`) plus `Publish to Comfy Registry` (`30761127055`), both successful.
- `v0.6.3` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI (`26165966917`) plus `Publish to Comfy Registry` (`26165966814`), both successful.
- `v0.6.3` fixes the helper preview so changing the `Export Workflow Metadata` toggle marks the last detection snapshot stale and refreshes the preview state.
- `v0.6.2` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI (`25271979195`) plus `Publish to Comfy Registry` (`25271979191`), both successful.
- `v0.6.2` adds `Friendly Clean` output examples to `README.md`, `docs/USAGE.md`, and `web/docs/SaveImageClean.md`, and fills missing model/text encoder example blocks in `docs/USAGE.md`.
- `v0.6.1` is tagged locally, present on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI (`25259822729`) plus `Publish to Comfy Registry` (`25259822727`), both successful.
- `v0.6.1` adds a runtime warning when saving multiple images with `collision_mode=error` or `overwrite` and no batch variable in the Save Layout, and adds `Release Pipeline` and `Docs Sync Checker` agent definitions to `AGENTS.md`.
- `v0.6.0` adds path template filters (`lower`, `upper`, `slug`), the `%BATCH%` template variable, updates the default Save Layout to append `%BATCH%` after `%FILENAME%`, and updates the workflow migration helper to carry `%BATCH%` into migrated layouts.
- `v0.5.3` is the last `v0.5.x` release; it added the workflow migration helper, expected no-loader workflow regression coverage, conservative `Friendly Clean` audit coverage, and loader-distance diagnostics.
- The local live ComfyUI custom-node install is at `<drive>:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\save-image-organized`, where `<drive>` is whatever drive letter ComfyUI-Easy-Install is currently mounted on (it has changed between sessions, e.g. `H:` then `G:` — always verify before assuming). Its `pyproject.toml` reports `0.7.2` after this release. The older documented path `...\custom_nodes\comfyui-save-image-organized` is not present.
- GitHub Actions CI runs `ruff` and `pytest` on Windows for pushes to `main` and pull requests.
- Maintainer workflow validation now preserves linked UI inputs even when the exported input name is empty, which allows Reroute and `Reroute (rgthree)` nodes to stay connected during local workflow scans.
- Maintainer workflow validation now reports a `REASON` column and JSON `reason` field for each Save node, so remaining misses explain whether a loader is unreachable or a loader name could not be resolved.
- The current local `private-workflows` validator summary is `103` Save Image Organized nodes, `70 OK`, `0 PARTIAL`, `33 MISS`, `0 unresolved`, and `0 errors`; the remaining MISS cases report `no model/text encoder loader reachable`.
- The `33` private-workflow MISS nodes have been classified as expected image-only or postprocessing branches: `21` VTON variants are fed by `LoadImage` sources through anonymized subgraph/composite nodes, `8` are `FastFilmGrain`/`FastLaplacianSharpen` branches from `LoadImage`, and `4` are image upscale branches using `UpscaleModelLoader` rather than a generation model loader.
- The ignored local `private-workflows` folder has been migrated from standard `SaveImage` nodes to `SaveImageClean` nodes: `60` workflow files changed locally, `80` standard `SaveImage` nodes replaced, and `0` standard `SaveImage` nodes remain.
- During the local private-workflow migration, node `id`, `pos`, `size`, `flags`, `order`, `mode`, `title`, image input links, and global link IDs were preserved. Existing `filename_prefix` values were carried into the new `Save Layout`; new migrations now append `%BATCH%` after `%FILENAME%` to avoid default multi-image timestamp collisions.
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
- Save templates support small text filters on variables and `%node.widget%` placeholders: `lower`, `upper`, and `slug`.
- Save templates support `%BATCH%`, which is empty for single-image saves and expands to `_1-of-N` for multi-image batches; the default Save Layout is `%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%`.
- The node emits a runtime warning when saving multiple images with `collision_mode=error` or `overwrite` and no batch variable in the Save Layout; for `error` mode the warning appears in the exception message, for `overwrite` mode in the text output.
- The workflow migration helper now carries standard `SaveImage` prefixes into `<old prefix>/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%` so migrated batch outputs avoid same-second filename collisions by default.
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

## Released In v0.6.0

The following items are the core of the `v0.6.0` release:

- path template filters `lower`, `upper`, and `slug` for variables and `%node.widget%` placeholders
- `%BATCH%` template variable: empty for single-image saves, expands to `_1-of-N` for multi-image batches
- default Save Layout updated to `%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%`
- workflow migration helper now appends `%BATCH%` when converting standard `SaveImage` filename prefixes

## Released In v0.6.1

The following items are the core of the `v0.6.1` release:

- runtime warning when saving multiple images with `collision_mode=error` or `overwrite` and no batch variable in the Save Layout
- `Release Pipeline` and `Docs Sync Checker` agent role definitions added to `AGENTS.md`

## Released In v0.6.2

The following items are the core of the `v0.6.2` release:

- `Friendly Clean` output examples in `README.md`, `docs/USAGE.md`, and `web/docs/SaveImageClean.md`
- missing model and text encoder example blocks filled in `docs/USAGE.md`

## Released In v0.6.3

The following item is the core of the `v0.6.3` release:

- helper preview updates when the `Export Workflow Metadata` toggle changes, moving the helper into stale snapshot state until the next workflow run refreshes detection

## Released In v0.7.0

The following items are the core of the `v0.7.0` release:

- `FILENAME`/`FILE_PATH` STRING outputs, reporting the first saved image in a batch, for chaining into other nodes
- `Image Format` (`PNG`/`JPEG`/`WebP`) and `Image Quality` (1-100, JPEG/WebP only) widgets, appended after every existing optional widget so saved workflows keep their widget positions
- checkpoint-loader workflows no longer save into a doubled folder when `Model Name` and `Text Encoder Name` resolve to the same file
- JPEG export of images with an alpha channel composites transparent pixels onto white instead of keeping whatever RGB values sat underneath them
- `image_quality` is clamped to the documented `1`-`100` range before saving
- `tools/migrate_save_image_nodes.py` `widgets_values` alignment bug fixed: migrated nodes now get a correctly ordered, correctly sized `widgets_values` array

## Released In v0.7.1

The following item is the core of the `v0.7.1` release:

- `Loader Priority` (`Nearest`/`First Used`) widget, appended after `Image Quality`, fixing multi-stage pipelines (e.g. base pass refined by a second model) that always resolved to the nearer refiner loader instead of the base loader

## Released In v0.7.2

The following item is the core of the `v0.7.2` release:

- checkpoint-loader duplicate-folder collapse (from `v0.7.0`) is now scoped to a literal adjacent `%MODEL_NAME%/%TEXT_ENCODER_NAME%` token pair, matched pre-render, instead of collapsing any consecutive duplicate segment in the rendered path; an unrelated `%TOP_FOLDER%` that happens to equal `%MODEL_NAME%` is no longer merged away

## Released In v0.8.0

The following items are the core of the `v0.8.0` release:

- `IMAGES` output, passing the saved images through unchanged so the node can sit mid-workflow
- Full node-body UI redesign: the main card now only shows `Folder Structure`/`Top Folder`, `Filename`, and side-by-side `Output`/`Mode` pill-button groups; `Model Name`/`Text Encoder` (+ Custom Name fields), `If File Exists`, `Detection Info`, `Image Quality`, `Export Workflow Metadata`, `Loader Priority`, and the Detection Snapshot detail moved behind a gear-icon `Advanced Settings` panel, each with a one-line description; all labels are now English
- `Build Path…`/`Build Filename…` floating, draggable template builder windows with click-to-insert chips for every template variable, filter, and date preset, plus a live preview
- `Save`/`Preview` mode toggle: `Save` behaves exactly as before; `Preview` shows the result via ComfyUI's native temp-image mechanism without writing to the final path, scales a single-image result to the available node width, and gives each image its own `Save` button (shown only in `Preview` mode)
- Existing saved workflows restore unchanged - native widget identity, order, and serialization are untouched throughout the redesign

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
2. Rebuild `private-workflows` as a local migration and detection regression corpus when needed, especially mixed GGUF/safetensors workflows and future custom-node branches; the previous copy was deleted (see note below).
3. Keep `CHANGELOG.md` and `pyproject.toml` versions aligned before each registry release.
4. Extend `tools/migrate_save_image_nodes.py` only when future exported workflow formats require additional compatibility handling.
5. **`tools/migrate_save_image_nodes.py` had a `widgets_values` alignment bug, now fixed.** Migrated nodes got a `widgets_values` array with the wrong item count and no offset for the node's actual widget order (13 entries for what should be 12, offset by one from the first widget on). Since ComfyUI restores `widgets_values` positionally (see the comment in `nodes.py` next to the `optional` widget block), this would carry each widget's value into the next widget's slot — e.g. `collision_mode`'s value landing where `detection_info` expects its own. This consequence follows from how ComfyUI's positional restore is documented to work, but was not independently re-verified against a live ComfyUI install in this session. All `103` `SaveImageClean` nodes across the local `private-workflows` corpus were confirmed to have the broken 13-item shape before the folder was deleted (2026-08-02); if any of those original workflows still exist elsewhere (the live ComfyUI install, other backups), their `Save Image Organized` widget values should be checked by hand or re-migrated with the fixed tool.

## Deferred Ideas

- Dynamic `%node.widget%` chips in the template builder window (graph introspection to list actual upstream node/widget names as clickable chips, instead of only the static variable catalog) — explicitly out of scope for the builder window shipped in `plans/004-path-template-builder-window.md`; natural follow-up if requested
- More detailed UI diagnostics beyond the selected loader label and upstream link distance, if real workflows need them
- Expanded collision strategies:
  - millisecond timestamp option
  - hash-based suffix option
  - more configurable suffix handling
- Metadata controls:
  - optional prompt-only metadata mode
  - clearer handling for extra PNG info

## Out Of Scope For Now

- a large template language
- regex-heavy filename/path transformation features
- too many export modes or save options
- major UI expansion that makes the node harder to scan

## Manual Test Checklist

- Verify default save layout produces `%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%`.
- Verify `Friendly`, `Friendly Clean`, `Exact`, and `Custom` selection for both model and text encoder.
- Verify `Friendly Clean` removes known packager prefixes such as `mradermacher -` and `Goekdeniz-Guelmez_` while preserving creator/producer names like `Lockout` and `Huihui`.
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
- Verify batch collision warning appears for `overwrite` and `error` modes when no batch variable is in a custom Save Layout with multiple images.
- Verify PNG prompt metadata is preserved in saved files.
- Verify the frontend helper panel updates when relevant widgets change.
- For ignored `private-workflows`, verify standard `SaveImage` node count stays `0` after migrations and rerun `tools/validate_local_workflows.py private-workflows --json`.
- For repeat migrations, run `tools/migrate_save_image_nodes.py private-workflows --verify-no-standard` after any `--write` pass.

## Release Checklist

- `v0.8.0` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI and `Publish to Comfy Registry`.
- `v0.7.2` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI and `Publish to Comfy Registry`.
- `v0.7.1` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI and `Publish to Comfy Registry`.
- `v0.7.0` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI and `Publish to Comfy Registry`.
- `v0.6.3` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI and `Publish to Comfy Registry`.
- `v0.6.2` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by the final release gate.
- `v0.6.1` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by the final release gate.
- `v0.6.0` is tagged locally and on `origin`, published as a GitHub Release, published to the Comfy Registry, and verified by passing GitHub Actions CI and `Publish to Comfy Registry`.
- `v0.5.3` is tagged locally and on `origin`, published as a GitHub Release, and published to the Comfy Registry.
- For every release, use `tools/check_release_ready.py --tag <tag> --github --workflows --fail-on-unresolved-detection` as the final gate.
- Verify `Publish to Comfy Registry` succeeds after pushing a `pyproject.toml` version change.
- Confirm `README.md`, `docs/USAGE.md`, and Info-tab docs still match the actual UI labels before tagging.

## Notes

- `CONTINUE.md` is intentionally tracked and part of the shared maintainer handoff.
