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

    return { widget, root, selectEl: select, valueEl: valueText };
}
