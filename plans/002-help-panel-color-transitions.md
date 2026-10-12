# 002 — Transition the help panel's status badge, note, and preview-border color changes

- **Status**: DONE
- **Commit**: 90009ad
- **Severity**: MEDIUM
- **Category**: Missed opportunities / Physicality
- **Estimated scope**: 1 file, 3 line additions

## Problem

**Depends on plan 001** (adds the `--sic-ease` custom property this plan uses). Apply 001 first.

`createHelpPanelWidget` (`web/save_image_clean.js:850-981`) builds three elements whose colors change together, once per workflow run or relevant widget edit, via direct inline-style assignment with no CSS transition at all — they teleport:

1. `statusEl` (the "Sample Preview" / "Fresh Detection" / "Last Detection Snapshot" badge), styled at creation:
   ```js
   /* web/save_image_clean.js:882-898 — current */
   const statusEl = document.createElement("div");
   statusEl.style.cssText = [
       "display:inline-flex",
       "align-items:center",
       "min-height:20px",
       "padding:0 8px",
       "border-radius:999px",
       "font-size:10px",
       "font-weight:600",
       "letter-spacing:0.03em",
       "text-transform:uppercase",
       "color:#cfcfcf",
       "background:rgba(255,255,255,0.06)",
       "border:1px solid rgba(255,255,255,0.08)",
       "box-sizing:border-box",
       "white-space:nowrap",
   ].join(";");
   ```
   Its `color`/`background`/`borderColor` are reassigned in `setHelperStatus` (`web/save_image_clean.js:1057-1083`).

2. `noteEl` (the helper text line under the badge), styled at creation:
   ```js
   /* web/save_image_clean.js:900-906 — current */
   const noteEl = document.createElement("div");
   noteEl.style.cssText = [
       "font-size:11px",
       "line-height:1.35",
       "color:#a9a9a9",
       "min-height:14px",
   ].join(";");
   ```
   Its `color` is reassigned directly in `updateHelp` (`web/save_image_clean.js:1107,1115,1126`).

3. `outputValueEl` (the monospace path preview), built by the `createPreviewValue` factory:
   ```js
   /* web/save_image_clean.js:908-928 — current */
   const createPreviewValue = () => {
       const valueEl = document.createElement("div");
       valueEl.style.cssText = [
           "display:flex",
           "align-items:center",
           "font-family:Consolas, 'Courier New', monospace",
           "font-size:12px",
           "line-height:1.4",
           "color:#f5f5f5",
           "background:rgba(0,0,0,0.18)",
           "border-radius:8px",
           "padding:10px 12px 11px 12px",
           "min-height:28px",
           "box-sizing:border-box",
           "white-space:nowrap",
           "overflow:hidden",
           "text-overflow:ellipsis",
           "border:1px solid transparent",
       ].join(";");
       return valueEl;
   };
   ```
   Its `borderColor` is reassigned directly in `updateHelp` (`web/save_image_clean.js:1108,1116,1127-1131`).

All three are "state indication" changes (the run just completed, or the preview just went stale) — an occasional event, not a per-keystroke one, so animating it does not violate the frequency rule. Leaving some of the three transitioned and others not would look worse than leaving all untransitioned, so this plan fixes all three together (same root cause, same fix pattern, one file — per the plan-authoring rule, these merge into one plan).

## Target

Add a `transition` declaration to each of the three elements' `style.cssText`, using the `--sic-ease` token from plan 001, at 160ms (within the audit's button/small-popover duration budget):

```js
/* target: statusEl */
statusEl.style.cssText = [
    "display:inline-flex",
    "align-items:center",
    "min-height:20px",
    "padding:0 8px",
    "border-radius:999px",
    "font-size:10px",
    "font-weight:600",
    "letter-spacing:0.03em",
    "text-transform:uppercase",
    "color:#cfcfcf",
    "background:rgba(255,255,255,0.06)",
    "border:1px solid rgba(255,255,255,0.08)",
    "box-sizing:border-box",
    "white-space:nowrap",
    "transition:background 160ms var(--sic-ease), color 160ms var(--sic-ease), border-color 160ms var(--sic-ease)",
].join(";");
```

```js
/* target: noteEl */
noteEl.style.cssText = [
    "font-size:11px",
    "line-height:1.35",
    "color:#a9a9a9",
    "min-height:14px",
    "transition:color 160ms var(--sic-ease)",
].join(";");
```

```js
/* target: createPreviewValue's valueEl */
valueEl.style.cssText = [
    "display:flex",
    "align-items:center",
    "font-family:Consolas, 'Courier New', monospace",
    "font-size:12px",
    "line-height:1.4",
    "color:#f5f5f5",
    "background:rgba(0,0,0,0.18)",
    "border-radius:8px",
    "padding:10px 12px 11px 12px",
    "min-height:28px",
    "box-sizing:border-box",
    "white-space:nowrap",
    "overflow:hidden",
    "text-overflow:ellipsis",
    "border:1px solid transparent",
    "transition:border-color 160ms var(--sic-ease)",
].join(";");
```

No change to `setHelperStatus` or `updateHelp` themselves — they already just assign `.style.color`/`.style.background`/`.style.borderColor` directly, and a CSS `transition` on the element picks up any such direct style assignment automatically.

## Repo conventions to follow

- Inline `style.cssText` built from a joined array is this file's only styling pattern for non-button elements (see `createHelpPanelWidget`, `web/save_image_clean.js:850-981` throughout) — do not introduce a CSS class or external stylesheet rule for this.
- `var(--sic-ease)` is readable here because plan 001 defines it on `:root` in a stylesheet injected into `document.head`, which is global — no extra wiring needed to make it visible to these inline styles.

## Steps

1. Apply plan 001 first (adds `--sic-ease`).
2. In `web/save_image_clean.js`, in `createHelpPanelWidget`, add the `"transition:..."` line to `statusEl.style.cssText`'s array (currently lines 882-898) as shown in Target.
3. Add the `"transition:..."` line to `noteEl.style.cssText`'s array (currently lines 900-906) as shown in Target.
4. Add the `"transition:..."` line to the `createPreviewValue` factory's `valueEl.style.cssText` array (currently lines 908-928) as shown in Target.

## Boundaries

- Do NOT add a transition to `detailsEl` or `detailsTitleEl` — those are shown/hidden via `display:none`/`display:block` toggling (plan 003's concern, a layout change, not a color change) and `display` cannot be transitioned.
- Do NOT modify `setHelperStatus` or `updateHelp` — the fix is entirely in the three elements' initial `style.cssText`.
- Do NOT change any color values, only add the `transition` property.
- If the current code does not match the excerpts above (drift since commit `90009ad`), STOP and report instead of improvising.

## Verification

- **Mechanical**: `node --check web/save_image_clean.js` must pass.
- **Feel check**: in the paired local ComfyUI install, add a `Save Image Organized` node and queue a workflow through it:
  - Before the run, the badge should read "Sample Preview" in neutral gray. After the run completes, it should fade (not snap) to "Fresh Detection" in blue over ~160ms.
  - Edit the `Save Layout` field after a successful run — the badge should fade to the amber "Last Detection Snapshot" state, and the preview box's border should fade to amber alongside it, not jump.
  - In DevTools, set Animations panel playback to 10% and confirm the badge's background/text color genuinely interpolates rather than jump-cutting.
  - Toggle `prefers-reduced-motion` (Rendering panel) — these are pure color transitions with no transform, so they are allowed to keep running unchanged; confirm nothing breaks.
- **Done when**: all three elements visibly cross-fade their color on every status change instead of snapping, and `node --check` passes.
