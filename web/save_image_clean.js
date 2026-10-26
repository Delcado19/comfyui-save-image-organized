import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_NAME = "SaveImageClean";
const MODEL_OPTIONS = ["Friendly", "Friendly Clean", "Exact", "Custom"];
const CLIP_OPTIONS = ["Friendly", "Friendly Clean", "Exact", "Custom"];

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

const IMAGE_FORMAT_EXTENSIONS = { PNG: "png", JPEG: "jpg", WebP: "webp" };
const KNOWN_IMAGE_EXTENSION_RE = /\.(png|jpe?g|webp)$/i;

const SAMPLE_MODEL = "flux-2-klein-9b-Q5_K_M.gguf";
const SAMPLE_CLIP = "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf";
const DEFAULT_LAYOUT = "%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%%BATCH%";
const DEFAULT_FILENAME = "%date:yyyy-MM-dd_hh-mm-ss%";
const VARIABLE_TOKEN_RE = /%([A-Z0-9_]+)((?::[a-z]+)*)%/g;
const NODE_WIDGET_TOKEN_RE = /%([^%./\\]+)\.([^%./\\:]+)((?::[a-z]+)*)%/g;
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
const KNOWN_RELEASER_PREFIX_RE = /^(?:goekdeniz[-_]?guelmez|mradermacher)\s*(?:[-_]+\s*|\s+-\s+)(.+)$/i;
const SPACED_RELEASER_PREFIX_RE = /^\s*[^\\/]{2,40}\s+-\s+(.+)$/;
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
    "STEPS",
    "CFG",
    "SAMPLER",
    "SCHEDULER",
    "DENOISE",
    "BATCH",
    "BATCH_INDEX",
    "BATCH_SIZE",
    "FRIENDLY_MODEL_NAME",
    "CLEAN_FRIENDLY_MODEL_NAME",
    "EXACT_MODEL_NAME",
    "CUSTOM_MODEL_NAME",
    "FRIENDLY_TEXT_ENCODER_NAME",
    "CLEAN_FRIENDLY_TEXT_ENCODER_NAME",
    "EXACT_TEXT_ENCODER_NAME",
    "CUSTOM_TEXT_ENCODER_NAME",
]);
const TEMPLATE_FILTERS = new Set(["lower", "upper", "slug"]);
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

function stripReleaserPrefix(value) {
    const baseValue = basenameWithoutKnownExtension(value);
    const knownMatch = baseValue.match(KNOWN_RELEASER_PREFIX_RE);
    if (knownMatch) {
        return knownMatch[1].trim();
    }

    const spacedMatch = baseValue.match(SPACED_RELEASER_PREFIX_RE);
    if (spacedMatch) {
        return spacedMatch[1].trim();
    }

    return value;
}

function humanizeCleanDisplayName(value, kind = "generic") {
    return humanizeDisplayName(stripReleaserPrefix(value), kind);
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
    const cleaned = String(value || "")
        .split(/[\\/]+/)
        .filter(Boolean)
        .map((part) => sanitizePathPart(part))
        .join("/");
    // Mirrors nodes.py _sanitize_relative_path: a template that renders to
    // nothing (e.g. an empty %TOP_FOLDER%-only layout) still needs a name,
    // instead of a preview showing a bare ".png"/".jpg"/".webp".
    return cleaned || "unnamed";
}

const MODEL_CLIP_TOKEN_PAIR_RE = /%MODEL_NAME(?::[^%]*)?%[\\/]+%TEXT_ENCODER_NAME(?::[^%]*)?%/;

// Mirrors nodes.py _collapse_duplicate_model_clip_tokens: a checkpoint loader
// provides one file for both model and text encoder, so an adjacent
// %MODEL_NAME%/%TEXT_ENCODER_NAME% token pair can render two identical
// segments back to back. Only that specific token pair is merged (before
// variables are substituted), so an unrelated duplicate elsewhere in the
// rendered path (e.g. %TOP_FOLDER% happening to equal %MODEL_NAME%, see
// issue raised 2026-08-13) is left alone.
function collapseDuplicateModelClipTokens(layout, cleanModel, cleanClip) {
    if (!cleanModel || cleanModel !== cleanClip) {
        return layout;
    }
    return layout.replace(MODEL_CLIP_TOKEN_PAIR_RE, "%MODEL_NAME%");
}

function getImageExtension(node) {
    const format = String(getWidget(node, "image_format")?.value || "PNG");
    return IMAGE_FORMAT_EXTENSIONS[format] || "png";
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

function buildFilenameValue(node, now, variables = null) {
    const pattern = String(getWidget(node, "filename_datetime")?.value || DEFAULT_FILENAME);
    let rendered = pattern.replace(/%date:([^%]+)%/g, (_, format) => renderDateFormat(format, now));
    rendered = rendered.replace(/%strftime:([^%]+)%/g, (_, format) => renderStrftime(format, now));
    if (variables) {
        // Mirrors nodes.py's _render_filename_value: the Filename field accepts the
        // same %VARIABLE% tokens as the Output Path Template (e.g. %SEED%, %SAMPLER%),
        // otherwise this preview mismatches the backend render and leaves the tokens
        // as literal text inside %FILENAME%.
        rendered = rendered.replace(VARIABLE_TOKEN_RE, (placeholder, key, filterText) => {
            if (variables[key] === undefined) {
                return placeholder;
            }
            return applyTemplateFilters(variables[key], parseTemplateFilters(filterText, placeholder, []));
        });
    }
    return sanitizePathPart(rendered);
}

function resolveSelectedValue(sourceLabel, variables, kind) {
    const sourceMap = kind === "model"
        ? {
            Friendly: "FRIENDLY_MODEL_NAME",
            "Friendly Clean": "CLEAN_FRIENDLY_MODEL_NAME",
            Exact: "EXACT_MODEL_NAME",
            Custom: "CUSTOM_MODEL_NAME",
        }
        : {
            Friendly: "FRIENDLY_TEXT_ENCODER_NAME",
            "Friendly Clean": "CLEAN_FRIENDLY_TEXT_ENCODER_NAME",
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
    const cleanFriendlyModelName = detectionSnapshot?.clean_friendly_model_name
        || humanizeCleanDisplayName(SAMPLE_MODEL, "model");
    const cleanFriendlyTextEncoderName = detectionSnapshot?.clean_friendly_text_encoder_name
        || humanizeCleanDisplayName(SAMPLE_CLIP, "text_encoder");

    const variables = {
        TOP_FOLDER: topFolder.trim() ? sanitizePathPart(topFolder) : "",
        EXACT_MODEL_NAME: sanitizePathPart(exactModelName),
        EXACT_TEXT_ENCODER_NAME: sanitizePathPart(exactTextEncoderName),
        FRIENDLY_MODEL_NAME: sanitizePathPart(friendlyModelName),
        FRIENDLY_TEXT_ENCODER_NAME: sanitizePathPart(friendlyTextEncoderName),
        CLEAN_FRIENDLY_MODEL_NAME: sanitizePathPart(cleanFriendlyModelName),
        CLEAN_FRIENDLY_TEXT_ENCODER_NAME: sanitizePathPart(cleanFriendlyTextEncoderName),
        CUSTOM_MODEL_NAME: customModelName,
        CUSTOM_TEXT_ENCODER_NAME: customTextEncoderName,
        WIDTH: String(detectionSnapshot?.width || "1024"),
        HEIGHT: String(detectionSnapshot?.height || "1024"),
        SEED: String(detectionSnapshot?.seed || "123456789"),
        STEPS: String(detectionSnapshot?.steps || "20"),
        CFG: String(detectionSnapshot?.cfg || "7"),
        SAMPLER: String(detectionSnapshot?.sampler || "euler"),
        SCHEDULER: String(detectionSnapshot?.scheduler || "normal"),
        DENOISE: String(detectionSnapshot?.denoise || "1"),
        BATCH_INDEX: String(detectionSnapshot?.batch_index || "1"),
        BATCH_SIZE: String(detectionSnapshot?.batch_size || "1"),
    };
    variables.BATCH = Number(variables.BATCH_SIZE) > 1 ? `_${variables.BATCH_INDEX}-of-${variables.BATCH_SIZE}` : "";
    variables.MODEL_NAME = resolveSelectedValue(modelSource, variables, "model");
    variables.TEXT_ENCODER_NAME = resolveSelectedValue(clipSource, variables, "clip");
    // MODEL_NAME/TEXT_ENCODER_NAME must already be set before this call so the Filename
    // field can also use them (same %VARIABLE% tokens as the path template).
    variables.FILENAME = buildFilenameValue(node, now, variables);
    return variables;
}

function buildLegacyExample(node, variables) {
    const parts = [];
    if (variables.TOP_FOLDER) {
        parts.push(variables.TOP_FOLDER);
    }
    parts.push(variables.MODEL_NAME);
    if (variables.TEXT_ENCODER_NAME !== variables.MODEL_NAME) {
        parts.push(variables.TEXT_ENCODER_NAME);
    }
    parts.push(`${variables.FILENAME}.${getImageExtension(node)}`);
    return parts.join("/");
}

function slugifyTemplateValue(value) {
    const slug = String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return slug || "unnamed";
}

function parseTemplateFilters(filterText, placeholder, notes) {
    const filters = String(filterText || "").split(":").filter(Boolean);
    const unknown = filters.find((filterName) => !TEMPLATE_FILTERS.has(filterName));
    if (unknown) {
        notes.push(formatPreviewNote(
            `Preview warning: unknown template filter ${unknown} in ${placeholder}`,
            "warning",
        ));
    }
    return filters.filter((filterName) => TEMPLATE_FILTERS.has(filterName));
}

function applyTemplateFilters(value, filters) {
    return filters.reduce((rendered, filterName) => {
        if (filterName === "lower") {
            return rendered.toLowerCase();
        }
        if (filterName === "upper") {
            return rendered.toUpperCase();
        }
        if (filterName === "slug") {
            return slugifyTemplateValue(rendered);
        }
        return rendered;
    }, String(value || ""));
}

function formatPreviewNote(message, tone = "info") {
    return {
        message,
        tone,
    };
}

function buildLayoutExample(node, variables, now) {
    let layout = String(getWidget(node, "path_template")?.value || DEFAULT_LAYOUT).trim();
    layout = collapseDuplicateModelClipTokens(layout, variables.MODEL_NAME, variables.TEXT_ENCODER_NAME);
    const notes = [];
    let usesWidgetPlaceholder = false;

    let rendered = layout.replace(/%date:([^%]+)%/g, (_, format) => renderDateFormat(format, now));
    rendered = rendered.replace(/%strftime:([^%]+)%/g, (_, format) => renderStrftime(format, now));
    rendered = rendered.replace(NODE_WIDGET_TOKEN_RE, (placeholder, nodeName, widgetName, filterText) => {
        usesWidgetPlaceholder = true;
        parseTemplateFilters(filterText, placeholder, notes);
        return `{${nodeName}.${widgetName}${filterText || ""}}`;
    });
    rendered = rendered.replace(VARIABLE_TOKEN_RE, (placeholder, key, filterText) => {
        if (variables[key] === undefined) {
            return `%${key}${filterText || ""}%`;
        }
        return applyTemplateFilters(
            variables[key],
            parseTemplateFilters(filterText, placeholder, notes),
        );
    });

    const remainingTokens = [...rendered.matchAll(UNKNOWN_TOKEN_RE)].map((match) => match[1]);
    const unknownVariables = remainingTokens.filter((token) => {
        const match = token.match(/^([A-Z0-9_]+)((?::[a-z]+)*)$/);
        return match && !VALID_TEMPLATE_VARIABLES.has(match[1]);
    });
    const unknownPlaceholders = remainingTokens.filter((token) => !/^([A-Z0-9_]+)((?::[a-z]+)*)$/.test(token));

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
    cleanPath = cleanPath.replace(KNOWN_IMAGE_EXTENSION_RE, "");
    cleanPath = `${cleanPath}.${getImageExtension(node)}`;
    return {
        path: cleanPath,
        notes,
    };
}

import { el, injectDesignTokens, buildSegmentedControl, buildDropdownRow, buildSwitchRow, buildSliderRow, buildTextRow } from "./sic_components.mjs";

const IMAGE_FORMAT_IDS = ["PNG", "JPEG", "WebP"];
const SAVE_MODE_IDS = ["Save", "Preview"];

function setActiveFormatButton(node, activeId) {
    node.__saveImageCleanFormatSeg?.setActive(activeId);
}

function setActiveSaveModeButton(node, activeId) {
    node.__saveImageCleanSaveModeSeg?.setActive(activeId);
}

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
        // min-width:0 on every flex level below (grid -> body -> cell) -
        // found live 2026-10-13: a flex item's default min-width is "auto",
        // which for a flex item containing a replaced element (the <img>)
        // resolves to the IMAGE'S OWN INTRINSIC PIXEL WIDTH, not 0 and not
        // the width:100% rule below. A generated image (e.g. 1024px wide)
        // then forces .sic-preview-cell, .sic-preview-grid-body and the
        // whole .sic-inner column wider than the node itself, bleeding the
        // image/Save button/Example Output past the node's own right edge
        // (litegraph draws the node boundary independently of DOM layout,
        // so overflowing DOM content isn't clipped by anything on its own).
        // flex:1/min-height:0 down this whole chain (grid -> body -> cell ->
        // thumb) so extra height from a manual node resize goes INTO the
        // image instead of sitting as dead space below it (user report
        // 2026-10-14: a tall node left a big empty gap with the image still
        // capped at its old fixed max-height). display:none when there's no
        // preview means flex:1 costs nothing in that state.
        ".sic-preview-grid{display:flex;flex-direction:column;min-width:0;flex:1;min-height:0;}",
        ".sic-preview-grid-body{display:flex;flex-wrap:wrap;gap:8px;padding:6px 8px;min-width:0;}",
        ".sic-preview-cell{display:flex;flex-direction:column;align-items:center;gap:4px;width:92px;min-width:0;}",
        ".sic-preview-thumb{width:100%;max-width:100%;aspect-ratio:1;object-fit:cover;border-radius:6px;",
        "border:1px solid rgba(255,255,255,0.14);background:rgba(0,0,0,0.2);}",
        ".sic-preview-dims{font-size:9px;color:#9d9d9d;}",
        // Single-image run (the common case): fill the available node width
        // AND height instead of staying at a fixed max-height - a preview
        // node you can't make out the image on defeats its own purpose
        // (user request 2026-10-13, enlarged on 2026-10-14). Batches of 2+
        // keep the compact grid.
        ".sic-preview-grid-body.sic-preview-single{flex-wrap:nowrap;flex:1;min-height:0;}",
        ".sic-preview-grid-body.sic-preview-single .sic-preview-cell{width:100%;flex:1;min-height:0;}",
        ".sic-preview-grid-body.sic-preview-single .sic-preview-thumb{",
        "aspect-ratio:auto;width:100%;height:100%;flex:1;min-height:0;object-fit:contain;}",
        // The Save button's width:100% matched the 92px grid thumbnail fine,
        // but inherited the single-image thumb's full card width too,
        // reading as oversized (user request 2026-10-13) - natural width,
        // centered, same size regardless of how wide the image above it is.
        ".sic-preview-grid-body.sic-preview-single .sic-preview-save-btn{",
        "width:auto;align-self:center;padding:5px 24px;font-size:var(--sic-font-base);}",
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

function buildPreviewImageUrl(entry) {
    const params = new URLSearchParams({
        filename: entry.filename,
        type: entry.type || "temp",
        subfolder: entry.subfolder || "",
    });
    return api.apiURL(`/view?${params.toString()}`);
}

function buildPreviewCell(node, entry, { showSaveButton }) {
    const cell = document.createElement("div");
    cell.className = "sic-preview-cell";

    const img = document.createElement("img");
    img.className = "sic-preview-thumb";
    img.src = buildPreviewImageUrl(entry);
    img.alt = `Preview ${entry.batch_index}`;
    cell.appendChild(img);

    // Pixel size readout (user request 2026-10-14) - nodes.py already
    // measures width/height per image for the path template, so this just
    // forwards it rather than re-deriving it from the loaded <img>.
    if (entry.width && entry.height) {
        cell.appendChild(el("div", "sic-preview-dims", `${entry.width}×${entry.height}`));
    }

    // Save mode already saves every image on its own; the per-thumbnail
    // Save button only makes sense in Preview mode (user request 2026-10-13).
    if (!showSaveButton) {
        return cell;
    }

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
            // Echo back the node_id/run_token the backend attached to this entry, rather than
            // deriving node.id locally: inside a subgraph the backend's real node id (e.g.
            // "12:5") differs from the frontend's local node.id, and two nodes/tabs can share
            // a local id, so a locally-derived id can save the wrong image to the wrong path.
            const response = await api.fetchApi("/save_image_organized/save_now", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ node_id: entry.node_id, batch_index: entry.batch_index, run_token: entry.run_token }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data?.error || `Save failed (${response.status})`);
            }
            saveBtn.textContent = "✓ Saved";
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

    cell.appendChild(saveBtn);
    cell.appendChild(statusEl);
    return cell;
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
        node.setDirtyCanvas?.(true, true);
        return;
    }

    const showSaveButton = getWidget(node, "save_mode")?.value !== "Save";
    refs.body.classList.toggle("sic-preview-single", entries.length === 1);
    for (const entry of entries) {
        refs.body.appendChild(buildPreviewCell(node, entry, { showSaveButton }));
    }
    refs.container.style.display = "flex";
    // The native per-node thumbnail strip is driven by node.imgs, populated by
    // ComfyUI's own default onExecuted from message.images. In Preview mode
    // the temp images never reach node.imgs in the first place (kept out of
    // message.images, see nodes.py's save_image_clean_preview key), so this
    // is purely defensive there. In Save mode, save_image_clean_preview now
    // mirrors the already-saved files (user report 2026-10-26: that
    // thumbnail used the native strip's fixed small size, never resized with
    // the node like this grid does) and message.images IS populated, so this
    // clear is load-bearing: without it, the native strip would render the
    // same image a second time underneath this grid.
    node.imgs = [];
    node.setDirtyCanvas?.(true, true);
}

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
        ".sic-builder-trigger{flex:none;white-space:nowrap;padding:3px 9px;font-size:9px;font-weight:600;",
        "letter-spacing:0.02em;border-radius:5px;",
        "border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.04);",
        "color:#b7b7b7;cursor:pointer;font-family:inherit;",
        "transition:transform 120ms var(--sic-ease-out), border-color 120ms var(--sic-ease), color 120ms var(--sic-ease);}",
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
        // setPointerCapture below would otherwise swallow the click event on
        // the close button (a child of this drag handle) before the browser
        // can synthesize it on that specific element.
        if (event.target.closest(".sic-builder-close")) {
            return;
        }
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
        ".sic-adv-row{display:flex;flex-direction:column;gap:3px;padding:5px 0;}",
        ".sic-adv-row-desc{font-size:10px;line-height:1.35;color:#8f8f8f;padding:0 var(--sic-space-md);}",
    ].join("");
    document.head.appendChild(style);
}

// Every Advanced Settings entry now gets a one-line visible description
// (user request 2026-10-13, after an earlier round moved Loader Priority's
// into a tooltip for consistency with the others, which had none - the user
// wanted the opposite: short text on every row instead of on none). Text is
// a shortened, same-voice version of nodes.py's own INPUT_TYPES tooltip for
// that field, not invented wording.
//
// elements can be more than one node (e.g. a dropdown plus its conditional
// Custom-name field) so they share ONE .sic-adv-row wrapper - found live
// 2026-10-13: wrapping a paired dropdown+field in two separate rows left an
// empty wrapper (padding only) in the layout whenever setRowDisabled hid the
// inner field via display:none, which read as a stray gap (user request:
// "kompakter anordnen").
function addAdvancedRow(body, elements, descText) {
    const wrap = document.createElement("div");
    wrap.className = "sic-adv-row";
    for (const el of [].concat(elements)) {
        wrap.appendChild(el);
    }
    if (descText) {
        const desc = document.createElement("div");
        desc.className = "sic-adv-row-desc";
        desc.textContent = descText;
        wrap.appendChild(desc);
    }
    body.appendChild(wrap);
    return wrap;
}

// Advanced Settings now holds every secondary control (user request,
// 2026-10-13 live QA): source/encoder naming, collision handling, detection
// verbosity, metadata export, quality and the detection snapshot - the main
// card only keeps path/filename/output-format/mode so the node stays short.
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
    trigger.textContent = "⚙"; // gear
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
    closeBtn.textContent = "✕";
    closeBtn.addEventListener("click", () => closeTemplateBuilderPanel(panel));
    header.appendChild(title);
    header.appendChild(closeBtn);

    const body = document.createElement("div");
    body.className = "sic-builder-body";

    const loaderDropdown = buildDropdownRow(node, "loader_priority", "Loader Priority", ["Nearest", "First Used"]);
    if (loaderDropdown) {
        addAdvancedRow(body, loaderDropdown.root,
            "Nearest: fewest upstream links, right for most single-pass workflows. " +
            "First Used: furthest upstream, e.g. a base pass refined by a second model.");
    }

    const modelRow = buildDropdownRow(node, "model_source", "Model Name", MODEL_OPTIONS);
    node.__saveImageCleanModelRow = modelRow;
    const modelFolderRow = buildTextRow(node, "model_folder", { placeholder: "Custom Model Name" });
    node.__saveImageCleanModelFolderRow = modelFolderRow;
    if (modelRow) {
        addAdvancedRow(body, [modelRow.root, modelFolderRow?.root].filter(Boolean),
            "How the model name should look - Friendly is easiest for most people, " +
            "Custom uses the name typed below.");
    }

    const clipRow = buildDropdownRow(node, "clip_source", "Text Encoder", CLIP_OPTIONS);
    node.__saveImageCleanClipRow = clipRow;
    const clipFolderRow = buildTextRow(node, "clip_folder", { placeholder: "Custom Text Encoder Name" });
    node.__saveImageCleanClipFolderRow = clipFolderRow;
    if (clipRow) {
        addAdvancedRow(body, [clipRow.root, clipFolderRow?.root].filter(Boolean),
            "How the text encoder name should look - Friendly is easiest for most people, " +
            "Custom uses the name typed below.");
    }

    const collisionRow = buildDropdownRow(node, "collision_mode", "If File Exists",
        ["increment", "overwrite", "error", "seconds"],
        { optionLabels: { increment: "Increment number", overwrite: "Overwrite", error: "Error", seconds: "Add seconds" } });
    if (collisionRow) {
        addAdvancedRow(body, collisionRow.root,
            "What to do if the target filename already exists - Increment is the safest default.");
    }

    const detectionRow = buildDropdownRow(node, "detection_info", "Detection Info", ["Off", "Summary", "Verbose"]);
    if (detectionRow) {
        addAdvancedRow(body, detectionRow.root,
            "Optional detection summary in the node output - use Summary or Verbose to see " +
            "which model/text encoder were detected.");
    }

    const qualityRow = buildSliderRow(node, "image_quality", "Image Quality", { min: 1, max: 100 });
    node.__saveImageCleanQualityRow = qualityRow;
    if (qualityRow) {
        addAdvancedRow(body, qualityRow.root, "JPEG/WebP quality - ignored when Image Format is PNG.");
    }

    const metadataRow = buildSwitchRow(node, "export_workflow_metadata", "Export Workflow Metadata");
    node.__saveImageCleanMetadataRow = metadataRow;
    if (metadataRow) {
        addAdvancedRow(body, metadataRow.root,
            "Stores prompt/workflow metadata in the PNG - turn off for clean PNG files without it.");
    }

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

    node.__saveImageCleanAdvancedPanel = {
        trigger, panel, body, loaderDropdown,
        modelRow, modelFolderRow, clipRow, clipFolderRow,
        collisionRow, detectionRow, qualityRow, metadataRow,
    };
    return node.__saveImageCleanAdvancedPanel;
}

function createTemplateBuilderWidget(node, widgetName, triggerLabel) {
    const targetWidget = getWidget(node, widgetName);
    const triggerKey = `__saveImageCleanBuilder_${widgetName}_trigger`;
    const panelKey = `__saveImageCleanBuilder_${widgetName}_panel`;
    if (!targetWidget) {
        return null;
    }
    if (node[panelKey]) {
        return { trigger: node[triggerKey], panel: node[panelKey] };
    }

    injectTemplateBuilderCss();

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "sic-builder-trigger";
    // Trailing ellipsis + a tooltip naming what it builds (user request
    // 2026-10-13: "Build" alone didn't signal it opens another view).
    // buttons.md - Desktop (macOS): "Append a trailing ellipsis to the
    // title when a push button opens another window, view, or app."
    trigger.textContent = "✎ Build…";
    trigger.title = triggerLabel;

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

    const preview = document.createElement("div");
    preview.className = "sic-builder-preview";

    const updatePreview = () => {
        const now = new Date();
        const variables = buildVariables(node, now, node.__saveImageCleanLastRunInfo?.detection || null);
        if (widgetName === "filename_datetime") {
            preview.textContent = buildFilenameValue(node, now, variables);
            return;
        }
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

    node[triggerKey] = trigger;
    node[panelKey] = panel;
    return { trigger, panel };
}

// Extracted from the pre-Task-8 createHelpPanelWidget: same element
// construction and node.__saveImageCleanHelpRefs assignment, but returns the
// built container instead of also calling node.addDOMWidget itself - Task 8's
// single root widget is the only addDOMWidget call left in the whole file.
function buildHelpPanelContent(node) {
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

    const headerEl = document.createElement("div");
    headerEl.style.cssText = [
        "display:flex",
        "align-items:center",
        "justify-content:space-between",
        "gap:8px",
    ].join(";");

    const titleEl = document.createElement("div");
    titleEl.style.cssText = "font-size:12px;font-weight:600;color:#f3f3f3;";

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
        "transition:background 160ms var(--sic-ease), color 160ms var(--sic-ease), border-color 160ms var(--sic-ease)",
    ].join(";");

    const noteEl = document.createElement("div");
    noteEl.style.cssText = [
        "font-size:11px",
        "line-height:1.35",
        "color:#a9a9a9",
        "min-height:14px",
        "transition:color 160ms var(--sic-ease)",
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
            "padding:10px 12px 11px 11px",
            "min-height:28px",
            "box-sizing:border-box",
            "white-space:nowrap",
            "overflow:hidden",
            "text-overflow:ellipsis",
            "cursor:default",
            // Status color used to live on all four sides as border-color,
            // which reads exactly like an editable field's :focus ring -
            // user request 2026-10-13: this read-only preview looked
            // editable. A left accent strip keeps the same fresh/stale
            // color signal without borrowing input-focus visual language.
            "border:none",
            "border-left:3px solid transparent",
            "transition:border-color 160ms var(--sic-ease)",
            // Final-review finding (2026-10-13): the parent container sets
            // pointer-events:none so the help panel never intercepts clicks
            // meant for the node underneath; that also silently blocked this
            // element's own title= tooltip from ever firing, leaving a long
            // resolved path clipped with no way to see the rest (Review
            // Focus item 4). Re-enabled on just this element.
            "pointer-events:auto",
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

    headerEl.appendChild(titleEl);
    headerEl.appendChild(statusEl);
    container.appendChild(headerEl);
    container.appendChild(noteEl);
    container.appendChild(outputValueEl);
    container.appendChild(detailsTitleEl);
    container.appendChild(detailsEl);

    node.__saveImageCleanHelpRefs = {
        titleEl,
        statusEl,
        noteEl,
        outputValueEl,
        detailsTitleEl,
        detailsEl,
    };

    return container;
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

function formatDetectionSourceLabel(source, value, sourceLabel = "", sourceDistance = null) {
    if (source === "workflow") {
        const parsedDistance = Number(sourceDistance);
        const distanceLabel = Number.isInteger(parsedDistance)
            ? `${parsedDistance} upstream link${parsedDistance === 1 ? "" : "s"}`
            : "";
        const sourceDetail = [sourceLabel, distanceLabel].filter(Boolean).join(", ");
        const suffix = sourceDetail ? ` (from ${sourceDetail})` : "";
        return `workflow loader -> ${value || "(empty)"}${suffix}`;
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
        `Model detection: ${formatDetectionSourceLabel(
            snapshot.model_detection_source,
            snapshot.detected_model_name,
            snapshot.model_detection_label,
            snapshot.model_detection_distance,
        )}`,
        `Model output: ${snapshot.selected_model_source} -> ${snapshot.selected_model_name}`,
        `Text encoder detection: ${formatDetectionSourceLabel(
            snapshot.text_encoder_detection_source,
            snapshot.detected_text_encoder_name,
            snapshot.text_encoder_detection_label,
            snapshot.text_encoder_detection_distance,
        )}`,
        `Text encoder output: ${snapshot.selected_text_encoder_source} -> ${snapshot.selected_text_encoder_name}`,
    ];
}

function setHelperStatus(refs, status) {
    const states = {
        sample: {
            label: "Sample Preview",
            color: "#b7b7b7",
            background: "rgba(255,255,255,0.06)",
            border: "rgba(255,255,255,0.08)",
        },
        fresh: {
            label: "Fresh Detection",
            color: "#8eb7ff",
            background: "rgba(142,183,255,0.12)",
            border: "rgba(142,183,255,0.28)",
        },
        stale: {
            label: "Last Detection Snapshot",
            color: "#f0be47",
            background: "rgba(240,190,71,0.12)",
            border: "rgba(240,190,71,0.28)",
        },
    };
    const current = states[status] || states.sample;
    refs.statusEl.textContent = current.label;
    refs.statusEl.style.color = current.color;
    refs.statusEl.style.background = current.background;
    refs.statusEl.style.borderColor = current.border;
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

    setActiveFormatButton(node, getWidget(node, "image_format")?.value);
    setActiveSaveModeButton(node, getWidget(node, "save_mode")?.value);
    for (const row of node.__saveImageCleanSyncers || []) {
        row.sync?.();
    }

    if (lastRunInfo && !lastRunInfo.stale) {
        setHelperStatus(refs, "fresh");
        refs.outputValueEl.textContent = lastRunInfo.path;
        refs.noteEl.textContent = "Last run used real detected values.";
        refs.noteEl.style.color = "#8eb7ff";
        refs.outputValueEl.style.borderColor = "rgba(142, 183, 255, 0.3)";
    } else if (useLegacyOrder) {
        setHelperStatus(refs, detectionSnapshot ? "stale" : "sample");
        refs.outputValueEl.textContent = buildLegacyExample(node, variables);
        refs.noteEl.textContent = detectionSnapshot
            ? "Preview uses the last detected values from a previous run."
            : defaultNote;
        refs.noteEl.style.color = detectionSnapshot ? "#f0be47" : "#a9a9a9";
        refs.outputValueEl.style.borderColor = detectionSnapshot ? "rgba(240, 190, 71, 0.35)" : "transparent";
    } else {
        setHelperStatus(refs, detectionSnapshot ? "stale" : "sample");
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
    // Final-review finding (2026-10-13): nowrap+ellipsis clips a long
    // resolved path with no indication there's more - mirror the full text
    // into title= (now reachable since pointer-events is re-enabled above)
    // so hovering shows it, the same resting-state-truncation fix Task 6
    // already applied to the text-row inputs.
    refs.outputValueEl.title = refs.outputValueEl.textContent;

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
        "export_workflow_metadata",
        "image_format",
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
            updateContextualVisibility(node);
            return result;
        };

        if (widget.inputEl) {
            widget.inputEl.addEventListener("input", () => {
                markLastRunStateStale(node);
                updateHelp(node);
                updateContextualVisibility(node);
            });
            widget.inputEl.addEventListener("change", () => {
                markLastRunStateStale(node);
                updateHelp(node);
                updateContextualVisibility(node);
            });
        }

        widget.__saveImageCleanHooked = true;
    }
}

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
        // expand and resize both rendered correctly) - so the absolutely-
        // positioned inner-layer escape hatch is skipped; a plain flex
        // column on .sic-inner is sufficient (see the spec's Open Items).
        // overflow:hidden as a safety net (found live 2026-10-13 via the
        // preview-grid min-width:auto bug above): litegraph draws the
        // node's own boundary independently of this DOM widget's actual
        // rendered size, so any future layout bug that pushes content wider
        // than the node would otherwise bleed past its right edge with
        // nothing to clip it, instead of just looking wrong internally.
        // height:100% on both (user report 2026-10-14: enlarging the node by
        // hand left a dead gray gap below Example Output/Advanced instead of
        // growing the preview image) - without it, .sic-inner only ever sizes
        // to its own content height, so a node resized taller than that
        // content just shows empty canvas below a short, unstretched column.
        ".sic-root{width:100%;height:100%;max-width:100%;box-sizing:border-box;overflow:hidden;}",
        ".sic-inner{display:flex;flex-direction:column;min-width:0;height:100%;",
        "gap:var(--sic-space-lg);padding:var(--sic-space-outer) var(--sic-space-md);box-sizing:border-box;}",
        ".sic-section{display:flex;flex-direction:column;gap:var(--sic-space-sm);}",
        ".sic-section-head{display:flex;align-items:center;justify-content:space-between;",
        "padding:0 var(--sic-space-md);}",
        ".sic-eyebrow{font-size:var(--sic-font-section);font-weight:600;letter-spacing:0.03em;",
        "text-transform:uppercase;color:#9d9d9d;}",
        // Output/Mode: one wrapping row of pill groups at natural width,
        // packed left (Pixaroma's .pix-si-btnrow, user request 2026-10-13) -
        // no more flex:1 columns forcing the groups to equal widths.
        ".sic-output-mode-row{display:flex;flex-wrap:wrap;gap:var(--sic-space-md);",
        "align-items:center;padding:0 var(--sic-space-md);}",
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

function measureRootFloor(node, inner) {
    // FLOOR only, no getMaxHeight and no custom computeSize override (the
    // Pixaroma-proven pattern, index.js:1017-1020 in ComfyUI-Pixaroma) - the
    // node grows freely and a user's manual resize is never fought. Rounded
    // to a 4px grid purely so the floor doesn't jitter by 1px between calls
    // as sub-pixel layout rounding varies.
    const measured = inner.scrollHeight || 0;
    return Math.max(Math.round(measured / 4) * 4, 160);
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

    // --- SAVE LAYOUT (minimal: path + top folder; everything else moved to
    // Advanced Settings per 2026-10-13 live QA) ---
    const saveLayoutSection = buildSection("SAVE LAYOUT");
    const pathBuilder = createTemplateBuilderWidget(node, "path_template", "Build Path");
    saveLayoutSection.appendChild(buildHeadingRow("Folder Structure", pathBuilder?.trigger));
    const pathRow = buildTextRow(node, "path_template");
    if (pathRow) saveLayoutSection.appendChild(pathRow.root);
    const subfolderRow = buildTextRow(node, "subfolder", { placeholder: "Top Folder", tokenLabel: "%TOP_FOLDER%" });
    if (subfolderRow) saveLayoutSection.appendChild(subfolderRow.root);
    inner.appendChild(saveLayoutSection);

    // --- FILENAME (minimal: filename only) ---
    // No "FILENAME" eyebrow here (unlike SAVE LAYOUT's "Folder Structure"
    // heading, which reads as a distinct label): the heading row right below
    // already says "Filename", so the eyebrow was just the same word printed
    // twice (user report 2026-10-14).
    const filenameSection = buildSection();
    const filenameBuilder = createTemplateBuilderWidget(node, "filename_datetime", "Build Filename");
    filenameSection.appendChild(buildHeadingRow("Filename", filenameBuilder?.trigger));
    const filenameRow = buildTextRow(node, "filename_datetime");
    if (filenameRow) filenameSection.appendChild(filenameRow.root);
    inner.appendChild(filenameSection);

    // --- Advanced Settings trigger row (moved up here, 2026-10-14 user
    // report: it used to sit after Example Output near the node's bottom,
    // disconnected from the rest of the settings it toggles) ---
    const advanced = createAdvancedPanel(node);
    const advRow = el("div", "sic-section-head");
    const advLabel = el("span", "sic-eyebrow", "ADVANCED");
    advRow.appendChild(advLabel);
    advRow.appendChild(advanced.trigger);
    inner.appendChild(advRow);

    // --- OUTPUT + MODE, one wrapping row of pill groups at natural width
    // (Pixaroma's save_image/ui.mjs .pix-si-btnrow pattern, named by the
    // user as the reference 2026-10-13) - dropped the separate "OUTPUT"/
    // "MODE" eyebrow sections stretched to equal flex:1 widths, which forced
    // the 3-option format group and the 2-option mode group into mismatched
    // segment sizes for no reason; each pill group's tooltip (getTitle)
    // already carries the labeling Pixaroma also relies on instead of a
    // heading. ---
    const outputModeRow = el("div", "sic-output-mode-row");
    const formatSeg = buildSegmentedControl(node, "image_format", IMAGE_FORMAT_IDS, {
        getTitle: (id) => `Save as ${id}`,
    });
    node.__saveImageCleanFormatSeg = formatSeg;
    if (formatSeg) outputModeRow.appendChild(formatSeg.root);

    const saveModeSeg = buildSegmentedControl(node, "save_mode", SAVE_MODE_IDS, {
        getTitle: (id) => (id === "Preview"
            ? "Show the result without saving; save individual images later"
            : "Save immediately, as before"),
    });
    node.__saveImageCleanSaveModeSeg = saveModeSeg;
    if (saveModeSeg) outputModeRow.appendChild(saveModeSeg.root);
    inner.appendChild(outputModeRow);

    // --- Preview grid (Preview-mode only), existing internals reused ---
    injectPreviewGridCss();
    const gridContainer = el("div", "sic-preview-grid");
    gridContainer.style.display = "none";
    const gridBody = el("div", "sic-preview-grid-body");
    gridContainer.appendChild(gridBody);
    node.__saveImageCleanPreviewGridRefs = { container: gridContainer, body: gridBody };
    inner.appendChild(gridContainer);

    // --- Example Output, moved below the preview grid toward the node
    // bottom (user request 2026-10-13); its Detection Snapshot sub-section
    // is re-parented into the Advanced panel below, same refs either way. ---
    const helpRoot = buildHelpPanelContent(node);
    inner.appendChild(helpRoot);

    const helpRefs = node.__saveImageCleanHelpRefs;
    if (helpRefs) {
        advanced.body.appendChild(helpRefs.detailsTitleEl);
        advanced.body.appendChild(helpRefs.detailsEl);
    }

    const rootWidget = node.addDOMWidget("save_image_clean_root", "custom", root, {
        getMinHeight: () => measureRootFloor(node, inner),
        serialize: false,
        hideOnZoom: false,
        // Non-zero margin (matches --sic-space-outer) so the DOM widget
        // doesn't extend flush to the node's bottom-right corner - found
        // live 2026-10-13: margin:0 let this widget's own content cover the
        // canvas-drawn resize handle, leaving only the top edge (title bar,
        // not covered by any DOM overlay) able to start a resize drag.
        margin: 14,
    });
    // Found live 2026-10-13, confirmed via DevTools (not guessed - this is
    // after 7 earlier attempts at this node's width tracking): ComfyUI's
    // per-frame DOM-widget positioner (GraphView bundle, hooked into
    // onDrawForeground) computes this widget's on-screen width as
    // `(widget.width ?? node.width) - margin*2`. addDOMWidget sets
    // `widget.width` ONCE, to the node's width at creation time, and NEVER
    // updates it again on resize - confirmed live: rootWidget.width stayed
    // frozen at the node's original width (364.4) while node.width/
    // node.size[0] correctly tracked a live resize (913.77 = 913.77).
    // Since widget.width is never undefined once set, it always wins over
    // the (already correctly live) node.width fallback. Fix: make the
    // property undefined again instead of feeding it node.size[0]
    // ourselves - an own value here risks being read elsewhere as a
    // minimum-width floor (the same one-way-ratchet failure class as the
    // height setSize() bug fixed earlier this session), where returning
    // undefined just restores the normal, already-correct node.width
    // fallback. A no-op setter avoids breaking whatever internal write set
    // the original static value.
    Object.defineProperty(rootWidget, "width", {
        get: () => undefined,
        set: () => {},
        configurable: true,
    });
    // Plan code originally omitted this line (caught before committing, not
    // live-verified): comfyui_frontend_package 1.53.10's
    // serialiseWidgetValues()/widgets_values restore both check
    // widget.serialize === false directly - the addDOMWidget options.serialize
    // flag above is never copied there (same root cause as the 2026-10-12
    // widgets_values corruption bug this plan's earlier tasks already fixed
    // for every other custom widget). Without this, the single root widget
    // would itself get counted as a real positional widgets_values slot.
    rootWidget.serialize = false;

    // Final-review finding (2026-10-13, static analysis against the
    // installed frontend bundle): onNodeCreated builds every row above from
    // each native widget's DEFAULT value. When a saved workflow loads
    // instead, configure() restores the real values with a plain assignment
    // (no callback, no input event), so the dropdowns/switch/slider/tooltips
    // built here keep showing their defaults even though the underlying
    // widget.value (and therefore the save) is already correct. updateHelp
    // runs on every relevant pass, including once after configure()'s own
    // restore completes, so it re-runs every row's sync() there too.
    node.__saveImageCleanSyncers = [
        pathRow, subfolderRow, filenameRow,
        advanced.modelRow, advanced.clipRow, advanced.modelFolderRow, advanced.clipFolderRow,
        advanced.collisionRow, advanced.detectionRow, advanced.qualityRow, advanced.metadataRow,
        advanced.loaderDropdown,
    ].filter(Boolean);
}

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

    // REVERTED 2026-10-13: the node.size[1]-only shrink tried here caused
    // the node to render far wider than its content immediately after a
    // mode switch (reported live, screenshot evidence) even though this
    // code never touches size[0] and no getMinWidth-style hook exists in
    // the installed frontend bundle (checked directly, not guessed) that
    // could tie DOM content back to node width. Cause not yet proven, but
    // the timing correlation is strong enough that shipping it further
    // isn't worth the risk - reverted to no auto-shrink (the known, lesser
    // issue: a leftover empty gap after a mode switch) until this is
    // understood. No manual setSize() call here at all - see commit
    // 14c8d27's finding: calling it on every widget edit replaces
    // node.size with a new array and breaks manual corner-drag resize.
    node.setDirtyCanvas?.(true, true);
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
                buildNodeUI(this);
                hookWidgetUpdates(this);
                updateHelp(this);
                updateContextualVisibility(this);
            });
            return result;
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            // Deferred to match `configure()` below: on a freshly-dropped
            // node, ComfyUI's native STRING widgets (path_template,
            // filename_datetime, subfolder, model_folder, clip_folder) do
            // not have `.inputEl` populated yet at this synchronous point,
            // so buildTextRow()'s `!widget.inputEl` guard silently skips
            // them - they stay un-hidden native widgets instead of custom
            // rows (found live 2026-10-13: all 5 text fields leaking above
            // the custom UI on a fresh node). One frame later it's ready.
            requestAnimationFrame(() => {
                setFriendlyLabels(this);
                buildNodeUI(this);
                hookWidgetUpdates(this);
                updateHelp(this);
                updateContextualVisibility(this);
            });
            return result;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const result = onExecuted?.apply(this, arguments);
            setLastRunStateFromMessage(this, message);
            updateHelp(this);
            updatePreviewGrid(this, message);
            // Was missing here (found live 2026-10-13): this is exactly
            // where the preview grid's visibility/height changes the most
            // (Preview mode run -> image+button shown; Save mode run ->
            // grid hidden), so it's exactly where updateContextualVisibility's
            // sticky-floor shrink check needs to run too, not just on
            // onNodeCreated/configure.
            updateContextualVisibility(this);
            return result;
        };

        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            const result = onRemoved?.apply(this, arguments);
            this.__saveImageCleanBuilder_path_template_panel?.remove();
            this.__saveImageCleanBuilder_filename_datetime_panel?.remove();
            // Final-review finding (2026-10-13): createAdvancedPanel (Task 7)
            // appends its panel to document.body the same way the two
            // template-builder panels above do, but onRemoved never cleaned
            // it up - every add/remove cycle left another detached floating
            // panel on screen, and a panel left open when its node is
            // deleted kept writing to a dead node's widget.
            this.__saveImageCleanAdvancedPanel?.panel.remove();
            return result;
        };
    },
});
