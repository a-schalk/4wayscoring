# 🪂 FAI 4-Way Formation Skydiving Debriefing & Scoring System

Ein professionelles Briefing- und Debriefing-Tool für 4-Way Formation Skydiving Teams zur Rundenauswertung, Sprunganalyse und Vorbereitung.

---

## 📑 Inhaltsverzeichnis

- [Überblick](#-überblick)
- [Hauptfunktionen](#-hauptfunktionen)
  - [1. Video-Trimming & Schnitt (GoPro Cutter)](#1-video-trimming--schnitt-gopro-cutter)
  - [2. Dual Cam Modus (Zwei-Kamera-Perspektive)](#2-dual-cam-modus-zwei-kamera-perspektive)
  - [3. Working Time Timer & Exit-Erfassung](#3-working-time-timer--exit-erfassung)
  - [4. Präzises Point Judging & Key Tracking](#4-präzises-point-judging--key-tracking)
  - [5. Interaktive Zeitleiste (Scoring Timeline)](#5-interaktive-zeitleiste-scoring-timeline)
  - [6. Telestration Glass Pane Overlay (Video-Zeichenwerkzeuge)](#6-telestration-glass-pane-overlay-video-zeichenwerkzeuge)
  - [7. Debrief Analytics & Report-Export](#7-debrief-analytics--report-export)
- [Programmglobale Tastaturkürzel](#-programmglobale-tastaturkürzel)
- [Anleitung: Dual Cam Modus](#-anleitung-dual-cam-modus)
- [Standard-Ordner & Quick Links (Favoriten)](#-standard-ordner--quick-links-favoriten)
- [Projektstruktur](#-projektstruktur)
- [Installation & Voraussetzungen](#-installation--voraussetzungen)
- [Starten der Anwendungen](#-starten-der-anwendungen)

---

## 🎯 Überblick

Das System besteht aus zwei aufeinander abgestimmten Anwendungen:
1. **`scoring.py`**: Interaktives Debriefing-, Video- und Wertungstool mit genauer Zeiterfassung, Frame-by-Frame-Steuerung, Telestration und Leistungsstatistiken.
2. **`formation_tool.py`**: Interaktiver 3D Formation Explorer zur dreidimensionalen Visualisierung des FAI Dive Pools, Head Switches, Griffverbindungen (Grips) und Key-Zuordnungen.

---

## 🚀 Hauptfunktionen

### 1. Video-Trimming & Schnitt (GoPro Cutter)
- Schnelles Schneiden von GoPro Rohvideos direkt in der Anwendung via `ffmpeg`.
- Markieren von Start Frame (`In`) und End Frame (`Out`).
- Vollständig stumm geschalteter Export (`-an`), optimiert für kompakte Dateigrößen und flüssige Wiedergabe.
- Der geschnittene Clip wird nach Abschluss automatisch geladen.

### 2. Dual Cam Modus (Zwei-Kamera-Perspektive)
- Parallele, synchrone Wiedergabe von zwei Blickwinkeln (z.B. Helm-Kamera Outside-Videographer + Zweitperspektive / Innenkamera).
- Automatische Zeitsynchronisation beim Laden und gemeinsame Steuerung (Play/Pause, Frame-Steps, Seek).
- Beide Videofenster verfügen über unabhängige Telestration-Overlays.

### 3. Working Time Timer & Exit-Erfassung
- Ein-Klick-Setzen des Exit-Zeitpunkts (`Taste T`).
- Presets für Working Time:
  - **35s (Competition)**: Offizielle FAI Wettbewerbszeit
  - **20s (Rookie / Speed)**
  - **60s (Training)**
  - **Custom**: Beliebige eigene Dauer
- Live-Anzeige: Pre-Exit Countdown, verbleibende Arbeitszeit mit Fortschrittsbalken und optische Warnung bei Zeitablauf.

### 4. Präzises Point Judging & Key Tracking
- **Formation Finished (`F`)**: Markiert den genauen Zeitpunkt, an dem alle Griffe einer Formation geschlossen wurden.
- **Key Given (`K`)**: Markiert den Schlüssel / Bruch zur nächsten Formation.
- **Punkt Anerkannt (`S` oder `1`)**: Wertet die Formation als gültigen Score (+1).
- **Bust / Fehler (`B` oder `0`)**: Wertet die Formation als Bust (0).
- Automatische Berechnung von:
  - **Hold Time**: Zeitdauer zwischen Griffschluss und Key.
  - **Transition Time**: Übergangszeit vom vorherigen Key bis zum nächsten Griffschluss.

### 5. Interaktive Zeitleiste (Scoring Timeline)
- Optische Darstellung der gesamten Sprungzeit:
  - Schnittbereich (In/Out) in Hellblau
  - Working Time Fenster ab Exit in Grün
  - Gezählte Punkte (Grüne Badges = Approved, Rote Badges = Bust)
  - Key-Zeitpunkte als goldene Diamanten mit Verbindungsbalken zur Formation
- Klick- und Zieh-Navigation (Scrubber) mit millimetergenauer Positionierung.

### 6. Telestration Glass Pane Overlay (Video-Zeichenwerkzeuge)
- Zeichnen direkt auf dem pausierten oder laufenden Video:
  - **Cursor-Modus (`Escape`)**: Standard-Mauszeiger
  - **Linie**: Verbindungslinien zwischen Springern
  - **Pfeil**: Bewegungsrichtungen und Drehachsen
  - **Winkel (°)**: 3-Punkt-Winkelmessung mit automatischer Gradanzeige
  - **Freihand**: Beliebige Skizzen
- Undo (`Strg+Z`) und Gesamtlöschen.

### 7. Debrief Analytics & Report-Export
- Vollständige Wertungstabelle mit Spalten für Formation, Status, Fertig-Zeit, Key-Zeit, Hold-Dauer, Transition-Dauer und bearbeitbaren Notizen.
- Automatischer Sprung zur Videoposition beim Navigieren durch die Tabelle (`Pfeil Oben / Unten`).
- Performance-Metriken: Durchschnittliche Haltezeit, durchschnittliche Übergangszeit und Pace (Sekunden pro Punkt).
- **Session Speichern / Laden (`.json`)**: Speichert alle gesetzten Punkte, Zeiten, Notizen und Videopfade (inkl. Cam 2).
- **Report Export (`.md`)**: Generiert einen sauberen Markdown-Debrief-Bericht für das Team.

---

## ⌨️ Programmglobale Tastaturkürzel

Alle Shortcuts funktionieren im gesamten Programm zuverlässig, unabhängig davon, ob zuvor ein Button, die Zeitleiste oder die Tabelle angeklickt wurde.

| Taste / Kürzel | Funktion | Beschreibung |
| :--- | :--- | :--- |
| **`Leertaste`** | Play / Pause | Video abspielen oder anhalten |
| **`Pfeil Rechts`** | Frame-Step Vor | 1 Einzelbild vorwärts |
| **`Pfeil Links`** | Frame-Step Zurück | 1 Einzelbild rückwärts |
| **`Shift + Pfeil Rechts`** | +1.0s Sprung | 1 Sekunde vorwärts springen |
| **`Shift + Pfeil Links`** | -1.0s Sprung | 1 Sekunde rückwärts springen |
| **`T`** | Timer / Exit | Exit-Zeitpunkt auf aktuelle Videoposition setzen |
| **`F`** | Formation Fertig | Zeitpunkt des Griffschlusses markieren (Completion) |
| **`K`** | Key Gegeben | Zeitpunkt des Schlüssels / Bruchs markieren (Break) |
| **`S`** oder **`1`** | Score (+1) | Formation anerkannt und gewertet |
| **`B`** oder **`0`** | Bust (0) | Fehler / Bust gewertet |
| **`[`** oder **`I`** | Start Frame (In) | In-Point für Trimmer setzen |
| **`]`** oder **`O`** | End Frame (Out) | Out-Point für Trimmer setzen |
| **`Entf`** / **`Backspace`** | Punkt löschen | Ausgewählten Punkt aus Wertungstabelle entfernen |
| **`Pfeil Oben / Unten`** | Tabelle navigieren | Zeilen wechseln (Video springt zum jeweiligen Punkt) |
| **`Strg + Z`** | Telestration Undo | Letzte Zeichnung rückgängig machen |
| **`Escape`** | Abbrechen / Reset | Telestration zurück zu Cursor / Texteingabefeld verlassen |
| **`Strg + S`** | Session speichern | Aktuelle Wertung als `.json` speichern |
| **`Strg + O`** | Session laden | Gespeicherte Debrief-Session `.json` öffnen |
| **`Strg + E`** | Report exportieren | Debrief-Report als `.md` Datei exportieren |
| **`F1`** | Shortcuts-Hilfe | Interaktives Hilfefenster mit allen Kürzeln öffnen |

> [!NOTE]
> **Texteingabe-Schutz:** Befindet sich der Eingabefokus in einem Textfeld (z.B. Draw-Sequenz, Sprungname oder Notizfeld in der Tabelle), tippen alle Tasten normal Text. Mit **`Enter`** oder **`Escape`** wird das Textfeld verlassen und die globale Steuerung ist sofort wieder aktiv.

---

## 👥 Anleitung: Dual Cam Modus

Der Dual Cam Modus ermöglicht die parallele, synchrone Betrachtung zweier Kameras.

1. **Dual Cam Ansicht aktivieren:**
   - Klicke in der oberen Trimmer-Leiste auf den Button **`👥 Dual Cam Ansicht`**.
   - Die Videoanzeige teilt sich in zwei Bildschirme:
     - **Links:** `Cam 1 (Hauptkamera)`
     - **Rechts:** `Cam 2 (Zweitkamera)`

2. **Zweites Video laden:**
   - Klicke auf den lila Button **`📹 Cam 2 laden...`** in der oberen Toolbar **oder** direkt auf **`📂 Video 2 wählen...`** über dem rechten Videobildschirm.
   - Wähle die Videodatei der Zweitkamera aus.

3. **Synchrone Wiedergabe:**
   - Das zweite Video synchronisiert sich beim Laden automatisch auf die aktuelle Position und den Play/Pause-Status von Cam 1.
   - Alle Shortcuts (`Leertaste`, Einzelbild-Stepping etc.) steuern beide Videos parallel synchron an.
   - Der Pfad zu Cam 2 wird beim Speichern der Session (`Strg+S`) automatisch mitgesichert und beim Laden (`Strg+O`) direkt wiederhergestellt.

---

## 📂 Standard-Ordner & Quick Links (Favoriten)

Um den Workflow beim Laden von GoPro-Footage und Debriefing-Videos maximal zu beschleunigen, bietet das Tool konfigurierbare Pfade und Quick-Links:

### 1. Konfigurations-Dialog (`⚙️ Pfade & Ordner...`)
- Klicke im oberen Header-Bereich auf **`⚙️ Pfade & Ordner...`** (oder im Dropdown-Menü **`⚡ Quick Links ▾`** auf *Pfade & Quick Links konfigurieren*).
- **Standard-Ordner (Default Video Directory):**
  - Legt fest, welches Verzeichnis der Dateidialog beim Klick auf `Video 1 laden...` oder `Video 2 wählen...` automatisch öffnet.
  - Standardmäßig auf `~/Videos` voreingestellt.
  - Kann über **`📂 Auswählen...`** frei angepasst oder mit **`↺ Standard`** zurückgesetzt werden.
- **Quick Links / Favoriten-Ordner:**
  - Füge über **`➕ Ordner hinzufügen...`** beliebige Verzeichnisse (z.B. Dropzone-Ordner, Team-Trainings, Saison-Archive) hinzu.
  - Diese Ordner erscheinen **automatisch als Lesezeichen in der linken Seitenleiste** jedes Qt-Dateidialogs.
  - Mit **`➖ Entfernen`** können Einträge wieder gelöscht werden.
- **Automatische SD-Karten-Erkennung:**
  - Klicke auf **`🔍 GoPro / SD-Karte suchen`**. Das System durchsucht typische Linux-Mount-Pfade (`/media/$USER/.../DCIM`, `/run/media/...`) und fügt gefundene Kameras direkt zu den Quick Links hinzu.
- Alle Einstellungen werden dauerhaft in der Benutzerkonfiguration (`QSettings`) gespeichert.

### 2. Dropdown-Schnellzugriff (`⚡ Quick Links ▾`)
- Direkt neben dem Button `📹 Video 1 laden...` befindet sich das Schnellmenü **`⚡ Quick Links ▾`**:
  - **Quick-Link Ordner:** Klick öffnet den Dateidialog direkt im gewählten Verzeichnis.
  - **Zuletzt geöffnete Videos:** Listet die letzten Videos auf – ein Klick lädt das Video sofort, ohne Umweg über einen Dateidialog.
  - **GoPro / SD-Karte suchen:** Schneller Scan nach frisch eingesteckten Speicherkarten.

---

## 📁 Projektstruktur

```
4wayscoring/
├── scoring.py               # Hauptanwendung: Debriefing, Videoplayer, Trimmer & Scoring
├── formation_tool.py        # 3D Formation Explorer & Visualizer
├── formation_db.py          # FAI 4-Way Dive Pool Datenbank (Randoms A-Q, Blöcke 1-22)
├── 4way_knowledge_base.md   # Wissensdatenbank: FAI Regeln, Griffdefinitionen, Key-Prinzipien
├── 4way.md                  # Projektnotizen und Architektur-Übersicht
├── todo.md                  # Anforderungskatalog
├── 4wayCheatSheet.svg       # Visuelle Übersicht aller Formationen
├── 4way-Randoms-Only.pdf    # FAI Pool Übersicht Randoms
├── 4way-Blocks-Only.pdf     # FAI Pool Übersicht Blöcke
├── AlternateEngineering.pdf # Block-Technik Referenz
└── README.md                # Projektdokumentation
```

---

## ⚙️ Installation & Voraussetzungen

### Systemanforderungen:
- **Betriebssystem:** Linux / macOS / Windows
- **Python:** Version 3.10 oder neuer
- **System-Abhängigkeiten:** `mpv` / `libmpv` und `ffmpeg`

Unter Ubuntu / Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip libmpv-dev libmpv2 ffmpeg
```

### Python-Pakete installieren:
```bash
pip install PyQt6 python-mpv
```

---

## 🎬 Starten der Anwendungen

### Debriefing & Scoring Tool starten:
```bash
python3 scoring.py
```

### 3D Formation Explorer direkt starten:
```bash
python3 formation_tool.py
```
*(Der 3D Explorer kann auch jederzeit direkt aus `scoring.py` über den Button **`🎯 3D Formationen...`** geöffnet werden.)*
