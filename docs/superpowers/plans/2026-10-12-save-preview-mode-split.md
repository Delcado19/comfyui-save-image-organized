# Save/Preview Mode Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `Save`/`Preview` mode toggle to `SaveImageClean` so a node can show its result without writing to the final path, then let the user save any individual image from that batch later with its own button.

**Architecture:** `SaveImageClean` gets a new `save_mode` widget (`Save`/`Preview`, default `Save`). The existing per-image Pillow write logic is extracted into a standalone `_write_image_to_path` function so both the immediate-save path and a new `save_now` aiohttp route write files identically. In `Preview` mode the node skips the final write, shows the result via ComfyUI's own native temp-image mechanism (the same one `Preview Image` uses), and parks each image in an in-memory, per-node-id cache. The new route consumes that cache when the user clicks a per-image `Save` button in a new frontend preview grid.

**Tech Stack:** Python 3.10+ (pytest, Pillow, NumPy — the existing stack), vanilla ES module JavaScript (ComfyUI's litegraph frontend, no build step, no new frontend dependency), aiohttp (ComfyUI's own bundled web framework, imported defensively since it is not installed in this repo's test environment).

**Spec:** `docs/superpowers/specs/2026-10-12-save-preview-mode-design.md`

## Global Constraints

- Default `save_mode` is `"Save"`; every existing workflow must behave exactly as before unless the widget is explicitly switched to `"Preview"` (spec: Purpose).
- No "Save All" control — only a per-image `Save` button (spec: Non-Goals).
- No explicit discard action — a parked preview is dropped only by a new run on that node, or a ComfyUI restart (spec: Non-Goals).
- No path/filename editing before saving a parked preview — always use the path resolved at preview-run time (spec: Non-Goals).
- No new temp-file management of our own — `Preview` mode uses only ComfyUI's existing native temp-image mechanism (`folder_paths.get_temp_directory()`, `ui.images`-style entries with `type: "temp"`) (spec: Non-Goals).
- `_write_image_to_path` is the single place that ever writes an image file for this node — both the immediate-save path and the `save_now` route call it, so a deferred save behaves identically to an immediate one (spec: Backend Design).
- All 89 existing tests (as of commit `c92f89b`) must stay green throughout; no regression in current `Save`-mode behavior.

## Review Focus

- A double-click (or any repeat click) on the same preview `Save` button after it already succeeded must 404/raise, never double-write or crash — Task 3.
- A multi-image `Preview` batch where only some images get saved must track each `batch_index` independently; saving one must not disturb the others still pending for that same node — Task 3.
- Switching a node from `Preview` back to `Save` and running it again must clear that node's stale `Preview`-mode cache entries, not leave orphaned images a user could no longer reach — Task 2.
- An out-of-range `image_quality` (e.g. from hand-edited or migrated workflow JSON) reaching `_write_image_to_path` through a cached `Preview` entry, not just through the normal immediate-save call site, must still clamp to `1`-`100` rather than crash the WebP encoder — Task 1.
- A `save_now` request naming a `batch_index` that does not exist for a node that otherwise *does* have cached entries must still raise cleanly, not raise a raw `KeyError` — Task 3.
- Collision handling (`If File Exists`) must still apply at the moment a parked preview is actually saved — if another file now occupies the cached raw path (e.g. the node ran again outside `Preview` mode in between), `save_now` must increment/error/use-seconds exactly like an immediate save would, not silently overwrite or crash. This is explicit in the spec's Edge Cases section ("Collision handling only applies at the actual save_now write") and was missed in the first draft of this plan; fixed in Tasks 1 and 3 below.

---

## Task 1: Extract `_write_image_to_path` and refactor the immediate-save path to use it

**Files:**
- Modify: `nodes.py:1869-1994` (`SaveImageClean.save_images` body) and the area just before `nodes.py:1239` (`class StripModelExtension:`)
- Test: `tests/test_nodes.py` (new tests placed directly after the `DummyImage` class, currently ending at `tests/test_nodes.py:694`)

**Interfaces:**
- Produces: `_write_image_to_path(image, target_path: Path, image_format: str, image_quality: int, metadata: PngImagePlugin.PngInfo | None, *, compress_level: int = 4) -> Path` — a module-level function in `nodes.py`. Creates `target_path`'s parent directories if missing, converts `image` (any object exposing `.cpu().numpy()`, matching the existing per-image convention in this file) to a Pillow image, clamps `image_quality` to `1`-`100`, and saves it in the format named by `image_format` (falling back to `PNG` for an unknown name, matching existing `IMAGE_FORMAT_INFO.get(image_format, IMAGE_FORMAT_INFO["PNG"])` behavior). Returns the same `target_path` it was given, for caller convenience.
- Produces: `_resolve_collision_path(candidate: Path, collision_mode: str, extension: str) -> Path` — a module-level function in `nodes.py`, extracted from the existing `SaveImageClean._resolve_target_path` method body (which becomes a thin wrapper over it, so all of its existing tests keep passing unchanged). Task 3's `_handle_save_now` calls this directly, since it has no `SaveImageClean` instance to call the method on.

- [ ] **Step 1: Write the failing tests**

Add directly after the `DummyImage` class definition in `tests/test_nodes.py` (currently ends at line 694, right before `def test_save_images_includes_detection_summary_in_ui_text`):

```python
def test_write_image_to_path_creates_missing_parent_directory(tmp_path):
    target = tmp_path / "nested" / "dir" / "out.png"
    image = DummyImage(np.zeros((2, 2, 3), dtype=np.float32))

    result = nodes._write_image_to_path(image, target, "PNG", 95, None)

    assert result == target
    assert target.exists()


def test_write_image_to_path_clamps_out_of_range_quality(tmp_path):
    target = tmp_path / "out.webp"
    image = DummyImage(np.ones((2, 2, 3), dtype=np.float32))

    # WebP's encoder raises ValueError on an out-of-range quality instead of
    # clamping it itself, so this would crash if _write_image_to_path did not
    # clamp internally (not just at the original save_images() call site).
    nodes._write_image_to_path(image, target, "WebP", 500, None)

    assert target.exists()


def test_resolve_collision_path_increments_existing_files(tmp_path):
    existing = tmp_path / "example.png"
    existing.write_bytes(b"first")

    target = nodes._resolve_collision_path(existing, "increment", "png")

    assert target == tmp_path / "example-2.png"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv-tests/Scripts/python.exe -m pytest tests/test_nodes.py -k "write_image_to_path or resolve_collision_path" -v`
Expected: FAIL with `AttributeError: module 'nodes' has no attribute '_write_image_to_path'` (and, once that's fixed, the same for `_resolve_collision_path`)

- [ ] **Step 3: Add `_write_image_to_path` to `nodes.py`**

Insert directly after `_render_filename_value` (currently ends at `nodes.py:1236` with `return _sanitize_path_component(rendered)`) and before `class StripModelExtension:` (currently `nodes.py:1239`):

```python
def _write_image_to_path(
    image: Any,
    target_path: Path,
    image_format: str,
    image_quality: int,
    metadata: PngImagePlugin.PngInfo | None,
    *,
    compress_level: int = 4,
) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
    pil_image = Image.fromarray(array)
    format_info = IMAGE_FORMAT_INFO.get(image_format, IMAGE_FORMAT_INFO["PNG"])
    pillow_format = format_info["pillow_format"]
    # The widget clamps to 1-100 in the UI, but hand-edited or migrated workflow JSON,
    # or a cached Preview-mode entry saved later, can carry a value outside that range.
    # Pillow's WebP encoder raises ValueError on an out-of-range quality instead of
    # clamping it, so enforce the documented range here, at the one place that
    # actually writes the file.
    quality = max(1, min(100, image_quality))
    if pillow_format == "PNG":
        pil_image.save(target_path, format=pillow_format, pnginfo=metadata, compress_level=compress_level)
    else:
        if pillow_format == "JPEG" and pil_image.mode != "RGB":
            # JPEG has no alpha channel. Image.convert("RGB") on its own would just drop
            # the alpha data and keep whatever RGB values sit underneath transparent
            # pixels, which can show up as unexpected colors/fringing. Composite onto a
            # white background first so transparent areas flatten the way users expect.
            if "A" in pil_image.getbands():
                flattened = Image.new("RGB", pil_image.size, (255, 255, 255))
                flattened.paste(pil_image, mask=pil_image.convert("RGBA").getchannel("A"))
                pil_image = flattened
            else:
                pil_image = pil_image.convert("RGB")
        pil_image.save(target_path, format=pillow_format, quality=quality)
    return target_path


def _resolve_collision_path(candidate: Path, collision_mode: str, extension: str) -> Path:
    candidate.parent.mkdir(parents=True, exist_ok=True)

    if collision_mode == "overwrite":
        return candidate
    if not candidate.exists():
        return candidate
    if collision_mode == "error":
        raise FileExistsError(f"Target file already exists: {candidate}")
    if collision_mode == "seconds":
        second_name = _sanitize_path_component(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        candidate = candidate.with_name(f"{second_name}.{extension}")
        if not candidate.exists():
            return candidate

    stem = candidate.stem
    for index in range(2, 10000):
        numbered = candidate.with_name(f"{stem}-{index}.{extension}")
        if not numbered.exists():
            return numbered

    raise RuntimeError("Could not create a unique filename after many attempts.")
```

Then, inside the `SaveImageClean` class, replace the body of the existing `_resolve_target_path` method (currently `nodes.py:1819-1848`) with a thin delegation, so every existing test that calls `saver._resolve_target_path(...)` keeps passing unchanged:

```python
    def _resolve_target_path(
        self,
        *,
        output_root: Path,
        relative_path: Path,
        collision_mode: str,
        extension: str,
    ) -> Path:
        return _resolve_collision_path(output_root / relative_path, collision_mode, extension)
```

- [ ] **Step 4: Refactor `save_images` to use it**

In `nodes.py`, remove the now-redundant early clamp (currently right after the `pillow_format = format_info["pillow_format"]` line, around `nodes.py:1874-1877`):

```python
# nodes.py — remove these 4 lines (comment + statement):
        # The widget clamps to 1-100 in the UI, but hand-edited or migrated workflow JSON can
        # submit values outside that range directly. Pillow's WebP encoder raises ValueError on
        # an out-of-range quality instead of clamping it, so enforce the documented range here.
        image_quality = max(1, min(100, image_quality))
```

Then replace the inline Pillow save block inside the per-image loop (currently `nodes.py:1955-1970`):

```python
# nodes.py — current, to be replaced:
            pil_image = Image.fromarray(array)
            if pillow_format == "PNG":
                pil_image.save(target_path, format=pillow_format, pnginfo=metadata, compress_level=self.compress_level)
            else:
                if pillow_format == "JPEG" and pil_image.mode != "RGB":
                    # JPEG has no alpha channel. Image.convert("RGB") on its own would just drop
                    # the alpha data and keep whatever RGB values sit underneath transparent
                    # pixels, which can show up as unexpected colors/fringing. Composite onto a
                    # white background first so transparent areas flatten the way users expect.
                    if "A" in pil_image.getbands():
                        flattened = Image.new("RGB", pil_image.size, (255, 255, 255))
                        flattened.paste(pil_image, mask=pil_image.convert("RGBA").getchannel("A"))
                        pil_image = flattened
                    else:
                        pil_image = pil_image.convert("RGB")
                pil_image.save(target_path, format=pillow_format, quality=image_quality)
```

with:

```python
            _write_image_to_path(image, target_path, image_format, image_quality, metadata, compress_level=self.compress_level)
```

- [ ] **Step 5: Run the new tests, then the full suite**

Run: `.venv-tests/Scripts/python.exe -m pytest tests/test_nodes.py -k "write_image_to_path or resolve_collision_path" -v`
Expected: PASS (3 tests)

Run: `.venv-tests/Scripts/python.exe -m pytest -q`
Expected: all tests pass (89 existing + 3 new = 92), no regressions — this refactor must not change any observable save behavior, and the existing `test_resolve_target_path_*` tests must still pass unchanged against the new thin-wrapper method.

Run: `.venv-tests/Scripts/python.exe -m ruff check .`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add nodes.py tests/test_nodes.py
git commit -m "Extract _write_image_to_path and _resolve_collision_path from save_images for reuse by the save-now route"
```

---

## Task 2: `save_mode` widget and `Preview`-mode write path

**Files:**
- Modify: `nodes.py` — imports, `IMAGE_FORMAT_INFO` area (new module-level cache), `SaveImageClean.__init__`, `INPUT_TYPES`, `save_images` signature and body
- Modify: `tests/conftest.py`
- Test: `tests/test_nodes.py`

**Interfaces:**
- Consumes: `_write_image_to_path`, `_resolve_collision_path` (Task 1), `IMAGE_FORMAT_INFO`, `self._resolve_relative_output_path` (all pre-existing or from Task 1).
- Produces: module-level `_PREVIEW_CACHE: dict[str, dict[int, dict[str, Any]]]`, keyed by `str(unique_id)` then `batch_index`, each entry `{"image": ..., "target_path": Path, "image_format": str, "image_quality": int, "metadata": PngImagePlugin.PngInfo | None, "collision_mode": str}`. Task 3 reads and mutates this directly, and needs `collision_mode` to apply collision handling at the actual save-now write (see Review Focus).
- Produces: `ui["save_image_clean_preview"]`, a list of `{"batch_index": int, "filename": str, "subfolder": str, "type": "temp"}` dicts, present in the returned dict only when `save_mode == "Preview"` and at least one image was parked. Task 5 (frontend) reads this from the `message` object in `onExecuted`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_nodes.py`, near `test_save_images_returns_filename_and_absolute_path_outputs` (currently around line 1304):

```python
def test_save_images_preview_mode_does_not_write_final_file(workspace_tmp_path, tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    saver.temp_dir = str(tmp_path / "temp")
    images = [DummyImage(np.zeros((2, 2, 3), dtype=np.float32))]

    result = saver.save_images(
        images=images,
        path_template="%TOP_FOLDER%/%FILENAME%",
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Off",
        export_workflow_metadata=True,
        subfolder="output-tests",
        filename_datetime="preview-check",
        save_mode="Preview",
        prompt={"1": {"class_type": "SaveImageClean", "inputs": {}}},
        unique_id="42",
    )

    filename, file_path, passthrough_images = result["result"]
    assert filename == ""
    assert file_path == ""
    assert passthrough_images is images
    assert not (workspace_tmp_path / "output-tests" / "preview-check.png").exists()
    assert result["ui"]["images"] == []

    preview_payload = result["ui"]["save_image_clean_preview"]
    assert len(preview_payload) == 1
    assert preview_payload[0]["batch_index"] == 1
    assert preview_payload[0]["type"] == "temp"
    temp_file = Path(saver.temp_dir) / preview_payload[0]["filename"]
    assert temp_file.exists()


def test_save_images_preview_mode_replaces_prior_cache_entry_on_rerun(workspace_tmp_path, tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    saver.temp_dir = str(tmp_path / "temp")
    images = [DummyImage(np.zeros((2, 2, 3), dtype=np.float32))]
    kwargs = dict(
        images=images,
        path_template="%TOP_FOLDER%/%FILENAME%",
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Off",
        export_workflow_metadata=True,
        subfolder="output-tests",
        filename_datetime="preview-cache",
        save_mode="Preview",
        prompt={"1": {"class_type": "SaveImageClean", "inputs": {}}},
        unique_id="cache-node",
    )

    saver.save_images(**kwargs)
    first_entry = nodes._PREVIEW_CACHE["cache-node"][1]
    assert first_entry["target_path"].name == "preview-cache.png"

    saver.save_images(**kwargs)
    second_entry = nodes._PREVIEW_CACHE["cache-node"][1]
    assert second_entry is not first_entry
    assert len(nodes._PREVIEW_CACHE["cache-node"]) == 1


def test_save_images_switching_back_to_save_clears_stale_preview_cache(workspace_tmp_path, tmp_path):
    saver = nodes.SaveImageClean()
    saver.output_dir = str(workspace_tmp_path)
    saver.temp_dir = str(tmp_path / "temp")
    images = [DummyImage(np.zeros((2, 2, 3), dtype=np.float32))]
    base_kwargs = dict(
        images=images,
        path_template="%TOP_FOLDER%/%FILENAME%",
        collision_mode="increment",
        model_source="Friendly",
        clip_source="Friendly",
        detection_info="Off",
        export_workflow_metadata=True,
        subfolder="output-tests",
        filename_datetime="switch-back",
        prompt={"1": {"class_type": "SaveImageClean", "inputs": {}}},
        unique_id="switch-node",
    )

    saver.save_images(save_mode="Preview", **base_kwargs)
    assert "switch-node" in nodes._PREVIEW_CACHE

    saver.save_images(save_mode="Save", **base_kwargs)
    assert "switch-node" not in nodes._PREVIEW_CACHE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv-tests/Scripts/python.exe -m pytest tests/test_nodes.py -k preview_mode -v`
Expected: FAIL (`save_images()` does not accept keyword argument `save_mode`, and/or `AttributeError` on `saver.temp_dir` / `nodes._PREVIEW_CACHE`)

- [ ] **Step 3: Implement the widget, cache, and `Preview`-mode write path**

In `nodes.py`, add `uuid4` to the stdlib imports (alphabetically after `typing`):

```python
# nodes.py:9 area — add this line after `from typing import Any`
from uuid import uuid4
```

Add the module-level cache right after `DEFAULT_FILENAME_PATTERN` (currently `nodes.py:157`):

```python
DEFAULT_FILENAME_PATTERN = "%date:yyyy-MM-dd_hh-mm-ss%"
# In-memory cache for parked Preview-mode images, keyed by node id (str(unique_id))
# then batch index. Replaced wholesale on every run of that node, in either mode,
# and dropped entirely on process restart -- see
# docs/superpowers/specs/2026-10-12-save-preview-mode-design.md.
_PREVIEW_CACHE: dict[str, dict[int, dict[str, Any]]] = {}
```

In `SaveImageClean.__init__` (currently `nodes.py:1301-1305`), add a cached temp directory next to the existing output directory:

```python
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.temp_dir = folder_paths.get_temp_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4
```

In `INPUT_TYPES`'s `"optional"` block, add `save_mode` directly after `loader_priority` (currently ending at `nodes.py:1457`, right before the closing `},` of the optional dict and the `"hidden"` block):

```python
                "loader_priority": (
                    LOADER_PRIORITY_OPTIONS,
                    {
                        "default": "Nearest",
                        "tooltip": (
                            "How to pick a model/text-encoder when more than one loader feeds "
                            "this save. Nearest picks the loader with the fewest upstream links "
                            "(right for most single-pass workflows). First Used picks the loader "
                            "furthest upstream, i.e. the first one applied in a multi-stage "
                            "pipeline such as a base pass refined by a second model."
                        ),
                    },
                ),
                "save_mode": (
                    ["Save", "Preview"],
                    {
                        "default": "Save",
                        "tooltip": (
                            "Save writes every image immediately, as before. Preview shows the "
                            "result without writing to the final path; use the per-image Save "
                            "button in the preview grid to write one later, to the path already "
                            "shown here."
                        ),
                    },
                ),
```

In `save_images`'s signature (currently `nodes.py:1850-1869`), add `save_mode` after `loader_priority`:

```python
        loader_priority: str = "Nearest",
        save_mode: str = "Save",
        prompt: Any = None,
```

At the top of `save_images`'s body, right before the `for batch_index, image in enumerate(images, start=1):` loop (after the existing `batch_collision_warning` block), add:

```python
        node_key = str(unique_id)
        _PREVIEW_CACHE.pop(node_key, None)
        preview_entries: dict[int, dict[str, Any]] = {}
        preview_entries_ui: list[dict[str, Any]] = []
        preview_run_token = uuid4().hex[:8]
```

Inside the loop, directly after the existing `if not preview:` detection-bookkeeping block and before the existing `try: target_path = self._resolve_target_path(...)` block, insert the mode branch:

```python
            if save_mode == "Preview":
                target_path = output_root / relative_path
                preview_entries[batch_index] = {
                    "image": image,
                    "target_path": target_path,
                    "image_format": image_format,
                    "image_quality": image_quality,
                    "metadata": metadata,
                    "collision_mode": collision_mode,
                }
                temp_dir = Path(self.temp_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_filename = f"save_image_organized_preview_{node_key}_{preview_run_token}_{batch_index}.png"
                Image.fromarray(array).save(temp_dir / temp_filename, format="PNG", compress_level=1)
                preview_entries_ui.append(
                    {
                        "batch_index": batch_index,
                        "filename": temp_filename,
                        "subfolder": "",
                        "type": "temp",
                    }
                )
                continue
```

(The existing `try: target_path = self._resolve_target_path(...)` block and the `_write_image_to_path(...)` call from Task 1 remain unchanged below this — they only run for `save_mode == "Save"` now, since the `Preview` branch above ends with `continue`.)

After the loop, where `ui = {"images": saved, "text": text_output}` is built (currently `nodes.py:1985-1987`), add the preview payload and commit the cache:

```python
        ui = {"images": saved, "text": text_output}
        if detection_ui_payload is not None:
            ui["save_image_clean"] = [detection_ui_payload]
        if save_mode == "Preview" and preview_entries_ui:
            ui["save_image_clean_preview"] = preview_entries_ui
            _PREVIEW_CACHE[node_key] = preview_entries
```

In `tests/conftest.py`, add a temp-directory stub next to the existing output-directory stub, and an autouse fixture that isolates `nodes._PREVIEW_CACHE` between tests:

```python
# tests/conftest.py:16-18 — current:
folder_paths = types.ModuleType("folder_paths")
folder_paths.get_output_directory = lambda: str(REPO_ROOT / "test-output")
sys.modules.setdefault("folder_paths", folder_paths)
```

becomes:

```python
folder_paths = types.ModuleType("folder_paths")
folder_paths.get_output_directory = lambda: str(REPO_ROOT / "test-output")
folder_paths.get_temp_directory = lambda: str(REPO_ROOT / "test-output-temp")
sys.modules.setdefault("folder_paths", folder_paths)


@pytest.fixture(autouse=True)
def _clear_preview_cache():
    import nodes

    nodes._PREVIEW_CACHE.clear()
    yield
    nodes._PREVIEW_CACHE.clear()
```

(Place this fixture before the existing `workspace_tmp_path` fixture.)

- [ ] **Step 4: Run the new tests, then the full suite**

Run: `.venv-tests/Scripts/python.exe -m pytest tests/test_nodes.py -k preview_mode -v`
Expected: PASS (3 tests)

Run: `.venv-tests/Scripts/python.exe -m pytest -q`
Expected: all tests pass (92 + 3 = 95), no regressions.

Run: `.venv-tests/Scripts/python.exe -m ruff check .`
Expected: `All checks passed!`

- [ ] **Step 5: Commit**

```bash
git add nodes.py tests/conftest.py tests/test_nodes.py
git commit -m "Add save_mode widget and Preview-mode write path to SaveImageClean"
```

---

## Task 3: `save_now` route and its cache-consuming logic

**Files:**
- Modify: `nodes.py` — add `PreviewNotFoundError`, `_handle_save_now`, and a guarded aiohttp route registration
- Test: `tests/test_nodes.py`

**Interfaces:**
- Consumes: `_PREVIEW_CACHE` (Task 2), `_write_image_to_path`, `_resolve_collision_path` (Task 1), `IMAGE_FORMAT_INFO`.
- Produces: `PreviewNotFoundError` (exception class), `_handle_save_now(node_id: str, batch_index: int) -> dict[str, str]` returning `{"filename": str, "file_path": str}` on success or raising `PreviewNotFoundError` otherwise. Task 5 (frontend) calls the route this wraps.

**Note on testing approach:** The spec's testing plan describes exercising the route "via an aiohttp test client," but neither `aiohttp` nor ComfyUI's `server` module is installed in this repo's `.venv-tests` (confirmed: `import aiohttp` and `import server` both raise `ModuleNotFoundError` there). Adding `aiohttp` as a new test-only dependency was considered and rejected — the route itself is a thin wrapper with no logic of its own beyond JSON parsing and status-code mapping, so this plan instead puts all real logic in `_handle_save_now`, a plain function tested directly with no new dependency. The route wrapper's own correctness (status codes, JSON shape) is verified manually against the live ComfyUI install in Task 6, consistent with how this repo already treats its frontend changes.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_nodes.py`, after the new tests from Task 2:

```python
def test_handle_save_now_writes_cached_entry_and_clears_it(tmp_path):
    target = tmp_path / "out" / "save-now.png"
    nodes._PREVIEW_CACHE["node-a"] = {
        1: {
            "image": DummyImage(np.zeros((2, 2, 3), dtype=np.float32)),
            "target_path": target,
            "image_format": "PNG",
            "image_quality": 95,
            "metadata": None,
            "collision_mode": "increment",
        }
    }

    result = nodes._handle_save_now("node-a", 1)

    assert result == {"filename": "save-now.png", "file_path": str(target.resolve())}
    assert target.exists()
    assert "node-a" not in nodes._PREVIEW_CACHE


def test_handle_save_now_raises_for_unknown_node(tmp_path):
    with pytest.raises(nodes.PreviewNotFoundError):
        nodes._handle_save_now("does-not-exist", 1)


def test_handle_save_now_raises_for_wrong_batch_index_on_known_node(tmp_path):
    nodes._PREVIEW_CACHE["node-known"] = {
        1: {
            "image": DummyImage(np.zeros((2, 2, 3), dtype=np.float32)),
            "target_path": tmp_path / "known.png",
            "image_format": "PNG",
            "image_quality": 95,
            "metadata": None,
            "collision_mode": "increment",
        }
    }

    with pytest.raises(nodes.PreviewNotFoundError):
        nodes._handle_save_now("node-known", 2)


def test_handle_save_now_raises_on_second_call_after_success(tmp_path):
    target = tmp_path / "save-now-twice.png"
    nodes._PREVIEW_CACHE["node-b"] = {
        1: {
            "image": DummyImage(np.ones((2, 2, 3), dtype=np.float32)),
            "target_path": target,
            "image_format": "PNG",
            "image_quality": 95,
            "metadata": None,
            "collision_mode": "increment",
        }
    }

    nodes._handle_save_now("node-b", 1)
    with pytest.raises(nodes.PreviewNotFoundError):
        nodes._handle_save_now("node-b", 1)


def test_handle_save_now_saving_one_batch_image_leaves_siblings_pending(tmp_path):
    nodes._PREVIEW_CACHE["node-c"] = {
        1: {
            "image": DummyImage(np.zeros((2, 2, 3), dtype=np.float32)),
            "target_path": tmp_path / "first.png",
            "image_format": "PNG",
            "image_quality": 95,
            "metadata": None,
            "collision_mode": "increment",
        },
        2: {
            "image": DummyImage(np.ones((2, 2, 3), dtype=np.float32)),
            "target_path": tmp_path / "second.png",
            "image_format": "PNG",
            "image_quality": 95,
            "metadata": None,
            "collision_mode": "increment",
        },
    }

    nodes._handle_save_now("node-c", 1)

    assert "node-c" in nodes._PREVIEW_CACHE
    assert 1 not in nodes._PREVIEW_CACHE["node-c"]
    assert 2 in nodes._PREVIEW_CACHE["node-c"]
    assert (tmp_path / "first.png").exists()
    assert not (tmp_path / "second.png").exists()


def test_handle_save_now_applies_collision_mode_at_save_time(tmp_path):
    # Something now occupies the exact raw path that was cached at preview time
    # (e.g. the node ran again outside Preview mode in between) -- save_now must
    # still increment rather than silently overwrite it or crash.
    cached_path = tmp_path / "collide.png"
    cached_path.write_bytes(b"already here")
    nodes._PREVIEW_CACHE["node-d"] = {
        1: {
            "image": DummyImage(np.zeros((2, 2, 3), dtype=np.float32)),
            "target_path": cached_path,
            "image_format": "PNG",
            "image_quality": 95,
            "metadata": None,
            "collision_mode": "increment",
        }
    }

    result = nodes._handle_save_now("node-d", 1)

    assert result["filename"] == "collide-2.png"
    assert (tmp_path / "collide-2.png").exists()
    assert cached_path.read_bytes() == b"already here"  # untouched, not overwritten
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv-tests/Scripts/python.exe -m pytest tests/test_nodes.py -k handle_save_now -v`
Expected: FAIL with `AttributeError: module 'nodes' has no attribute 'PreviewNotFoundError'` (or `_handle_save_now`) — 6 tests should fail/error at collection or run time.

- [ ] **Step 3: Implement `PreviewNotFoundError`, `_handle_save_now`, and the route**

In `nodes.py`, insert directly after `_write_image_to_path` (Task 1) and before `class StripModelExtension:`:

```python
class PreviewNotFoundError(Exception):
    """Raised when a save-now request names a preview that is missing or already saved."""


def _handle_save_now(node_id: str, batch_index: int) -> dict[str, str]:
    node_cache = _PREVIEW_CACHE.get(node_id)
    entry = node_cache.get(batch_index) if node_cache else None
    if entry is None:
        raise PreviewNotFoundError(
            f"No pending preview for node {node_id!r}, batch index {batch_index}. Rerun the node."
        )

    # The raw path cached at preview time is never edited (see spec Non-Goals), but
    # collision handling was deliberately skipped during the preview run itself, so
    # it must run now, at the moment something actually gets written to disk.
    extension = IMAGE_FORMAT_INFO.get(entry["image_format"], IMAGE_FORMAT_INFO["PNG"])["extension"]
    resolved_path = _resolve_collision_path(entry["target_path"], entry["collision_mode"], extension)

    target_path = _write_image_to_path(
        entry["image"],
        resolved_path,
        entry["image_format"],
        entry["image_quality"],
        entry["metadata"],
    )

    del node_cache[batch_index]
    if not node_cache:
        del _PREVIEW_CACHE[node_id]

    return {"filename": target_path.name, "file_path": str(target_path.resolve())}
```

At the very end of `nodes.py`, after the existing `NODE_DISPLAY_NAME_MAPPINGS` dict, add the guarded route registration:

```python
try:
    from aiohttp import web
    from server import PromptServer
except ImportError:  # running outside a real ComfyUI install, e.g. under pytest
    PromptServer = None
    web = None


if PromptServer is not None:

    @PromptServer.instance.routes.post("/save_image_organized/save_now")
    async def _save_image_organized_save_now(request):
        payload = await request.json()
        node_id = str(payload.get("node_id", ""))
        try:
            batch_index = int(payload.get("batch_index"))
        except (TypeError, ValueError):
            return web.json_response({"error": "batch_index must be an integer"}, status=400)

        try:
            result = _handle_save_now(node_id, batch_index)
        except PreviewNotFoundError as exc:
            return web.json_response({"error": str(exc)}, status=404)
        except Exception as exc:  # noqa: BLE001 - surface the real write failure to the UI
            return web.json_response({"error": str(exc)}, status=500)

        return web.json_response(result)
```

- [ ] **Step 4: Run the new tests, then the full suite**

Run: `.venv-tests/Scripts/python.exe -m pytest tests/test_nodes.py -k handle_save_now -v`
Expected: PASS (6 tests)

Run: `.venv-tests/Scripts/python.exe -m pytest -q`
Expected: all tests pass (95 + 6 = 101), no regressions.

Run: `.venv-tests/Scripts/python.exe -m py_compile nodes.py` (via `G:\ComfyUI-Easy-Install\python_embeded\python.exe -m py_compile nodes.py` if available, otherwise the `.venv-tests` interpreter)
Expected: no output, exit code 0 — confirms the guarded `try`/`except ImportError` block is syntactically sound even though `aiohttp`/`server` are not installed here.

Run: `.venv-tests/Scripts/python.exe -m ruff check .`
Expected: `All checks passed!`

- [ ] **Step 5: Commit**

```bash
git add nodes.py tests/test_nodes.py
git commit -m "Add save_now route and preview-cache handling for Preview mode"
```

---

## Task 4: Frontend Save/Preview pill toggle

**Files:**
- Modify: `web/save_image_clean.js`

**Interfaces:**
- Consumes: `getWidget`, `hideNativeWidget`, `insertWidgetBefore`, `injectFormatButtonsCss` (all pre-existing, same pattern as `createFormatButtonsWidget`).
- Produces: `createSaveModeToggleWidget(node)`, `setActiveSaveModeButton(node, activeId)` — both follow the exact shape of `createFormatButtonsWidget`/`setActiveFormatButton` (`web/save_image_clean.js:850-917`), the established precedent for a native combo widget replaced by a button row in this file.

No automated frontend test runner exists in this repo (consistent with every prior UI change here) — verification is `node --check` plus a manual feel-check against the paired local ComfyUI install.

- [ ] **Step 1: Add the `save_mode` label and the `SAVE_MODE_IDS` constant**

In `web/save_image_clean.js`, add `save_mode: "Save Mode",` to the `LABELS` object (currently `web/save_image_clean.js:7-21`), directly after `loader_priority: "Loader Priority",`:

```js
const LABELS = {
    path_template: "Save Layout",
    model_source: "Model Name",
    clip_source: "Text Encoder Name",
    filename_datetime: "Filename",
    collision_mode: "If File Exists",
    detection_info: "Detection Info",
    export_workflow_metadata: "Export Workflow Metadata",
    image_format: "Image Format",
    image_quality: "Image Quality",
    loader_priority: "Loader Priority",
    save_mode: "Save Mode",
    subfolder: "Top Folder",
    model_folder: "Custom Model Name",
    clip_folder: "Custom Text Encoder Name",
};
```

Add a new constant directly after `const IMAGE_FORMAT_IDS = ["PNG", "JPEG", "WebP"];` (currently `web/save_image_clean.js:809`):

```js
const SAVE_MODE_IDS = ["Save", "Preview"];
```

- [ ] **Step 2: Add `setActiveSaveModeButton` and `createSaveModeToggleWidget`**

Insert directly after `createFormatButtonsWidget` ends (currently `web/save_image_clean.js:917`, the closing `}` after `return widget;`):

```js
function setActiveSaveModeButton(node, activeId) {
    const buttons = node.__saveImageCleanSaveModeButtons;
    if (!buttons) {
        return;
    }
    for (const [id, button] of Object.entries(buttons)) {
        button.classList.toggle("active", id === activeId);
    }
}

function createSaveModeToggleWidget(node) {
    const modeWidget = getWidget(node, "save_mode");
    if (!modeWidget || node.__saveImageCleanSaveModeWidget) {
        return node.__saveImageCleanSaveModeWidget;
    }

    injectFormatButtonsCss();
    hideNativeWidget(modeWidget);

    const row = document.createElement("div");
    row.className = "sic-fmt-row";

    const buttons = {};
    for (const id of SAVE_MODE_IDS) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "sic-fmt-btn";
        button.textContent = id;
        button.title = id === "Preview"
            ? "Show the result without saving; save individual images later"
            : "Save immediately, as before";
        button.addEventListener("click", () => {
            if (modeWidget.value === id) {
                return;
            }
            modeWidget.value = id;
            modeWidget.callback?.(id);
            setActiveSaveModeButton(node, id);
        });
        row.appendChild(button);
        buttons[id] = button;
    }

    const widget = node.addDOMWidget("save_image_clean_save_mode_buttons", "custom", row, {
        getMinHeight: () => 26,
        getMaxHeight: () => 28,
        serialize: false,
        hideOnZoom: false,
        margin: 2,
    });

    node.__saveImageCleanSaveModeWidget = widget;
    node.__saveImageCleanSaveModeButtons = buttons;
    insertWidgetBefore(node, widget, "save_mode");
    setActiveSaveModeButton(node, modeWidget.value);
    return widget;
}
```

- [ ] **Step 3: Wire it into the lifecycle hooks and the help-panel resync**

In `app.registerExtension`'s `configure` override, add `createSaveModeToggleWidget(this);` directly after `createFormatButtonsWidget(this);`:

```js
                createFormatButtonsWidget(this);
                createSaveModeToggleWidget(this);
```

Do the same in the `onNodeCreated` override, directly after its own `createFormatButtonsWidget(this);` line.

In `updateHelp` (where it currently resyncs the format buttons — look for `setActiveFormatButton(node, getWidget(node, "image_format")?.value);`), add a matching resync line directly after it:

```js
    setActiveFormatButton(node, getWidget(node, "image_format")?.value);
    setActiveSaveModeButton(node, getWidget(node, "save_mode")?.value);
```

- [ ] **Step 4: Verify and commit**

Run: `node --check web/save_image_clean.js`
Expected: no output, exit code 0.

```bash
git add web/save_image_clean.js
git commit -m "Add Save/Preview mode toggle widget to the frontend"
```

---

## Task 5: Frontend preview grid with per-image Save buttons

**Files:**
- Modify: `web/save_image_clean.js`

**Interfaces:**
- Consumes: `api.apiURL` (new import from `../../scripts/api.js`), `insertWidgetBefore`, `message.save_image_clean_preview` (produced by Task 2's backend change, each entry `{batch_index, filename, subfolder, type}`).
- Produces: `createPreviewGridWidget(node)`, `updatePreviewGrid(node, message)`, called from the node's lifecycle hooks and `onExecuted` respectively.

No automated frontend test runner exists in this repo — verification is `node --check` plus a manual feel-check against the paired local ComfyUI install (queue a workflow through a `Preview`-mode node, confirm the grid appears with working per-image Save buttons, and that `Save`-mode nodes show no grid at all).

- [ ] **Step 1: Add the `api` import and the preview-grid CSS injector**

In `web/save_image_clean.js`, change the single import line (currently `web/save_image_clean.js:1`):

```js
import { app } from "../../scripts/app.js";
```

to:

```js
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
```

Insert a new CSS injector directly after `createSaveModeToggleWidget` ends (Task 4) and before `createHelpPanelWidget` begins:

```js
let _previewGridCssInjected = false;
function injectPreviewGridCss() {
    if (_previewGridCssInjected || document.getElementById("save-image-clean-preview-grid-css")) {
        _previewGridCssInjected = true;
        return;
    }
    _previewGridCssInjected = true;
    const style = document.createElement("style");
    style.id = "save-image-clean-preview-grid-css";
    style.textContent = [
        ".sic-preview-grid{display:flex;flex-direction:column;}",
        ".sic-preview-grid-body{display:flex;flex-wrap:wrap;gap:8px;padding:6px 8px;}",
        ".sic-preview-cell{display:flex;flex-direction:column;align-items:center;gap:4px;width:92px;}",
        ".sic-preview-thumb{width:100%;aspect-ratio:1;object-fit:cover;border-radius:6px;",
        "border:1px solid rgba(255,255,255,0.14);background:rgba(0,0,0,0.2);}",
        ".sic-preview-save-btn{width:100%;padding:3px 0;font-size:10px;font-weight:600;border-radius:5px;",
        "border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.05);color:#cfcfcf;",
        "cursor:pointer;font-family:inherit;",
        "transition:transform 120ms var(--sic-ease-out), border-color 120ms var(--sic-ease), color 120ms var(--sic-ease);}",
        ".sic-preview-save-btn:hover{border-color:rgba(142,183,255,0.5);color:#e3e3e3;}",
        ".sic-preview-save-btn:active{transform:scale(0.97);}",
        ".sic-preview-save-btn.saved{background:#2f8f5b;border-color:#2f8f5b;color:#fff;cursor:default;}",
        ".sic-preview-save-btn:disabled{opacity:0.7;}",
        ".sic-preview-status{font-size:9px;color:#e08a8a;text-align:center;min-height:11px;}",
    ].join("");
    document.head.appendChild(style);
}
```

- [ ] **Step 2: Add the URL builder and the per-cell factory**

Insert directly after `injectPreviewGridCss`:

```js
function buildPreviewImageUrl(entry) {
    const params = new URLSearchParams({
        filename: entry.filename,
        type: entry.type || "temp",
        subfolder: entry.subfolder || "",
    });
    return api.apiURL(`/view?${params.toString()}`);
}

function buildPreviewCell(node, entry) {
    const cell = document.createElement("div");
    cell.className = "sic-preview-cell";

    const img = document.createElement("img");
    img.className = "sic-preview-thumb";
    img.src = buildPreviewImageUrl(entry);
    img.alt = `Preview ${entry.batch_index}`;

    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.className = "sic-preview-save-btn";
    saveBtn.textContent = "Save";

    const statusEl = document.createElement("div");
    statusEl.className = "sic-preview-status";

    saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        statusEl.textContent = "";
        try {
            const response = await fetch(api.apiURL("/save_image_organized/save_now"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ node_id: String(node.id), batch_index: entry.batch_index }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data?.error || `Save failed (${response.status})`);
            }
            saveBtn.textContent = "\u2713 Saved";
            saveBtn.title = data.file_path || data.filename || "";
            saveBtn.classList.add("saved");
            setTimeout(() => {
                saveBtn.textContent = "Saved";
            }, 2000);
        } catch (err) {
            saveBtn.disabled = false;
            statusEl.textContent = err?.message || "Save failed";
        }
    });

    cell.appendChild(img);
    cell.appendChild(saveBtn);
    cell.appendChild(statusEl);
    return cell;
}
```

- [ ] **Step 3: Add `createPreviewGridWidget` and `updatePreviewGrid`**

Insert directly after `buildPreviewCell`:

```js
function createPreviewGridWidget(node) {
    if (node.__saveImageCleanPreviewGridRefs) {
        return node.__saveImageCleanPreviewGridRefs;
    }

    injectPreviewGridCss();

    const container = document.createElement("div");
    container.className = "sic-preview-grid";
    container.style.display = "none";

    const body = document.createElement("div");
    body.className = "sic-preview-grid-body";
    container.appendChild(body);

    const widget = node.addDOMWidget("save_image_clean_preview_grid", "custom", container, {
        getMinHeight: () => (container.style.display === "none" ? 0 : 130),
        getMaxHeight: () => (container.style.display === "none" ? 0 : 260),
        serialize: false,
        hideOnZoom: false,
        margin: 4,
    });

    const refs = { widget, container, body };
    node.__saveImageCleanPreviewGridRefs = refs;
    insertWidgetBefore(node, widget, "save_mode");
    return refs;
}

function updatePreviewGrid(node, message) {
    const refs = node.__saveImageCleanPreviewGridRefs;
    if (!refs) {
        return;
    }

    const entries = Array.isArray(message?.save_image_clean_preview) ? message.save_image_clean_preview : [];
    refs.body.replaceChildren();

    if (!entries.length) {
        refs.container.style.display = "none";
        node.setSize?.(node.computeSize());
        node.setDirtyCanvas?.(true, true);
        return;
    }

    for (const entry of entries) {
        refs.body.appendChild(buildPreviewCell(node, entry));
    }
    refs.container.style.display = "flex";
    // The native per-node thumbnail strip is driven by node.imgs, populated by
    // ComfyUI's own default onExecuted from message.images. Preview-mode temp
    // images are intentionally kept out of message.images (see nodes.py's
    // save_image_clean_preview key) so they never reach node.imgs in the first
    // place; this clears it defensively in case that ever changes upstream.
    node.imgs = [];
    const newSize = node.computeSize();
    newSize[0] = Math.max(newSize[0], node.size[0]);
    newSize[1] = Math.max(newSize[1], node.size[1]);
    node.setSize?.(newSize);
    node.setDirtyCanvas?.(true, true);
}
```

- [ ] **Step 4: Wire it into the lifecycle hooks and `onExecuted`**

In both the `configure` and `onNodeCreated` overrides, add `createPreviewGridWidget(this);` directly after the `createSaveModeToggleWidget(this);` line added in Task 4:

```js
                createSaveModeToggleWidget(this);
                createPreviewGridWidget(this);
```

In the `onExecuted` override (look for `nodeType.prototype.onExecuted = function (message) {`), add a call to `updatePreviewGrid` after the existing `updateHelp(this);` line:

```js
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const result = onExecuted?.apply(this, arguments);
            setLastRunStateFromMessage(this, message);
            updateHelp(this);
            updatePreviewGrid(this, message);
            return result;
        };
```

- [ ] **Step 5: Verify and commit**

Run: `node --check web/save_image_clean.js`
Expected: no output, exit code 0.

Manual feel-check against the paired local ComfyUI install (`G:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\save-image-organized`, after copying the updated `web/save_image_clean.js` there and refreshing the browser — no server restart needed, this is a frontend-only file):
- A node in `Save` mode (the default) looks and behaves exactly as before: native image preview, `FILENAME`/`FILE_PATH` populated, no grid.
- Switching a node to `Preview` and queueing it shows no native thumbnail strip; instead the new grid appears with one thumbnail and one `Save` button per batch image.
- Clicking a `Save` button writes that one file (check it lands at the path shown in the node's own `Example Output` panel), the button turns into a disabled "Saved" state with the real path as its tooltip, and the other buttons in the same grid remain independently clickable.
- Clicking an already-saved button a second time (if re-enabled via a page reload) shows the inline "preview expired" error text instead of crashing anything.

```bash
git add web/save_image_clean.js
git commit -m "Add per-image preview grid with Save buttons for Preview mode"
```

---

## Task 6: Documentation sync and final verification

**Files:**
- Modify: `CHANGELOG.md`, `README.md`, `docs/USAGE.md`, `web/docs/SaveImageClean.md`, `CONTINUE.md`

Per this project's `AGENTS.md` "Docs Sync Checker Agent" policy, these five files must reflect the new `save_mode` widget, the preview grid, and the empty `FILENAME`/`FILE_PATH` outputs in `Preview` mode.

- [ ] **Step 1: `CHANGELOG.md`**

Add a new bullet under the existing `## [Unreleased]` / `### Added` section (alongside the `IMAGES` output, format-button, and template-builder entries already there):

```
- `Save`/`Preview` mode toggle. `Save` behaves exactly as before. `Preview` shows the result without writing anything to the final path; each image gets its own `Save` button in a preview grid, writing it later to the path already resolved when the node ran
```

- [ ] **Step 2: `README.md`**

Add a bullet to the `## Why Use It` list, directly after the `Build Path`/`Build Filename` bullet added previously:

```
- a `Preview` mode that shows the result without saving, with a per-image `Save` button when you're ready
```

Add a new section directly after `### Image Format And Quality` and before `### Outputs`:

```
### Save And Preview Modes

`Save` (default) writes every image immediately, exactly as before. `Preview` shows the result the
same way ComfyUI's built-in `Preview Image` node does, without writing anything to the final path.
Each image gets its own `Save` button in the preview grid below the node; clicking it writes that
one image to the path that was already resolved when the node ran. Nothing is written until you
click `Save` on an image, and a parked preview is dropped the next time the node runs or ComfyUI
restarts — there is no separate "discard" action.
```

- [ ] **Step 3: `docs/USAGE.md`**

Add a new section directly after the existing `### Image Quality` section and before `### Loader Priority`:

```
### Save And Preview Modes

`Save` (default) behaves exactly as every earlier version: every image in the batch is written to
its resolved path immediately when the node runs.

`Preview` shows the result without writing to the final path, using ComfyUI's own built-in
temporary-image mechanism (the same one `Preview Image` uses) so nothing new accumulates on disk.
Each image in the batch gets its own `Save` button, shown directly under its thumbnail. Clicking it
writes that image to the path that was already resolved when the node ran, using the `Image Format`,
`Image Quality`, and `Export Workflow Metadata` settings active at that time, not whatever they are
when you click `Save`.

A parked (not-yet-saved) preview is dropped automatically the next time that node runs again, or
when ComfyUI restarts. There is no separate "discard" button.
```

Update the existing `## Outputs` section (the one that currently ends with `` `IMAGES` passes through the full batch.``) by appending one sentence:

```
In `Preview` mode, `FILENAME` and `FILE_PATH` are always empty strings, since nothing is written
until you click `Save` on an image — see Save And Preview Modes above.
```

- [ ] **Step 4: `web/docs/SaveImageClean.md`**

Add a new section directly after the existing `### Loader Priority` section and before `## Outputs`:

```
## Save And Preview Modes

`Save` (default) writes every image immediately. `Preview` shows the result using ComfyUI's own
built-in temporary-image mechanism — nothing new is written to disk — and gives each image its own
`Save` button so you can write it later, to the path already shown when the node ran. A parked
preview disappears the next time the node runs again or ComfyUI restarts; there is no separate
discard action.

`FILENAME`/`FILE_PATH` are empty strings in `Preview` mode, since nothing has been saved yet.
```

- [ ] **Step 5: `CONTINUE.md`**

Remove the now-implemented "Save/Preview mode split" bullet from the `## Deferred Ideas` section (keep the `%node.widget%` chips bullet and everything after it).

Add a new bullet to the "Current State" section, alongside the other not-yet-released feature bullets from this session:

```
- Also unreleased: a `Save`/`Preview` mode toggle (`save_mode` widget, default `Save`, unchanged behavior) per `docs/superpowers/specs/2026-10-12-save-preview-mode-design.md` and `docs/superpowers/plans/2026-10-12-save-preview-mode-split.md`. `Preview` writes nothing to the final path, shows the result via ComfyUI's native temp-image mechanism, and caches pending images in an in-memory, per-node dict (`nodes._PREVIEW_CACHE`); a new `POST /save_image_organized/save_now` route (guarded import, a no-op outside a real ComfyUI install such as pytest) commits one cached image per click from a new per-image Save button in the node's preview grid. Not yet verified against the live ComfyUI install or released.
```

- [ ] **Step 6: Final verification and commit**

Run the full check suite:

```bash
node --check web/save_image_clean.js
.venv-tests/Scripts/python.exe -m py_compile nodes.py
.venv-tests/Scripts/python.exe -m pytest -q
.venv-tests/Scripts/python.exe -m ruff check .
```

Expected: all green, 101 tests passing.

Sync the updated frontend and backend files to the paired local ComfyUI install, then restart it (Python changed this time, unlike the frontend-only Tasks 4-5 — a restart, not just a browser refresh, is required for `nodes.py` changes to take effect):

```bash
cp nodes.py "G:/ComfyUI-Easy-Install/ComfyUI/custom_nodes/save-image-organized/nodes.py"
cp web/save_image_clean.js "G:/ComfyUI-Easy-Install/ComfyUI/custom_nodes/save-image-organized/web/save_image_clean.js"
```

```bash
git add CHANGELOG.md README.md docs/USAGE.md web/docs/SaveImageClean.md CONTINUE.md
git commit -m "Sync docs for the Save/Preview mode split"
```
