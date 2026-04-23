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
    subfolder: "Top Folder",
    model_folder: "Custom Model Name",
    clip_folder: "Custom Text Encoder Name",
};

const SAMPLE_MODEL = "flux-2-klein-9b-Q5_K_M.gguf";
const SAMPLE_CLIP = "Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf";
const DEFAULT_LAYOUT = "%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%";
const DEFAULT_FILENAME = "%date:yyyy-MM-dd_hh-mm-ss%";
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
const QUANT_RE = /^(.*?)(?:[ ._-]+)?(Q\d+_K_[MS]|Q\d+_K|Q\d+_0|Q\d+|IQ\d+_[A-Z]+|FP8_e4m3fn|FP8_e5m2|BF16|F16)$/i;
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
        Q4_K_M: "[4K-M]",
        Q4_K_S: "[4K-S]",
        Q5_K_M: "[5K-M]",
        Q5_K_S: "[5K-S]",
        Q6_K: "[6K]",
        Q8_0: "[q8]",
        Q8: "[q8]",
        FP8_E4M3FN: "[FP8-E4M3FN]",
        FP8_E5M2: "[FP8-E5M2]",
        BF16: "[BF16]",
        F16: "[FP16]",
    };
    if (exactMap[normalized]) {
        return exactMap[normalized];
    }
    const match = normalized.match(/^IQ(\d+)_([A-Z]+)$/);
    if (match) {
        return `[IQ${match[1]}-${match[2]}]`;
    }
    const plainQuant = normalized.match(/^Q(\d+)$/);
    if (plainQuant) {
        return `[q${plainQuant[1]}]`;
    }
    return `[${normalized}]`;
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

function humanizeDisplayName(value) {
    let baseValue = basenameWithoutKnownExtension(value || "");
    let quantDisplay = "";
    const quantMatch = baseValue.match(QUANT_RE);
    if (quantMatch) {
        baseValue = quantMatch[1].replace(/[ ._-]+$/, "");
        quantDisplay = formatQuantDisplay(quantMatch[2]);
    }

    const tagMatch = baseValue.match(/^(?:[A-Z0-9]{2,8}[_-]+)(.+)$/);
    if (tagMatch) {
        baseValue = tagMatch[1];
    }

    baseValue = baseValue
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

function buildVariables(node, now) {
    const topFolder = getWidget(node, "subfolder")?.value || "";
    const customModelName = stripKnownExtension(getWidget(node, "model_folder")?.value || "");
    const customTextEncoderName = stripKnownExtension(getWidget(node, "clip_folder")?.value || "");
    const modelSource = getWidget(node, "model_source")?.value || "Friendly";
    const clipSource = getWidget(node, "clip_source")?.value || "Friendly";

    const variables = {
        TOP_FOLDER: topFolder.trim() ? sanitizePathPart(topFolder) : "",
        EXACT_MODEL_NAME: basenameWithoutKnownExtension(SAMPLE_MODEL) || "model",
        EXACT_TEXT_ENCODER_NAME: basenameWithoutKnownExtension(SAMPLE_CLIP) || "text-encoder",
        FRIENDLY_MODEL_NAME: humanizeDisplayName(SAMPLE_MODEL),
        FRIENDLY_TEXT_ENCODER_NAME: humanizeDisplayName(SAMPLE_CLIP),
        CUSTOM_MODEL_NAME: customModelName,
        CUSTOM_TEXT_ENCODER_NAME: customTextEncoderName,
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

function buildLayoutExample(node, variables, now) {
    const layout = String(getWidget(node, "path_template")?.value || DEFAULT_LAYOUT).trim();
    let rendered = layout.replace(/%date:([^%]+)%/g, (_, format) => renderDateFormat(format, now));
    rendered = rendered.replace(/%strftime:([^%]+)%/g, (_, format) => renderStrftime(format, now));
    rendered = rendered.replace(/%([^%./\\]+)\.([^%./\\]+)%/g, (_, nodeName, widgetName) => `<${nodeName}.${widgetName}>`);
    rendered = rendered.replace(/%([A-Z0-9_]+)%/g, (_, key) => variables[key] ?? `%${key}%`);

    let cleanPath = sanitizeRelativePath(rendered);
    if (!cleanPath.toLowerCase().endsWith(".png")) {
        cleanPath = `${cleanPath}.png`;
    }
    return cleanPath;
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
        ].join(";");
        return valueEl;
    };

    const outputValueEl = createPreviewValue();

    container.appendChild(titleEl);
    container.appendChild(outputValueEl);

    node.__saveImageCleanHelpRefs = {
        titleEl,
        outputValueEl,
    };
    node.__saveImageCleanHelpWidget = node.addDOMWidget("save_image_clean_help", "custom", container, {
        getMinHeight: () => 74,
        getMaxHeight: () => 84,
        serialize: false,
        hideOnZoom: false,
        margin: 8,
    });

    return node.__saveImageCleanHelpWidget;
}

function updateHelp(node) {
    const refs = node.__saveImageCleanHelpRefs;
    if (!refs) {
        return;
    }

    const now = new Date();
    const saveLayout = String(getWidget(node, "path_template")?.value || "").trim();
    const variables = buildVariables(node, now);
    const useLegacyOrder = saveLayout === "";

    ensureSectionLabel(node, "save_layout", "Save Layout", "path_template");
    ensureSectionLabel(node, "filename", "Filename", "filename_datetime");

    refs.outputValueEl.textContent = useLegacyOrder
        ? buildLegacyExample(node, variables)
        : buildLayoutExample(node, variables, now);
    refs.titleEl.textContent = "Example Output";

    const newSize = node.computeSize();
    newSize[0] = Math.max(newSize[0], node.size[0]);
    newSize[1] = Math.max(newSize[1], 390);
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
            updateHelp(node);
            return result;
        };

        if (widget.inputEl) {
            widget.inputEl.addEventListener("input", () => updateHelp(node));
            widget.inputEl.addEventListener("change", () => updateHelp(node));
        }

        widget.__saveImageCleanHooked = true;
    }
}

app.registerExtension({
    name: "comfyui-clean-save-nodes.save-image-clean-ux",
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
    },
});
