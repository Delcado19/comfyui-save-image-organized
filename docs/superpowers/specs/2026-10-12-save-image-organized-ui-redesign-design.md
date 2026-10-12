# Save Image Organized — UI/UX Redesign Design

**Goal:** Replace the current widget-by-widget LiteGraph layout of the `SaveImageClean` node with one coherent, flex-based custom UI that eliminates the overlap/spacing bugs, groups controls by real dependency, and establishes a design-token system that governs this node's UI going forward — all while keeping the existing `nodes.py` backend contract (INPUT_TYPES names/order/types, `FUNCTION` signature, `widgets_values` positional serialization) completely unchanged.

**Architecture:** One root `addDOMWidget` per node, holding a real CSS flex-column tree. Every row inside it is a custom-styled component that reads and writes the *existing* native ComfyUI widgets (hidden, exactly like `image_format`/`save_mode` already are) — never a parallel state store. This is the one technique separated out of Pixaroma's `ComfyUI-Pixaroma` node (studied as primary source, see "Pixaroma reference" below) that is safe to copy; their JSON-blob-in-`node.properties` serialization is explicitly *not* copied, for compatibility reasons explained below.

**Tech Stack:** Vanilla DOM/CSS inside `web/save_image_clean.js` (ComfyUI's `addDOMWidget` mechanism), no new dependencies. Python side (`nodes.py`) is unmodified structurally.

**Spec sources (binding, verbatim, see Appendix A and B):**
- Appendix A: the user's full original German requirements brief ("Auftrag: Vollständiges UI/UX-Redesign von Save Image Organized"), all 10 sections — binding for this redesign and for future work on this node's UI.
- Appendix B: the user-supplied concept mockup screenshot (`Screenshot 2026-10-12 174942.png`) showing the target visual hierarchy — a simplified, non-exhaustive sketch (its own footer says so), used here as the visual language reference, not a literal 1:1 spec.

This document resolves the open questions Appendix A leaves to implementation judgment (A §4.4, §4.5, §6), through conversational brainstorming with the user, and records the reasoning so a future session does not have to re-derive it.

## Current State — Widget-to-Implementation Inventory

Verified by reading the actual source (not assumed), worktree `save-preview-mode-split`, `nodes.py` 2165 lines / `web/save_image_clean.js` 1762 lines at the time of writing.

### Backend contract (`nodes.py`, unchanged by this redesign)

`SaveImageClean.INPUT_TYPES` (`nodes.py:1422-1590`), required then optional, in this exact order — **this order and these names are the serialization contract and must not change**:

| # | Key | Type | Default | Options | nodes.py |
|---|---|---|---|---|---|
| 1 | `images` | IMAGE (socket) | — | — | 1425 |
| 2 | `path_template` | STRING | `DEFAULT_TEMPLATE` | — | 1426-1437 |
| 3 | `model_source` | COMBO | `Friendly` | `MODEL_SOURCE_OPTIONS` (140) = Friendly / Friendly Clean / Exact / Custom | 1438-1447 |
| 4 | `clip_source` | COMBO | `Friendly` | `CLIP_SOURCE_OPTIONS` (141), same 4 | 1448-1457 |
| 5 | `filename_datetime` | STRING | `DEFAULT_FILENAME_PATTERN` | — | 1458-1468 |
| 6 | `collision_mode` | COMBO | `increment` | increment / overwrite / error / seconds | 1469-1478 |
| 7 | `detection_info` | COMBO | `Off` | `DETECTION_INFO_OPTIONS` (142) = Off / Summary / Verbose | 1479-1489 |
| 8 | `export_workflow_metadata` | BOOLEAN | `true` | — | 1490-1500 |
| 9 | `subfolder` (optional) | STRING | `""` | — | 1503-1512 |
| 10 | `model_folder` (optional) | STRING | `""` | — | 1513-1523 |
| 11 | `clip_folder` (optional) | STRING | `""` | — | 1524-1534 |
| 12 | `image_format` (optional) | COMBO | `PNG` | `IMAGE_FORMAT_OPTIONS` (143) = PNG / JPEG / WebP | 1539-1548 |
| 13 | `image_quality` (optional) | INT slider | `95` | 1-100 | 1549-1558 |
| 14 | `loader_priority` (optional) | COMBO | `Nearest` | `LOADER_PRIORITY_OPTIONS` (149) = Nearest / First Used | 1559-1571 |
| 15 | `save_mode` (optional) | COMBO | `Save` | Save / Preview | 1572-1583 |

`save_images(...)` (`nodes.py:1950-1975` area) takes every one of these as a named keyword parameter — confirmed by reading the signature directly, not assumed. A saved workflow's `widgets_values` array is positional over this exact list (see the existing code comment at `nodes.py:1535-1538` explaining why new optional fields may only be appended, never inserted).

### Frontend (`web/save_image_clean.js`)

| Concern | Function | Lines | Technique today |
|---|---|---|---|
| Friendly labels | `setFriendlyLabels` | 170-177 | sets `widget.label` from `LABELS` map (8-23) |
| Section heading + Build button | `ensureSectionLabel` | 205-248 | one `addDOMWidget` per heading, `margin:0`, own inline CSS margin (just fixed: `2px 0 3px 0`, was `-2px` causing overlap — commit `a5f4dcd`) |
| Template-builder trigger + floating panel | `createTemplateBuilderWidget` | 1230-1341 | `.sic-builder-trigger` button (`padding:3px 9px;font-size:9px`, cf. A §4.1 "klein, schlecht positioniert"), `position:fixed` panel, `makeDraggable`, outside-click close, `prefers-reduced-motion` handled |
| Format segmented control | `createFormatButtonsWidget` | 863-907 | hides native `image_format` combo (`hideNativeWidget`, 844-851), draws `.sic-fmt-row` of 3 buttons, own `addDOMWidget` (`margin:2`) |
| Save/Preview segmented control | `createSaveModeToggleWidget` | 909-965 | same pattern, hides native `save_mode` combo — **confirmed not actually hiding it in the live install, see Known Issues below** |
| Preview grid (Preview-mode only) | `createPreviewGridWidget` / `updatePreviewGrid` | 1056-1123 | own `addDOMWidget`, `getMinHeight`/`getMaxHeight` toggle between 0 and 130/260 based on content, manual `node.setSize(node.computeSize())` call |
| "Example Output" / Ausgabepfad panel | `createHelpPanelWidget` / `updateHelp` | 1343-1656 | own `addDOMWidget` (`margin:8`), 3-state status badge (`sample`/`fresh`/`stale`, `setHelperStatus` 1553-1579), manual `node.setSize()` call, **never repositioned via `insertWidgetBefore`, so it always lands last in the widget list** — this, not just the hide-bug, is why it visually sits directly under Save Mode |
| Widget-order management | `insertWidgetBefore` | 179-190 | splices a widget to just before a named native widget |
| Live re-render on edit | `hookWidgetUpdates` | 1658-1700 | wraps `widget.callback` + `input`/`change` listeners for a fixed `watchedNames` list — **does not include `save_mode`, `image_quality`, or `loader_priority`**, i.e. changing those doesn't refresh the Ausgabepfad preview live (acceptable today since none of them feed the path string, but worth knowing before adding new contextual show/hide logic keyed on `image_format`/`model_source`/`clip_source`, which *are* watched) |
| Extension registration | `app.registerExtension` | 1702-1762 | `onNodeCreated` and `configure` (wrapped in `requestAnimationFrame`) both call the same widget-build sequence |

### Known Issues found during this investigation (not yet fixed, informs the redesign's first verification step)

1. **"Save Mode" native combo widget renders duplicated, under the Save/Preview pills.** Confirmed via live screenshot at default node width (`Screenshot 2026-10-12 181929.png`) and confirmed interactively by the user: clicking the Preview/Save pills *does* update the native row's value and arrow highlight (same underlying widget object, `modeWidget.value = id` in `save_image_clean.js:944`), proving the JS did run — so `hideNativeWidget(modeWidget)` (`save_image_clean.js:926`) is not suppressing the native row's rendering for this widget, while the identical call for `image_format` (`870`) *does* work (no stray "Image Format" row observed in the same screenshot). Because the same function works for one widget and not the other, **the most likely explanation is a stale browser JS cache showing a version between two commits**, not a structural incompatibility with the hide technique on the current ComfyUI frontend — but this is unconfirmed. **First implementation step: hard-refresh (`Strg+Shift+R`), reload the workflow, and re-check before writing any new code against `hideNativeWidget`.** If the duplicate row survives a hard refresh, `hideNativeWidget`'s mechanism itself needs to change (e.g. confirm against the exact `comfyui_frontend_package` version in `G:\ComfyUI-Easy-Install\python_embeded\Lib\site-packages\comfyui_frontend_package`) before this redesign relies on the same technique for five more widgets.
2. Even with hiding fixed, the native "Save Mode" row and the "Example Output" header sit with effectively no gap (both default `addDOMWidget` row spacing), which is what made them read as one bar to a quick glance. Root-caused: `createHelpPanelWidget`'s widget is never moved via `insertWidgetBefore`, so it just lands wherever `addDOMWidget` appended it (last) — adjacent to whatever happens to be last before it, by accident of call order, not by design. The single-flex-root architecture below removes this entire class of bug, because there is only one `addDOMWidget` left and all internal spacing is one `gap` value.

## Pixaroma reference (primary source, `ComfyUI-Pixaroma` installed at `G:\ComfyUI-Easy-Install\ComfyUI\custom_nodes\ComfyUI-Pixaroma`)

Read directly (not assumed) to answer "how did they get a tidier result":

- `js/save_image/ui.mjs` (318 lines): **one** `addDOMWidget` call (`index.js:1014`, id `"pixaroma_save_image"`) holding `.pix-si-root > .pix-si-inner`, the inner layer `position:absolute;inset:0;display:flex;flex-direction:column;gap:10px` — one spacing source for the entire node body, which is the actual reason it reads as tidy (not a difference in colors or fonts).
- Their own code comment (`ui.mjs:6-8`) documents a real ComfyUI gotcha: *"ComfyUI forces the addDOMWidget ROOT to inline display:block on rebuild / collapse"* — hence the absolutely-positioned inner flex layer as an escape hatch. **Must be verified against our ComfyUI frontend version before relying on it** (A §3's "no assumptions without checking the source or a reproducible test" applies here directly).
- Segmented pill controls (`.pix-si-seg`, `border-radius:999px`) and all action buttons (Open/Copy/Folder) share **one** flex-wrap toolbar row (`.pix-si-btnrow`, `ui.mjs:202-244`), not two independent rows.
- Rare settings (quality, counter digits, which buttons show, button colour) live behind a gear icon in a floating panel (`.pix-si-panel`), confirmed live by the user's own screenshot (`Screenshot 2026-10-12 183511.png`): each row is **label + one-line grey description + right-aligned control** (toggle switch, slider, or segmented control). This row pattern is adopted for our own "Erweitert" panel below.
- Sizing (`index.js:1014-1020`): `getMinHeight` only, computed by measuring the real DOM floor height and rounding to a 4px grid; **no `getMaxHeight`, no custom `computeSize` override** — comment: *"FLOOR only... so the preview area absorbs all free height."*
- **Not copied:** `js/save_image/state.mjs` serializes every setting as one JSON blob into `node.properties.saveImageState`, with a single hidden string input carrying it to Python. See "Why Pixaroma's state model doesn't fit us" below — this is the one piece of their architecture this redesign deliberately does not adopt.

### Why Pixaroma's state model doesn't fit us (recorded from the design discussion)

ComfyUI calls a node's `FUNCTION` with one keyword argument per `INPUT_TYPES` key (confirmed against our own `save_images` signature above). A saved workflow's `widgets_values` is a flat array, positional over the current widget list in declaration order (the existing `nodes.py:1535-1538` comment already documents this constraint for us). Collapsing our 14 individually-typed fields into one JSON blob the way Pixaroma does would:

1. Break **every already-saved workflow** containing this node — their old positional `widgets_values` array would no longer line up with a widget list that now holds one hidden blob field instead of 14 named ones; values could silently land on the wrong field (e.g. a workflow that had `save_mode="Preview"` could silently revert to the `Save` default and start overwriting files, with no error).
2. Break **any API/script caller** that sets fields by name (e.g. `"inputs": {"save_mode": "Preview"}` against ComfyUI's `/prompt` endpoint) — a blob is not individually addressable.
3. Remove the ability to **"Convert to Input"** on any of these fields (a standard ComfyUI feature, letting another node drive e.g. `save_mode` through a graph socket) — not possible against a value packed inside an opaque JSON string.
4. Require either a parse/validate layer in `save_images` or a signature rewrite — both are "backend semantics changed for a prettier frontend," which Appendix A §7 explicitly forbids.

Conclusion, and the central architectural decision of this redesign: **copy the DOM/CSS technique (one root widget, real flexbox, floor-only sizing), never the serialization technique.** Every row in the new layout continues to read/write the existing native widget object (`getWidget(node, name).value = x; widget.callback?.(x)`), exactly as `createFormatButtonsWidget`/`createSaveModeToggleWidget` already do for 2 of the 15 fields today — this redesign extends that same, already-proven-compatible pattern to the rest, rather than inventing a new one.

## Target Information Architecture

Resolves Appendix A §6 ("the grouping is a proposal, must be checked against real functional dependencies") against the actual `nodes.py` tooltips and defaults read above, refined through the concept mockup (Appendix B) and conversation.

**SAVE LAYOUT**
- *Ordnerstruktur* heading + Build trigger → `path_template`
- Modellname (dropdown row) → `model_source`
- Text-Encoder (dropdown row) → `clip_source`
- Top Folder (text row, always visible — independent of source, structurally part of the path, used often) → `subfolder`
- Custom Model Name / Custom Text Encoder Name (text rows, **shown only when the matching source dropdown = "Custom"**) → `model_folder` / `clip_folder`. Not an arbitrary grouping choice: `nodes.py:1519` and `:1530` already document these as "used directly in Custom mode, and also as a fallback" — the contextual reveal follows the actual dependency, confirmed live in the default-width screenshot where both sat empty and prominent for the ~75% of users who never touch "Custom".

**FILENAME**
- *Dateiname* heading + Build trigger → `filename_datetime`
- Datei vorhanden (dropdown row) → `collision_mode`
- Detection-Informationen (dropdown row, 3 states Off/Summary/Verbose — A §4.5's "binary switch" caution doesn't apply, this already has 3 states) → `detection_info`

**OUTPUT**
- Bildformat (segmented control, unchanged mechanism) → `image_format`
- Image Quality (styled native `<input type=range>` row) → `image_quality`, **enabled only when `image_format != PNG`**, matching the existing tooltip ("Ignored when Image Format is PNG", `nodes.py:1556`) — resolves A §4.7's open question against actual backend behavior, not a guess
- Export Workflow Metadata (new Switch component) → `export_workflow_metadata`, **enabled only when `image_format == PNG`**, mirroring the existing tooltip ("PNG only", `nodes.py:1497`)
- Speichermodus (segmented control, unchanged mechanism) → `save_mode`
- Preview grid (existing, Preview-mode only), directly below

**ERWEITERT (gear-triggered floating panel, Pixaroma row pattern: label + description line + control)**
- Loader Priority (dropdown row, with its existing long tooltip surfaced as the visible description line) → `loader_priority`

**AUSGABEPFAD** (renamed from "Example Output", final section, own clear boundary — no more accidental adjacency to Save Mode)
- Existing 3-state badge logic (`sample`/`fresh`/`stale`) and detection detail lines preserved exactly as implemented today (`setHelperStatus`, `buildDetectionSnapshotLines`) — this already satisfies A §4.9's 4-state requirement (sample / fresh real run / stale / warning-note), it just needs to stop colliding visually with its neighbor.

## New Reusable Components

All of these live inside the **one** root flex widget; all read/write the existing native widget as their data source.

| Component | Used for | Technique |
|---|---|---|
| Dropdown row | Model Name, Text Encoder, If File Exists, Detection Info, Loader Priority | Transparent native `<select>` (`opacity:0`, exact same box as the visible label/value/chevron row underneath) — gets native keyboard nav, scroll-wheel, and the OS dropdown list for free, satisfying A §4.4's "vollständige Tastaturbedienbarkeit" without hand-building a listbox/ARIA stack |
| Segmented control | Bildformat, Speichermodus | Existing `.sic-fmt-row`/`.sic-fmt-btn` pattern, kept, just regrouped under one OUTPUT heading in the same flex root |
| Switch | Export Workflow Metadata | New: visible pill track + native `<input type=checkbox>` for keyboard/a11y, same overlay idea as the dropdown row |
| Slider row | Image Quality | Styled native `<input type=range>`, CSS `accent-color: var(--sic-accent)` — no overlay needed, range inputs are natively CSS-styleable |
| Text row | Save Layout, Filename, Top Folder, Custom Names | Existing native STRING widget, kept as the data source; visually wrapped the same way as the dropdown rows for consistent height/label alignment. Already supports full cursor navigation and horizontal scroll while focused (native `<input>` behavior) — A §4.2's complaint is about the *unfocused* rendering being clipped with no indication more text exists; fixed by giving it a proper truncating row with `title=` (full value on hover) rather than LiteGraph's bare canvas clip |
| Section heading + Build trigger | Ordnerstruktur, Dateiname | Existing pattern, enlarged per A §4.1 (bigger click target, builder sits next to the readable heading, not the tiny eyebrow label) |
| Gear / Advanced panel | Loader Priority (room for future rarely-used settings) | Reuses the existing floating-panel mechanism already built for the template builder (`position:fixed`, `makeDraggable`, outside-click close, `prefers-reduced-motion`), row style per the Pixaroma reference above |

## Design System (binding for this redesign and future work on this node)

| Token | Value | CSS variable |
|---|---|---|
| Base spacing | 8px | `--sic-space-md` |
| Small spacing | 4px | `--sic-space-sm` |
| Group spacing | 14px | `--sic-space-lg` |
| Outer/node-edge spacing | 14px | `--sic-space-outer` |
| Standard row height | 30px | `--sic-row-height` |
| Compact button minimum | 28px | `--sic-btn-min` |
| Base text | 12px | `--sic-font-base` |
| Secondary text | 11px | `--sic-font-sub` |
| Section heading | 11px, 600 weight | `--sic-font-section` |
| Corner radius | 7px | `--sic-radius` |
| Pill radius | 999px | `--sic-radius-pill` |
| Accent color | `#4c86e0` (existing blue, unchanged — now a variable instead of hardcoded 5×) | `--sic-accent` |

These are starting values per Appendix A §5's own framing ("Entwurfswerte, anschließend im laufenden ComfyUI überprüfen") — verify visually against the real running node before locking them in, not just by reading the CSS.

Principles carried forward from this session's design-skill research (Apple HIG / Emil Kowalski, via the locally available `apple-design` and `improve-animations` skills — the external `dickwu/apple-design-skill` and `emilkowalski/skills` GitHub repos named in Appendix A were not available as installed skills in this environment, so local equivalents were used; fetch the externals directly if a future session needs their exact wording):

- **One spacing source per region** (flex `gap`, no per-widget margin hacks) — directly fixes the root cause of the Build-button overlap bug fixed earlier this session (`a5f4dcd`)
- **Immediate feedback** on press, no artificial delay
- **Animation only with purpose** — keep the existing `--sic-ease-out` press/panel transitions, add nothing decorative
- **Restrained color** — accent only for active/selected state, never decoration
- **Progressive disclosure** — gear panel, contextual Custom-Name/Quality/Metadata fields
- **Reduced motion respected** on every new transition, extending the existing `@media (prefers-reduced-motion: reduce)` block

## Dynamic Sizing Strategy

Replace the current three scattered `node.setSize(node.computeSize())` calls (`updatePreviewGrid` ~1102/1118-1121, `updateHelp` ~1651-1655) with the Pixaroma-proven pattern: **one** root `addDOMWidget` with `getMinHeight` computed from the real measured DOM height (rounded to a 4px grid), **no `getMaxHeight`**, no custom `computeSize` override. The node grows freely; a user's manual resize is never fought.

**Must verify before implementation relies on it:** Pixaroma's own comment about ComfyUI forcing the `addDOMWidget` root to `display:block` on rebuild/collapse, against our actual `comfyui_frontend_package` version (`G:\ComfyUI-Easy-Install\python_embeded\Lib\site-packages\comfyui_frontend_package`) — confirm with a real test, not by assumption, per Appendix A §3.

## Compatibility & Data Safety (binding, see Appendix A §7)

- `nodes.py` `INPUT_TYPES` keys, order, and types: **unchanged**.
- `save_images` signature: **unchanged**.
- Every row's control continues to read/write the existing native widget object — no new `node.properties` blob, no new hidden state input.
- No existing workflow needs its `SaveImageClean` node replaced after this ships (this was raised mid-session as a real pain point the user is hitting today — root-caused to browser JS caching and, separately, to node-definition vs. already-placed-instance timing; recorded as a standing test discipline below, not something this redesign needs to newly solve, since `INPUT_TYPES` itself never changes here).

## Testing Plan

All of Appendix A §8's list, plus, specific to this session's findings:

- Hard-refresh (`Strg+Shift+R`) **and** reload-the-workflow, not just a node replace, after every iteration — distinguishes real bugs from stale browser cache (this exact confusion cost real time twice this session).
- Explicit first test: does `hideNativeWidget` fully suppress the native row for `save_mode` after a confirmed hard refresh? (see Known Issue #1 above) — blocks trusting the same technique for the five new dropdown rows if it doesn't.
- Contextual visibility: toggle `model_source`/`clip_source` to "Custom" and back (Custom Name rows appear/disappear correctly); toggle `image_format` between PNG and JPEG/WebP (Quality/Metadata rows swap enabled state correctly).
- Real visual check in a running ComfyUI, screenshots compared against the "before" screenshots already captured this session (`Screenshot 2026-10-12 171840.png` wide view, `Screenshot 2026-10-12 181929.png` default width) — per A §9, code review and automated tests alone are never reported as "visually verified."

## Acceptance Criteria

Appendix A §9 verbatim, plus: the "Save Mode" duplicate-row issue is resolved (root cause confirmed, not just hidden behind a CSS patch), and the design-token table above is the single source of truth for spacing/color/radius across every component (no new hardcoded pixel values introduced alongside the token system).

## Open Items for the Implementation Plan

1. Confirm the `hideNativeWidget`/browser-cache question live before writing new widget-hiding code for 5 more fields.
2. Confirm the Pixaroma `display:block`-on-rebuild gotcha against our actual frontend version before committing to the absolutely-positioned-inner-layer escape hatch.
3. Decide final pixel values for the design-token table against the real running node (the table above is a starting point, per A §5).

---

## Appendix A — Original requirements brief (verbatim, user-supplied, binding)

> # Auftrag: Vollständiges UI/UX-Redesign von Save Image Organized
>
> ## 1. Zielsetzung
>
> Überarbeite die Benutzeroberfläche des ComfyUI-Custom-Nodes **Save Image Organized** grundlegend.
>
> Repository:
> https://github.com/Delcado19/comfyui-save-image-organized
>
> Verbindliche Designreferenzen:
>
> - Apple Design Skill: https://github.com/dickwu/apple-design-skill
> - Emil Kowalski Design Skills: https://github.com/emilkowalski/skills
> - Vergleichsreferenz: Save Image Pixaroma (siehe bereitgestellten Screenshot)
>
> **Dies ist kein kosmetischer CSS-Fix. Es handelt sich um ein strukturelles UI/UX-Redesign bei vollständigem Erhalt der vorhandenen Funktionalität.**
>
> Der linke Node im Screenshot ist das zu überarbeitende Produkt. Der rechte Pixaroma-Node ist ein Vergleich für visuelle Qualität, Konsistenz und Verständlichkeit, keine Vorlage zum blinden Kopieren.
>
> ## 2. Designreferenzen verpflichtend auswerten
>
> ### Apple
>
> Lies die tatsächlichen Dateien aus `dickwu/apple-design-skill`, insbesondere:
>
> - `SKILL.md`
> - `references/hig/layout.md`
> - `references/hig/typography.md`
> - `references/hig/color.md`
> - `references/hig/accessibility.md`
> - `references/hig/buttons.md`
> - `references/hig/text-fields.md`
> - `references/hig/pop-up-buttons.md`
> - `references/hig/dark-mode.md`
> - `references/cross-platform.md`
>
> Übertrage die einschlägigen Grundsätze auf die ComfyUI-Oberfläche.
>
> Wichtige Ziele:
>
> - Eindeutige visuelle Hierarchie
> - Saubere Ausrichtung
> - Konsistente Bedienelemente
> - Lesbare Typografie
> - Verständliche Interaktionszustände
> - Barrierearme Nutzung
> - Gute Skalierbarkeit
> - Zurückhaltender Farbeinsatz
> - Progressive Disclosure
>
> Verwende keine Liquid-Glass-Effekte, nur um Apple zu imitieren. Die Gestaltung soll sich natürlich in ComfyUI einfügen.
>
> ### Emil Kowalski
>
> Lies mindestens:
>
> - `skills/emil-design-eng/SKILL.md`
> - `skills/apple-design/SKILL.md`
> - `skills/animation-performance/SKILL.md`, soweit für Interaktionen relevant.
>
> Berücksichtige insbesondere:
>
> - Präzision der Abstände und Ausrichtung
> - Konsistente Komponenten und Zustände
> - Unmittelbares visuelles Feedback
> - Sinnvolle Animationen statt Dekoration
> - Hochwertige Typografie
> - Gut erkennbare Interaktionsflächen
> - Konsistenz zwischen sichtbarem Zustand und tatsächlichem Verhalten
>
> Animationen nur einsetzen, wenn sie eine konkrete Funktion erfüllen. Bei häufig verwendeten ComfyUI-Bedienelementen sind direkte, verzögerungsfreie Reaktionen wichtiger als Bewegung.
>
> ## 3. Technische Bestandsaufnahme
>
> Untersuche vor Änderungen:
>
> - `nodes.py`
> - `web/save_image_clean.js`
> - Die Widget-Registrierung
> - Die dynamische Größenberechnung
> - Die DOM-Widget-Implementierung
> - Die Template-Builder
> - Die Preview- und Detection-Logik
> - Die verfügbaren ComfyUI-Frontend-APIs
> - Die vorhandenen automatisierten Tests
>
> Erstelle eine Zuordnung aller sichtbaren Bedienelemente zu ihrem tatsächlichen Widget beziehungsweise ihrer Implementierung.
>
> Unterscheide sauber zwischen nativen ComfyUI-Widgets und zusätzlichen DOM-Widgets.
>
> Prüfe, ob das bestehende Layout mit der aktuell verwendeten ComfyUI-Frontend-Version zuverlässig funktionieren kann.
>
> **Keine Annahmen über API-Verhalten ohne Prüfung des Quellcodes oder eines reproduzierbaren Tests.**
>
> ## 4. Konkrete Layoutfehler beseitigen
>
> ### 4.1 Build-Buttons
>
> Derzeit sind die Build-Buttons klein, schlecht positioniert und optisch nicht sauber mit ihren Bereichen verbunden.
>
> Anforderungen:
>
> - Einheitliche Buttonhöhe
> - Gleiche Gestaltung für beide Builder
> - Saubere vertikale Zentrierung
> - Ausreichende Klickfläche
> - Klare Zuordnung zur jeweiligen Eingabe
> - Kein Abschneiden oder Überlappen
> - Eindeutiger Hover-, Pressed-, Focus- und Disabled-Zustand
> - Verständliche Beschriftung, beispielsweise „Builder" oder „Bearbeiten"
>
> Die Builder müssen auch bei veränderter Node-Breite korrekt positioniert bleiben.
>
> ### 4.2 Save Layout
>
> Die lange Ordnerstruktur ist abgeschnitten.
>
> Anforderungen:
>
> - Der Benutzer muss die gesamte Zeichenfolge bearbeiten können.
> - Einzeilige Darstellung ist nur zulässig, wenn horizontales Scrollen und Cursor-Navigation korrekt funktionieren.
> - Alternativ eine kompakte, erweiterbare mehrzeilige Eingabe verwenden.
> - Template-Variablen dürfen nicht beschädigt werden.
> - Fehlermeldungen gehören direkt zur betroffenen Eingabe.
> - Die Darstellung des Builders muss mit der Eingabe synchron sein.
>
> ### 4.3 Filename
>
> Dateinameneingabe und Builder müssen exakt dieselben Gestaltungsregeln wie Save Layout verwenden.
>
> Beide Bereiche müssen wie Komponenten derselben Anwendung aussehen.
>
> ### 4.4 Dropdowns
>
> Die vorhandenen Dropdowns wirken optisch zu flach und zusammengedrängt.
>
> Anforderungen:
>
> - Einheitliche Zeilenhöhe
> - Einheitliche Innenabstände
> - Gleiche Pfeilsymbole
> - Gleiche Textposition
> - Klare Trennung von Label und ausgewähltem Wert
> - Ausreichende Breite für Werte
> - Verständliche Zustände
> - Vollständige Tastaturbedienbarkeit, soweit vom Frontend unterstützt
>
> Keine eigenmächtigen Ersatz-Dropdowns implementieren, wenn native ComfyUI-Komponenten diese Anforderungen zuverlässig erfüllen.
>
> ### 4.5 Detection Info
>
> Die Option darf nicht rätselhaft bleiben.
>
> Prüfe ihre tatsächliche Funktion und überarbeite Beschriftung sowie Darstellung.
>
> Verwende einen semantisch passenden Steuerelementtyp. Ein binärer Schalter darf nicht als Dropdown dargestellt werden, wenn ausschließlich zwei Zustände existieren. Wenn mehrere Zustände verfügbar sind, muss die Auswahl diese verständlich darstellen.
>
> ### 4.6 Bildformat
>
> PNG, JPEG und WebP müssen eine echte, optisch einheitliche segmentierte Auswahl ergeben.
>
> Anforderungen:
>
> - Gleichmäßige Höhe
> - Sichtbare Trennung
> - Genau eine aktive Auswahl
> - Gleiche Eckenradien
> - Ausgewogene Textposition
> - Keine benachbarten oder überlappenden Farbflächen
> - Klarer Fokuszustand
>
> ### 4.7 Image Quality
>
> Das Qualitätselement muss eindeutig als Slider erkennbar sein.
>
> Zeige einen verständlichen numerischen Wert, beispielsweise `95`.
>
> Falls Qualität bei PNG technisch keine Wirkung hat, prüfe, ob der Regler deaktiviert oder kontextabhängig ausgeblendet werden muss. Die Entscheidung muss dem tatsächlichen Backend-Verhalten entsprechen.
>
> ### 4.8 Save, Preview und Save Mode
>
> Überprüfe zuerst die tatsächliche Bedeutung sämtlicher vorhandener Save-/Preview-Optionen.
>
> Unterscheide zwischen:
>
> - Bildformat
> - Speichermodus
> - Vorschauverhalten
> - Eventuellen unmittelbaren Aktionen
>
> Einstellungen dürfen nicht aussehen wie Aktionen und Aktionen nicht wie Einstellungen.
>
> Es darf keinen Bereich geben, in dem mehrere Zeilen optisch zusammenstoßen oder eine Auswahl versehentlich als Bestandteil der nächsten Zeile interpretiert wird.
>
> ### 4.9 Example Output
>
> Der untere Preview-Bereich muss grundlegend überarbeitet werden.
>
> Anforderungen:
>
> - Eigenständiger, sauber abgegrenzter Bereich
> - Eindeutige Überschrift
> - Klarer Status der Vorschau
> - Gute Lesbarkeit des Dateipfads
> - Keine Überlagerung mit Save Mode
> - Kein abgeschnittener Inhalt
> - Bei Bedarf dynamische Höhe
> - Optional eine Schaltfläche zum Kopieren des vollständigen Pfads
>
> Die Zustände müssen unterscheidbar bleiben:
>
> 1. Beispiel mit Platzhalterwerten
> 2. Ergebnis aus dem letzten erfolgreichen Workflow-Lauf
> 3. Veraltete Erkennungsdaten nach Änderungen
> 4. Warnung beziehungsweise Fehler
>
> Eine simulierte Vorschau darf niemals als tatsächlich gespeicherter Pfad ausgegeben werden.
>
> ### 4.10 Dynamische Node-Größe
>
> Prüfe insbesondere das Zusammenspiel von:
>
> - `computeSize()`
> - `setSize()`
> - `addDOMWidget()`
> - `getMinHeight()`
> - `getMaxHeight()`
> - Tatsächlicher DOM-Höhe
> - Zoomverhalten
> - Dynamisch ein- und ausgeblendeten Bereichen
>
> Ersetze die starre Höhenlogik dort, wo sie dynamischen Inhalt nicht zuverlässig aufnehmen kann.
>
> Keine kosmetischen Pixel-Offsets verwenden, um Renderingfehler zu überdecken.
>
> Der Node muss beim Vergrößern, Verkleinern und Ändern der Eingaben stabil bleiben.
>
> ## 5. Einheitliches Designsystem
>
> Definiere zentrale Gestaltungsregeln.
>
> Als Ausgangspunkt, anschließend im laufenden ComfyUI überprüfen:
>
> | Element | Zielwert |
> |---|---|
> | Grundabstand | 8 px |
> | Kleine Abstände | 4 px |
> | Gruppenabstand | 12–16 px |
> | Außenabstand | 12–16 px |
> | Standard-Widgethöhe | 28–32 px |
> | Kompakte Buttons | Mindestens 28 px, sofern praktikabel |
> | Normaler Text | 12–13 px |
> | Sekundärer Text | 11–12 px |
> | Abschnittsüberschriften | 11–12 px, Semibold |
> | Eckenradius | 6–8 px |
> | Animation | Nur bei erkennbarem Nutzwert |
>
> Dies sind Entwurfswerte, keine starren Vorgaben für jede ComfyUI-Version.
>
> Farben, Abstände und Schriftgrößen sollen zentral verwaltet und möglichst aus den Theme-Variablen von ComfyUI abgeleitet werden.
>
> Vermeide unnötige `!important`-Regeln und globale CSS-Selektoren, die andere Nodes beeinflussen könnten.
>
> ## 6. Informationsarchitektur
>
> Erarbeite eine sinnvolle Gruppierung:
>
> **Ordnerstruktur**
> - Save Layout
> - Model Name
> - Text Encoder Name
> - Top Folder
> - Custom Names, sofern benötigt
>
> **Dateiname**
> - Filename
> - Collision Handling
> - Detection Info
>
> **Bildausgabe**
> - Bildformat
> - Bildqualität
> - Metadata Export
> - Loader Priority
> - Speichermodus
>
> **Ergebnisvorschau**
> - Aufgelöster Pfad
> - Erkennungsstatus
> - Warnungen
> - Zusätzliche Details
>
> Die Gruppierung ist ein Vorschlag und muss mit den tatsächlichen Funktionsabhängigkeiten abgeglichen werden.
>
> Selten verwendete Einstellungen sollen über aufklappbare Bereiche erreichbar sein.
>
> Keine Funktion darf verloren gehen.
>
> ## 7. Kompatibilität und Datensicherheit
>
> Unbedingt erhalten:
>
> - Bestehende Node-Typen und Identifikatoren
> - Backend-Eingaben und Ausgaben
> - Gespeicherte Workflow-Kompatibilität
> - Existierende Template-Syntax
> - Variablenersetzung und Filter
> - Modell- und Text-Encoder-Erkennung
> - Dateikollisionsbehandlung
> - Speicherpfad-Semantik
> - PNG-Metadaten
> - Format- und Qualitätsverhalten
> - Bestehende Defaults, sofern keine ausdrücklich begründete Änderung vereinbart wurde
>
> Keine Änderung an der Backend-Semantik allein für ein schöneres Frontend.
>
> Wenn eine UI-Überarbeitung Änderungen an serialisierten Widget-Werten erfordert, müssen Kompatibilität und Migration ausdrücklich gelöst werden.
>
> ## 8. Testanforderungen
>
> Teste mindestens:
>
> - Kleine und große Node-Breiten
> - Zoomstufen
> - Lange Template-Zeichenfolgen
> - Lange Modellnamen und Text-Encoder-Namen
> - Leere Eingaben
> - Umschalten aller Dropdowns
> - Alle Bildformate
> - Alle Speichermodi
> - Dynamische Vorschauänderungen
> - Ein- und ausgeblendete Detection-Details
> - Speichern und erneutes Laden eines Workflows
> - Bereits vorhandene Workflows
> - Helles und dunkles Theme, soweit relevant
> - Tastaturfokus und Bedienbarkeit
> - Keine Überschneidungen
> - Keine abgeschnittenen Texte ohne Zugriff auf den vollständigen Inhalt
>
> Automatisierte Tests sind erforderlich, aber nicht ausreichend.
>
> **Führe zusätzlich eine tatsächliche visuelle Prüfung in ComfyUI durch.** Ein erfolgreicher JavaScript-Syntaxcheck beweist nicht, dass das Layout richtig gerendert wird.
>
> Vergleiche den fertigen Node anhand neuer Screenshots mit dem Ausgangszustand.
>
> ## 9. Abnahmekriterien
>
> Die Arbeit gilt erst als abgeschlossen, wenn:
>
> - Keine Bedienelemente überlappen.
> - Die Builder korrekt ausgerichtet sind.
> - Alle Dropdowns konsistent aussehen.
> - Sämtliche Texte lesbar sind.
> - Die Vorschau ihren Inhalt vollständig zugänglich macht.
> - Der Node bei Größenänderungen stabil bleibt.
> - Selten verwendete Funktionen sinnvoll eingeordnet sind.
> - Ein konsistentes Designsystem verwendet wird.
> - Alle vorhandenen Funktionen erhalten bleiben.
> - Alte Workflows kompatibel bleiben.
> - Die automatisierten Tests erfolgreich sind.
> - Eine echte visuelle Kontrolle durchgeführt und dokumentiert wurde.
>
> Melde keine Arbeit als visuell geprüft, wenn nur der Quellcode untersucht oder Tests ausgeführt wurden.
>
> ## 10. Vorgehensweise und Abschluss
>
> Arbeite in dieser Reihenfolge:
>
> 1. Quellcode und Designreferenzen lesen.
> 2. Sichtbare Fehler mit Implementierungsstellen abgleichen.
> 3. Technische Ursachen für Überlagerungen ermitteln.
> 4. Neues Layout und Designsystem entwerfen.
> 5. Änderungen implementieren.
> 6. Automatisierte Tests durchführen.
> 7. Visuelle Kontrolle im echten ComfyUI.
> 8. Festgestellte Fehler nachbessern.
> 9. Dokumentation synchronisieren.
> 10. Änderungen committen und pushen, sofern die Projektregeln dies vorsehen.
>
> Lies vor Git-Operationen die Anweisungen in `AGENTS.md`.
>
> Liefere am Ende eine nachvollziehbare Gegenüberstellung der alten und neuen Komponenten, einen Testbericht und die verbleibenden bekannten Einschränkungen.
>
> **Keine oberflächliche Designpolitur. Keine vorgetäuschte visuelle Verifikation. Keine Funktionsverluste. Keine weiteren Layout-Hacks.**
>
> Das Ziel ist ein hochwertiger ComfyUI-Node, dessen Gestaltung und Bedienung dem Funktionsumfang gerecht werden.

## Appendix B — Concept mockup (user-supplied, visual-language reference)

Source file: `C:\Users\Delcado\Pictures\Screenshots\Screenshot 2026-10-12 174942.png` ("3. Das Design, das ich für deinen Node verlangen würde"). The mockup's own footer explicitly disclaims it as "Nur eine konzeptionelle Darstellung der visuellen Hierarchie, kein vollständiger Funktionsumfang und kein ausführbarer ComfyUI-Node" — a simplified sketch of the hierarchy, not a literal pixel spec, and it deliberately omits Top Folder, Custom Names, Export Workflow Metadata, Image Quality, and Loader Priority (all reintroduced above via the contextual/gear-panel rules).

Captured structure: a "Konzept" badge top-right; **SAVE LAYOUT** eyebrow label; "Ordnerstruktur" bold heading with a pill "⊞ Builder" button at its row's right edge; the template string shown in full below as plain monospace secondary text; a divider; "Modellname"/"Text-Encoder" as flat label-left/value-right rows ending in a single chevron, no box, no cycle-arrows; **FILENAME** eyebrow label; "Dateiname" heading with its own Builder button; "Datei vorhanden"/"Detection-Informationen" as the same flat dropdown-row style; **OUTPUT** eyebrow label; "Bildformat" and "Speichermodus" as compact, right-aligned segmented pills next to their label (not full-width bars); a final "Ausgabepfad" heading with the resolved path shown as plain monospace text, no competing badge visible in this simplified sketch.

The central implication this redesign had to resolve (see Architecture above): this flat, borderless dropdown-row look is **not achievable with LiteGraph's native canvas-drawn combo widgets** (which always render their own box background and cycle-arrows) — reaching it requires the native widget hidden and a custom DOM row drawn in its place, the same way `image_format`/`save_mode` already work today. The user explicitly ruled on this tension with Appendix A §4.4 ("ganz pragmatisch, wenn comfyui mit bordmitteln... nicht die möglichkeit geben kann... dann müssen wir wohl einen eigenen UI stack bauen") — native-first is overridden by the visual target when the two conflict, keeping native behavior (keyboard, scroll-wheel, OS dropdown list) via the transparent-overlay technique rather than a hand-built listbox.
