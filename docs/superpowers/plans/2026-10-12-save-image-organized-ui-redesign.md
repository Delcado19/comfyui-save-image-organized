# Save Image Organized UI/UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the `SaveImageClean` node's frontend (`web/save_image_clean.js`) as one coherent, flex-based custom UI — replacing today's widget-by-widget LiteGraph layout, which produces overlap/spacing bugs and a buried Save/Preview toggle — while leaving `nodes.py`'s `INPUT_TYPES` structure and `save_images` signature completely untouched.

**Architecture:** One root `addDOMWidget` per node holding a real CSS flex-column tree. Every row inside it is a reusable component (dropdown row, segmented control, switch, slider row, text row) that reads/writes the *existing* native ComfyUI widget as its data source — the same hide-native-widget-and-draw-a-DOM-row technique `image_format`/`save_mode` already use today, just extended to the rest of the fields and consolidated into one widget instead of many.

**Tech Stack:** Vanilla DOM/CSS, ES modules (ComfyUI already loads `web/save_image_clean.js` as a module — confirmed by its existing `import { app } from "../../scripts/app.js";`). No new dependencies, no build step.

**Spec:** `docs/superpowers/specs/2026-10-12-save-image-organized-ui-redesign-design.md`

## Global Constraints

- `nodes.py` `INPUT_TYPES` keys, order, and types are **not modified** by any task in this plan — this is a frontend-only rewrite (verbatim from the spec's Compatibility section).
- `save_images`' signature is **not modified**.
- Every custom row's control reads/writes the pre-existing native ComfyUI widget object for its field (`getWidget(node, name).value = x; widget.callback?.(x)`) — never a new `node.properties` blob (spec's "Why Pixaroma's state model doesn't fit us").
- Design tokens (spacing/radius/font/accent) are CSS custom properties on `:root`, defined once, reused everywhere — no new hardcoded pixel/color literals once a task introduces the token for that purpose (spec's Design System table).
- No JS unit-test framework exists in this repo (`web/` has no test runner; only `node --check web/save_image_clean.js` validates syntax, and `pytest` covers `nodes.py` only, which this plan never touches). Every task therefore substitutes **`node --check` (syntax) + a precise manual verification checklist in a real running ComfyUI** for the "write a failing test" step — per the spec, an automated check alone is never reported as "visually verified."
- After every task: hard-refresh the browser (`Strg+Shift+R`) and reload the workflow before judging the result — not just a node replace — per the spec's Testing Plan (this session's own caching confusion is the reason this is called out explicitly).
- Live install mirror: after each task's commit, copy `web/save_image_clean.js` (and any new file under `web/`) to `G:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\save-image-organized\web\` before manual verification — this repo's established workflow for testing against the real ComfyUI install (seen throughout this session).
- Keep the file split proposed in Task 2 (`web/sic_components.mjs` for reusable DOM component factories, `web/save_image_clean.js` keeps template-rendering logic, the template-builder panel, and orchestration) — do not invent additional files beyond what a task explicitly creates.

## Review Focus

Five failure modes the spec implies but which don't automatically fall out of "build each component" — each gets its test added to the task that owns the relevant code:

1. **A workflow saved before this redesign still loads correctly** — `widgets_values` positional restore must land every old value on the right field after every native widget is hidden-and-rewrapped, not just the two that were already hidden before this plan. Covered by Task 8's manual verification (load a workflow saved before this plan's changes).
2. ~~Converting a hidden-and-rewrapped widget to a graph input still works (ComfyUI's "Convert to Input")~~ — resolved 2026-10-12 as not applicable: confirmed live that `comfyui_frontend_package` 1.53.10 no longer offers "Convert Widget to Input" in the right-click context menu for ANY widget, including a completely unmodified native `KSampler` node's `sampler_name` combo. This is a platform-wide UI change on this ComfyUI version, not something this redesign's dropdown-row overlay broke. No fix needed; later tasks' verification steps drop this check.
3. **Rapid format toggling (PNG → JPEG → PNG) doesn't leave Image Quality/Export Metadata in a stuck disabled or stuck stale state** — the contextual show/hide must re-evaluate on every change, not just once at node creation. Covered by Task 9's verification.
4. **A very long `path_template` or long detected model/text-encoder name doesn't blow out the node width or get silently clipped with no way to see the rest** — covered by Task 6's verification (paste a 200-character template, confirm `title=` full-value tooltip and no horizontal overflow of the node).
5. **Resizing the node smaller than its content, then larger again, doesn't leave stale/clipped DOM** — floor-only sizing must recover correctly in both directions, not just grow. Covered by Task 10's verification.

---

## Task 1: Verify (and fix if needed) the native-widget-hide and addDOMWidget-rebuild behavior

This blocks every later task: four more fields get hidden-and-rewrapped the same way `save_mode` already is, and the single-root assembly's sizing strategy depends on knowing whether ComfyUI forces the root to `display:block` on rebuild. Both are currently assumptions, not confirmed facts (spec's "Open Items" #1 and #2).

**Files:**
- Modify: `web/save_image_clean.js:844-851` (`hideNativeWidget`), only if investigation shows it needs a fix
- Test: none (investigation + manual verification only)

**Interfaces:**
- Consumes: nothing new
- Produces: a confirmed, documented answer (in this task's commit message and a short note added to the spec's "Open Items" section) for: (a) does `hideNativeWidget` reliably suppress the native row for every combo widget on the user's real ComfyUI frontend version, and (b) does the `addDOMWidget` root get forced to `display:block` on rebuild/collapse. Later tasks build on these answers.

- [ ] **Step 1: Confirm the live install is current**

```bash
diff -q web/save_image_clean.js "/g/ComfyUI-Easy-Install/ComfyUI/custom_nodes/save-image-organized/web/save_image_clean.js"
```
Expected: `identical`. If not, copy the worktree file over before continuing — otherwise the next steps test stale code.

- [ ] **Step 2: Ask the user to hard-refresh and reload the workflow**

This step needs a human with the real ComfyUI browser tab open — stop here and ask them to: open the workflow containing a `SaveImageClean` node, press `Strg+Shift+R`, and confirm the node is still showing the "Save Mode" duplicate row described in the spec's Known Issues section (a second `◀ Save Mode ... Save ▶` row under the Save/Preview pills).

- [ ] **Step 3a: If the duplicate row is GONE after hard refresh**

It was stale browser cache, not a real bug. Record in the spec's "Open Items" section (edit the file, replace item 1 with a one-line resolution note: "Resolved 2026-10-DD: confirmed stale browser cache, not a hideNativeWidget defect — a hard refresh fully suppressed the native save_mode row. No code change needed."). Skip to Step 4.

- [ ] **Step 3b: If the duplicate row is STILL there after hard refresh**

This is a real `hideNativeWidget` defect on the current frontend version. Open the browser devtools console on the node and run:

```js
const node = app.graph.findNodesByType("SaveImageClean")[0];
const w = node.widgets.find(w => w.name === "save_mode");
console.log(w.type, w.computeSize && w.computeSize(0));
```

Expected if the hide call ran: `type` is `"hidden"`, `computeSize(0)` is `[0, -4]`. If both match but the row still renders, the current ComfyUI frontend ("Nodes 2.0") is drawing widgets from a DOM/React layer that no longer respects `widget.type = "hidden"` for suppressing its own row the way the old canvas renderer did. Confirm by checking the installed version:

```bash
cat /g/ComfyUI-Easy-Install/python_embeded/Lib/site-packages/comfyui_frontend_package/package.json 2>/dev/null | grep '"version"'
```

Fix `hideNativeWidget` (`web/save_image_clean.js:840-851`) to also explicitly hide the widget's DOM element when one exists, which is the one thing `type = "hidden"` doesn't reliably cover on newer frontends:

```javascript
function hideNativeWidget(widget) {
    if (!widget || widget.__saveImageCleanHidden) {
        return;
    }
    widget.__saveImageCleanHidden = true;
    widget.computeSize = () => [0, -4];
    widget.type = "hidden";
    // Nodes 2.0's DOM-backed widget renderer can keep painting a widget's own
    // row even after type/computeSize say "hidden" (confirmed on this node's
    // save_mode widget, 2026-10-12) — hiding the element directly closes that
    // gap without touching how the widget itself still holds/serializes value.
    if (widget.element) {
        widget.element.style.display = "none";
    }
}
```

- [ ] **Step 4: Test the addDOMWidget-rebuild gotcha**

Ask the user to resize the `SaveImageClean` node smaller (drag a corner) then collapse it (click the node's collapse circle) then expand it again, while watching the existing "Example Output" panel (any `addDOMWidget` body). Expected if Pixaroma's documented gotcha applies here too: on expand, the panel's content might flash or briefly render unstyled before `display:flex` reapplies, or stay visibly broken. Record the result directly in the spec file, replacing "Open Items" #2 with a resolution note, e.g.: "Resolved 2026-10-DD: confirmed — the root does get forced to display:block on expand-after-collapse on this ComfyUI version. Task 8's root wrapper must use the absolutely-positioned inner-flex-layer escape hatch from the Pixaroma reference." or "...not reproduced on this version; a plain `display:flex` on the addDOMWidget root itself is sufficient, no inner absolute layer needed."

- [ ] **Step 5: Commit**

```bash
git add web/save_image_clean.js docs/superpowers/specs/2026-10-12-save-image-organized-ui-redesign-design.md
git commit -m "Verify native-widget-hide and addDOMWidget-rebuild behavior on the real frontend

Confirms (or fixes) the two assumptions the rest of the UI redesign
depends on: whether hideNativeWidget reliably suppresses a combo
widget's own row, and whether ComfyUI forces addDOMWidget roots back
to display:block on rebuild/collapse. Findings recorded in the spec."
```

---

## Task 2: Design tokens + shared segmented-control factory

**Files:**
- Create: `web/sic_components.mjs`
- Modify: `web/save_image_clean.js:811-965` (replace `createFormatButtonsWidget`/`createSaveModeToggleWidget`'s duplicated button-row code with calls into the new shared factory; keep both functions' current call sites and behavior identical from the node's perspective)
- Test: none (manual verification)

**Interfaces:**
- Produces (from `sic_components.mjs`, consumed by every later task):
  - `export function injectDesignTokens()` — idempotent `:root` CSS variable injection, extends the existing `--sic-ease`/`--sic-ease-out` block
  - `export function el(tag, className, text)` — tiny element-creation helper (`document.createElement` + className + textContent), used by every component factory below to keep them terse
  - `export function buildSegmentedControl(node, widgetName, optionIds, { getTitle } = {})` — returns `{ widget, root, buttons }`; hides the native widget for `widgetName`, builds a `.sic-seg-row` of one button per `optionIds` entry, wires click → `widget.value = id; widget.callback?.(id)`, keeps the active button in sync via a returned `setActive(id)` function attached to the returned object as `.setActive`

- [ ] **Step 1: Create `web/sic_components.mjs` with tokens + `el` + `buildSegmentedControl`**

```javascript
// web/sic_components.mjs
// Reusable DOM-widget component factories for SaveImageClean's node body.
// Every factory here hides the matching native ComfyUI widget (the same
// technique image_format/save_mode already used) and draws a styled DOM row
// in its place; the native widget stays the single source of truth and the
// only thing that gets serialized, so workflow/API compatibility is
// untouched. See docs/superpowers/specs/2026-10-12-save-image-organized-ui-redesign-design.md
// for the full rationale (this file never introduces a parallel state store).

export function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
}

let _tokensInjected = false;
export function injectDesignTokens() {
    if (_tokensInjected || document.getElementById("sic-design-tokens")) {
        _tokensInjected = true;
        return;
    }
    _tokensInjected = true;
    const style = document.createElement("style");
    style.id = "sic-design-tokens";
    style.textContent = [
        ":root{",
        "--sic-ease-out:cubic-bezier(0.23,1,0.32,1);--sic-ease:ease;",
        "--sic-space-sm:4px;--sic-space-md:8px;--sic-space-lg:14px;--sic-space-outer:14px;",
        "--sic-row-height:30px;--sic-btn-min:28px;",
        "--sic-font-base:12px;--sic-font-sub:11px;--sic-font-section:11px;",
        "--sic-radius:7px;--sic-radius-pill:999px;",
        "--sic-accent:#4c86e0;--sic-accent-hover:#5d93e6;",
        "}",
    ].join("");
    document.head.appendChild(style);
}

function getWidget(node, name) {
    return (node.widgets || []).find((widget) => widget.name === name);
}

// Same technique as the pre-existing image_format/save_mode hide, pulled out
// so every component factory below shares one implementation instead of
// five near-duplicates.
export function hideNativeWidget(widget) {
    if (!widget || widget.__saveImageCleanHidden) {
        return;
    }
    widget.__saveImageCleanHidden = true;
    widget.computeSize = () => [0, -4];
    widget.type = "hidden";
    // comfyui_frontend_package 1.53.10 no longer suppresses a widget's own
    // row from widget.type === "hidden" alone (confirmed live, Task 1,
    // 2026-10-12). ComfyUI's own built-in extensions hide widgets via a
    // dedicated `hidden` flag instead - mirrored here.
    widget.hidden = true;
    if (widget.options) {
        widget.options.hidden = true;
    }
}

let _segCssInjected = false;
function injectSegmentedCss() {
    if (_segCssInjected || document.getElementById("sic-seg-css")) {
        _segCssInjected = true;
        return;
    }
    _segCssInjected = true;
    const style = document.createElement("style");
    style.id = "sic-seg-css";
    style.textContent = [
        ".sic-seg-row{display:flex;gap:4px;width:100%;box-sizing:border-box;}",
        ".sic-seg-btn{flex:1;padding:5px 0;min-height:var(--sic-btn-min);font-size:var(--sic-font-base);font-weight:600;",
        "border-radius:var(--sic-radius);border:1px solid rgba(255,255,255,0.14);",
        "background:rgba(255,255,255,0.04);color:#b7b7b7;cursor:pointer;font-family:inherit;",
        "transition:transform 120ms var(--sic-ease-out), background 120ms var(--sic-ease), color 120ms var(--sic-ease), border-color 120ms var(--sic-ease);}",
        ".sic-seg-btn:hover{border-color:rgba(142,183,255,0.5);color:#e3e3e3;}",
        ".sic-seg-btn:active{transform:scale(0.97);}",
        ".sic-seg-btn:focus-visible{outline:2px solid var(--sic-accent);outline-offset:1px;}",
        ".sic-seg-btn.active{background:var(--sic-accent);border-color:var(--sic-accent);color:#fff;}",
        ".sic-seg-btn.active:hover{border-color:var(--sic-accent-hover);}",
    ].join("");
    document.head.appendChild(style);
}

/**
 * One native combo widget (e.g. image_format, save_mode) rendered as a row of
 * equal-width buttons, exactly one active at a time. The native widget stays
 * the data source: a click sets its .value and calls its .callback, so every
 * existing consumer of that widget (hookWidgetUpdates, the Python backend's
 * serialized value) keeps working unchanged.
 */
export function buildSegmentedControl(node, widgetName, optionIds, { getTitle } = {}) {
    const widget = getWidget(node, widgetName);
    if (!widget) {
        return null;
    }
    injectSegmentedCss();
    hideNativeWidget(widget);

    const root = el("div", "sic-seg-row");
    const buttons = {};
    for (const id of optionIds) {
        const button = el("button", "sic-seg-btn", id);
        button.type = "button";
        if (getTitle) {
            button.title = getTitle(id);
        }
        button.addEventListener("click", () => {
            if (widget.value === id) {
                return;
            }
            widget.value = id;
            widget.callback?.(id);
            setActive(id);
        });
        root.appendChild(button);
        buttons[id] = button;
    }

    function setActive(activeId) {
        for (const [id, button] of Object.entries(buttons)) {
            button.classList.toggle("active", id === activeId);
        }
    }
    setActive(widget.value);

    return { widget, root, buttons, setActive };
}
```

- [ ] **Step 2: Run the syntax check**

```bash
node --check web/sic_components.mjs
```
Expected: no output, exit code 0.

- [ ] **Step 3: Replace the duplicated button-row code in `web/save_image_clean.js`**

Replace `IMAGE_FORMAT_IDS`/`SAVE_MODE_IDS` constants, `injectFormatButtonsCss`, `hideNativeWidget`, `setActiveFormatButton`, `createFormatButtonsWidget`, `setActiveSaveModeButton`, `createSaveModeToggleWidget` (`web/save_image_clean.js:811-965`) with:

```javascript
import { el, injectDesignTokens, buildSegmentedControl } from "./sic_components.mjs";

const IMAGE_FORMAT_IDS = ["PNG", "JPEG", "WebP"];
const SAVE_MODE_IDS = ["Save", "Preview"];

function createFormatButtonsWidget(node) {
    if (node.__saveImageCleanFormatWidget) {
        return node.__saveImageCleanFormatWidget;
    }
    injectDesignTokens();
    const seg = buildSegmentedControl(node, "image_format", IMAGE_FORMAT_IDS, {
        getTitle: (id) => `Save as ${id}`,
    });
    if (!seg) {
        return null;
    }
    const widget = node.addDOMWidget("save_image_clean_format_buttons", "custom", seg.root, {
        getMinHeight: () => 26,
        getMaxHeight: () => 28,
        serialize: false,
        hideOnZoom: false,
        margin: 2,
    });
    node.__saveImageCleanFormatWidget = widget;
    node.__saveImageCleanFormatSeg = seg;
    insertWidgetBefore(node, widget, "image_format");
    return widget;
}

function createSaveModeToggleWidget(node) {
    if (node.__saveImageCleanSaveModeWidget) {
        return node.__saveImageCleanSaveModeWidget;
    }
    injectDesignTokens();
    const seg = buildSegmentedControl(node, "save_mode", SAVE_MODE_IDS, {
        getTitle: (id) => (id === "Preview"
            ? "Show the result without saving; save individual images later"
            : "Save immediately, as before"),
    });
    if (!seg) {
        return null;
    }
    const widget = node.addDOMWidget("save_image_clean_save_mode_buttons", "custom", seg.root, {
        getMinHeight: () => 26,
        getMaxHeight: () => 28,
        serialize: false,
        hideOnZoom: false,
        margin: 2,
    });
    node.__saveImageCleanSaveModeWidget = widget;
    node.__saveImageCleanSaveModeSeg = seg;
    insertWidgetBefore(node, widget, "save_mode");
    return widget;
}
```

Keep every other reference to `setActiveFormatButton(node, id)` / `setActiveSaveModeButton(node, id)` elsewhere in the file (there are calls inside `updateHelp`, `web/save_image_clean.js:1597-1598`) working by adding two tiny compatibility wrappers right after the two functions above:

```javascript
function setActiveFormatButton(node, activeId) {
    node.__saveImageCleanFormatSeg?.setActive(activeId);
}

function setActiveSaveModeButton(node, activeId) {
    node.__saveImageCleanSaveModeSeg?.setActive(activeId);
}
```

- [ ] **Step 4: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 5: Manual verification**

Copy both files to the live install, hard-refresh, reload the workflow. Confirm: PNG/JPEG/WebP and Save/Preview still look and behave exactly as before this task (this is a pure refactor — no visual change is expected yet). Click every button in both rows; confirm the active state still highlights correctly and the underlying value still changes (check via the `Ausgabepfad` preview text updating for format, or the devtools console snippet from Task 1 Step 3b for save_mode).

- [ ] **Step 6: Commit**

```bash
git add web/sic_components.mjs web/save_image_clean.js
git commit -m "Extract segmented-control + design-token foundation into sic_components.mjs

Removes the near-duplicate button-row code between the format and
save-mode toggles in favor of one shared buildSegmentedControl
factory, and adds the design-token CSS variables the rest of this
redesign builds on. Pure refactor — no behavior change."
```

---

## Task 3: Dropdown-row component (transparent `<select>` overlay) + apply to five fields

**Files:**
- Modify: `web/sic_components.mjs` (add `buildDropdownRow`)
- Modify: `web/save_image_clean.js` (new `createDropdownRowWidget` wrapper + 5 call sites, replacing the native rendering for `model_source`, `clip_source`, `collision_mode`, `detection_info`, `loader_priority` — `loader_priority`'s row is built here but not yet placed in the UI; Task 7 mounts it inside the gear panel)
- Test: none (manual verification)

**Interfaces:**
- Consumes: `el`, `injectDesignTokens`, `hideNativeWidget` from Task 2
- Produces: `export function buildDropdownRow(node, widgetName, label, optionIds, { optionLabels } = {})` in `sic_components.mjs` — returns `{ widget, root, selectEl, valueEl }`; `root` is the full row (label + value + chevron + invisible `<select>` on top), `selectEl` is the real native `<select>` (keeps keyboard/scroll-wheel/OS dropdown list working, satisfies spec's A §4.4 "vollständige Tastaturbedienbarkeit")

- [ ] **Step 1: Add `buildDropdownRow` to `web/sic_components.mjs`**

```javascript
let _dropdownCssInjected = false;
function injectDropdownCss() {
    if (_dropdownCssInjected || document.getElementById("sic-dropdown-css")) {
        _dropdownCssInjected = true;
        return;
    }
    _dropdownCssInjected = true;
    const style = document.createElement("style");
    style.id = "sic-dropdown-css";
    style.textContent = [
        ".sic-row{position:relative;display:flex;align-items:center;justify-content:space-between;",
        "min-height:var(--sic-row-height);padding:0 var(--sic-space-md);gap:var(--sic-space-sm);",
        "border-radius:var(--sic-radius);box-sizing:border-box;}",
        ".sic-row:hover{background:rgba(255,255,255,0.03);}",
        ".sic-row-label{font-size:var(--sic-font-base);color:#d7d7d7;pointer-events:none;}",
        ".sic-row-value{display:flex;align-items:center;gap:4px;font-size:var(--sic-font-base);",
        "color:#b7b7b7;pointer-events:none;white-space:nowrap;}",
        ".sic-row-chevron{font-size:9px;opacity:0.7;}",
        ".sic-row-select{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer;",
        "border:none;margin:0;padding:0;font-size:var(--sic-font-base);}",
        ".sic-row-select:focus-visible ~ .sic-row-value,",
        ".sic-row:has(.sic-row-select:focus-visible){outline:2px solid var(--sic-accent);outline-offset:-2px;border-radius:var(--sic-radius);}",
        ".sic-row.disabled{opacity:0.45;}",
        ".sic-row.disabled .sic-row-select{pointer-events:none;}",
    ].join("");
    document.head.appendChild(style);
}

function getWidget2(node, name) {
    return (node.widgets || []).find((widget) => widget.name === name);
}

/**
 * One native combo widget rendered as a flat "Label ... Value v" row. A real,
 * fully transparent <select> sits on top of the row and does the actual work
 * (keyboard nav, scroll-wheel, the OS's own dropdown list) — only its paint
 * is hidden, so this keeps full native accessibility instead of hand-rolling
 * a listbox. The native combo widget stays the data source.
 */
export function buildDropdownRow(node, widgetName, label, optionIds, { optionLabels } = {}) {
    const widget = getWidget2(node, widgetName);
    if (!widget) {
        return null;
    }
    injectDesignTokens();
    injectDropdownCss();
    hideNativeWidget(widget);

    const root = el("div", "sic-row");
    const labelEl = el("span", "sic-row-label", label);
    const valueWrap = el("span", "sic-row-value");
    const valueText = el("span");
    const chevron = el("span", "sic-row-chevron", "\u25BE");
    valueWrap.appendChild(valueText);
    valueWrap.appendChild(chevron);

    const select = document.createElement("select");
    select.className = "sic-row-select";
    for (const id of optionIds) {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = optionLabels?.[id] || id;
        select.appendChild(option);
    }
    select.value = widget.value;

    const render = () => {
        valueText.textContent = optionLabels?.[widget.value] || widget.value;
    };
    render();

    select.addEventListener("change", () => {
        if (widget.value === select.value) {
            return;
        }
        widget.value = select.value;
        widget.callback?.(select.value);
        render();
    });

    root.appendChild(labelEl);
    root.appendChild(valueWrap);
    root.appendChild(select);

    return { widget, root, selectEl: select, valueEl: valueText };
}
```

- [ ] **Step 2: Run the syntax check**

```bash
node --check web/sic_components.mjs
```
Expected: no output, exit code 0.

- [ ] **Step 3: Add `createDropdownRowWidget` and the five call sites in `web/save_image_clean.js`**

Add near `createFormatButtonsWidget` (after Task 2's edits):

```javascript
import { buildDropdownRow } from "./sic_components.mjs";

const DROPDOWN_FIELDS = {
    model_source: { label: "Model Name", options: MODEL_OPTIONS },
    clip_source: { label: "Text Encoder", options: CLIP_OPTIONS },
    collision_mode: {
        label: "If File Exists",
        options: ["increment", "overwrite", "error", "seconds"],
        optionLabels: {
            increment: "Increment number",
            overwrite: "Overwrite",
            error: "Error",
            seconds: "Add seconds",
        },
    },
    detection_info: {
        label: "Detection Info",
        options: ["Off", "Summary", "Verbose"],
    },
    loader_priority: {
        label: "Loader Priority",
        options: ["Nearest", "First Used"],
    },
};

function createDropdownRowWidget(node, widgetName) {
    const storeKey = `__saveImageCleanDropdown_${widgetName}`;
    if (node[storeKey]) {
        return node[storeKey];
    }
    const field = DROPDOWN_FIELDS[widgetName];
    const row = buildDropdownRow(node, widgetName, field.label, field.options, {
        optionLabels: field.optionLabels,
    });
    if (!row) {
        return null;
    }
    const widget = node.addDOMWidget(`save_image_clean_dropdown_${widgetName}`, "custom", row.root, {
        getMinHeight: () => 30,
        getMaxHeight: () => 32,
        serialize: false,
        hideOnZoom: false,
        margin: 0,
    });
    node[storeKey] = { widget, row };
    insertWidgetBefore(node, widget, widgetName);
    return node[storeKey];
}
```

`MODEL_OPTIONS`/`CLIP_OPTIONS` already exist at `web/save_image_clean.js:5-6` — reused here rather than redefined.

This task only creates the component and the five entries; it does not yet remove the old friendly-label-only rendering those widgets got via `setFriendlyLabels` (`web/save_image_clean.js:170-177`). Task 8 (single-root assembly) is what actually calls `createDropdownRowWidget` for each of the five fields and places them in the final layout — building the component here, wiring it up there, keeps this task's diff reviewable on its own (the component in isolation) without a half-migrated node in between.

- [ ] **Step 4: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 5: Manual verification (temporary call, removed again after checking)**

Temporarily add `createDropdownRowWidget(this, "model_source");` right after `createSaveModeToggleWidget(this);` in both `onNodeCreated` and `configure` (`web/save_image_clean.js:1718`/`1737` after Task 2's edits), copy to the live install, hard-refresh, reload the workflow. Confirm: a "Model Name ... Friendly ⌄" row appears, clicking it opens the real OS dropdown list with all 4 options, selecting one updates the row's text, and right-clicking the row still offers ComfyUI's "Convert to Input" context menu option (Review Focus item 2). Then remove the temporary call — Task 8 is what wires this in for real.

- [ ] **Step 6: Commit**

```bash
git add web/sic_components.mjs web/save_image_clean.js
git commit -m "Add dropdown-row component for the five remaining combo widgets

Transparent native <select> overlay keeps full keyboard/scroll-wheel/
OS-dropdown-list behavior and Convert-to-Input support, while the
visible row matches the segmented controls' design language. Not yet
wired into the node body — Task 8 does that as part of the single-
root assembly."
```

---

## Task 4: Switch component + apply to Export Workflow Metadata

**Files:**
- Modify: `web/sic_components.mjs` (add `buildSwitchRow`)
- Modify: `web/save_image_clean.js` (add `createSwitchRowWidget` wrapper, not yet wired into the layout — same staged pattern as Task 3)
- Test: none (manual verification)

**Interfaces:**
- Consumes: `el`, `injectDesignTokens`, `hideNativeWidget`
- Produces: `export function buildSwitchRow(node, widgetName, label)` in `sic_components.mjs` — returns `{ widget, root, checkboxEl }`

- [ ] **Step 1: Add `buildSwitchRow` to `web/sic_components.mjs`**

```javascript
let _switchCssInjected = false;
function injectSwitchCss() {
    if (_switchCssInjected || document.getElementById("sic-switch-css")) {
        _switchCssInjected = true;
        return;
    }
    _switchCssInjected = true;
    const style = document.createElement("style");
    style.id = "sic-switch-css";
    style.textContent = [
        ".sic-switch-track{position:relative;width:34px;height:18px;border-radius:9px;",
        "background:#555;flex:0 0 auto;transition:background 150ms var(--sic-ease);pointer-events:none;}",
        ".sic-switch-track::after{content:\"\";position:absolute;top:2px;left:2px;width:14px;height:14px;",
        "border-radius:50%;background:#ccc;transition:left 150ms var(--sic-ease);}",
        ".sic-switch-track.on{background:var(--sic-accent);}",
        ".sic-switch-track.on::after{left:18px;background:#fff;}",
        ".sic-row-checkbox{position:absolute;inset:0;width:100%;height:100%;opacity:0;",
        "cursor:pointer;margin:0;}",
    ].join("");
    document.head.appendChild(style);
}

function getWidget3(node, name) {
    return (node.widgets || []).find((widget) => widget.name === name);
}

/**
 * One native BOOLEAN widget rendered as a label + pill switch. A real,
 * fully transparent <input type=checkbox> handles click/keyboard/focus; the
 * visible track is pure decoration driven off its checked state.
 */
export function buildSwitchRow(node, widgetName, label) {
    const widget = getWidget3(node, widgetName);
    if (!widget) {
        return null;
    }
    injectDesignTokens();
    injectSwitchCss();
    hideNativeWidget(widget);

    const root = el("div", "sic-row");
    root.style.position = "relative";
    const labelEl = el("span", "sic-row-label", label);
    const track = el("span", "sic-switch-track");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "sic-row-checkbox";
    checkbox.checked = Boolean(widget.value);

    const render = () => {
        track.classList.toggle("on", Boolean(widget.value));
    };
    render();

    checkbox.addEventListener("change", () => {
        widget.value = checkbox.checked;
        widget.callback?.(checkbox.checked);
        render();
    });

    root.appendChild(labelEl);
    root.appendChild(track);
    root.appendChild(checkbox);

    return { widget, root, checkboxEl: checkbox };
}
```

- [ ] **Step 2: Run the syntax check**

```bash
node --check web/sic_components.mjs
```
Expected: no output, exit code 0.

- [ ] **Step 3: Add `createSwitchRowWidget` in `web/save_image_clean.js`**

```javascript
import { buildSwitchRow } from "./sic_components.mjs";

function createSwitchRowWidget(node, widgetName, label) {
    const storeKey = `__saveImageCleanSwitch_${widgetName}`;
    if (node[storeKey]) {
        return node[storeKey];
    }
    const row = buildSwitchRow(node, widgetName, label);
    if (!row) {
        return null;
    }
    const widget = node.addDOMWidget(`save_image_clean_switch_${widgetName}`, "custom", row.root, {
        getMinHeight: () => 30,
        getMaxHeight: () => 32,
        serialize: false,
        hideOnZoom: false,
        margin: 0,
    });
    node[storeKey] = { widget, row };
    insertWidgetBefore(node, widget, widgetName);
    return node[storeKey];
}
```

- [ ] **Step 4: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 5: Manual verification (temporary call)**

Temporarily call `createSwitchRowWidget(this, "export_workflow_metadata", "Export Workflow Metadata");` in `onNodeCreated`, copy to the live install, hard-refresh. Confirm: a labeled pill switch appears, click toggles it, drag-and-drop a PNG saved with this node back into ComfyUI still reloads the workflow only when the switch was on at save time (confirms the underlying boolean widget value is really being written, not just the visual track). Remove the temporary call afterward.

- [ ] **Step 6: Commit**

```bash
git add web/sic_components.mjs web/save_image_clean.js
git commit -m "Add switch-row component for Export Workflow Metadata

Replaces the native BOOLEAN widget's low-contrast rendering (flagged
in the design spec from the default-width screenshot) with a labeled
pill switch, keyboard-accessible via a transparent native checkbox.
Not yet wired into the node body."
```

---

## Task 5: Slider-row component + apply to Image Quality

**Files:**
- Modify: `web/sic_components.mjs` (add `buildSliderRow`)
- Modify: `web/save_image_clean.js` (add `createSliderRowWidget` wrapper, staged, not yet wired)
- Test: none (manual verification)

**Interfaces:**
- Consumes: `el`, `injectDesignTokens`, `hideNativeWidget`
- Produces: `export function buildSliderRow(node, widgetName, label, { min, max } = {})` in `sic_components.mjs` — returns `{ widget, root, inputEl, valueEl }`

- [ ] **Step 1: Add `buildSliderRow` to `web/sic_components.mjs`**

```javascript
let _sliderCssInjected = false;
function injectSliderCss() {
    if (_sliderCssInjected || document.getElementById("sic-slider-css")) {
        _sliderCssInjected = true;
        return;
    }
    _sliderCssInjected = true;
    const style = document.createElement("style");
    style.id = "sic-slider-css";
    style.textContent = [
        ".sic-slider-row{display:flex;flex-direction:column;gap:2px;",
        "padding:4px var(--sic-space-md);box-sizing:border-box;}",
        ".sic-slider-head{display:flex;align-items:center;justify-content:space-between;}",
        ".sic-slider-label{font-size:var(--sic-font-base);color:#d7d7d7;}",
        ".sic-slider-value{font-size:var(--sic-font-base);color:var(--sic-accent);min-width:26px;text-align:right;}",
        ".sic-slider-input{width:100%;accent-color:var(--sic-accent);}",
        ".sic-slider-row.disabled{opacity:0.45;pointer-events:none;}",
    ].join("");
    document.head.appendChild(style);
}

function getWidget4(node, name) {
    return (node.widgets || []).find((widget) => widget.name === name);
}

/**
 * One native INT-slider widget rendered via a real <input type=range>,
 * directly CSS-styleable (accent-color), so no transparent-overlay trick is
 * needed the way combo/boolean widgets require.
 */
export function buildSliderRow(node, widgetName, label, { min = 1, max = 100 } = {}) {
    const widget = getWidget4(node, widgetName);
    if (!widget) {
        return null;
    }
    injectDesignTokens();
    injectSliderCss();
    hideNativeWidget(widget);

    const root = el("div", "sic-slider-row");
    const head = el("div", "sic-slider-head");
    const labelEl = el("span", "sic-slider-label", label);
    const valueEl = el("span", "sic-slider-value", String(widget.value));
    head.appendChild(labelEl);
    head.appendChild(valueEl);

    const input = document.createElement("input");
    input.type = "range";
    input.className = "sic-slider-input";
    input.min = String(min);
    input.max = String(max);
    input.value = String(widget.value);

    input.addEventListener("input", () => {
        const next = Number(input.value);
        widget.value = next;
        widget.callback?.(next);
        valueEl.textContent = String(next);
    });

    root.appendChild(head);
    root.appendChild(input);

    return { widget, root, inputEl: input, valueEl };
}
```

- [ ] **Step 2: Run the syntax check**

```bash
node --check web/sic_components.mjs
```
Expected: no output, exit code 0.

- [ ] **Step 3: Add `createSliderRowWidget` in `web/save_image_clean.js`**

```javascript
import { buildSliderRow } from "./sic_components.mjs";

function createSliderRowWidget(node, widgetName, label, opts) {
    const storeKey = `__saveImageCleanSlider_${widgetName}`;
    if (node[storeKey]) {
        return node[storeKey];
    }
    const row = buildSliderRow(node, widgetName, label, opts);
    if (!row) {
        return null;
    }
    const widget = node.addDOMWidget(`save_image_clean_slider_${widgetName}`, "custom", row.root, {
        getMinHeight: () => 40,
        getMaxHeight: () => 44,
        serialize: false,
        hideOnZoom: false,
        margin: 0,
    });
    node[storeKey] = { widget, row };
    insertWidgetBefore(node, widget, widgetName);
    return node[storeKey];
}
```

- [ ] **Step 4: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 5: Manual verification (temporary call)**

Temporarily call `createSliderRowWidget(this, "image_quality", "Image Quality", { min: 1, max: 100 });` in `onNodeCreated`, copy to the live install, hard-refresh. Confirm: a label + numeric readout + styled range input appears, dragging it updates the number live, set it to 50, switch `image_format` to JPEG and run the workflow once, confirm the saved JPEG's actual file size reflects quality 50 (not silently still 95) — proves the native widget's value is really being written. Remove the temporary call afterward.

- [ ] **Step 6: Commit**

```bash
git add web/sic_components.mjs web/save_image_clean.js
git commit -m "Add slider-row component for Image Quality

Styled native <input type=range> (CSS accent-color, no overlay trick
needed) replaces the canvas-drawn slider so it matches the rest of
the redesigned rows. Not yet wired into the node body."
```

---

## Task 6: Text-row component + apply to Save Layout, Filename, Top Folder, Custom Names

**Files:**
- Modify: `web/sic_components.mjs` (add `buildTextRow`)
- Modify: `web/save_image_clean.js` (add `createTextRowWidget` wrapper, staged)
- Test: none (manual verification)

**Interfaces:**
- Consumes: `el`, `injectDesignTokens`, `hideNativeWidget`
- Produces: `export function buildTextRow(node, widgetName, { placeholder } = {})` in `sic_components.mjs` — returns `{ widget, root, inputEl }`. Reuses the native STRING widget's real `<input>` element as-is (not replaced), but — unlike the original version of this note — **does** call `hideNativeWidget(widget)` like every other row. Live-verified during Task 6: leaving the native widget un-hidden kept it active in ComfyUI's per-frame widget-position loop, which fought with this row's own `addDOMWidget` position updates over the same reused `<input>` and made drag/resize of every node on the canvas choppy for several seconds after load. `hideNativeWidget` only flips layout/sizing flags on the widget object (`computeSize`, `type`, `hidden`) — it never touches `widget.inputEl` itself — so the native text-editing behavior (cursor, selection, keyboard nav) is unaffected; only the competing position updates stop.
- `hideNativeWidget` has a second side effect live-verified during Task 6: comfyui_frontend_package 1.53.10 reads it as "this widget has no live DOM element" and falls back to its own canvas-level hover tooltip, which reads `nodes.py`'s static `INPUT_TYPES` description (e.g. "Main save layout...") instead of this row's `title=` tooltip. That canvas tooltip checks the widget's own `.tooltip` instance property before the static description, so `buildTextRow` mirrors the live value onto `widget.tooltip` (not just `inputEl.title`) — fixes both tooltip paths regardless of which one wins the hover.

- [ ] **Step 1: Add `buildTextRow` to `web/sic_components.mjs`**

```javascript
let _textRowCssInjected = false;
function injectTextRowCss() {
    if (_textRowCssInjected || document.getElementById("sic-textrow-css")) {
        _textRowCssInjected = true;
        return;
    }
    _textRowCssInjected = true;
    const style = document.createElement("style");
    style.id = "sic-textrow-css";
    style.textContent = [
        ".sic-text-row{padding:0 var(--sic-space-md);box-sizing:border-box;}",
        ".sic-text-input{width:100%;box-sizing:border-box;min-height:var(--sic-row-height);",
        "padding:0 8px;font-size:var(--sic-font-base);font-family:Consolas,'Courier New',monospace;",
        "color:#f0f0f0;background:rgba(0,0,0,0.18);border:1px solid rgba(255,255,255,0.1);",
        "border-radius:var(--sic-radius);outline:none;overflow:hidden;text-overflow:ellipsis;",
        "transition:border-color 120ms var(--sic-ease);}",
        ".sic-text-input:focus{border-color:var(--sic-accent);}",
    ].join("");
    document.head.appendChild(style);
}

function getWidget5(node, name) {
    return (node.widgets || []).find((widget) => widget.name === name);
}

/**
 * Wraps an EXISTING native STRING widget's real <input> element (ComfyUI
 * already gives text widgets a real DOM input) in a styled row that also
 * shows the full value as a title= tooltip and never clips with no way to
 * see the rest, resolving the "Save Layout truncated" complaint without
 * replacing the native text-editing behavior at all.
 *
 * hideNativeWidget() still runs here even though the native widget's real
 * DOM input is reused as-is (not hidden visually) - the native STRING
 * widget keeps re-positioning that same <input> every frame during node
 * drag/resize unless its own widget entry is marked hidden, which fights
 * with this row's own addDOMWidget position updates and made every node's
 * drag/resize choppy for several seconds after load (confirmed live by
 * removing just this wiring and seeing it clear up).
 *
 * hideNativeWidget() also drops comfyui_frontend_package 1.53.10's own
 * marker for "this widget has a live DOM element", so hovering this row
 * falls back to the canvas-level widget tooltip (which reads nodes.py's
 * static INPUT_TYPES description, e.g. "Main save layout...") instead of
 * this <input>'s native title= tooltip - confirmed live: hovering showed
 * the static description, not the path. That fallback tooltip checks the
 * widget's own `.tooltip` property FIRST, before the static description,
 * so mirroring the live value onto `widget.tooltip` (not just inputEl's
 * title=) fixes both tooltip paths at once regardless of which one wins
 * the hover.
 */
export function buildTextRow(node, widgetName, { placeholder } = {}) {
    const widget = getWidget5(node, widgetName);
    if (!widget || !widget.inputEl) {
        return null;
    }
    injectDesignTokens();
    injectTextRowCss();
    hideNativeWidget(widget);

    const root = el("div", "sic-text-row");
    const inputEl = widget.inputEl;
    inputEl.classList.add("sic-text-input");
    if (placeholder) {
        inputEl.placeholder = placeholder;
    }

    const syncTitle = () => {
        inputEl.title = inputEl.value;
        widget.tooltip = inputEl.value;
    };
    syncTitle();
    inputEl.addEventListener("input", syncTitle);

    root.appendChild(inputEl);
    return { widget, root, inputEl };
}
```

Note for the implementer: `widget.inputEl` only exists once ComfyUI has created the widget's backing `<input>` — confirmed already true for every STRING widget in this node today (`insertTokenIntoWidget`, `web/save_image_clean.js:192-203`, already reads `widget?.inputEl` the same way). If a future ComfyUI version stops eagerly creating it, this function's `!widget.inputEl` guard returns `null` safely rather than throwing — verify this against the real node in Step 5 below, don't assume.

- [ ] **Step 2: Run the syntax check**

```bash
node --check web/sic_components.mjs
```
Expected: no output, exit code 0.

- [ ] **Step 3: Add `createTextRowWidget` in `web/save_image_clean.js`**

```javascript
import { buildTextRow } from "./sic_components.mjs";

function createTextRowWidget(node, widgetName, opts) {
    const storeKey = `__saveImageCleanTextRow_${widgetName}`;
    if (node[storeKey]) {
        return node[storeKey];
    }
    const row = buildTextRow(node, widgetName, opts);
    if (!row) {
        return null;
    }
    const widget = node.addDOMWidget(`save_image_clean_textrow_${widgetName}`, "custom", row.root, {
        getMinHeight: () => 34,
        getMaxHeight: () => 36,
        serialize: false,
        hideOnZoom: false,
        margin: 0,
    });
    node[storeKey] = { widget, row };
    insertWidgetBefore(node, widget, widgetName);
    return node[storeKey];
}
```

- [ ] **Step 4: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 5: Manual verification (temporary call)**

Temporarily call `createTextRowWidget(this, "path_template");` in `onNodeCreated`, copy to the live install, hard-refresh. Confirm `widget.inputEl` exists and the row renders. Paste a 200-character template string into the field; confirm: it no longer clips with no indication there's more (ellipsis + hovering shows the full string via the `title` tooltip), the cursor still moves correctly through the whole string with arrow keys, and the Build-panel preview (Task 3's existing template-builder trigger) still stays in sync. Remove the temporary call afterward.

- [ ] **Step 6: Commit**

```bash
git add web/sic_components.mjs web/save_image_clean.js
git commit -m "Add text-row component for Save Layout, Filename, and the Top/Custom Name fields

Wraps the existing native STRING widget input (not replaced, per the
spec: it already supports full cursor navigation while focused) in a
styled row with a title= tooltip for the full value, fixing the
resting-state truncation the design brief flagged.

hideNativeWidget() is called here too (deviates from the original
brief) because leaving the native widget un-hidden kept it in
ComfyUI's per-frame widget-position loop, fighting this row's own
addDOMWidget position updates and making drag/resize of every node
on the canvas choppy. Hiding it also drops comfyui_frontend_package
1.53.10's live-DOM-element marker, so hover fell back to the native
INPUT_TYPES description instead of this row's title= tooltip; mirrors
the live value onto widget.tooltip too so both tooltip paths agree.
Not yet wired into the node body."
```

---

## Task 7: Gear/Advanced floating panel + apply to Loader Priority

**Files:**
- Modify: `web/save_image_clean.js` (new `createAdvancedPanel` function, reusing the existing floating-panel CSS/positioning/drag mechanism already built for the template builder, `web/save_image_clean.js:1125-1341`)
- Test: none (manual verification)

**Interfaces:**
- Consumes: `createDropdownRowWidget`'s underlying `buildDropdownRow` (Task 3) for the Loader Priority row's content; the existing `openTemplateBuilderPanel`-style positioning/`makeDraggable` pattern (reused, not reimplemented — see Step 1)
- Produces: `function createAdvancedPanel(node)` — returns `{ trigger, panel }`; `trigger` is a small gear-icon button meant to sit in a section heading row (consumed by Task 8)

- [ ] **Step 1: Add shared floating-panel CSS and `createAdvancedPanel` in `web/save_image_clean.js`**

The existing `injectTemplateBuilderCss` (`web/save_image_clean.js:1126-1174`) already defines `.sic-builder-panel`/`.sic-builder-header`/`.sic-builder-close` and the reduced-motion handling — reused as-is for the Advanced panel rather than duplicated, since the visual language (floating, draggable, outside-click-to-close) is identical. Add a new, Pixaroma-row-styled body:

```javascript
let _advancedPanelCssInjected = false;
function injectAdvancedPanelCss() {
    if (_advancedPanelCssInjected || document.getElementById("sic-advanced-css")) {
        _advancedPanelCssInjected = true;
        return;
    }
    _advancedPanelCssInjected = true;
    const style = document.createElement("style");
    style.id = "sic-advanced-css";
    style.textContent = [
        ".sic-adv-trigger{flex:none;width:24px;height:24px;border-radius:var(--sic-radius);",
        "border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.04);",
        "color:#b7b7b7;cursor:pointer;font-size:13px;line-height:1;",
        "transition:transform 120ms var(--sic-ease-out), border-color 120ms var(--sic-ease), color 120ms var(--sic-ease);}",
        ".sic-adv-trigger:hover{border-color:rgba(142,183,255,0.5);color:#e3e3e3;}",
        ".sic-adv-trigger:active{transform:scale(0.95);}",
        ".sic-adv-row{display:flex;flex-direction:column;gap:3px;padding:6px 0;}",
        ".sic-adv-row-head{display:flex;align-items:center;justify-content:space-between;}",
        ".sic-adv-row-label{font-size:12px;font-weight:600;color:#e4e4e4;}",
        ".sic-adv-row-desc{font-size:10px;line-height:1.4;color:#8f8f8f;}",
    ].join("");
    document.head.appendChild(style);
}

function createAdvancedPanel(node) {
    if (node.__saveImageCleanAdvancedPanel) {
        return node.__saveImageCleanAdvancedPanel;
    }
    injectDesignTokens();
    injectTemplateBuilderCss();
    injectAdvancedPanelCss();

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "sic-adv-trigger";
    trigger.textContent = "\u2699"; // gear
    trigger.title = "Advanced settings";

    const panel = document.createElement("div");
    panel.className = "sic-builder-panel";

    const header = document.createElement("div");
    header.className = "sic-builder-header";
    const title = document.createElement("span");
    title.textContent = "Advanced Settings";
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "sic-builder-close";
    closeBtn.textContent = "\u2715";
    closeBtn.addEventListener("click", () => closeTemplateBuilderPanel(panel));
    header.appendChild(title);
    header.appendChild(closeBtn);

    const body = document.createElement("div");
    body.className = "sic-builder-body";

    const loaderRow = document.createElement("div");
    loaderRow.className = "sic-adv-row";
    const loaderHead = document.createElement("div");
    loaderHead.className = "sic-adv-row-head";
    const loaderDropdown = buildDropdownRow(node, "loader_priority", "Loader Priority", ["Nearest", "First Used"]);
    if (loaderDropdown) {
        loaderHead.appendChild(loaderDropdown.root);
    }
    const loaderDesc = document.createElement("div");
    loaderDesc.className = "sic-adv-row-desc";
    loaderDesc.textContent =
        "How to pick a model/text-encoder when more than one loader feeds this save. " +
        "Nearest picks the loader with the fewest upstream links (right for most single-pass " +
        "workflows). First Used picks the loader furthest upstream, i.e. the first one applied " +
        "in a multi-stage pipeline such as a base pass refined by a second model.";
    loaderRow.appendChild(loaderHead);
    loaderRow.appendChild(loaderDesc);
    body.appendChild(loaderRow);

    panel.appendChild(header);
    panel.appendChild(body);
    document.body.appendChild(panel);
    makeDraggable(panel, header);

    trigger.addEventListener("click", () => {
        if (panel.classList.contains("open")) {
            closeTemplateBuilderPanel(panel);
            return;
        }
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

    node.__saveImageCleanAdvancedPanel = { trigger, panel };
    return node.__saveImageCleanAdvancedPanel;
}
```

The loader-priority description text above is copied verbatim from the existing `nodes.py:1563-1568` tooltip, per the spec's instruction to surface it as a visible description line instead of only a hover title.

- [ ] **Step 2: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 3: Manual verification (temporary mount)**

Temporarily append `document.body.appendChild(createAdvancedPanel(this).trigger)` style test — simplest is to temporarily call `const adv = createAdvancedPanel(this); node.widgets[0].element?.parentElement?.prepend(adv.trigger);` right after `createSaveModeToggleWidget(this);` in `onNodeCreated`, purely to get the gear button on-screen for this check (Task 8 mounts it properly). Copy to the live install, hard-refresh. Click the gear icon: confirm the panel opens near the trigger, is draggable by its header, shows "Loader Priority" with the full description text, clicking Nearest/First Used changes the value, clicking outside or the × closes it. Remove the temporary mount line afterward.

- [ ] **Step 4: Commit**

```bash
git add web/save_image_clean.js
git commit -m "Add Advanced-settings gear panel for Loader Priority

Reuses the existing floating-panel/drag/outside-click mechanism built
for the template builder. Row style (label + visible description +
control) follows the Pixaroma reference confirmed live this session.
Not yet mounted in the node body."
```

---

## Task 8: Single root-widget assembly

This is where every component from Tasks 2–7 gets composed into the one flex tree, in the target information architecture, replacing the current sequence of independent `addDOMWidget` calls.

**Files:**
- Modify: `web/save_image_clean.js:1702-1762` (`app.registerExtension`'s `onNodeCreated`/`configure`) and the functions they call
- Test: none (manual verification, Review Focus items 1 and 2)

**Interfaces:**
- Consumes: every factory from Tasks 2–7 (`createFormatButtonsWidget`, `createSaveModeToggleWidget`, `createDropdownRowWidget`, `createSwitchRowWidget`, `createSliderRowWidget`, `createTextRowWidget`, `createAdvancedPanel`), plus the existing `createTemplateBuilderWidget`, `createPreviewGridWidget`/`updatePreviewGrid`, `createHelpPanelWidget`/`updateHelp` (kept, but their *mounting* changes — their internal DOM-building logic for the preview grid cells and the 3-state Ausgabepfad badge stays exactly as implemented, per the spec)
- Produces: `function buildNodeUI(node)` — the new single entry point `onNodeCreated`/`configure` call instead of today's eight separate calls

- [ ] **Step 1: Write `buildNodeUI`**

Add this function, and the supporting section-building helpers, near the bottom of `web/save_image_clean.js` before `app.registerExtension`:

```javascript
let _rootCssInjected = false;
function injectRootCss() {
    if (_rootCssInjected || document.getElementById("sic-root-css")) {
        _rootCssInjected = true;
        return;
    }
    _rootCssInjected = true;
    const style = document.createElement("style");
    style.id = "sic-root-css";
    style.textContent = [
        // Task 1 confirmed live (2026-10-12, comfyui_frontend_package
        // 1.53.10) that the Pixaroma-documented display:block-on-rebuild
        // gotcha does NOT reproduce on this ComfyUI version (collapse/
        // expand and resize both rendered correctly) — so the absolutely-
        // positioned inner-layer escape hatch is skipped; a plain flex
        // column on .sic-inner is sufficient (see the spec's Open Items).
        ".sic-root{width:100%;box-sizing:border-box;}",
        ".sic-inner{display:flex;flex-direction:column;",
        "gap:var(--sic-space-lg);padding:var(--sic-space-outer) var(--sic-space-md);box-sizing:border-box;}",
        ".sic-section{display:flex;flex-direction:column;gap:var(--sic-space-sm);}",
        ".sic-section-head{display:flex;align-items:center;justify-content:space-between;",
        "padding:0 var(--sic-space-md);}",
        ".sic-eyebrow{font-size:var(--sic-font-section);font-weight:600;letter-spacing:0.03em;",
        "text-transform:uppercase;color:#9d9d9d;}",
    ].join("");
    document.head.appendChild(style);
}

function buildSection(eyebrowText) {
    const section = el("div", "sic-section");
    if (eyebrowText) {
        const eyebrow = el("div", "sic-eyebrow", eyebrowText);
        eyebrow.style.cssText = "padding:0 var(--sic-space-md);";
        section.appendChild(eyebrow);
    }
    return section;
}

function buildHeadingRow(headingText, triggerEl) {
    const row = el("div", "sic-section-head");
    const heading = el("span", null, headingText);
    heading.style.cssText = "font-size:13px;font-weight:600;color:#f0f0f0;";
    row.appendChild(heading);
    if (triggerEl) {
        row.appendChild(triggerEl);
    }
    return row;
}

function buildNodeUI(node) {
    if (node.__saveImageCleanRootBuilt) {
        return;
    }
    node.__saveImageCleanRootBuilt = true;
    injectDesignTokens();
    injectRootCss();

    const root = el("div", "sic-root");
    const inner = el("div", "sic-inner");
    root.appendChild(inner);

    // --- SAVE LAYOUT ---
    const saveLayoutSection = buildSection("SAVE LAYOUT");
    const pathBuilder = createTemplateBuilderWidget(node, "path_template", "Build Path");
    saveLayoutSection.appendChild(buildHeadingRow("Ordnerstruktur", pathBuilder?.trigger));
    const pathRow = buildTextRow(node, "path_template");
    if (pathRow) saveLayoutSection.appendChild(pathRow.root);
    const modelRow = buildDropdownRow(node, "model_source", "Model Name", MODEL_OPTIONS);
    if (modelRow) saveLayoutSection.appendChild(modelRow.root);
    const clipRow = buildDropdownRow(node, "clip_source", "Text Encoder", CLIP_OPTIONS);
    if (clipRow) saveLayoutSection.appendChild(clipRow.root);
    const subfolderRow = buildTextRow(node, "subfolder", { placeholder: "Top Folder" });
    if (subfolderRow) saveLayoutSection.appendChild(subfolderRow.root);
    const modelFolderRow = buildTextRow(node, "model_folder", { placeholder: "Custom Model Name" });
    const clipFolderRow = buildTextRow(node, "clip_folder", { placeholder: "Custom Text Encoder Name" });
    if (modelFolderRow) saveLayoutSection.appendChild(modelFolderRow.root);
    if (clipFolderRow) saveLayoutSection.appendChild(clipFolderRow.root);
    inner.appendChild(saveLayoutSection);

    // --- FILENAME ---
    const filenameSection = buildSection("FILENAME");
    const filenameBuilder = createTemplateBuilderWidget(node, "filename_datetime", "Build Filename");
    filenameSection.appendChild(buildHeadingRow("Dateiname", filenameBuilder?.trigger));
    const filenameRow = buildTextRow(node, "filename_datetime");
    if (filenameRow) filenameSection.appendChild(filenameRow.root);
    const collisionRow = buildDropdownRow(node, "collision_mode", "Datei vorhanden",
        ["increment", "overwrite", "error", "seconds"],
        { optionLabels: { increment: "Increment number", overwrite: "Overwrite", error: "Error", seconds: "Add seconds" } });
    if (collisionRow) filenameSection.appendChild(collisionRow.root);
    const detectionRow = buildDropdownRow(node, "detection_info", "Detection-Informationen", ["Off", "Summary", "Verbose"]);
    if (detectionRow) filenameSection.appendChild(detectionRow.root);
    inner.appendChild(filenameSection);

    // --- OUTPUT ---
    const outputSection = buildSection("OUTPUT");
    const formatSeg = buildSegmentedControl(node, "image_format", IMAGE_FORMAT_IDS, {
        getTitle: (id) => `Save as ${id}`,
    });
    node.__saveImageCleanFormatSeg = formatSeg;
    if (formatSeg) outputSection.appendChild(formatSeg.root);
    const qualityRow = buildSliderRow(node, "image_quality", "Image Quality", { min: 1, max: 100 });
    node.__saveImageCleanQualityRow = qualityRow;
    if (qualityRow) outputSection.appendChild(qualityRow.root);
    const metadataRow = buildSwitchRow(node, "export_workflow_metadata", "Export Workflow Metadata");
    node.__saveImageCleanMetadataRow = metadataRow;
    if (metadataRow) outputSection.appendChild(metadataRow.root);
    const saveModeSeg = buildSegmentedControl(node, "save_mode", SAVE_MODE_IDS, {
        getTitle: (id) => (id === "Preview"
            ? "Show the result without saving; save individual images later"
            : "Save immediately, as before"),
    });
    node.__saveImageCleanSaveModeSeg = saveModeSeg;
    if (saveModeSeg) outputSection.appendChild(saveModeSeg.root);
    inner.appendChild(outputSection);

    // --- Preview grid (Preview-mode only), existing internals reused ---
    injectPreviewGridCss();
    const gridContainer = el("div", "sic-preview-grid");
    gridContainer.style.display = "none";
    const gridBody = el("div", "sic-preview-grid-body");
    gridContainer.appendChild(gridBody);
    node.__saveImageCleanPreviewGridRefs = { container: gridContainer, body: gridBody };
    inner.appendChild(gridContainer);

    // --- ERWEITERT (gear panel trigger lives in its own small row) ---
    const advanced = createAdvancedPanel(node);
    const advRow = el("div", "sic-section-head");
    const advLabel = el("span", "sic-eyebrow", "ERWEITERT");
    advRow.appendChild(advLabel);
    advRow.appendChild(advanced.trigger);
    inner.appendChild(advRow);

    // --- AUSGABEPFAD, existing internals reused ---
    const helpRoot = buildHelpPanelContent(node);
    inner.appendChild(helpRoot);

    node.addDOMWidget("save_image_clean_root", "custom", root, {
        getMinHeight: () => measureRootFloor(node, inner),
        serialize: false,
        hideOnZoom: false,
        margin: 0,
    });
}
```

`buildHelpPanelContent` is a small extraction from the existing `createHelpPanelWidget` (`web/save_image_clean.js:1343-1477`): same element construction, same `node.__saveImageCleanHelpRefs` assignment, just returning the built `container` element instead of also calling `node.addDOMWidget` itself (the one root widget above is the only `addDOMWidget` call left in the whole file). `measureRootFloor` is written in Task 10 — stub it for now so this task's code runs:

```javascript
function measureRootFloor(node, inner) {
    return Math.max(inner.scrollHeight || 0, 200);
}
```

- [ ] **Step 2: Replace `onNodeCreated`/`configure`/`onExecuted` in `app.registerExtension`**

```javascript
const onConfigure = nodeType.prototype.configure;
nodeType.prototype.configure = function () {
    const result = onConfigure?.apply(this, arguments);
    requestAnimationFrame(() => {
        setFriendlyLabels(this);
        buildNodeUI(this);
        hookWidgetUpdates(this);
        updateHelp(this);
    });
    return result;
};

const onNodeCreated = nodeType.prototype.onNodeCreated;
nodeType.prototype.onNodeCreated = function () {
    const result = onNodeCreated?.apply(this, arguments);
    setFriendlyLabels(this);
    buildNodeUI(this);
    hookWidgetUpdates(this);
    updateHelp(this);
    return result;
};
```

`onExecuted`/`onRemoved` stay as they are — they already only reference `setLastRunStateFromMessage`/`updateHelp`/`updatePreviewGrid`/the template-builder panels, none of which change shape here.

- [ ] **Step 3: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 4: Manual verification**

Copy to the live install, hard-refresh, reload the workflow. Confirm against the spec's target information architecture: SAVE LAYOUT → FILENAME → OUTPUT → (preview grid when in Preview mode) → ERWEITERT gear row → AUSGABEPFAD, in that order, with consistent spacing (one `gap` value, no overlaps). Then specifically check **Review Focus item 1**: open a workflow JSON saved *before* this task (e.g. from `Screenshot 2026-10-12 181929.png`'s session, or any workflow file the user already has with this node in it) and confirm every field restores its old value correctly — this is the compatibility-critical check for this task. Review Focus item 2 (Convert Widget to Input) was resolved in Task 3 as not applicable on this ComfyUI version (confirmed absent even on unmodified native nodes) — no check needed here.

- [ ] **Step 5: Commit**

```bash
git add web/save_image_clean.js
git commit -m "Assemble the node body into one root flex widget

Replaces the independent addDOMWidget-per-section sequence with a
single root widget and real CSS flex layout, composed from the
component factories built in Tasks 2-7, in the SAVE LAYOUT / FILENAME
/ OUTPUT / ERWEITERT / AUSGABEPFAD architecture from the design spec.
Old saved workflows verified to restore correctly."
```

---

## Task 9: Contextual show/hide wiring

**Files:**
- Modify: `web/save_image_clean.js` (extend `buildNodeUI` and `hookWidgetUpdates`)
- Test: none (manual verification, Review Focus item 3)

**Interfaces:**
- Consumes: the row/seg objects stored on `node` by Task 8 (`node.__saveImageCleanFormatSeg`, `node.__saveImageCleanQualityRow`, `node.__saveImageCleanMetadataRow`, plus the model/clip dropdown row objects — store those too, see Step 1)
- Produces: `function updateContextualVisibility(node)`, called from `hookWidgetUpdates`'s callback wrapper on every relevant change

- [ ] **Step 1: Store the dropdown/custom-name row references needed for contextual logic**

In `buildNodeUI` (Task 8), keep references to the four rows this task needs:

```javascript
node.__saveImageCleanModelRow = modelRow;
node.__saveImageCleanClipRow = clipRow;
node.__saveImageCleanModelFolderRow = modelFolderRow;
node.__saveImageCleanClipFolderRow = clipFolderRow;
```

(add these four lines right after their corresponding `const ... = buildDropdownRow(...)`/`buildTextRow(...)` calls in Task 8's `buildNodeUI`)

- [ ] **Step 2: Write `updateContextualVisibility`**

```javascript
function setRowDisabled(row, disabled) {
    if (!row) {
        return;
    }
    row.root.classList.toggle("disabled", disabled);
    row.root.style.display = disabled && row.root.dataset.hideWhenDisabled === "true" ? "none" : "";
}

function updateContextualVisibility(node) {
    const modelSourceValue = getWidget(node, "model_source")?.value;
    const clipSourceValue = getWidget(node, "clip_source")?.value;
    const formatValue = getWidget(node, "image_format")?.value;

    const modelFolderRow = node.__saveImageCleanModelFolderRow;
    if (modelFolderRow) {
        modelFolderRow.root.dataset.hideWhenDisabled = "true";
        setRowDisabled(modelFolderRow, modelSourceValue !== "Custom");
    }
    const clipFolderRow = node.__saveImageCleanClipFolderRow;
    if (clipFolderRow) {
        clipFolderRow.root.dataset.hideWhenDisabled = "true";
        setRowDisabled(clipFolderRow, clipSourceValue !== "Custom");
    }

    const qualityRow = node.__saveImageCleanQualityRow;
    if (qualityRow) {
        qualityRow.inputEl.disabled = formatValue === "PNG";
        qualityRow.root.classList.toggle("disabled", formatValue === "PNG");
    }
    const metadataRow = node.__saveImageCleanMetadataRow;
    if (metadataRow) {
        metadataRow.checkboxEl.disabled = formatValue !== "PNG";
        metadataRow.root.classList.toggle("disabled", formatValue !== "PNG");
    }

    const newSize = node.computeSize();
    newSize[0] = Math.max(newSize[0], node.size[0]);
    newSize[1] = Math.max(newSize[1], node.size[1]);
    node.setSize?.(newSize);
    node.setDirtyCanvas?.(true, true);
}
```

- [ ] **Step 3: Call it from `hookWidgetUpdates` and after `buildNodeUI`**

Add `"image_format"` is already in `hookWidgetUpdates`'s `watchedNames` (`web/save_image_clean.js:1659-1671`); add `"model_source"` and `"clip_source"` — both are already present too (same list). So no new entries are needed in `watchedNames` itself; instead, call `updateContextualVisibility(node)` inside the existing wrapped callback, right next to the existing `updateHelp(node)` call (`web/save_image_clean.js:1683`):

```javascript
widget.callback = function () {
    const result = originalCallback?.apply(this, arguments);
    markLastRunStateStale(node);
    updateHelp(node);
    updateContextualVisibility(node);
    return result;
};
```
and the same addition next to the two `updateHelp(node)` calls inside the `inputEl` `input`/`change` listeners a few lines below. Also call `updateContextualVisibility(this);` once at the end of both `onNodeCreated` and `configure` (Task 8's edit site), right after `updateHelp(this);`, so the initial state is correct on load, not only after the first edit.

- [ ] **Step 4: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 5: Manual verification**

Copy to the live install, hard-refresh. Confirm: Custom Model Name/Custom Text Encoder Name rows are hidden by default (source = Friendly), appear the instant Model Name/Text Encoder is switched to "Custom", disappear again when switched back. Confirm Image Quality is greyed out/disabled at PNG, enables the instant format switches to JPEG or WebP; confirm Export Workflow Metadata is the mirror image. **Review Focus item 3**: toggle `image_format` PNG → JPEG → PNG rapidly several times in a row; confirm Quality/Metadata end up in the correct final state every time, never stuck.

- [ ] **Step 6: Commit**

```bash
git add web/save_image_clean.js
git commit -m "Wire contextual show/hide for Custom Names and format-dependent rows

Custom Model/Text-Encoder Name now only show when their source
dropdown is 'Custom'; Image Quality and Export Workflow Metadata
enable/disable based on the selected image format, matching the
existing backend tooltips. Re-evaluated on every relevant change, not
just once at node creation."
```

---

## Task 10: Floor-only dynamic sizing

**Files:**
- Modify: `web/save_image_clean.js` (replace the `measureRootFloor` stub from Task 8; remove the now-redundant manual `node.setSize(node.computeSize())` calls inside `updateHelp` and `updatePreviewGrid`)
- Test: none (manual verification, Review Focus item 5)

**Interfaces:**
- Consumes: the single root widget from Task 8
- Produces: a real `measureRootFloor(node, inner)` implementation; `updateHelp`/`updatePreviewGrid` no longer call `node.setSize()` themselves — they only toggle `display`/content, and the root widget's `getMinHeight` (called by LiteGraph on its own layout pass) picks up the new height automatically

- [ ] **Step 1: Implement `measureRootFloor`**

```javascript
function measureRootFloor(node, inner) {
    // FLOOR only, no getMaxHeight and no custom computeSize override (the
    // Pixaroma-proven pattern, index.js:1017-1020 in ComfyUI-Pixaroma) — the
    // node grows freely and a user's manual resize is never fought. Rounded
    // to a 4px grid purely so the floor doesn't jitter by 1px between calls
    // as sub-pixel layout rounding varies.
    const measured = inner.scrollHeight || 0;
    return Math.max(Math.round(measured / 4) * 4, 160);
}
```

- [ ] **Step 2: Remove the manual resize calls in `updateHelp` and `updatePreviewGrid`**

In `updateHelp` (`web/save_image_clean.js`, the lines that were ~1651-1655 before Task 8's edits moved things around — find the block):

```javascript
const newSize = node.computeSize();
newSize[0] = Math.max(newSize[0], node.size[0]);
newSize[1] = Math.max(newSize[1], node.size[1], 404);
node.setSize?.(newSize);
node.setDirtyCanvas?.(true, true);
```

delete it entirely — `node.setDirtyCanvas?.(true, true);` alone is kept (still needed to repaint), the size line and the two `newSize` lines above it are removed, since `getMinHeight` now reflects the real DOM height on its own. Do the same in `updatePreviewGrid`'s two similar blocks (the "entries.length" early-return block, and the main block after appending cells) — keep `node.setDirtyCanvas?.(true, true);`, drop the `node.setSize(...)` calls.

Leave `updateContextualVisibility`'s `node.setSize(...)` call from Task 9 in place for now — re-examine it in Step 3 below.

- [ ] **Step 3: Decide whether `updateContextualVisibility` still needs its own resize call**

With `getMinHeight` now measuring the real floor on every LiteGraph layout pass, showing/hiding the Custom Name rows should already change the node's height automatically the next time LiteGraph asks for `computeSize()`. Remove `updateContextualVisibility`'s manual `node.setSize`/`newSize` block too (keep `node.setDirtyCanvas?.(true, true);`), then do the manual verification in Step 4 — if row toggling doesn't resize the node without a manual nudge, restore a single `node.setSize?.(node.computeSize());` call there (LiteGraph's `computeSize()` already consults `getMinHeight`, so this one remaining call, if needed, is not fighting the new strategy — it's just prompting LiteGraph to re-ask).

- [ ] **Step 4: Run the syntax check**

```bash
node --check web/save_image_clean.js
```
Expected: no output, exit code 0.

- [ ] **Step 5: Manual verification**

Copy to the live install, hard-refresh. **Review Focus item 5**: drag-resize the node much smaller than its content, then drag it back larger — confirm no clipped/stale DOM in either direction. Switch to Preview mode and run the workflow (grid appears, node grows); switch back to Save mode (grid disappears) — confirm the grid content/space is gone (correction, found in final review 2026-10-13: floor-only sizing is a FLOOR, so a user-enlarged node does not auto-shrink back down on its own the way the original "node shrinks back down" wording implied — only a node still at its floor height shrinks when content leaves; don't read a merely-unshrunk larger node as a bug). Toggle Model Name to "Custom" and back — confirm the node height adjusts to the Custom Name row appearing/disappearing (this is what Step 3 above determines, resolve it here).

- [ ] **Step 6: Commit**

```bash
git add web/save_image_clean.js
git commit -m "Switch to floor-only dynamic sizing

Replaces the three scattered manual node.setSize(node.computeSize())
calls with one getMinHeight on the root widget, measured from the
real DOM height (Pixaroma-proven pattern). The node now grows and
shrinks correctly without fighting a user's manual resize."
```

---

## Task 11: Full visual QA pass + docs sync + before/after comparison

**Files:**
- Modify (docs only, per AGENTS.md's Docs Sync Checker Agent conventions): `README.md`, `docs/USAGE.md`, `web/docs/SaveImageClean.md`, `CHANGELOG.md`, `CONTINUE.md` — only where they describe the node's visible UI (none of them describe backend behavior that changed, since none did)
- Test: full `pytest` run (confirms the untouched backend still passes), `node --check web/save_image_clean.js` and `node --check web/sic_components.mjs`

**Interfaces:**
- Consumes: the finished node from Tasks 1–10
- Produces: the spec's required "nachvollziehbare Gegenüberstellung der alten und neuen Komponenten, einen Testbericht und die verbleibenden bekannten Einschränkungen" (A §10's closing requirement) — written into this plan's final report, not a new file, unless the user asks for one separately

- [ ] **Step 1: Run the full automated check suite**

```bash
node --check web/save_image_clean.js
node --check web/sic_components.mjs
G:\ComfyUI-Easy-Install\python_embeded\python.exe -m py_compile nodes.py
G:\ComfyUI-Easy-Install\python_embeded\python.exe -m pytest
G:\ComfyUI-Easy-Install\python_embeded\python.exe -m ruff check .
```
Expected: all pass, pytest count unchanged from before this plan (confirms the untouched `nodes.py` backend truly wasn't touched).

- [ ] **Step 2: Work through the spec's Appendix A §8 test list in the real ComfyUI**

Small and large node widths; multiple zoom levels; a template string over 150 characters; a model/text-encoder name over 60 characters; every field emptied out; every dropdown opened and changed at least once; all three image formats; both save modes; a Preview-mode run followed by a per-image Save click; Detection Info set to each of Off/Summary/Verbose; save the workflow, reload ComfyUI, reload the workflow; open a workflow saved before this plan's changes; light and dark ComfyUI theme if the installation has both; keyboard-only operation of every dropdown/switch/slider (Tab to focus, arrow keys/Space to operate, no mouse). Record any failure found as a new, separate fix — do not silently patch around it without noting what broke.

- [ ] **Step 3: Take after screenshots and compare against the session's before screenshots**

Capture the node at default width and at the wide/zoomed width used earlier this session, compare directly against `Screenshot 2026-10-12 171840.png` (wide, original) and `Screenshot 2026-10-12 181929.png` (default width, original) — confirm every item in the spec's Acceptance Criteria is visibly true in the new screenshots, not inferred from reading the code.

- [ ] **Step 4: Sync documentation**

Read `README.md`, `docs/USAGE.md`, `web/docs/SaveImageClean.md`, `CHANGELOG.md`, `CONTINUE.md` and update only the passages that describe the node's on-canvas appearance/control layout (e.g. if any of them mention "Save Mode" as a dropdown rather than a toggle, or describe widget positions that moved). Add a `CHANGELOG.md` `[Unreleased]` entry summarizing the redesign in one or two lines, English, no AI attribution per the global CLAUDE.md policy. Update `CONTINUE.md`'s current-state section to reflect the finished redesign.

- [ ] **Step 5: Write the before/after component table and test report directly in this plan's final status, then commit**

```bash
git add README.md docs/USAGE.md web/docs/SaveImageClean.md CHANGELOG.md CONTINUE.md
git commit -m "Sync documentation for the UI/UX redesign"
```

Then report back to the user (in chat, per this repo's German-chat convention) with: the old-vs-new component table (reuse the spec's "New Reusable Components" table as the backbone, adding a one-line before/after note per row), the automated-check results from Step 1, the manual-test results from Step 2, and any known remaining limitation found along the way (e.g. if Task 1 found the `addDOMWidget`-rebuild gotcha does apply and a workaround beyond the inner-flex-layer is still needed, or if any single dropdown's keyboard behavior differs slightly from the native widget it replaced).

---

## Self-Review Notes (writing-plans skill step)

**Spec coverage:** Every numbered item in Appendix A §4 maps to a task — 4.1 (Build buttons) is fixed as a side effect of Task 8's `buildHeadingRow`, which gives both builder triggers identical, larger styling next to a real heading instead of the tiny eyebrow label; 4.2/4.3 → Task 6; 4.4 → Task 3; 4.5 → Task 3 (Detection Info is already 3-state, confirmed in the spec, no special-casing needed beyond the standard dropdown row); 4.6 → Task 2 (already correct mechanism, kept); 4.7 → Task 5 + Task 9 (contextual disable); 4.8 → Task 8 (segmented controls both live under one OUTPUT heading now, settings vs. actions distinction preserved — no row in this redesign introduces an action disguised as a setting or vice versa); 4.9 → Task 8 (Ausgabepfad gets its own section, no more accidental adjacency) with the existing 3-state badge logic untouched; 4.10 → Task 1 (investigation) + Task 10 (fix). §5 (design system) → Task 2. §6 (information architecture) → Task 8. §7 (compatibility) → the Global Constraints section plus every task's "native widget stays the data source" framing. §8 (testing) → Task 11 Step 2. §9 (acceptance) → Task 11 Step 3. §10 (process order) → the task sequence itself follows the same order (read → map bugs → find causes → design → implement → test → visual check → fix → docs → commit).

**Placeholder scan:** none found — every step either has runnable code or a precise manual-check procedure with concrete pass/fail criteria.

**Type consistency:** `buildDropdownRow`/`buildSwitchRow`/`buildSliderRow`/`buildTextRow`/`buildSegmentedControl` all follow the same return shape (`{ widget, root, ...extras }`) and the same `(node, widgetName, ...)` argument order throughout every task that uses them; `createXRowWidget` wrapper functions all follow the same `(node, widgetName, ...) -> addDOMWidget` pattern. Verified consistent across Tasks 2-9.

**Review Focus:** all five items have an owning task and an explicit manual-check step (see the Review Focus section above, each line names its task).
