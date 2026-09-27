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

### 4. FAI 4-Way Dive Pool & Block-Behandlung (2 Punkte pro Block)
- **Randoms (A–Q)**: Zählen jeweils als 1 einzelner Wertungspunkt (z.B. `A`, `B`, `C`).
- **FAI-Blöcke (1–22)**: Bestehen im 4-Way stets aus zwei getrennten Punkten:
  1. **Initial-Formation** (Start des Blocks, z.B. `12-1 Bundy`)
  2. **Closing-Formation** (Abschluss nach dem Block-Inter, z.B. `12-2 Bundy`)
- **Zyklus-Expansion**: Ein eingegebenes Draw wie `A - 12 - 7 - B` wird automatisch in eine Sequenz von 6 Wertungspunkten pro Zyklus übersetzt:
  `A` ➔ `12-1` ➔ `12-2` ➔ `7-1` ➔ `7-2` ➔ `B` ➔ `A` ...
- Die automatische Punktezählung rotiert präzise durch diese Sequenz, sodass jeder Block korrekt mit 2 Punkten in die Wertung und Rundenanalyse einfließt.

### 5. Umfassende Wertungs- & Zeitlogik
Das System unterscheidet zwischen Griffschluss (Completion), Schlüssel (Key/Break) und der eigentlichen Wertung (Score/Bust):

- **Griffschluss / Formation Fertig (`Taste F`)**:
  - Markiert den Moment, an dem alle 4 Springer die Formation vollständig aufgebaut und alle Griffe geschlossen haben.
  - Wenn kein Punkt ausgewählt ist, wird dieser Zeitpunkt für den nächsten anstehenden Punkt vorgemerkt.
- **Key Gegeben (`Taste K`)**:
  - Markiert den Moment, an dem der Key (z.B. Kopfnicken, Bein- oder Griff-Key) zur Auflösung der Formation gegeben wird.
- **Wertung / Count Point (`Taste S` oder `1` für Score, `Taste B` oder `0` für Bust)**:
  - Vergibt den Status **APPROVED (+1)** oder **BUST (0)** und trägt den Punkt final in die Wertungstabelle ein.
  - Wurde zuvor kein separates `F` gedrückt, wird automatisch die aktuelle Videozeit als Fertig-Zeitpunkt übernommen.

#### 📐 Berechnung der Zeiten & Kennzahlen:
| Kennzahl | Berechnungsformel | Bedeutung & Funktion |
| :--- | :--- | :--- |
| **Hold Time (Haltezeit)** | $t_{\text{Key}} - t_{\text{Fertig}}$ | Dauer, die eine Formation sauber gestanden hat, bevor sie aufgelöst wurde. |
| **Transition Time (#1)** | $t_{\text{Fertig}}^{(1)} - t_{\text{Exit}}$ | Zeit vom Verlassen des Flugzeugs bis zum Griffschluss der ersten Formation. |
| **Transition Time (#i > 1)** | $t_{\text{Fertig}}^{(i)} - t_{\text{Key}}^{(i-1)}$ | Zeit vom Schlüssel der vorherigen Formation bis zum Griffschluss der neuen Formation. *(Fallback: $t_{\text{Fertig}}^{(i)} - t_{\text{Fertig}}^{(i-1)}$, falls kein Key gesetzt wurde).* |
| **Working Time Prüfung** | $t_{\text{Fertig}} \le t_{\text{Exit}} + \text{Dauer}$ | Liegt der Griffschluss nach Ablauf der Arbeitszeit (z.B. >35s), wird der Punkt als `SCORE (Out of WT)` markiert und zählt für das offizielle FAI-Ergebnis nicht mit. |

> [!TIP]
> **Transparente Fehlererkennung statt Falschberechnung:**
> Liegt ein gesetzter Key zeitlich *vor* dem Griffschluss oder ein Griffschluss *vor* dem vorherigen Key, wird dies nicht stillschweigend auf `0.00s` korrigiert. Die Tabelle zeigt die negative Differenz mit einem **`⚠️` Warnsymbol in roter Schrift** an. Ein informativer Tooltip erklärt dem Team sofort, wo die Zeitmarke ungenau gesetzt wurde.

### 6. Punkt-Auswahl & Nachträgliche Feinjustierung
Jeder bereits gesetzte Punkt kann jederzeit im Detail nachbearbeitet werden:
1. **Punkt auswählen**:
   - Durch Anklicken des Punktes in der **Zeitleiste** (Timeline-Badge) oder in der **Wertungstabelle**.
   - Das Video springt automatisch zum Griffschluss des Punktes.
   - Über der Tabelle erscheint die **blaue Aktionsleiste** für den ausgewählten Punkt.
2. **Zeiten und Status nachträglich anpassen**:
   - Taste **`F`** oder Klick auf `⏱️ Fertig auf Videozeit setzen`: Aktualisiert den Griffschluss auf die aktuelle Bildposition.
   - Taste **`K`** oder Klick auf `🔑 Key auf Videozeit setzen`: Aktualisiert oder setzt den Key auf die aktuelle Bildposition.
   - Taste **`S`** / **`B`** oder Klick auf `Score/Bust umschalten`: Ändert den Status des gewählten Punktes.
   - Taste **`Escape`** oder Klick auf `✕ Abwählen`: Hebt die Auswahl auf und schaltet zurück in den Modus für neue Wertungen.
3. **Direktes Editieren in der Tabelle**:
   - **Doppelklick** auf Fertig- oder Key-Zellen erlaubt die direkte manuelle Eingabe (unterstützt Formate wie `14.5`, `14.5s`, `00:14.50`).
   - Doppelklick auf die Status-Spalte schaltet direkt zwischen `SCORE` und `BUST` um.
   - Doppelklick auf Notizen erlaubt das Verfassen von Coaching-Kommentaren.
4. **Kontextmenü (Rechtsklick)**:
   - Rechtsklick auf eine Tabellenzeile öffnet ein Schnellmenü mit Aktionen für Fertig-Zeit, Key-Zeit, Statuswechsel, 3D Formation Explorer und Löschen.

### 7. Nachträgliches Anpassen des Draws (`🔄 Draw anwenden`)
Wurde ein Debriefing bereits durchgeführt oder geladen und das Draw nachträglich geändert (z.B. Korrektur eines Tippfehlers in der Sequenz oder Umstellung der Runden):
- Ein Klick auf den Button **`🔄 Draw anwenden`** (neben dem Draw-Eingabefeld) gleicht alle bestehenden Punkte an die neue Draw-Sequenz an.
- **Alle gestoppten Zeiten, gesetzten Keys, Score/Bust-Entscheidungen und geschriebenen Notizen bleiben zu 100% erhalten!**
- Die Sequenz-Badges und die Nächste-Formations-Anzeige aktualisieren sich synchron.

### 8. Interaktive Zeitleiste (Scoring Timeline)
- Optische Darstellung der gesamten Sprungzeit:
  - Schnittbereich (In/Out) in Hellblau
  - Working Time Fenster ab Exit in Grün
  - Gezählte Punkte (Grüne Badges = Approved, Rote Badges = Bust, gedimmte Badges = Out of WT)
  - Key-Zeitpunkte als goldene Diamanten mit Verbindungsbalken zur Formation
  - Farbige Hervorhebung des aktuell ausgewählten Punktes
- Klick- und Zieh-Navigation (Scrubber) mit millimetergenauer Positionierung.

### 9. Telestration Glass Pane Overlay (Video-Zeichenwerkzeuge)
- Zeichnen direkt auf dem pausierten oder laufenden Video:
  - **Cursor-Modus (`Escape`)**: Standard-Mauszeiger
  - **Linie**: Verbindungslinien zwischen Springern
  - **Pfeil**: Bewegungsrichtungen und Drehachsen
  - **Winkel (°)**: 3-Punkt-Winkelmessung mit automatischer Gradanzeige
  - **Freihand**: Beliebige Skizzen
- Undo (`Strg+Z`) und Gesamtlöschen.

### 10. Debrief Analytics & Report-Export
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
| **`F`** | Formation Fertig | Neuer Punkt: Vormerken des Griffschlusses; Bei ausgewähltem Punkt: Fertig-Zeit auf aktuelle Position aktualisieren |
| **`K`** | Key Gegeben | Neuer Punkt: Vormerken des Keys; Bei ausgewähltem Punkt: Key-Zeit auf aktuelle Position aktualisieren |
| **`S`** oder **`1`** | Score (+1) | Neuer Punkt: Formation als Score werten; Bei ausgewähltem Punkt: Status auf Score setzen |
| **`B`** oder **`0`** | Bust (0) | Neuer Punkt: Formation als Bust werten; Bei ausgewähltem Punkt: Status auf Bust setzen |
| **`[`** oder **`I`** | Start Frame (In) | In-Point für Trimmer setzen |
| **`]`** oder **`O`** | End Frame (Out) | Out-Point für Trimmer setzen |
| **`Entf`** / **`Backspace`** | Punkt löschen | Ausgewählten Punkt aus Wertungstabelle entfernen |
| **`Pfeil Oben / Unten`** | Tabelle navigieren | Zeilen wechseln (wählt Punkt aus & Video springt zum Griffschluss) |
| **`Strg + Z`** | Telestration Undo | Letzte Zeichnung rückgängig machen |
| **`Escape`** | Abwählen / Reset | Punkt-Auswahl aufheben (zurück zu neuem Punkt) / Telestration zurück zu Cursor / Textfeld verlassen |
| **`Strg + S`** | Session speichern | Aktuelle Wertung als `.json` speichern |
| **`Strg + O`** | Session laden | Gespeicherte Debrief-Session `.json` öffnen |
| **`Strg + E`** | Report exportieren | Debrief-Report als `.md` Datei exportieren |
| **`F1`** | Hilfe & Guide | Interaktives Hilfefenster mit Wertungsleitfaden und allen Kürzeln öffnen |

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
