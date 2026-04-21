# ComfyUI Clean Save Nodes

## Ziel

Dieses Custom-Node-Paket erweitert ComfyUI um eine saubere, minimalistische und workflow-orientierte Bildspeicherung.

Der Fokus liegt auf:

- klarer Ordnerstruktur (`Model / CLIP`)
- kurzen, konsistenten Dateinamen
- automatischer Erkennung aktiver Loader-Namen
- Template-basierten Speicherpfaden
- Erhalt von Prompt- und PNG-Metadaten

---

## Enthaltene Nodes

- `Save Image Clean`
- `Strip Model Extension`

---

## Schnellstart

1. Repository in `ComfyUI/custom_nodes/comfyui-clean-save-nodes` ablegen.
2. Abhaengigkeiten aus `requirements.txt` in der ComfyUI-Python-Umgebung installieren.
3. ComfyUI neu starten.
4. `Save Image Clean` im Workflow verwenden.

Weitere Doku:

- [Installation](docs/INSTALLATION.md)
- [Usage](docs/USAGE.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---

## Save Image Clean

`Save Image Clean` unterstützt jetzt zwei Modi:

- Legacy-Modus über `model_folder`, `clip_folder`, `subfolder` und `filename_datetime`
- Template-Modus über `path_template`

Wenn `path_template` leer ist, verwendet der Node weiter den Legacy-Modus. Das hält bestehende Workflows kompatibel.

### Legacy-Modus

Der Legacy-Modus speichert nach diesem Schema:

```text
<output_root>/<subfolder>/<model_folder>/<clip_folder>/<filename_datetime>.png
```

`filename_datetime` verwendet Python-`strftime`.

Beispiel:

```text
%Y-%m-%d_%H-%M
```

### Template-Modus

Wenn `path_template` gesetzt ist, wird der Zielpfad aus einem Template berechnet.

Empfohlener Startwert:

```text
%ACTIVE_UNET%/%ACTIVE_CLIP%/%date:yyyy-MM-dd_hh-mm%
```

Beispielergebnis:

```text
jibMixZIT_v10/Huihui-Qwen3-4B-abliterated-v2.Q8_0/2026-04-21_14-37.png
```

### Unterstützte Template-Variablen

- `%ACTIVE_UNET%`
- `%ACTIVE_CLIP%`
- `%MODEL_SHORT%`
- `%CLIP_SHORT%`
- `%MODEL_FOLDER%`
- `%CLIP_FOLDER%`
- `%SUBFOLDER%`

### Unterstützte Datumsplatzhalter

Der Template-Modus unterstützt ComfyUI-Style-Datumssegmente:

```text
%date:yyyy-MM-dd_hh-mm%
```

Aktuell werden diese Tokens umgesetzt:

- `yyyy`
- `yy`
- `MM`
- `dd`
- `HH`
- `hh`
- `mm`
- `ss`

Hinweis:
`hh` und `HH` werden beide als 24-Stunden-Ausgabe behandelt.

### Automatische Loader-Erkennung

Im Template-Modus versucht der Node, den aktiven Namen über den ComfyUI-`prompt`-Graph upstream vom aktuellen Save-Node zu erkennen.

Aktuell berücksichtigt die Erkennung vor allem:

- UNET-Loader über Klassen mit `UnetLoader` im Namen
- CLIP-Loader über Klassen mit `ClipLoader` im Namen
- Checkpoint-Loader als Fallback über Klassen mit `CheckpointLoader` im Namen

Wenn keine Erkennung möglich ist, fällt der Node auf die manuell gesetzten Felder `model_folder` und `clip_folder` zurück.

### Kürzere Namensvarianten

`%MODEL_SHORT%` und `%CLIP_SHORT%` entfernen bekannte Modell-Endungen und kürzen zusätzlich Prefixe im Stil:

```text
mradermacher - Huihui-Qwen3-4B-abliterated-v2.Q8_0.gguf
```

zu:

```text
Huihui-Qwen3-4B-abliterated-v2.Q8_0
```

### Pfad- und Namensbereinigung

Folgende Endungen werden automatisch entfernt:

- `.safetensors`
- `.gguf`
- `.ckpt`
- `.pt`
- `.pth`
- `.bin`
- `.onnx`

Außerdem werden ungültige Windows-Zeichen ersetzt, damit Pfade und Dateinamen stabil bleiben.

### Verhalten bei Namenskollisionen

Unterstützte Modi:

- `increment`
- `overwrite`
- `error`
- `seconds`

Beispiel für `increment`:

```text
2026-04-21_14-30.png
2026-04-21_14-30-2.png
```

### Metadaten

Beim Speichern werden vorhandene ComfyUI-Daten in die PNG-Datei geschrieben:

- `prompt`
- Inhalte aus `extra_pnginfo`

### UI-Vorschau

Nach dem Ausführen liefert der Node einen UI-Text mit dem aufgelösten relativen Zielpfad zurück.

Das ist eine Laufzeit-Vorschau nach Template-Auflösung, keine permanente Live-Vorschau im Node vor dem Ausführen.

---

## Strip Model Extension

Dieser Utility-Node entfernt genau eine bekannte Modell-Dateiendung am Ende eines Strings.

Beispiel:

```text
my-model.safetensors -> my-model
```

---

## Was Weiterhin Nicht Implementiert Ist

Der aktuelle Stand deckt die Kernfeatures ab, aber nicht alles aus der ursprünglichen Wunschliste.

Noch offen sind insbesondere:

- echte Live-Vorschau direkt im Node vor der Ausführung
- breitere Erkennung exotischer oder projektspezifischer Loader-Typen
- frei konfigurierbare String-Manipulation innerhalb des Templates
- weitergehende Kürzungsregeln über die aktuelle Prefix-Entfernung hinaus

---

## Designprinzipien

- Ordner = Struktur (`Model / CLIP`)
- Dateiname = klar und kurz
- Metadaten = vollständig erhalten
- Verhalten = explizit statt implizit

---

## Fazit

Der Node unterstützt jetzt sowohl den bisherigen manuellen Save-Workflow als auch einen automatischen Template-Workflow.

Wer `path_template` nutzt, kann Modell-, CLIP- und Zeitinformationen direkt im Zielpfad kombinieren, ohne den Pfad pro Workflow manuell umzubauen.
