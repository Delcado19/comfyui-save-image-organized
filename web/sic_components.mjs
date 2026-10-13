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
    const chevron = el("span", "sic-row-chevron", "▾");
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

    // Final-review finding (2026-10-13): onNodeCreated builds this row from
    // widget.value's default BEFORE configure() restores a saved workflow's
    // real value (plain assignment, no callback/input event - confirmed by
    // reading the installed frontend bundle). Without this resync, a loaded
    // workflow's dropdown shows the default option while the real widget
    // value (and therefore the save) is already correct - buildNodeUI
    // collects this into node.__saveImageCleanSyncers, called from
    // updateHelp on every relevant pass including the post-configure one.
    const sync = () => {
        select.value = widget.value;
        render();
    };

    return { widget, root, selectEl: select, valueEl: valueText, sync };
}

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

    // See buildDropdownRow's sync comment - same post-configure resync gap.
    const sync = () => {
        checkbox.checked = Boolean(widget.value);
        render();
    };

    return { widget, root, checkboxEl: checkbox, sync };
}

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

    // See buildDropdownRow's sync comment - same post-configure resync gap.
    const sync = () => {
        input.value = String(widget.value);
        valueEl.textContent = String(widget.value);
    };

    return { widget, root, inputEl: input, valueEl, sync };
}

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
 * Builds a styled <input> for a native STRING widget and makes it the row's
 * editable control, wired both ways to `widget.value`.
 *
 * Earlier versions of this function reused `widget.inputEl` on the
 * assumption that ComfyUI eagerly creates a persistent backing <input> for
 * every STRING widget (asserted by the plan, never actually live-verified
 * because browser access was blocked all of that session). Found live
 * 2026-10-13, after two rounds of user bug reports: `widget.inputEl` is NOT
 * reliably populated for single-line (multiline:false) STRING widgets in
 * this comfyui_frontend_package version, regardless of timing - it failed
 * identically from the synchronous onNodeCreated path, from onNodeCreated
 * deferred one requestAnimationFrame, AND from configure()'s own pre-existing
 * rAF defer. All 5 of this node's single-line STRING widgets (path_template,
 * filename_datetime, subfolder, model_folder, clip_folder) hit this every
 * time, so it isn't a race - this builder no longer depends on it at all: it
 * creates its own <input>, seeds it from widget.value, and writes back to
 * widget.value on input. `widget.inputEl` is still backfilled with this
 * element afterwards so any other code reading it (insertTokenIntoWidget's
 * cursor-position insert, hookWidgetUpdates' own inputEl-based listeners)
 * keeps working unchanged.
 *
 * hideNativeWidget() still runs to collapse the native widget's own row to
 * zero height (confirmed independently needed for smooth drag/resize, Task 1).
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
    if (!widget) {
        return null;
    }
    injectDesignTokens();
    injectTextRowCss();
    hideNativeWidget(widget);

    const root = el("div", "sic-text-row");
    const inputEl = document.createElement("input");
    inputEl.type = "text";
    inputEl.className = "sic-text-input";
    inputEl.value = widget.value ?? "";
    if (placeholder) {
        inputEl.placeholder = placeholder;
    }
    // Compatibility shim - see the function doc comment above.
    widget.inputEl = inputEl;

    const syncTitle = () => {
        inputEl.title = inputEl.value;
        widget.tooltip = inputEl.value;
    };
    inputEl.addEventListener("input", () => {
        widget.value = inputEl.value;
        syncTitle();
    });
    syncTitle();

    root.appendChild(inputEl);
    // configure()'s workflow-load restore writes widget.value directly with
    // a plain assignment (no callback, no input event - same class of bug as
    // the Final Review's C1 finding for the other row types), so sync() must
    // pull widget.value back into this owned inputEl, not just re-run
    // syncTitle against whatever inputEl already shows.
    const sync = () => {
        inputEl.value = widget.value ?? "";
        syncTitle();
    };
    return { widget, root, inputEl, sync };
}
