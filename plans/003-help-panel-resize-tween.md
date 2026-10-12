# 003 — Tween the help panel's node-height change instead of snapping

- **Status**: TODO
- **Commit**: 90009ad
- **Severity**: MEDIUM
- **Category**: Missed opportunities / Performance (litegraph canvas, not CSS)
- **Estimated scope**: 1 file, 1 new function (~35 lines) + 1 call-site change

## Problem

`updateHelp` (`web/save_image_clean.js:1085-1159`) shows or hides a block of detection-snapshot detail lines depending on state (see the `if (detailLines.length) { ... } else { ... }` block at lines 1136-1151, which toggles `refs.detailsEl.style.display` and `refs.detailsTitleEl.style.display` between `"block"` and `"none"`). Right after that, the node's own height is recomputed and applied immediately and unconditionally:

```js
/* web/save_image_clean.js:1154-1158 — current */
const newSize = node.computeSize();
newSize[0] = Math.max(newSize[0], node.size[0]);
newSize[1] = Math.max(newSize[1], node.size[1], 404);
node.setSize?.(newSize);
node.setDirtyCanvas?.(true, true);
```

Whenever the detail block appears or disappears (first run, or any later edit that changes whether detection details are shown), the node's rendered height jumps abruptly on the canvas — a classic "state change that teleports" per the audit's missed-opportunities category. This is a litegraph canvas node, not a DOM element, so a plain CSS `transition` cannot apply here — there is no exemplar for animated motion in this file to imitate; this plan introduces the first one, using `requestAnimationFrame`.

## Target

Animate `node.size[1]` from its current value to the target over 220ms using the audit's exact strong ease-in-out curve (`cubic-bezier(0.77, 0, 0.175, 1)`), evaluated via a small cubic-bezier solver (no new dependency — implemented inline), and make the tween interruptible (a new resize mid-animation cancels the previous one and restarts from the *current* animated height, not the old target, per the audit's interruptibility rule and Apple's "always animate from the presentation value" principle):

```js
/* target: new function, placed after setHelperStatus (ends at web/save_image_clean.js:1083), before updateHelp */
function makeCubicBezierEasing(x1, y1, x2, y2) {
    const A = (a1, a2) => 1 - 3 * a2 + 3 * a1;
    const B = (a1, a2) => 3 * a2 - 6 * a1;
    const C = (a1) => 3 * a1;
    const bezier = (t, a1, a2) => ((A(a1, a2) * t + B(a1, a2)) * t + C(a1)) * t;
    const bezierSlope = (t, a1, a2) => 3 * A(a1, a2) * t * t + 2 * B(a1, a2) * t + C(a1);

    return function easing(t) {
        if (x1 === y1 && x2 === y2) {
            return t;
        }
        let guess = t;
        for (let i = 0; i < 6; i += 1) {
            const slope = bezierSlope(guess, x1, x2);
            if (slope === 0) {
                break;
            }
            guess -= (bezier(guess, x1, x2) - t) / slope;
        }
        return bezier(guess, y1, y2);
    };
}

// Matches the strong ease-in-out curve used for on-screen movement elsewhere
// in this project's design conventions: cubic-bezier(0.77, 0, 0.175, 1).
const SIC_EASE_IN_OUT = makeCubicBezierEasing(0.77, 0, 0.175, 1);

function animateNodeHeight(node, targetSize) {
    const targetWidth = targetSize[0];
    const targetHeight = targetSize[1];

    if (node.__saveImageCleanHeightTween) {
        cancelAnimationFrame(node.__saveImageCleanHeightTween.frame);
        delete node.__saveImageCleanHeightTween;
    }

    const startHeight = node.size[1];
    if (Math.abs(targetHeight - startHeight) < 1) {
        node.setSize?.([targetWidth, targetHeight]);
        node.setDirtyCanvas?.(true, true);
        return;
    }

    const duration = 220;
    const startTime = performance.now();
    const tweenState = { frame: 0 };
    node.__saveImageCleanHeightTween = tweenState;

    const step = (now) => {
        const elapsed = now - startTime;
        const t = Math.min(elapsed / duration, 1);
        const eased = SIC_EASE_IN_OUT(t);
        const currentHeight = Math.round(startHeight + (targetHeight - startHeight) * eased);
        node.setSize?.([targetWidth, currentHeight]);
        node.setDirtyCanvas?.(true, true);

        if (t < 1) {
            tweenState.frame = requestAnimationFrame(step);
        } else {
            delete node.__saveImageCleanHeightTween;
        }
    };

    tweenState.frame = requestAnimationFrame(step);
}
```

And the call site in `updateHelp`:

```js
/* target: web/save_image_clean.js:1154-1158 */
const newSize = node.computeSize();
newSize[0] = Math.max(newSize[0], node.size[0]);
newSize[1] = Math.max(newSize[1], node.size[1], 404);
animateNodeHeight(node, newSize);
```

(The old `node.setSize?.(newSize); node.setDirtyCanvas?.(true, true);` pair is replaced by the single `animateNodeHeight(node, newSize)` call — `animateNodeHeight` performs both itself, every frame.)

## Repo conventions to follow

- This file has no existing `requestAnimationFrame` usage and no existing exemplar for JS-driven motion — everything else is CSS transitions (see plans 001/002). This plan is the first of its kind here; keep it self-contained in these two additions and do not refactor unrelated code to match.
- State flags stored directly on the `node` object with a `__saveImageClean`-prefixed key is this file's established pattern for per-node state (e.g. `node.__saveImageCleanLastRunInfo`, `node.__saveImageCleanFormatWidget`) — `node.__saveImageCleanHeightTween` follows that naming convention.
- Never approximate the easing curve — `cubic-bezier(0.77, 0, 0.175, 1)` must be used exactly, via the bezier solver above, not a hand-rolled approximation.

## Steps

1. In `web/save_image_clean.js`, directly after `setHelperStatus` ends (currently line 1083) and before `function updateHelp(node) {` (currently line 1085), insert the `makeCubicBezierEasing`, `SIC_EASE_IN_OUT`, and `animateNodeHeight` definitions shown in Target, in that order.
2. In `updateHelp`, replace the five lines at the end of the function (currently lines 1154-1158) with the two-line Target call-site shown above.

## Boundaries

- Do NOT touch `node.computeSize()` or the `newSize[0]`/`newSize[1]` clamp logic above the replaced lines — only the final `setSize`/`setDirtyCanvas` pair changes.
- Do NOT animate `newSize[0]` (width) — only height visibly jumps today; do not add width-tweening behavior that doesn't exist as a problem.
- Do NOT add a general-purpose animation utility file or a dependency (e.g. a tweening library) — this one inline function is the whole scope.
- If the current code at `web/save_image_clean.js:1154-1158` does not match the excerpt in Problem (drift since commit `90009ad`), STOP and report instead of improvising.

## Verification

- **Mechanical**: `node --check web/save_image_clean.js` must pass.
- **Feel check**: in the paired local ComfyUI install, add a `Save Image Organized` node:
  - Queue a workflow through it so detection succeeds and the Detection Snapshot lines appear — the node should visibly grow in height smoothly over ~220ms, not jump instantly.
  - Immediately after, trigger another change that hides the details (e.g. edit `Save Layout` to clear the snapshot relevance) while the first tween might still be running, and confirm the node height does not stutter, jump backward, or restart from the wrong value — it should smoothly redirect from wherever it currently is.
  - Rapidly toggle a watched widget several times in a row (e.g. retype part of the filename pattern) and confirm no runaway animation frames accumulate (check the browser's performance/FPS meter briefly) and that `node.__saveImageCleanHeightTween` is `undefined` a moment after the last edit settles (inspectable via the console: `app.graph._nodes.find(n => n.type === "SaveImageClean").__saveImageCleanHeightTween`).
- **Done when**: node height changes smoothly and interruptibly instead of snapping, rapid toggling never leaves a dangling animation frame, and `node --check` passes.
