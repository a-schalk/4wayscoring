# 📚 4-Way Knowledge Base & Reference Hub

This document aggregates FAI 4-Way Formation Skydiving competition rules, terminology, timing logic, and references for developers and agents.

---

## 1. Quick Reference: FAI 4-Way Dive Pool

The official FAI / ISC 4-Way Open (AAA) dive pool consists of **16 Randoms** and **22 Blocks**:

### 🎯 Randoms (A through Q, excluding J) — 1 Point Each
| Code | Name | Code | Name |
| :---: | :--- | :---: | :--- |
| **A** | Unipod | **I** | Satellite |
| **B** | Stairstep Diamond | **K** | Hook |
| **C** | Murphy Flake | **L** | Adder |
| **D** | Yuan | **M** | Star |
| **E** | Meeker | **N** | Crank |
| **F** | Open Accordion | **O** | Satellite |
| **G** | Cataccord | **P** | Sidebody |
| **H** | Bow | **Q** | Phalanx |

### 🧱 Blocks (1 through 22) — 2 Points Each (Initial + Closing)
| Block | Initial Formation | Closing Formation | Points |
| :---: | :--- | :--- | :---: |
| **1** | Molar | Molar | 2 (`1-1`, `1-2`) |
| **2** | Sidebody Donut | Sideflake Donut | 2 (`2-1`, `2-2`) |
| **3** | Sideflake Opal | Turf | 2 (`3-1`, `3-2`) |
| **4** | Monopod | Monopod | 2 (`4-1`, `4-2`) |
| **5** | Opal | Opal | 2 (`5-1`, `5-2`) |
| **6** | Stardian | Stardian | 2 (`6-1`, `6-2`) |
| **7** | Sidebuddies | Sidebuddies | 2 (`7-1`, `7-2`) |
| **8** | Canadian Tee | Canadian Tee | 2 (`8-1`, `8-2`) |
| **9** | Cat + Accordion | Cat + Accordion | 2 (`9-1`, `9-2`) |
| **10** | Diamond | Bunyip | 2 (`10-1`, `10-2`) |
| **11** | Photon | Photon | 2 (`11-1`, `11-2`) |
| **12** | Bundy | Bundy | 2 (`12-1`, `12-2`) |
| **13** | Mixed Accordion | Mixed Accordion | 2 (`13-1`, `13-2`) |
| **14** | Bipole | Bipole | 2 (`14-1`, `14-2`) |
| **15** | Caterpillar | Caterpillar | 2 (`15-1`, `15-2`) |
| **16** | Compressed Accordion | Box | 2 (`16-1`, `16-2`) |
| **17** | Danish Tee | Murphy | 2 (`17-1`, `17-2`) |
| **18** | Zircon | Zircon | 2 (`18-1`, `18-2`) |
| **19** | Ritz | Ice Pick | 2 (`19-1`, `19-2`) |
| **20** | Piver | Viper | 2 (`20-1`, `20-2`) |
| **21** | Zig Zag | Marquis | 2 (`21-1`, `21-2`) |
| **22** | Tee | Chinese Tee | 2 (`22-1`, `22-2`) |

---

## 2. FAI AAA Draw Generation Rules

When generating a competition draw (10 rounds):
1. **Target Points per Round**: Each round consists of 5 to 6 points (maximum 6 points).
2. **Composition**:
   - A round is built by randomly drawing formations until the point total reaches 5 or 6 points.
   - If drawing a Block (2 points) would make the round 7 points, that block cannot be added to that round.
3. **Pool Depletion & Repetition**:
   - In a 10-round competition, all 22 blocks and 16 randoms are drawn before any formation can be repeated.
   - Once all blocks or all randoms are used, that pool is refilled.

---

## 3. Timing & Judging Rules

1. **Working Time**:
   - **35.0 seconds** in competition.
   - Begins the exact frame the first performer breaks contact with the aircraft (Exit).
   - Any formation whose completion ($t_{\text{complete}}$) occurs after $t_{\text{exit}} + \text{duration}$ is out of working time.
2. **Hold Time**:
   - Time between formation completion and key: $t_{\text{key}} - t_{\text{complete}}$.
   - Must be positive; negative indicates key was marked before full grip completion.
3. **Transition Time**:
   - Point 1: $t_{\text{complete}}^{(1)} - t_{\text{exit}}$
   - Point $i > 1$: $t_{\text{complete}}^{(i)} - t_{\text{key}}^{(i-1)}$
4. **Bust Conditions**:
   - Incomplete grip, grip on wrong body part, early grip before complete inter-separation, or grip not visible to videographer.

---

## 4. Reference Files & External Literature

- **[`docs/4way_knowledge_base.md`](./4way_knowledge_base.md)**: Master training manual covering flight mechanics, creeping, head switching, slots, and debriefing methodologies.
- **[`docs/pdf/4way-Blocks-Only.pdf`](./pdf/4way-Blocks-Only.pdf)**: Visual diagrams of all 22 FAI blocks.
- **[`docs/pdf/4way-Randoms-Only.pdf`](./pdf/4way-Randoms-Only.pdf)**: Visual diagrams of all 16 FAI randoms.
- **[`docs/pdf/AlternateEngineering.pdf`](./pdf/AlternateEngineering.pdf)**: Advanced engineering guide for block inter techniques.
- **[`assets/4wayCheatSheet.svg`](../assets/4wayCheatSheet.svg)**: Vector diagram cheat sheet of all formations.
