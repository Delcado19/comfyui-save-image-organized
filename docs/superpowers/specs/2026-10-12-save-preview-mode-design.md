# Save/Preview Mode Split — Design Spec

Date: 2026-10-12
Status: Approved by maintainer, ready for implementation planning.

## Purpose

`SaveImageClean` currently always writes its output to disk on every run. This
spec adds a per-node `Save`/`Preview` mode. In `Preview` mode, the node shows
the result the same way ComfyUI's stock `Preview Image` node does (ComfyUI's
own temp-image mechanism), without writing anything to the final output path.
The user can then save any individual image from that batch later, with a
per-image button, using the exact target path that was already resolved when
the node ran.

This is purely additive: default mode is `Save`, so existing workflows behave
exactly as before unless the user explicitly switches a node to `Preview`.

## Non-Goals

- No "Save All" button — only a per-image save action (maintainer decision).
- No explicit "discard" action for a parked preview — it is dropped when the
  node runs again, or when ComfyUI restarts (RAM-only cache, maintainer
  decision).
- No ability to edit the target path/filename before saving a parked preview
  — it always uses the path resolved at preview-run time (maintainer
  decision).
- No custom temp-file management on disk for previews — previews use
  ComfyUI's existing native temp-image mechanism (`folder_paths.get_temp_directory()`,
  `ui.images` with `type: "temp"`), the same one every stock `Preview Image`
  node already relies on. This repo adds no new temp folder of its own.

## Backend Design

### New widget

`save_mode`: combo `("Save", "Preview")`, default `"Save"`, appended after
`Loader Priority` (the current last optional widget), so existing
`widgets_values` positions are untouched.

### Shared save routine

Extract the existing per-image write logic (path already resolved, collision
handling already run, format/quality/metadata already decided) out of
`save_images()` into a standalone function, e.g.:

```python
def _write_image_to_path(image, target_path, image_format, image_quality, metadata) -> Path:
    ...
```

Both the normal immediate-save path and the new "save now" route handler call
this function. This guarantees the deferred save behaves identically to an
immediate save (same JPEG alpha compositing, same PNG metadata embedding,
same quality clamping).

### Preview mode behavior

When `save_mode == "Preview"`, for each image in the batch:

1. Resolve the target path exactly as today (template rendering). Collision
   handling (`If File Exists`) is **not** evaluated yet — nothing is being
   written to that path right now, so there is nothing to collide with.
2. Encode the image into ComfyUI's temp directory via the same mechanism a
   stock `Preview Image` node uses, and add it to the `ui.images` result with
   `type: "temp"` instead of the real output folder.
3. Store an entry in a module-level, in-memory cache keyed by node id:
   `{batch_index: {image, target_path, image_format, image_quality, metadata}}`.
   A new run on the same node id replaces the entire entry — no accumulation
   across runs.

`FILENAME` and `FILE_PATH` outputs are empty strings in `Preview` mode (since
nothing was written at execution time). `IMAGES` always passes the full batch
through unchanged, regardless of mode — this is unaffected by this feature.

### New route

`POST /save_image_organized/save_now` with JSON body `{node_id, batch_index}`:

- Look up the cache entry. Missing or already-saved entry → `404` with a
  clear JSON error (`{"error": "preview expired, rerun the node"}`).
- On success, call `_write_image_to_path(...)` with the cached image, path,
  format, quality, and metadata. Remove the cache entry afterward (so a
  repeat click on the same button cleanly 404s instead of double-writing).
- Return `{"filename": ..., "file_path": ...}` on success.
- Any write failure (e.g. unwritable path) surfaces as `500` with the real
  exception message — the same error quality as the existing immediate-save
  path, not a generic wrapper.

### Cache lifetime

Pure in-memory, process-lifetime only. No disk persistence, no cleanup job
needed: a new run on the same node overwrites its entry, and a ComfyUI
restart drops the whole cache. Multiple preview-mode nodes in one workflow
are independent since the cache key is the node id.

## Frontend Design

### Mode toggle

`save_mode` is hidden via the existing `hideNativeWidget` helper and replaced
with a two-button pill (`Save` / `Preview`), reusing the `.sic-fmt-row` /
`.sic-fmt-btn` CSS already built for the `Image Format` buttons.

### Save mode (unchanged)

When the last run's `save_mode` was `Save`, the node's display is unchanged
from today: native ComfyUI image preview, no extra buttons, no custom grid.

### Preview mode

When the last run's `save_mode` was `Preview`, `onExecuted` builds a new
`addDOMWidget` grid (`createPreviewGridWidget(node)`) that replaces the
native preview for that result:

- One thumbnail (`<img>`) per batch image, source = the `/view` URL from the
  temp-type entries in the execution's `ui.images` result.
- A small "Save" button under each thumbnail.
- Click → `fetch('/save_image_organized/save_now', {method: 'POST', body: {node_id, batch_index}})`.
  - Success: button shows a brief "Saved ✓" state (~2s) then disables, with
    the real saved filename as its tooltip.
  - Failure: a short inline error message at the button (no alert/dialog),
    using the server's error text.

No "Save All" control and no discard control are added (see Non-Goals).

## Edge Cases

- **Widgets changed after the preview run, before saving**: the save uses the
  format/quality/metadata/path captured at run time, not the node's current
  widget values. This matches "use the path that was already set."
- **Double-click Save**: the second click 404s (entry already removed after
  first successful save) — no double write, no crash.
- **Collision handling** only applies at the actual `save_now` write, never
  during the preview run itself, so an unsaved preview can never trigger a
  spurious collision warning or increment.
- **Node deleted / workflow reloaded before saving**: the cache entry is
  simply never reached again; it disappears on the next ComfyUI restart with
  no leak-prevention code needed, since it is bounded by process lifetime.
- **Multiple preview nodes in one workflow**: independent, keyed by node id.

## Testing Plan

- Backend `pytest` coverage for:
  - `_write_image_to_path` directly (reuses existing save-path assertions).
  - The preview cache: a new run replaces a node's prior entry; a successful
    save removes the entry.
  - The `save_now` route via an aiohttp test client: success case and 404 on
    a missing/already-saved entry.
- Extend the existing `FILENAME`/`FILE_PATH`/`IMAGES` output test with a
  `Preview`-mode case: both string outputs empty, `IMAGES` still passes the
  batch through unchanged.
- No automated frontend test runner exists in this repo (consistent with the
  prior format-buttons/slider work) — frontend verification stays manual via
  the paired local ComfyUI install (`/object_info` check plus visual
  confirmation).
- All existing tests (89 as of this writing) must remain green.

## Documentation Impact

Per the project's Docs Sync Checker policy, once implemented this needs
updates to: `nodes.py`, `web/save_image_clean.js`, `README.md`,
`docs/USAGE.md`, `web/docs/SaveImageClean.md`, `CHANGELOG.md` (new
`[Unreleased]` entry), and `CONTINUE.md` (move this item out of "Deferred
Ideas").
