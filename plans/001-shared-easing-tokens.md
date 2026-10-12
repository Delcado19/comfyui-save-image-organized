# 001 — Introduce shared easing tokens and fix hover easing mismatch

- **Status**: DONE
- **Commit**: 90009ad
- **Severity**: LOW
- **Category**: Easing & duration / Cohesion & tokens
- **Estimated scope**: 1 file, ~3 line changes

## Problem

`web/save_image_clean.js:759-779` defines the only CSS in this node's frontend, injected once via `injectFormatButtonsCss()`. The `.sic-fmt-btn` rule animates four properties (`transform`, `background`, `color`, `border-color`) under a single `ease-out` curve:

```js
/* web/save_image_clean.js:767-777 — current */
style.textContent = [
    ".sic-fmt-row{display:flex;gap:4px;width:100%;box-sizing:border-box;padding:0 8px;}",
    ".sic-fmt-btn{flex:1;padding:5px 0;font-size:11px;font-weight:600;border-radius:6px;",
    "border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.04);color:#b7b7b7;",
    "cursor:pointer;font-family:inherit;",
    "transition:transform 120ms ease-out, background 120ms ease-out, color 120ms ease-out, border-color 120ms ease-out;}",
    ".sic-fmt-btn:hover{border-color:rgba(142,183,255,0.5);color:#e3e3e3;}",
    ".sic-fmt-btn:active{transform:scale(0.97);}",
    ".sic-fmt-btn.active{background:#4c86e0;border-color:#4c86e0;color:#fff;}",
    ".sic-fmt-btn.active:hover{border-color:#5d93e6;}",
].join("");
```

Per the audit rubric's easing decision order, hover/color changes should use plain `ease`, while only the `:active` press transform should use `ease-out`. Using `ease-out` for everything is a minor semantic mismatch. There is also no shared easing token anywhere in this codebase — every future animated widget (plans 002 and 004) would otherwise hand-type its own curve, which is exactly the "five hand-typed cubic-beziers that almost match" consolidation smell the audit flags.

## Target

Add two CSS custom properties on `:root` inside the same injected stylesheet, and split the `.sic-fmt-btn` transition so press feedback uses the strong `ease-out` curve and hover/color feedback uses plain `ease`:

```css
/* target */
:root {
  --sic-ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --sic-ease: ease;
}
.sic-fmt-btn {
  transition:
    transform 120ms var(--sic-ease-out),
    background 120ms var(--sic-ease),
    color 120ms var(--sic-ease),
    border-color 120ms var(--sic-ease);
}
```

`--sic-ease-out` is the strong custom ease-out curve from the audit playbook (`cubic-bezier(0.23, 1, 0.32, 1)`), copied verbatim — not approximated. `--sic-ease` is intentionally the plain built-in `ease` keyword (correct per the audit's hover/color-change rule, not a curve that needs strengthening).

## Repo conventions to follow

- CSS lives entirely inside JS template literals injected via a `<style>` tag with a stable `id`, guarded by a module-level `_xCssInjected` boolean plus an `document.getElementById` fallback check (see `injectFormatButtonsCss`, `web/save_image_clean.js:758-779`). Follow this exact guard pattern — do not introduce a different injection mechanism.
- Because the stylesheet is injected into `document.head` (global scope), a `:root` rule defined here is readable by any other element on the page, including DOM widgets created later for other widgets on this node (plans 002 and 004 rely on this).

## Steps

1. In `web/save_image_clean.js`, inside `injectFormatButtonsCss()` (starts at line 759), change the `style.textContent` array (lines 767-777) to:
   ```js
   style.textContent = [
       ":root{--sic-ease-out:cubic-bezier(0.23,1,0.32,1);--sic-ease:ease;}",
       ".sic-fmt-row{display:flex;gap:4px;width:100%;box-sizing:border-box;padding:0 8px;}",
       ".sic-fmt-btn{flex:1;padding:5px 0;font-size:11px;font-weight:600;border-radius:6px;",
       "border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.04);color:#b7b7b7;",
       "cursor:pointer;font-family:inherit;",
       "transition:transform 120ms var(--sic-ease-out), background 120ms var(--sic-ease), color 120ms var(--sic-ease), border-color 120ms var(--sic-ease);}",
       ".sic-fmt-btn:hover{border-color:rgba(142,183,255,0.5);color:#e3e3e3;}",
       ".sic-fmt-btn:active{transform:scale(0.97);}",
       ".sic-fmt-btn.active{background:#4c86e0;border-color:#4c86e0;color:#fff;}",
       ".sic-fmt-btn.active:hover{border-color:#5d93e6;}",
   ].join("");
   ```
2. Add a one-line comment directly above the `style.textContent` assignment noting that the `:root` rule is intentionally shared beyond this one widget:
   ```js
   // :root vars here are global (this stylesheet is injected once into document.head)
   // and are reused by the help-panel and template-builder widgets elsewhere in this file.
   ```

## Boundaries

- Do NOT rename the stylesheet `id` (`save-image-clean-format-css`) or the function name `injectFormatButtonsCss` — other code does not reference it by a more specific name, and renaming only inflates the diff.
- Do NOT touch `createFormatButtonsWidget`, `setActiveFormatButton`, or any other function in this file.
- Do NOT add a build step, a CSS file, or a new dependency — this stays a plain JS template literal, matching the existing pattern.
- If the current code at `web/save_image_clean.js:767-777` does not match the excerpt above (drift since commit `90009ad`), STOP and report instead of improvising.

## Verification

- **Mechanical**: `node --check web/save_image_clean.js` must pass (no syntax errors).
- **Feel check**: open the paired local ComfyUI install, add a `Save Image Organized` node, and:
  - Hover over a format button (PNG/JPEG/WebP) — the border/text color change should feel the same speed as before (120ms), just using a slightly different curve; there should be no visible regression or jump.
  - Click a format button and hold — the `scale(0.97)` press feedback must still be instant and snappy (unchanged `ease-out` curve).
  - In DevTools Elements panel, confirm `getComputedStyle(document.documentElement).getPropertyValue('--sic-ease-out')` returns `cubic-bezier(0.23, 1, 0.32, 1)`.
- **Done when**: the `:root` custom properties exist and resolve correctly in DevTools, `.sic-fmt-btn` hover/press still feel correct, and `node --check` passes.
