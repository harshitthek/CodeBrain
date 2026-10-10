# CodeBrain — Archival Dot-Matrix Technical Datasheet Design System

> Tactile industrial drafting sheet with 5×7 circular pin-matrix display typography, hairline rules, right-margin schematic circuit trace, and surgical vermilion accents.

**Theme:** Light Archival Blueprint (`#F2F0EC`)

---

## 1. Design Philosophy

CodeBrain's interface rejects dark-mode neon gradients, glassmorphic blur cards, and decorative SaaS chrome in favor of an **Archival Technical Datasheet**:

1. **Physical Paper & Carbon Ink**: The entire surface is warm archival stone paper (`#F2F0EC`) paired with deep carbon ink (`#262523`) and exposed `1px` structural drafting rules.
2. **True 5×7 Circular Dot-Matrix Display Typography**: Primary headings and subsystem identifiers are rendered on a physical 5×7 circular dot-matrix grid (`<DotMatrixText />`). Lit pins render in solid carbon (`#262523`) or signal vermilion (`#D95338`), while unlit pins remain visible as a faint underlying dot bed (`#DFDCD4`).
3. **Tabular Monospace Discipline**: All metadata, coordinates, file paths, rubric telemetry, and prose use `IBM Plex Mono` with `tabular-nums` and `slashed-zero`.
4. **Right-Margin Schematic Trace**: A continuous `1px` vertical drafting line runs along the right margin from the top crosshair datum (`(×)`) through hollow section station rings (`○`) to the bottom bullseye termination node (`◉`).

---

## 2. Color Tokens

| Token | Hex | Role |
|---|---|---|
| `--bg-sheet` | `#F2F0EC` | Primary archival drafting paper surface |
| `--bg-well` | `#EAE7E0` | Recessed input well and code inspection surface |
| `--bg-cell-hover` | `#ECE9E2` | Subtle row hover state |
| `--ink-primary` | `#262523` | Primary carbon ink for lit matrix dots, heavy rules, and primary text |
| `--ink-secondary` | `#57554F` | Technical body copy and specification descriptions |
| `--ink-muted` | `#87847C` | Column headers (`NO.`, `MODULE`, `ORIGIN`), sheet indices, and timestamps |
| `--ink-ghost-dot` | `#DFDCD4` | Unlit circular dots in the 5×7 character matrix bed |
| `--rule-heavy` | `#262523` | Major section boundary rules (`1.5px` / `1px` solid carbon) |
| `--rule-hairline` | `#D5D2C9` | Row dividers and internal tabular grid lines (`1px` solid) |
| `--signal-vermilion` | `#D95338` | Surgical technical accent for active prompts (`08`, `?`), SSRF blocks, and primary triggers |
| `--signal-forest` | `#2A6F4E` | Verified convergence and passing assertion state |

---

## 3. Typography & Hierarchy

| Role | Typeface | Scale | Tracking | Notes |
|---|---|---|---|---|
| **Sheet Metadata** | `IBM Plex Mono` | `11px`–`12px` | `0.16em` uppercase | Used for `CODEBRAIN / OPEN SOURCE`, `SHEET 01 / 05`, and table column headers |
| **Dot-Matrix Hero** | `DotMatrixText` (5×7 SVG grid) | `28px`–`44px` cell height | 1-dot inter-char gap | Circular dots (`r=2.1` lit, `r=1.25` unlit ghost grid) |
| **Dot-Matrix Row Label** | `DotMatrixText` (5×7 SVG grid) | `24px`–`34px` cell height | Padded to fixed column bed | Matches the `LINUX` / `PYTHON` / `YOURS ?` row specimen format |
| **Technical Body & Code** | `IBM Plex Mono` | `12px`–`14px` | `0.01em` | `font-variant-numeric: tabular-nums slashed-zero` |

---

## 4. Layout & Structural Rules

- **Zero Rounded Pills or Cards**: All interactive controls, inputs, and tabular cells use crisp `0px` corners and `1px` structural borders.
- **Exposed Grid Hairlines**: Content is organized into numbered horizontal ledger rows (`01`–`08`) and split specification sheets separated by full-width `1px` rules.
- **No AI-Slop Patterns**: No glowing gradients, no floating chatbots, no fake macOS window dots, and no generic marketing copy. Every label maps directly to a Python module or test invariant in the CodeBrain repository.
