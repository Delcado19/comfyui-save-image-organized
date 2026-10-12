# 004 — Floating path-template builder window (click-to-insert variable chips)

- **Status**: DONE
- **Commit**: 90009ad
- **Severity**: HIGH (new capability, maintainer-requested)
- **Category**: Missed opportunities / Physicality & origin (Apple fluid-interface + Emil craft applied to a new surface)
- **Estimated scope**: 1 file (`web/save_image_clean.js`), ~230 new lines, 1 new widget per text field, 1 new lifecycle hook

## Problem

`Save Layout` (`path_template`) and `Filename` (`filename_datetime`) are plain single-line text inputs (`nodes.py:1312-1348`, rendered as native `STRING` widgets with a real `.inputEl` — confirmed by the existing `hookWidgetUpdates` function at `web/save_image_clean.js:1161-1203`, which attaches `input`/`change` listeners directly to `widget.inputEl`). Users must currently type every `%TOKEN%` by hand, with no in-UI reference for the exact catalog of supported variables, filters, and date presets (that catalog exists only in `docs/USAGE.md:203-237,289-303`). The maintainer explicitly requested a point-and-click way to compose these templates, and specified it must live in a **separate floating window**, not inside the node itself, because the node has no spare width for a token palette.

## Target

A new trigger button appended right after each of the two text fields, opening a floating, draggable, non-modal panel (no dimming scrim — this is a parallel, non-blocking tool per Apple's fluid-interface guidance, not a blocking dialog) anchored to the trigger's screen position. Clicking a chip inserts the token at the current caret position of the target field and re-fires that field's existing `input` handling, so the node's own live preview panel (`updateHelp`) updates automatically with zero new synchronization code. The panel's own preview line reuses the existing `buildVariables`/`buildLayoutExample`/`buildFilenameValue` functions verbatim — no duplicated template-rendering logic.

**This plan depends on plan 001** (`--sic-ease-out` / `--sic-ease` custom properties) — apply it first.

### New constants

Insert after the existing `const TEMPLATE_FILTERS = new Set(["lower", "upper", "slug"]);` line (currently `web/save_image_clean.js:134`):

```js
const TEMPLATE_BUILDER_GROUPS = [
    {
        label: "Main",
        tokens: ["TOP_FOLDER", "MODEL_NAME", "TEXT_ENCODER_NAME", "FILENAME", "BATCH"],
    },
    {
        label: "Convenience",
        tokens: [
            "WIDTH", "HEIGHT", "SEED", "STEPS", "CFG", "SAMPLER", "SCHEDULER",
            "DENOISE", "BATCH_INDEX", "BATCH_SIZE",
        ],
    },
    {
        label: "Detailed",
        tokens: [
            "FRIENDLY_MODEL_NAME", "CLEAN_FRIENDLY_MODEL_NAME", "EXACT_MODEL_NAME", "CUSTOM_MODEL_NAME",
            "FRIENDLY_TEXT_ENCODER_NAME", "CLEAN_FRIENDLY_TEXT_ENCODER_NAME", "EXACT_TEXT_ENCODER_NAME",
            "CUSTOM_TEXT_ENCODER_NAME",
        ],
    },
];
const TEMPLATE_BUILDER_FILTERS = ["lower", "upper", "slug"];
const TEMPLATE_BUILDER_DATE_PRESETS = [
    { label: "yyyy-MM-dd", token: "%date:yyyy-MM-dd%" },
    { label: "yyyy-MM-dd_hh-mm-ss", token: "%date:yyyy-MM-dd_hh-mm-ss%" },
    { label: "hh-mm-ss", token: "%date:hh-mm-ss%" },
];
```

These mirror the exact catalog already documented in `docs/USAGE.md:203-237` (Main/Convenience/Detailed groups) and `docs/USAGE.md:289-303` (filters) — do not invent additional tokens beyond what `nodes.py` actually supports.

### New CSS

Insert a new injection function directly after `injectFormatButtonsCss` ends (currently `web/save_image_clean.js:779`):

```js
let _templateBuilderCssInjected = false;
function injectTemplateBuilderCss() {
    if (_templateBuilderCssInjected || document.getElementById("save-image-clean-builder-css")) {
        _templateBuilderCssInjected = true;
        return;
    }
    _templateBuilderCssInjected = true;
    const style = document.createElement("style");
    style.id = "save-image-clean-builder-css";
    style.textContent = [
        ".sic-builder-trigger{margin:2px 8px;padding:4px 8px;font-size:10px;font-weight:600;",
        "border-radius:6px;border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.04);",
        "color:#b7b7b7;cursor:pointer;font-family:inherit;",
        "transition:transform 120ms var(--sic-ease-out), border-color 120ms var(--sic-ease);}",
        ".sic-builder-trigger:hover{border-color:rgba(142,183,255,0.5);color:#e3e3e3;}",
        ".sic-builder-trigger:active{transform:scale(0.97);}",
        ".sic-builder-panel{position:fixed;z-index:10000;width:320px;max-height:420px;",
        "display:flex;flex-direction:column;overflow:hidden;",
        "background:rgba(32,32,36,0.97);border:1px solid rgba(255,255,255,0.12);",
        "border-radius:12px;box-shadow:0 12px 32px rgba(0,0,0,0.45);",
        "color:#e4e4e4;font-family:inherit;",
        "opacity:0;transform:scale(0.95);pointer-events:none;",
        "transition:opacity 200ms var(--sic-ease-out), transform 200ms var(--sic-ease-out);}",
        ".sic-builder-panel.open{opacity:1;transform:scale(1);pointer-events:auto;}",
        ".sic-builder-header{display:flex;align-items:center;justify-content:space-between;",
        "padding:8px 10px;cursor:grab;background:rgba(255,255,255,0.04);",
        "border-bottom:1px solid rgba(255,255,255,0.08);font-size:11px;font-weight:600;}",
        ".sic-builder-close{cursor:pointer;color:#9d9d9d;font-size:14px;line-height:1;background:none;border:none;}",
        ".sic-builder-close:hover{color:#e3e3e3;}",
        ".sic-builder-body{padding:8px 10px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;}",
        ".sic-builder-group-label{font-size:9px;font-weight:700;letter-spacing:0.04em;",
        "text-transform:uppercase;color:#8d8d8d;margin-bottom:4px;}",
        ".sic-builder-chip-row{display:flex;flex-wrap:wrap;gap:4px;}",
        ".sic-builder-chip{padding:3px 7px;font-size:10px;border-radius:5px;",
        "border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.05);color:#cfcfcf;",
        "cursor:pointer;font-family:Consolas,'Courier New',monospace;",
        "transition:transform 120ms var(--sic-ease-out), border-color 120ms var(--sic-ease), color 120ms var(--sic-ease);}",
        ".sic-builder-chip:hover{border-color:rgba(142,183,255,0.5);color:#e3e3e3;}",
        ".sic-builder-chip:active{transform:scale(0.97);}",
        ".sic-builder-preview{margin:4px 10px 10px 10px;padding:8px 10px;border-radius:8px;",
        "background:rgba(0,0,0,0.25);font-family:Consolas,'Courier New',monospace;font-size:11px;",
        "color:#8eb7ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}",
        "@media (prefers-reduced-motion: reduce){",
        ".sic-builder-panel{transition:opacity 200ms linear;transform:none !important;}",
        ".sic-builder-panel.open{transform:none !important;}",
        "}",
    ].join("");
    document.head.appendChild(style);
}
```

Note the entrance/exit uses `scale(0.95) -> scale(1)` + `opacity` (never `scale(0)`, per the audit's physicality rule), `transform-origin` is set dynamically in JS (below) to the trigger's position so the panel visibly grows from the button that opened it, and `prefers-reduced-motion` drops the transform and keeps a plain opacity fade.

### New helper: insert-after widget placement

The file already has `insertWidgetBefore` (`web/save_image_clean.js:150-161`) but nothing to insert *after* a target widget, which this plan needs (the trigger button goes directly after the text field it builds for). Insert directly after `insertWidgetBefore` ends (currently line 161):

```js
function insertWidgetAfter(node, widget, targetName) {
    const widgets = node.widgets || [];
    const widgetIndex = widgets.indexOf(widget);
    const targetIndex = widgets.findIndex((item) => item?.name === targetName);
    if (widgetIndex === -1 || targetIndex === -1 || widgetIndex === targetIndex + 1) {
        return;
    }

    widgets.splice(widgetIndex, 1);
    const newTargetIndex = widgets.findIndex((item) => item?.name === targetName);
    widgets.splice(newTargetIndex + 1, 0, widget);
}
```

This mirrors `insertWidgetBefore`'s exact structure (same guard shape, same splice-then-reinsert approach) — keep it that consistent.

### New helper: token insertion

Insert after `insertWidgetAfter`:

```js
function insertTokenIntoWidget(node, widgetName, token) {
    const widget = getWidget(node, widgetName);
    const inputEl = widget?.inputEl;
    if (!inputEl) {
        return;
    }
    const start = inputEl.selectionStart ?? inputEl.value.length;
    const end = inputEl.selectionEnd ?? inputEl.value.length;
    inputEl.focus();
    inputEl.setRangeText(token, start, end, "end");
    inputEl.dispatchEvent(new Event("input", { bubbles: true }));
}
```

`setRangeText(text, start, end, "end")` is the native `HTMLInputElement` API for inserting text at a position and moving the caret to the end of the inserted text in one call — no manual string splicing. Dispatching a real `input` event means the existing listener installed by `hookWidgetUpdates` (`web/save_image_clean.js:1190-1194`, already attached to `path_template` and `filename_datetime`'s `inputEl`) fires exactly as if the user had typed — this is what refreshes the node's own `Example Output` panel. No new sync code is needed because that listener already exists.

### New panel + trigger widget factory

Insert directly after `createFormatButtonsWidget` ends (currently `web/save_image_clean.js:848`), before `createHelpPanelWidget` begins:

```js
function closeTemplateBuilderPanel(panel) {
    panel.classList.remove("open");
}

function openTemplateBuilderPanel(panel, triggerEl) {
    const rect = triggerEl.getBoundingClientRect();
    const left = Math.min(rect.left, window.innerWidth - 336);
    const top = Math.min(rect.bottom + 6, window.innerHeight - 440);
    panel.style.left = `${Math.max(left, 8)}px`;
    panel.style.top = `${Math.max(top, 8)}px`;
    panel.style.transformOrigin = `${rect.left + rect.width / 2 - left}px 0px`;
    panel.classList.add("open");
}

function makeDraggable(panel, handle) {
    let pointerId = null;
    let startX = 0;
    let startY = 0;
    let originLeft = 0;
    let originTop = 0;

    handle.addEventListener("pointerdown", (event) => {
        if (pointerId !== null) {
            return;
        }
        pointerId = event.pointerId;
        handle.setPointerCapture(pointerId);
        startX = event.clientX;
        startY = event.clientY;
        originLeft = panel.offsetLeft;
        originTop = panel.offsetTop;
    });
    handle.addEventListener("pointermove", (event) => {
        if (event.pointerId !== pointerId) {
            return;
        }
        panel.style.left = `${originLeft + (event.clientX - startX)}px`;
        panel.style.top = `${originTop + (event.clientY - startY)}px`;
    });
    handle.addEventListener("pointerup", (event) => {
        if (event.pointerId !== pointerId) {
            return;
        }
        handle.releasePointerCapture(pointerId);
        pointerId = null;
    });
}

function createTemplateBuilderWidget(node, widgetName, triggerLabel) {
    const targetWidget = getWidget(node, widgetName);
    const storeKey = `__saveImageCleanBuilder_${widgetName}`;
    if (!targetWidget || node[storeKey]) {
        return node[storeKey];
    }

    injectTemplateBuilderCss();

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "sic-builder-trigger";
    trigger.textContent = triggerLabel;

    const panel = document.createElement("div");
    panel.className = "sic-builder-panel";

    const header = document.createElement("div");
    header.className = "sic-builder-header";
    const title = document.createElement("span");
    title.textContent = triggerLabel;
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "sic-builder-close";
    closeBtn.textContent = "✕";
    closeBtn.addEventListener("click", () => closeTemplateBuilderPanel(panel));
    header.appendChild(title);
    header.appendChild(closeBtn);

    const body = document.createElement("div");
    body.className = "sic-builder-body";

    const updatePreview = () => {
        const now = new Date();
        if (widgetName === "filename_datetime") {
            preview.textContent = buildFilenameValue(node, now);
            return;
        }
        const variables = buildVariables(node, now, node.__saveImageCleanLastRunInfo?.detection || null);
        preview.textContent = buildLayoutExample(node, variables, now).path;
    };

    const addChipRow = (label, chips) => {
        const groupLabel = document.createElement("div");
        groupLabel.className = "sic-builder-group-label";
        groupLabel.textContent = label;
        const row = document.createElement("div");
        row.className = "sic-builder-chip-row";
        for (const chip of chips) {
            const chipBtn = document.createElement("button");
            chipBtn.type = "button";
            chipBtn.className = "sic-builder-chip";
            chipBtn.textContent = chip.display;
            chipBtn.title = chip.token;
            chipBtn.addEventListener("click", () => {
                insertTokenIntoWidget(node, widgetName, chip.token);
                updatePreview();
            });
            row.appendChild(chipBtn);
        }
        body.appendChild(groupLabel);
        body.appendChild(row);
    };

    for (const group of TEMPLATE_BUILDER_GROUPS) {
        addChipRow(group.label, group.tokens.map((name) => ({ display: name, token: `%${name}%` })));
    }
    addChipRow("Filters (append to last token)", TEMPLATE_BUILDER_FILTERS.map((name) => ({
        display: `:${name}`,
        token: `:${name}`,
    })));
    addChipRow("Date presets", TEMPLATE_BUILDER_DATE_PRESETS.map((preset) => ({
        display: preset.label,
        token: preset.token,
    })));

    const preview = document.createElement("div");
    preview.className = "sic-builder-preview";

    panel.appendChild(header);
    panel.appendChild(body);
    panel.appendChild(preview);
    document.body.appendChild(panel);
    makeDraggable(panel, header);

    trigger.addEventListener("click", () => {
        if (panel.classList.contains("open")) {
            closeTemplateBuilderPanel(panel);
            return;
        }
        updatePreview();
        openTemplateBuilderPanel(panel, trigger);
    });

    document.addEventListener("pointerdown", (event) => {
        if (!panel.classList.contains("open")) {
            return;
        }
        if (panel.contains(event.target) || trigger.contains(event.target)) {
            return;
        }
        closeTemplateBuilderPanel(panel);
    });

    const widget = node.addDOMWidget(`save_image_clean_builder_trigger_${widgetName}`, "custom", trigger, {
        getMinHeight: () => 22,
        getMaxHeight: () => 24,
        serialize: false,
        hideOnZoom: false,
        margin: 0,
    });

    node[storeKey] = widget;
    node[`${storeKey}_panel`] = panel;
    insertWidgetAfter(node, widget, widgetName);
    return widget;
}
```

`preview` is referenced inside `updatePreview` and `addChipRow` before its own `const preview = ...` line textually appears — this works in the final code because `updatePreview` and the chip click handlers are closures only *called* later (after `preview` exists), and the `const` statement order shown above is the exact order to type it in (JS closures capture the variable, not its value at definition time, so this is correct as written — do not reorder `preview`'s declaration earlier just to "fix" an apparent ordering concern).

### Cleanup on node removal

The floating panels are appended to `document.body`, outside the node's own DOM — if a node is deleted without removing its panel, it leaks forever as an invisible, closed `<div>`. Add an `onRemoved` override inside `app.registerExtension`'s `beforeRegisterNodeDef`, alongside the existing `configure`/`onNodeCreated`/`onExecuted` overrides (`web/save_image_clean.js:1212-1246`):

```js
const onRemoved = nodeType.prototype.onRemoved;
nodeType.prototype.onRemoved = function () {
    const result = onRemoved?.apply(this, arguments);
    this.__saveImageCleanBuilder_path_template_panel?.remove();
    this.__saveImageCleanBuilder_filename_datetime_panel?.remove();
    return result;
};
```

### Wiring

In both the `configure` override and the `onNodeCreated` override (`web/save_image_clean.js:1212-1225` and `1227-1238`), add two calls right before the existing `createHelpPanelWidget(this)` line in each:

```js
createTemplateBuilderWidget(this, "path_template", "Build Path");
createTemplateBuilderWidget(this, "filename_datetime", "Build Filename");
createHelpPanelWidget(this);
```

## Repo conventions to follow

- Every DOM widget in this file follows the same shape: a module-level lazy CSS injector (`inject*Css`), a factory function that early-returns if already built (checked via a `node.__saveImageClean*` property), and registration via `node.addDOMWidget(...)` followed by `insertWidgetBefore`/`insertWidgetAfter`. Follow `createFormatButtonsWidget` (`web/save_image_clean.js:804-848`) as the exemplar — this plan's `createTemplateBuilderWidget` has the identical skeleton.
- `getWidget(node, name)` (`web/save_image_clean.js:137-139`) is the only way this file looks up a widget by name — use it, do not access `node.widgets` positionally.
- Reuse `buildVariables`, `buildLayoutExample`, and `buildFilenameValue` (already defined earlier in this file) for the panel's own preview line — do not reimplement template rendering.
- Out of scope for this plan: dynamic `%node.widget%` chips that introspect the live graph for actual upstream node/widget names. The current catalog only covers the static, always-available variables, filters, and date presets. Adding graph introspection is a natural follow-up but is a separate, larger feature — do not build it as part of this plan.

## Steps

1. Apply plan 001 first.
2. Add the `TEMPLATE_BUILDER_GROUPS` / `TEMPLATE_BUILDER_FILTERS` / `TEMPLATE_BUILDER_DATE_PRESETS` constants after line 134.
3. Add `injectTemplateBuilderCss` after `injectFormatButtonsCss` (after line 779).
4. Add `insertWidgetAfter` after `insertWidgetBefore` (after line 161).
5. Add `insertTokenIntoWidget` after `insertWidgetAfter`.
6. Add `closeTemplateBuilderPanel`, `openTemplateBuilderPanel`, `makeDraggable`, and `createTemplateBuilderWidget` after `createFormatButtonsWidget` ends (after line 848), before `createHelpPanelWidget` begins.
7. Add the `onRemoved` override inside `beforeRegisterNodeDef`, alongside the other lifecycle overrides.
8. Add the two `createTemplateBuilderWidget(...)` calls in both `configure` and `onNodeCreated`, each directly before their existing `createHelpPanelWidget(this)` line.

## Boundaries

- Do NOT implement dynamic `%node.widget%` introspection of the live graph (see "Out of scope" above).
- Do NOT add a "Save All" or bulk-insert control — one chip inserts one token, nothing more.
- Do NOT add a new Python route, a new backend endpoint, or touch `nodes.py` — this is entirely a frontend, client-side feature; no server round-trip is needed to insert a static token string.
- Do NOT add a new npm dependency, bundler, or build step — this file is a plain ES module loaded directly by ComfyUI's frontend, same as today.
- If any referenced line number has drifted from what's quoted above (changes since commit `90009ad`, including from plans 001-003 if applied first), re-locate the anchor by matching the quoted code snippet, not by line number alone, and proceed; if the snippet itself cannot be found at all, STOP and report.

## Verification

- **Mechanical**: `node --check web/save_image_clean.js` must pass.
- **Feel check**: in the paired local ComfyUI install, add a `Save Image Organized` node:
  - Click "Build Path" next to `Save Layout` — the panel should visibly grow from the button's position (not from its own center, not from `scale(0)`), reach full size within ~200ms, and show the current rendered path at the bottom.
  - Click a chip (e.g. `SEED`) — the token should appear in the `Save Layout` field at the cursor position, the field's own value should update, and the node's in-node `Example Output` panel should refresh immediately (proving the dispatched `input` event reached the existing listener).
  - Drag the panel by its header — it should follow the pointer 1:1 with no lag, and stay wherever it's released.
  - Click outside the panel — it should close. Click "Build Path" again — it should reopen in its last-used screen position with the same entrance animation.
  - Open "Build Filename" on the same node — it must be an independent panel from "Build Path" (both can be open at once without interfering).
  - Delete the node from the canvas, then inspect `document.querySelectorAll('.sic-builder-panel')` in DevTools — it must return zero elements (no leaked panel).
  - Toggle `prefers-reduced-motion` (Rendering panel in DevTools) and reopen the panel — it should fade in without the scale/grow motion.
- **Done when**: both trigger buttons work independently, chips insert tokens and refresh the node's own preview, dragging and outside-click-to-close both work, no DOM leak survives node deletion, and `node --check` passes.
