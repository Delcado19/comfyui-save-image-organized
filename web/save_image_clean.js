import { app } from "../../scripts/app.js";

const NODE_NAME = "SaveImageClean";
const MODEL_OPTIONS = ["Friendly", "Exact", "Custom"];
const CLIP_OPTIONS = ["Friendly", "Exact", "Custom"];

const LABELS = {
    path_template: "Save Layout",
    model_source: "Model Name",
    clip_source: "Text Encoder Name",
    filename_datetime: "Filename",
    collision_mode: "If File Exists",
    detection_info: "Detection Info",
    export_workflow_metadata: "Export Workflow Metadata",
    subfolder: "Top Folder",
    model_folder: "Custom Model Name",
    clip_folder: "Custom Text Encoder Name",
};

const SAMPLE_MODEL = "flux-2-klein-9b-Q5_K_M.gguf";
const SAMPLE_CLIP = "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf";
const DEFAULT_LAYOUT = "%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%";
const DEFAULT_FILENAME = "%date:yyyy-MM-dd_hh-mm-ss%";
const VARIABLE_TOKEN_RE = /%([A-Z0-9_]+)%/g;
const NODE_WIDGET_TOKEN_RE = /%([^%./\\]+)\.([^%./\\]+)%/g;
const UNKNOWN_TOKEN_RE = /%([^%]+)%/g;
const COMMON_EXTENSIONS = [
    ".safetensors",
    ".gguf",
    ".ckpt",
    ".pt",
    ".pth",
    ".bin",
    ".onnx",
];
const DATE_TOKEN_RE = /yyyy|yy|hh|h|MM|M|dd|d|mm|m|ss|s/g;
const SCALED_FP8_RE = /^(.*?)(?:[ ._-]+)?FP8[ ._-]*(E4M3FN|E5M2)[ ._-]*SCALED$/i;
const QUANT_RE = /^(.*?)(?:[ ._-]+)?(Q\d+_K_[MS]|Q\d+_K|Q\d+_0|Q\d+|IQ\d+_[A-Z]+|FP8_e4m3fn|FP8_e5m2|BF16|FP16|F16|FP32)$/i;
const DISPLAY_TAG_ABBREVIATIONS = {
    abliterated: "[Ablt]",
    instruct: "[Inst]",
    heretic: "[Her]",
    uncensored: "[Unc]",
    decensored: "[Dec]",
    thinking: "[Think]",
    reasoning: "[Rsn]",
    coder: "[Cod]",
    creative: "[Crtv]",
    roleplay: "[RP]",
    roleplaying: "[RP]",
    vision: "[Vis]",
    preview: "[Prev]",
    turbo: "[Tbo]",
};
const DISPLAY_DROP_WORDS = new Set(["gguf", "gptq", "awq"]);
const KNOWN_IMAGE_MODEL_DISPLAY_ALIASES = [
    ["flux2klein9b", "FLUX.2 Klein 9B"],
    ["flux2klein4b", "FLUX.2 Klein 4B"],
    ["flux2dev", "FLUX.2 Dev"],
    ["flux1kontextdev", "FLUX.1 Kontext Dev"],
    ["flux1filldev", "FLUX.1 Fill Dev"],
    ["flux1schnell", "FLUX.1 Schnell"],
    ["flux1dev", "FLUX.1 Dev"],
    ["hidreame11", "HiDream E1.1"],
    ["hidreame1", "HiDream E1"],
    ["hidreami1full", "HiDream I1 Full"],
    ["hidreami1fast", "HiDream I1 Fast"],
    ["hidreami1dev", "HiDream I1 Dev"],
    ["hidreami1", "HiDream I1"],
    ["qwenimageedit2511", "Qwen Image Edit 2511"],
    ["qwenimageedit2509", "Qwen Image Edit 2509"],
    ["qwenimageedit", "Qwen Image Edit"],
    ["qwenimage", "Qwen Image"],
    ["ovisimage7b", "Ovis Image"],
    ["ovisimage", "Ovis Image"],
    ["newbieimageexp01", "NewBie Image Exp0.1"],
    ["omnigen2", "OmniGen2"],
    ["ernieimageturbo", "ERNIE Image Turbo"],
    ["ernieimage", "ERNIE Image"],
    ["zimageturbo", "Z-Image Turbo"],
    ["zit", "Z-Image Turbo"],
    ["zimage", "Z-Image"],
    ["stablediffusion15", "Stable Diffusion 1.5"],
    ["sd15", "Stable Diffusion 1.5"],
];
const KNOWN_TEXT_ENCODER_DISPLAY_ALIASES = [
    ["qwen34b", "Qwen3 4B"],
    ["qwen25vl", "Qwen2.5 VL"],
    ["qwen257b", "Qwen2.5 7B"],
    ["clipl", "CLIP-L"],
    ["clipg", "CLIP-G"],
    ["t5xxl", "T5 XXL"],
    ["oldt5xxl", "Old T5 XXL"],
    ["t5base", "T5 Base"],
    ["mt5xl", "mT5 XL"],
    ["umt5xxl", "UMT5 XXL"],
    ["gemma22b", "Gemma 2 2B"],
    ["llama", "Llama"],
    ["bert", "BERT"],
];
const VALID_TEMPLATE_VARIABLES = new Set([
    "TOP_FOLDER",
    "MODEL_NAME",
    "TEXT_ENCODER_NAME",
    "FILENAME",
    "WIDTH",
    "HEIGHT",
    "SEED",
    "BATCH_INDEX",
    "FRIENDLY_MODEL_NAME",
    "EXACT_MODEL_NAME",
    "CUSTOM_MODEL_NAME",
    "FRIENDLY_TEXT_ENCODER_NAME",
    "EXACT_TEXT_ENCODER_NAME",
    "CUSTOM_TEXT_ENCODER_NAME",
]);
const DISPLAY_WORD_RE = /[A-Z]+(?=[A-Z][a-z]|\d|[^A-Za-z0-9]|$)|[A-Z]?[a-z]+|\d+(?:\.\d+)?/g;

function getWidget(node, name) {
    return (node.widgets || []).find((widget) => widget.name === name);
}

function setFriendlyLabels(node) {
    for (const [name, label] of Object.entries(LABELS)) {
        const widget = getWidget(node, name);
        if (widget) {
            widget.label = label;
        }
    }
}

function insertWidgetBefore(node, widget, targetName) {
    const widgets = node.widgets || [];
    const widgetIndex = widgets.indexOf(widget);
    const targetIndex = widgets.findIndex((item) => item?.name === targetName);
    if (widgetIndex === -1 || targetIndex === -1 || widgetIndex === targetIndex - 1) {
        return;
    }

    widgets.splice(widgetIndex, 1);
    const newTargetIndex = widgets.findIndex((item) => item?.name === targetName);
    widgets.splice(Math.max(newTargetIndex, 0), 0, widget);
}

function ensureSectionLabel(node, key, text, targetName) {
    const storeKey = `__saveImageCleanSection_${key}`;
    if (node[storeKey]) {
        insertWidgetBefore(node, node[storeKey], targetName);
        return node[storeKey];
    }

    const element = document.createElement("div");
    element.textContent = text;
    element.style.cssText = [
        "font-size:10px",
        "font-weight:600",
        "letter-spacing:0.03em",
        "text-transform:uppercase",
        "color:#9d9d9d",
        "padding:0 8px",
        "margin:2px 0 -2px 0",
        "pointer-events:none",
    ].join(";");

    const widget = node.addDOMWidget(`save_image_clean_section_${key}`, "custom", element, {
        getMinHeight: () => 14,
        getMaxHeight: () => 16,
        serialize: false,
        hideOnZoom: false,
        margin: 0,
    });
    node[storeKey] = widget;
    insertWidgetBefore(node, widget, targetName);
    return widget;
}

function stripKnownExtension(value) {
    const text = String(value || "").trim();
    const lower = text.toLowerCase();
    for (const ext of COMMON_EXTENSIONS) {
        if (lower.endsWith(ext)) {
            return text.slice(0, -ext.length);
        }
    }
    return text;
}

function basenameWithoutKnownExtension(value) {
    const stripped = stripKnownExtension(value);
    const parts = stripped.split(/[\\/]+/).filter(Boolean);
    return parts.length ? parts[parts.length - 1] : stripped;
}

function formatQuantDisplay(quant) {
    const normalized = String(quant || "").toUpperCase();
    const exactMap = {
        Q3_K_M: "[3K-M]",
        Q3_K_S: "[3K-S]",
        Q4_K_M: "[4K-M]",
        Q4_K_S: "[4K-S]",
        Q5_K_M: "[5K-M]",
        Q5_K_S: "[5K-S]",
        Q6_K: "[6K]",
        Q8_0: "[Q8]",
        Q8: "[Q8]",
        FP8_E4M3FN: "[FP8-E4M3FN]",
        FP8_E5M2: "[FP8-E5M2]",
        FP32: "[FP32]",
        BF16: "[BF16]",
        FP16: "[FP16]",
        F16: "[FP16]",
    };
    if (exactMap[normalized]) {
        return exactMap[normalized];
    }
    const match = normalized.match(/^IQ(\d+)_([A-Z]+)$/);
    if (match) {
        return `[IQ${match[1]}-${match[2]}]`;
    }
    const zeroQuant = normalized.match(/^Q(\d+)_0$/);
    if (zeroQuant) {
        return `[Q${zeroQuant[1]}]`;
    }
    const plainQuant = normalized.match(/^Q(\d+)$/);
    if (plainQuant) {
        return `[Q${plainQuant[1]}]`;
    }
    return "";
}

function joinDisplayParts(parts) {
    let result = "";
    for (const part of parts) {
        if (!part) {
            continue;
        }
        if (!result) {
            result = part;
            continue;
        }
        if (result.endsWith("]") && part.startsWith("[")) {
            result += part;
        } else {
            result += ` ${part}`;
        }
    }
    return result.trim();
}

function normalizeVersionToken(value) {
    const match = String(value || "").trim().match(/^v(\d+(?:\.\d+)*)$/i);
    return match ? `V${match[1]}` : "";
}

function normalizeDisplayIdentifier(value) {
    return String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function iterDisplayWords(value) {
    const text = String(value || "");
    return Array.from(text.matchAll(DISPLAY_WORD_RE)).map((match) => ({
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
    }));
}

function humanizeDisplayNameGeneric(value, quantDisplay = "") {
    let baseValue = String(value || "")
        .replace(/(?<!\d)\.|\.(?!\d)/g, " ")
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();

    const plainParts = [];
    const versionParts = [];
    const tagParts = [];
    for (const part of (baseValue || "unnamed").split(" ").filter(Boolean)) {
        if (DISPLAY_DROP_WORDS.has(part.toLowerCase())) {
            continue;
        }

        const quantPart = formatQuantDisplay(part);
        if (quantPart) {
            tagParts.push(quantPart);
            continue;
        }

        const version = normalizeVersionToken(part);
        if (version) {
            versionParts.push(version);
            continue;
        }

        const tagged = extractTagAndVersion(part);
        if (tagged.tag) {
            if (tagged.version) {
                versionParts.push(tagged.version);
            }
            tagParts.push(tagged.tag);
            continue;
        }

        plainParts.push(part);
    }

    const cleanBase = joinDisplayParts([...plainParts, ...versionParts, ...tagParts]) || "unnamed";
    return quantDisplay ? joinDisplayParts([cleanBase, quantDisplay]) : cleanBase;
}

function matchKnownDisplayAliases(value, aliases, quantDisplay = "") {
    const words = iterDisplayWords(value);
    if (!words.length) {
        return "";
    }

    const normalizedWords = words.map((word) => normalizeDisplayIdentifier(word.text));
    let bestMatch = null;

    for (let startIndex = 0; startIndex < normalizedWords.length; startIndex += 1) {
        let compact = "";
        for (let endIndex = startIndex; endIndex < normalizedWords.length; endIndex += 1) {
            compact += normalizedWords[endIndex];
            for (const [alias, display] of aliases) {
                if (compact !== alias) {
                    continue;
                }
                const candidate = {
                    length: alias.length,
                    startIndex,
                    endIndex,
                    display,
                };
                if (
                    !bestMatch
                    || candidate.length > bestMatch.length
                    || (
                        candidate.length === bestMatch.length
                        && (
                            candidate.startIndex > bestMatch.startIndex
                            || (
                                candidate.startIndex === bestMatch.startIndex
                                && candidate.endIndex > bestMatch.endIndex
                            )
                        )
                    )
                ) {
                    bestMatch = candidate;
                }
            }
        }
    }

    if (!bestMatch) {
        return "";
    }

    const text = String(value || "");
    const prefixRaw = text.slice(0, words[bestMatch.startIndex].start);
    const suffixRaw = text.slice(words[bestMatch.endIndex].end);
    const parts = [];

    if (prefixRaw.trim()) {
        const prefixDisplay = humanizeDisplayNameGeneric(prefixRaw);
        if (prefixDisplay !== "unnamed") {
            parts.push(prefixDisplay);
        }
    }

    parts.push(bestMatch.display);

    if (suffixRaw.trim()) {
        const suffixDisplay = humanizeDisplayNameGeneric(suffixRaw);
        if (suffixDisplay !== "unnamed") {
            parts.push(suffixDisplay);
        }
    }

    const cleanBase = joinDisplayParts(parts) || bestMatch.display;
    return quantDisplay ? joinDisplayParts([cleanBase, quantDisplay]) : cleanBase;
}

function extractTagAndVersion(value) {
    const text = String(value || "");
    const lowered = text.toLowerCase();
    const words = Object.keys(DISPLAY_TAG_ABBREVIATIONS).sort((a, b) => b.length - a.length);
    for (const word of words) {
        if (lowered === word) {
            return { tag: DISPLAY_TAG_ABBREVIATIONS[word], version: "" };
        }
        if (!lowered.startsWith(word)) {
            continue;
        }
        const version = normalizeVersionToken(text.slice(word.length));
        if (version) {
            return { tag: DISPLAY_TAG_ABBREVIATIONS[word], version };
        }
    }
    return { tag: "", version: "" };
}

function humanizeDisplayName(value, kind = "generic") {
    let baseValue = basenameWithoutKnownExtension(value || "");
    const extraParts = [];
    let quantDisplay = "";

    const scaledFp8Match = baseValue.match(SCALED_FP8_RE);
    if (scaledFp8Match) {
        baseValue = scaledFp8Match[1].replace(/[ ._-]+$/, "");
        extraParts.push("Scaled");
        quantDisplay = `[FP8-${scaledFp8Match[2].toUpperCase()}]`;
    } else {
        const quantMatch = baseValue.match(QUANT_RE);
        if (quantMatch) {
            baseValue = quantMatch[1].replace(/[ ._-]+$/, "");
            quantDisplay = formatQuantDisplay(quantMatch[2]) || `[${quantMatch[2].toUpperCase()}]`;
        }
    }

    const aliases = kind === "model"
        ? KNOWN_IMAGE_MODEL_DISPLAY_ALIASES
        : kind === "text_encoder"
            ? KNOWN_TEXT_ENCODER_DISPLAY_ALIASES
            : null;

    if (aliases) {
        const knownDisplay = matchKnownDisplayAliases(baseValue, aliases);
        if (knownDisplay) {
            return joinDisplayParts([knownDisplay, ...extraParts, quantDisplay]);
        }
    }

    const tagMatch = baseValue.match(/^(?:[A-Z0-9]{2,8}[_-]+)(.+)$/);
    if (tagMatch) {
        baseValue = tagMatch[1];
    }

    if (aliases) {
        const knownDisplay = matchKnownDisplayAliases(baseValue, aliases);
        if (knownDisplay) {
            return joinDisplayParts([knownDisplay, ...extraParts, quantDisplay]);
        }
    }

    const baseDisplay = humanizeDisplayNameGeneric(baseValue);
    return joinDisplayParts([baseDisplay, ...extraParts, quantDisplay]);
}

function sanitizePathPart(value) {
    let text = String(value || "").trim();
    for (const char of '<>:"/\\\\|?*') {
        text = text.replaceAll(char, "-");
    }
    text = text.replace(/[\t\r\n]+/g, " ").replace(/\s+/g, " ").replace(/[ .]+$/g, "");
    if (!text || text === "." || text === "..") {
        return "unnamed";
    }
    return text;
}

function sanitizeRelativePath(value) {
    return String(value || "")
        .split(/[\\/]+/)
        .filter(Boolean)
        .map((part) => sanitizePathPart(part))
        .join("/");
}

function renderDateFormat(format, now) {
    const tokenValues = {
        yyyy: String(now.getFullYear()).padStart(4, "0"),
        yy: String(now.getFullYear() % 100).padStart(2, "0"),
        MM: String(now.getMonth() + 1).padStart(2, "0"),
        M: String(now.getMonth() + 1),
        dd: String(now.getDate()).padStart(2, "0"),
        d: String(now.getDate()),
        hh: String(now.getHours()).padStart(2, "0"),
        h: String(now.getHours()),
        mm: String(now.getMinutes()).padStart(2, "0"),
        m: String(now.getMinutes()),
        ss: String(now.getSeconds()).padStart(2, "0"),
        s: String(now.getSeconds()),
    };
    return String(format || "").replace(DATE_TOKEN_RE, (token) => tokenValues[token] ?? token);
}

function pad(value, width = 2) {
    return String(value).padStart(width, "0");
}

function renderStrftime(format, now) {
    return String(format || "").replace(/%%|%[YymdHMSf]/g, (token) => {
        switch (token) {
            case "%%":
                return "%";
            case "%Y":
                return String(now.getFullYear());
            case "%y":
                return pad(now.getFullYear() % 100);
            case "%m":
                return pad(now.getMonth() + 1);
            case "%d":
                return pad(now.getDate());
            case "%H":
                return pad(now.getHours());
            case "%M":
                return pad(now.getMinutes());
            case "%S":
                return pad(now.getSeconds());
            case "%f":
                return "123456";
            default:
                return token;
        }
    });
}

function buildFilenameValue(node, now) {
    const pattern = String(getWidget(node, "filename_datetime")?.value || DEFAULT_FILENAME);
    let rendered = pattern.replace(/%date:([^%]+)%/g, (_, format) => renderDateFormat(format, now));
    rendered = rendered.replace(/%strftime:([^%]+)%/g, (_, format) => renderStrftime(format, now));
    return sanitizePathPart(rendered);
}

function resolveSelectedValue(sourceLabel, variables, kind) {
    const sourceMap = kind === "model"
        ? {
            Friendly: "FRIENDLY_MODEL_NAME",
            Exact: "EXACT_MODEL_NAME",
            Custom: "CUSTOM_MODEL_NAME",
        }
        : {
            Friendly: "FRIENDLY_TEXT_ENCODER_NAME",
            Exact: "EXACT_TEXT_ENCODER_NAME",
            Custom: "CUSTOM_TEXT_ENCODER_NAME",
        };
    const key = sourceMap[sourceLabel] || Object.values(sourceMap)[0];
    return sanitizePathPart(variables[key] || "unnamed");
}

function buildVariables(node, now, detectionSnapshot = null) {
    const topFolder = getWidget(node, "subfolder")?.value || "";
    const customModelName = stripKnownExtension(getWidget(node, "model_folder")?.value || "");
    const customTextEncoderName = stripKnownExtension(getWidget(node, "clip_folder")?.value || "");
    const modelSource = getWidget(node, "model_source")?.value || "Friendly";
    const clipSource = getWidget(node, "clip_source")?.value || "Friendly";

    const exactModelName = detectionSnapshot?.exact_model_name || basenameWithoutKnownExtension(SAMPLE_MODEL) || "model";
    const exactTextEncoderName = detectionSnapshot?.exact_text_encoder_name
        || basenameWithoutKnownExtension(SAMPLE_CLIP)
        || "text-encoder";
    const friendlyModelName = detectionSnapshot?.friendly_model_name || humanizeDisplayName(SAMPLE_MODEL, "model");
    const friendlyTextEncoderName = detectionSnapshot?.friendly_text_encoder_name
        || humanizeDisplayName(SAMPLE_CLIP, "text_encoder");

    const variables = {
        TOP_FOLDER: topFolder.trim() ? sanitizePathPart(topFolder) : "",
        EXACT_MODEL_NAME: sanitizePathPart(exactModelName),
        EXACT_TEXT_ENCODER_NAME: sanitizePathPart(exactTextEncoderName),
        FRIENDLY_MODEL_NAME: sanitizePathPart(friendlyModelName),
        FRIENDLY_TEXT_ENCODER_NAME: sanitizePathPart(friendlyTextEncoderName),
        CUSTOM_MODEL_NAME: customModelName,
        CUSTOM_TEXT_ENCODER_NAME: customTextEncoderName,
        WIDTH: String(detectionSnapshot?.width || "1024"),
        HEIGHT: String(detectionSnapshot?.height || "1024"),
        SEED: String(detectionSnapshot?.seed || "123456789"),
        BATCH_INDEX: String(detectionSnapshot?.batch_index || "1"),
        FILENAME: buildFilenameValue(node, now),
    };

    variables.MODEL_NAME = resolveSelectedValue(modelSource, variables, "model");
    variables.TEXT_ENCODER_NAME = resolveSelectedValue(clipSource, variables, "clip");
    return variables;
}

function buildLegacyExample(node, variables) {
    const parts = [];
    if (variables.TOP_FOLDER) {
        parts.push(variables.TOP_FOLDER);
    }
    parts.push(variables.MODEL_NAME);
    parts.push(variables.TEXT_ENCODER_NAME);
    parts.push(`${variables.FILENAME}.png`);
    return parts.join("/");
}

function formatPreviewNote(message, tone = "info") {
    return {
        message,
        tone,
    };
}

function buildLayoutExample(node, variables, now) {
    const layout = String(getWidget(node, "path_template")?.value || DEFAULT_LAYOUT).trim();
    const notes = [];
    let usesWidgetPlaceholder = false;

    let rendered = layout.replace(/%date:([^%]+)%/g, (_, format) => renderDateFormat(format, now));
    rendered = rendered.replace(/%strftime:([^%]+)%/g, (_, format) => renderStrftime(format, now));
    rendered = rendered.replace(NODE_WIDGET_TOKEN_RE, (_, nodeName, widgetName) => {
        usesWidgetPlaceholder = true;
        return `{${nodeName}.${widgetName}}`;
    });
    rendered = rendered.replace(VARIABLE_TOKEN_RE, (_, key) => variables[key] ?? `%${key}%`);

    const remainingTokens = [...rendered.matchAll(UNKNOWN_TOKEN_RE)].map((match) => match[1]);
    const unknownVariables = remainingTokens.filter((token) => /^[A-Z0-9_]+$/.test(token) && !VALID_TEMPLATE_VARIABLES.has(token));
    const unknownPlaceholders = remainingTokens.filter((token) => !/^[A-Z0-9_]+$/.test(token));

    if (unknownVariables.length || unknownPlaceholders.length) {
        const details = [
            unknownVariables.length ? `variables: ${unknownVariables.join(", ")}` : "",
            unknownPlaceholders.length ? `placeholders: ${unknownPlaceholders.join(", ")}` : "",
        ].filter(Boolean);
        notes.push(formatPreviewNote(`Preview warning: unknown ${details.join(" | ")}`, "warning"));
    }

    if (usesWidgetPlaceholder) {
        notes.push(formatPreviewNote("Widget placeholders show as {node.widget} until the workflow runs."));
    }

    let cleanPath = sanitizeRelativePath(rendered);
    if (!cleanPath.toLowerCase().endsWith(".png")) {
        cleanPath = `${cleanPath}.png`;
    }
    return {
        path: cleanPath,
        notes,
    };
}

function createHelpPanelWidget(node) {
    if (node.__saveImageCleanHelpWidget) {
        return node.__saveImageCleanHelpWidget;
    }

    const container = document.createElement("div");
    container.style.cssText = [
        "display:flex",
        "flex-direction:column",
        "gap:6px",
        "padding:6px 10px 12px 10px",
        "border-radius:10px",
        "background:rgba(255,255,255,0.03)",
        "border:1px solid rgba(255,255,255,0.08)",
        "color:#d7d7d7",
        "width:100%",
        "box-sizing:border-box",
        "overflow:hidden",
        "pointer-events:none",
    ].join(";");

    const titleEl = document.createElement("div");
    titleEl.style.cssText = "font-size:12px;font-weight:600;color:#f3f3f3;";

    const noteEl = document.createElement("div");
    noteEl.style.cssText = [
        "font-size:11px",
        "line-height:1.35",
        "color:#a9a9a9",
        "min-height:14px",
    ].join(";");

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

    const outputValueEl = createPreviewValue();

    const detailsTitleEl = document.createElement("div");
    detailsTitleEl.style.cssText = [
        "display:none",
        "font-size:10px",
        "font-weight:600",
        "letter-spacing:0.03em",
        "text-transform:uppercase",
        "color:#9d9d9d",
        "margin-top:2px",
    ].join(";");

    const detailsEl = document.createElement("div");
    detailsEl.style.cssText = [
        "display:none",
        "font-size:11px",
        "line-height:1.35",
        "color:#cfcfcf",
        "background:rgba(0,0,0,0.12)",
        "border-radius:8px",
        "padding:8px 10px",
        "white-space:pre-wrap",
        "word-break:break-word",
    ].join(";");

    container.appendChild(titleEl);
    container.appendChild(noteEl);
    container.appendChild(outputValueEl);
    container.appendChild(detailsTitleEl);
    container.appendChild(detailsEl);

    node.__saveImageCleanHelpRefs = {
        titleEl,
        noteEl,
        outputValueEl,
        detailsTitleEl,
        detailsEl,
    };
    node.__saveImageCleanHelpWidget = node.addDOMWidget("save_image_clean_help", "custom", container, {
        getMinHeight: () => 90,
        getMaxHeight: () => 104,
        serialize: false,
        hideOnZoom: false,
        margin: 8,
    });

    return node.__saveImageCleanHelpWidget;
}

function clearLastRunState(node) {
    delete node.__saveImageCleanLastRunInfo;
}

function markLastRunStateStale(node) {
    if (node.__saveImageCleanLastRunInfo) {
        node.__saveImageCleanLastRunInfo.stale = true;
    }
}

function getStructuredUiPayload(message) {
    const payload = Array.isArray(message?.save_image_clean)
        ? message.save_image_clean[0]
        : message?.save_image_clean;
    return payload && typeof payload === "object" ? payload : null;
}

function setLastRunStateFromMessage(node, message) {
    const textItems = Array.isArray(message?.text)
        ? message.text.filter((item) => typeof item === "string" && item.trim())
        : [];
    const payload = getStructuredUiPayload(message);
    if (!textItems.length && !payload) {
        clearLastRunState(node);
        return;
    }

    node.__saveImageCleanLastRunInfo = {
        path: payload?.preview || textItems[0] || "",
        details: Array.isArray(payload?.detection_lines) ? payload.detection_lines : textItems.slice(1),
        detection: payload,
        stale: false,
    };
}

function formatDetectionSourceLabel(source, value) {
    if (source === "workflow") {
        return `workflow loader -> ${value || "(empty)"}`;
    }
    if (source === "custom_fallback") {
        return `custom fallback -> ${value || "(empty)"}`;
    }
    return "default placeholder";
}

function buildDetectionSnapshotLines(snapshot) {
    if (!snapshot) {
        return [];
    }

    return [
        `Model detection: ${formatDetectionSourceLabel(snapshot.model_detection_source, snapshot.detected_model_name)}`,
        `Model output: ${snapshot.selected_model_source} -> ${snapshot.selected_model_name}`,
        `Text encoder detection: ${formatDetectionSourceLabel(snapshot.text_encoder_detection_source, snapshot.detected_text_encoder_name)}`,
        `Text encoder output: ${snapshot.selected_text_encoder_source} -> ${snapshot.selected_text_encoder_name}`,
    ];
}

function updateHelp(node) {
    const refs = node.__saveImageCleanHelpRefs;
    if (!refs) {
        return;
    }

    const now = new Date();
    const saveLayout = String(getWidget(node, "path_template")?.value || "").trim();
    const defaultNote = "Preview uses sample detected names until the workflow runs.";
    const lastRunInfo = node.__saveImageCleanLastRunInfo;
    const detectionSnapshot = lastRunInfo?.detection || null;
    const useLegacyOrder = saveLayout === "";
    const variables = buildVariables(node, now, detectionSnapshot);

    ensureSectionLabel(node, "save_layout", "Save Layout", "path_template");
    ensureSectionLabel(node, "filename", "Filename", "filename_datetime");

    if (lastRunInfo && !lastRunInfo.stale) {
        refs.outputValueEl.textContent = lastRunInfo.path;
        refs.noteEl.textContent = "Last run used real detected values.";
        refs.noteEl.style.color = "#8eb7ff";
        refs.outputValueEl.style.borderColor = "rgba(142, 183, 255, 0.3)";
    } else if (useLegacyOrder) {
        refs.outputValueEl.textContent = buildLegacyExample(node, variables);
        refs.noteEl.textContent = detectionSnapshot
            ? "Preview uses the last detected values from a previous run."
            : defaultNote;
        refs.noteEl.style.color = detectionSnapshot ? "#f0be47" : "#a9a9a9";
        refs.outputValueEl.style.borderColor = detectionSnapshot ? "rgba(240, 190, 71, 0.35)" : "transparent";
    } else {
        const preview = buildLayoutExample(node, variables, now);
        const warning = preview.notes.find((note) => note.tone === "warning");
        const staleMessage = detectionSnapshot
            ? "Preview uses the last detected values from a previous run. Run again to refresh."
            : "";
        refs.outputValueEl.textContent = preview.path;
        refs.noteEl.textContent = warning?.message || staleMessage || preview.notes[0]?.message || defaultNote;
        refs.noteEl.style.color = warning ? "#f0be47" : detectionSnapshot ? "#f0be47" : "#a9a9a9";
        refs.outputValueEl.style.borderColor = warning
            ? "rgba(240, 190, 71, 0.35)"
            : detectionSnapshot
                ? "rgba(240, 190, 71, 0.28)"
                : "transparent";
    }

    const snapshotLines = buildDetectionSnapshotLines(detectionSnapshot);
    const detailLines = snapshotLines.length ? snapshotLines : lastRunInfo?.details || [];
    if (detailLines.length) {
        refs.detailsTitleEl.textContent = lastRunInfo?.stale ? "Last Detection Snapshot" : "Detection Snapshot";
        refs.detailsTitleEl.style.display = "block";
        refs.detailsEl.textContent = detailLines.join("\n");
        refs.detailsEl.style.display = "block";
    } else if (useLegacyOrder) {
        refs.detailsTitleEl.textContent = "";
        refs.detailsTitleEl.style.display = "none";
        refs.detailsEl.textContent = "";
        refs.detailsEl.style.display = "none";
    } else {
        refs.detailsTitleEl.textContent = "";
        refs.detailsTitleEl.style.display = "none";
        refs.detailsEl.textContent = "";
        refs.detailsEl.style.display = "none";
    }
    refs.titleEl.textContent = "Example Output";

    const newSize = node.computeSize();
    newSize[0] = Math.max(newSize[0], node.size[0]);
    newSize[1] = Math.max(newSize[1], 404);
    node.setSize?.(newSize);
    node.setDirtyCanvas?.(true, true);
}

function hookWidgetUpdates(node) {
    const watchedNames = [
        "path_template",
        "model_source",
        "clip_source",
        "filename_datetime",
        "collision_mode",
        "detection_info",
        "subfolder",
        "model_folder",
        "clip_folder",
    ];

    for (const name of watchedNames) {
        const widget = getWidget(node, name);
        if (!widget || widget.__saveImageCleanHooked) {
            continue;
        }

        const originalCallback = widget.callback;
        widget.callback = function () {
            const result = originalCallback?.apply(this, arguments);
            markLastRunStateStale(node);
            updateHelp(node);
            return result;
        };

        if (widget.inputEl) {
            widget.inputEl.addEventListener("input", () => {
                markLastRunStateStale(node);
                updateHelp(node);
            });
            widget.inputEl.addEventListener("change", () => {
                markLastRunStateStale(node);
                updateHelp(node);
            });
        }

        widget.__saveImageCleanHooked = true;
    }
}

app.registerExtension({
    name: "comfyui-save-image-organized.save-image-organized-ux",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) {
            return;
        }

        const onConfigure = nodeType.prototype.configure;
        nodeType.prototype.configure = function () {
            const result = onConfigure?.apply(this, arguments);
            requestAnimationFrame(() => {
                setFriendlyLabels(this);
                ensureSectionLabel(this, "save_layout", "Save Layout", "path_template");
                ensureSectionLabel(this, "filename", "Filename", "filename_datetime");
                createHelpPanelWidget(this);
                hookWidgetUpdates(this);
                updateHelp(this);
            });
            return result;
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            setFriendlyLabels(this);
            ensureSectionLabel(this, "save_layout", "Save Layout", "path_template");
            ensureSectionLabel(this, "filename", "Filename", "filename_datetime");
            createHelpPanelWidget(this);
            hookWidgetUpdates(this);
            updateHelp(this);
            return result;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const result = onExecuted?.apply(this, arguments);
            setLastRunStateFromMessage(this, message);
            updateHelp(this);
            return result;
        };
    },
});
