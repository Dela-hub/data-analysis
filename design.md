# dela. — Data Visualisation Design Guide

> For agents, developers, and designers building dashboards and data interfaces for dela. clients.

---

## Philosophy

**One question, answered fast.**  
Every dashboard page should answer one primary question before the user scrolls. Lead with a declarative headline (e.g. *"Cooler pricing is in sight."*), then support it with KPIs, then charts, then detail.

**Data earns its place.**  
No filler statistics. No decorative numbers. Every metric shown must be directly actionable for the intended audience. When in doubt, cut it.

**Actuals vs. forecast are always visually distinct.**  
Solid lines for published data. Dashed lines or hatched fills for projections. Never mix them without a legend.

---

## Design Tokens

### Colours

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#07090f` | Page background |
| `--surface` | `#0e1420` | Cards, nav, sidebars |
| `--surface2` | `#141c2e` | Nested surfaces, table headers |
| `--surface3` | `#1a2438` | User chat bubbles, hover states |
| `--border` | `#1e2a40` | Default borders |
| `--border2` | `#253550` | Emphasis borders, focus rings |
| `--amber` | `#f59e0b` | Primary accent, Brent series, CTAs |
| `--amber-dim` | `rgba(245,158,11,0.10)` | Amber tints, badge backgrounds |
| `--blue` | `#60a5fa` | Secondary series (WTI), data highlights |
| `--green` | `#34d399` | Positive delta, spread lines, status |
| `--red` | `#f87171` | Negative delta, alerts |
| `--text` | `#e8edf5` | Primary text |
| `--muted` | `#7b8fae` | Secondary text, axis labels |
| `--subtle` | `#3d4f6a` | Tertiary text, timestamps |

> **Adapt accent colour per data domain:**  
> Oil/Energy → amber `#f59e0b`  
> Finance/Markets → blue `#60a5fa`  
> Environmental/Climate → green `#34d399`  
> Healthcare → violet `#a78bfa`  
> Logistics → orange `#fb923c`  
> Keep `--bg`, `--surface`, `--border` tokens constant across all domains.

### Typography

```css
font-family: 'DM Sans', sans-serif;    /* All UI text */
font-family: 'DM Mono', monospace;     /* All numeric values, data tables */
```

| Role | Size | Weight | Notes |
|---|---|---|---|
| Headline (H1) | 28px | 700 | Dashboard narrative headline |
| Section title (H2) | 15px | 600 | Chart/card headers |
| Sub-label | 13px | 500 | Filter buttons, table cells |
| Axis/meta | 11–12px | 400–600 | Chart axes, badges, timestamps |
| KPI value | 32px | 700 | Letter-spacing: -1px, tabular-nums |
| KPI unit | 16px | 400 | Appended to KPI value |

### Spacing & Radius

| Token | Value |
|---|---|
| Card padding | 20–24px |
| Page gutter | 28px |
| Grid gap (cards) | 12–20px |
| `--radius` | 10px |
| `--radius-lg` | 14–16px |
| Nav height | 56px |

---

## Page Anatomy

### Dashboard Page

```
┌─────────────────────────────────────────────────────┐
│  NAV  — Logo · Page title · Source badge · CTA      │
├─────────────────────────────────────────────────────┤
│  FILTER BAR — Benchmark · Range · Mode toggles      │
├─────────────────────────────────────────────────────┤
│  HEADLINE — Declarative H1 + 1-line context         │
├─────────────────────────────────────────────────────┤
│  KPI STRIP (4 cards) — Latest · Change · Forecast · │
│                         Secondary metric            │
├─────────────────────────────────────────────────────┤
│  MAIN CHART — Full-width timeline (actuals+fcast)   │
├─────────┬───────────────────────────────────────────┤
│ FORWARD │  SPREAD / DIFFERENTIAL                    │
│  BARS   │  or SECONDARY CHART                       │
├─────────┴───────────────────────────────────────────┤
│  FORWARD TABLE — Near-term monthly reference        │
├─────────────────────────────────────────────────────┤
│  PLANNING BRIEF (3 cards) — Actionable takeaways    │
├─────────────────────────────────────────────────────┤
│  FOOTER — Source attribution · Data download links  │
└─────────────────────────────────────────────────────┘
```

### Chat Page

```
┌──────────────┬──────────────────────────────────────┐
│   SIDEBAR    │  TOP BAR — Title · Status · Source   │
│  ─────────── │ ──────────────────────────────────── │
│  Logo/badge  │                                      │
│  Live KPI    │  MESSAGES                            │
│  context     │  (scrollable thread)                 │
│  ─────────── │                                      │
│  Suggested   │                                      │
│  questions   │                                      │
│  ─────────── │ ──────────────────────────────────── │
│  Back link   │  INPUT BAR + hint                    │
└──────────────┴──────────────────────────────────────┘
```

---

## Chart Design Rules

### 1. Always establish a visual hierarchy
- Primary series: `borderWidth: 2.5`, full opacity
- Secondary series: `borderWidth: 2`, slightly reduced opacity
- Forecast: `borderDash: [5, 4]`, same colour as actual series
- Reference lines/fills: muted, never louder than data

### 2. Chart.js configuration baseline

```js
// Grid lines
grid: { color: '#1e2a40', drawTicks: false }

// Ticks
ticks: { color: '#7b8fae', font: { family: 'DM Sans', size: 11 } }

// Tooltip
backgroundColor: '#0e1420'
borderColor: '#253550'
borderWidth: 1
titleColor: '#7b8fae'
bodyColor: '#e8edf5'
padding: 12
```

### 3. Series colour assignments (consistent across all views)

| Series | Colour |
|---|---|
| Primary / Brent | `#f59e0b` (amber) |
| Secondary / WTI | `#60a5fa` (blue) |
| Spread / differential | `#34d399` (green) |
| Forecast overlay | Same as series, dashed |
| Forecast fill | `rgba(series, 0.07)` |

### 4. Forecast zone treatment
- Bridge the last actual point to the first forecast point to avoid visual gaps
- Use `spanGaps: false` on actual datasets so nulls create a clear break
- Label forecast sections with a small "Forecast" tag in the tooltip or legend — never leave it ambiguous

### 5. Bar charts
- Use for discrete forward periods (3-month outlook) — not for continuous series
- `borderRadius: 6`, `borderSkipped: false`
- Set `min` on y-axis to ~85% of lowest value so bars have visible relative height

### 6. Axes
- Never show axis titles — use the chart card header instead
- Y-axis values always prefixed with `$` for monetary series
- X-axis: `maxTicksLimit: 10`, `maxRotation: 0`, `DM Mono` for numbers

---

## KPI Cards

Four-up strip, always first content below the headline. Rules:

1. **Left-most card** gets `highlight` class (full amber top-border accent)
2. **Card structure:** Label (uppercase 11px) → Value (32px DM Mono) → Delta badge → Sub-label
3. **Delta badge:** Green + upward arrow for positive MoM; Red + downward arrow for negative; neutral for spreads
4. **Never put more than 4 KPIs** in the strip — if you need more, use a second row or move to the table

```html
<!-- KPI delta colour logic -->
.kpi-delta.up   { color: #34d399; background: rgba(52,211,153,0.1); }
.kpi-delta.down { color: #f87171; background: rgba(248,113,113,0.1); }
```

---

## Filter Controls

- Group related filters with a `filter-group` (segmented control look)
- Separate groups with a thin `filter-sep` divider
- Active state: amber text + amber-dim background
- Use for: time range, series selection, view mode
- Never more than 2 rows of filters — if the dashboard needs more, use a sidebar/drawer

---

## Planning Brief Cards

Always end the dashboard with 3 actionable planning implications.

- Icon (simple SVG, 16px, amber-dim background)
- Short title (13px, 600 weight)
- 2–3 sentences of prose. Specific, numbered, decision-oriented.
- Never use generic titles like "Key Finding" — be specific: "Procurement timing", "Spread exposure", "Budget pressure-test"

---

## AI Chat Interface Rules

### Data context injection
Every chat session must inject the full data payload as a system context at the top of the first user message. Include:
- All actuals (formatted as a compact table)
- Forecast values and their source
- Computed metrics (MoM change, spreads, averages)
- Audience description and response format guidance

### Response formatting
| Response type | Format |
|---|---|
| Simple factual | 2–3 sentences, inline `$values` in mono |
| Trend analysis | 1 paragraph + data card |
| Comparative | Paragraph + 2-col data card |
| Executive brief | Bullet list (3 points max) |
| Budget/procurement | Prose + specific number ranges |

### Suggested questions
Always provide 5 pre-written questions in the sidebar. They should cover:
1. A causality question (what drove X?)
2. A comparative question (how does X compare to Y?)
3. A spread/differential question
4. A forward-looking / budget question
5. An executive-summary request

### UI behaviour
- Show typing indicator (3-dot bounce) while waiting for AI
- Auto-resize textarea up to 120px
- Disable send button while response is loading
- Never clear the message thread on page reload (use `localStorage` for history persistence if the thread is long)

---

## Adapting to Other Data Domains

When building a dashboard for a different data type, change these elements and keep everything else:

| Element | What to change |
|---|---|
| `--amber` accent | Domain-appropriate colour (see token table above) |
| Headline | Declarative sentence specific to the data's current state |
| KPI metrics | Replace with domain-relevant primary metrics |
| Chart series colours | Update primary/secondary to match new accent |
| Planning brief titles | Replace with domain-relevant action categories |
| AI context block | Replace data tables with domain data |
| Suggested questions | Replace with domain-relevant questions |
| Source attribution | Update footer with correct data source |

### Domain headline templates
- **Equities:** *"Volatility is compressing — range is tightening."*
- **FX:** *"Dollar strength is plateauing against major pairs."*
- **Climate/emissions:** *"Carbon intensity has fallen for three consecutive quarters."*
- **Supply chain:** *"Lead times are normalising — order now."*
- **Healthcare:** *"Admission rates are below seasonal baseline."*

---

## Accessibility & Responsiveness

- Minimum font size: 11px (labels), 13px (body), 28px (KPI values)
- All chart containers: `responsive: true, maintainAspectRatio: true`
- Grid layouts: collapse to 2-col at 900px, 1-col at 600px
- Sidebar: hide below 700px on chat page
- Colour alone is never the only signal — always pair with up/down arrows or dashed/solid line styles
- Scrollbar styling: `width: 5–6px`, thumb `--border2`, always scoped to containers not the page

---

## File Naming Convention

| File | Purpose |
|---|---|
| `Dashboard.html` | Primary data dashboard for a dataset |
| `Chat.html` | AI chat interface for querying the same dataset |
| `design.md` | This file — design system and agent instructions |

For multi-tenant deployments, prefix with the tenant/dataset slug:
`oil-prices/Dashboard.html`, `equities/Dashboard.html`, etc.

---

*Built by dela. · Last updated Apr 2026*

---

## Storytelling with Data — Applied Principles

> Based on Cole Nussbaumer Knaflic's *Storytelling with Data* (Wiley, 2015). These principles are binding for every dashboard and data communication produced by dela.

### The 6 Lessons

| # | Lesson | Applied in dela dashboards |
|---|---|---|
| 1 | Understand the context | WHO + WHAT before any chart |
| 2 | Choose the right visual | Line for trends, bar for discrete, table for lookup |
| 3 | Eliminate clutter | Remove borders, gridlines, legends, trailing zeros |
| 4 | Focus attention | Preattentive attributes: colour, size, position |
| 5 | Think like a designer | Affordances, accessibility, aesthetics, action titles |
| 6 | Tell a story | Setup → conflict → resolution on every page |

---

### Rule 1 — Context before charts (WHO + WHAT + HOW)

Before building any visual, answer these three questions:

- **WHO** is the audience? Be specific — "the procurement team", not "stakeholders"
- **WHAT** do you need them to know or do? This becomes the Big Idea
- **HOW** does the data support that point?

> "Concentrate on the pearls, not all 100 oysters." Show *explanatory* analysis, not *exploratory*.

---

### Rule 2 — The Big Idea (headline formula)

Every dashboard headline must be a **Big Idea** — a single sentence containing:

1. **Your unique point of view** — not neutral description
2. **What's at stake** — why the audience should care
3. **A complete sentence** — no fragment titles

| ❌ Weak | ✅ Strong (Big Idea) |
|---|---|
| "Oil Price Outlook" | "Prices peaked in April — the $20/bbl pullback window opens now." |
| "Q3 Sales Performance" | "Sales missed Q3 target by 12% — we need to approve the new territory plan." |
| "Climate Emissions Report" | "Scope 2 emissions fell 18% — we are on track but must act on logistics." |

---

### Rule 3 — Action titles on every chart

The chart title is prime real estate. State the **so what**, never a description.

| ❌ Descriptive | ✅ Action title |
|---|---|
| "Price timeline — actuals & forecast" | "Brent surged 79% in 8 weeks — EIA forecasts steady decline through July" |
| "3-month forward pricing" | "Every coming month is cheaper — act before the lever disappears" |
| "Brent–WTI spread" | "$15/bbl spread — your benchmark choice carries real cost exposure" |
| "Q3 Revenue by Region" | "APAC is the only region growing — double down or rebalance" |

---

### Rule 4 — Eliminate clutter (checklist)

Run this before publishing any chart:

- [ ] No chart border — use white space to separate from page
- [ ] Gridlines are light grey (`#1e2a40`), `drawTicks: false`
- [ ] No data markers unless a specific point needs calling out
- [ ] No trailing zeros on axis labels (`100` not `100.00`)
- [ ] No rotated x-axis labels — abbreviate instead (`Jan`, `Feb`)
- [ ] No legend if lines/bars can be labeled directly
- [ ] No 3D, no pie charts, no donut charts
- [ ] No secondary y-axis — split vertically or label directly
- [ ] Left-aligned text throughout — no centre alignment
- [ ] White space preserved — never stretch visuals to fill space

---

### Rule 5 — Focus attention with preattentive attributes

Use **one accent colour per insight**. Everything else is grey.

| Attribute | How we use it |
|---|---|
| **Colour** | Accent on the one series that matters; grey for all context data |
| **Size** | KPI values 32px; supporting text 11–13px |
| **Position** | Most important metric top-left; footnotes bottom |
| **Enclosure** | Light shading to separate forecast from actual (Gestalt enclosure) |
| **Connection** | Line charts for temporal data; never disconnected points for trends |
| **Proximity** | Label data directly next to the line/bar — never a distant legend |

> **The hawk rule:** "It's easy to spot a hawk in a sky full of pigeons. As the variety increases, the hawk becomes harder to find." If everything is colourful, nothing stands out.

---

### Rule 6 — Direct labeling over legends

Labels placed directly on or next to data are always better than a legend.

```js
// ❌ Avoid — requires eye travel between legend and data
legend: { display: true }

// ✅ Better — draw labels at end of each line via custom plugin
ctx.fillStyle = '#f59e0b';
ctx.fillText('Brent', lastX, lastY + 4);
```

---

### Rule 7 — Annotate inflection points on the chart

When something important happens in the data, say so in words — directly on the chart.

Key moments to always annotate:
- Peaks and troughs: `"$124 peak"`
- Where the forecast begins: `"FORECAST"` label with zone shading
- External events that explain a trend: `"Prices surged 79% in 8 weeks"`
- The point where action is needed

Use the Gestalt **enclosure principle** for forecast zones:
```js
ctx.fillStyle = 'rgba(255,255,255,0.025)';
ctx.fillRect(fcastX, top, right - fcastX, bottom - top);
ctx.fillText('FORECAST', fcastX + 7, top + 14);
```

---

### Rule 8 — Tell a story: setup → conflict → resolution

Every planning brief and summary section must follow this arc:

| Act | Purpose | Example — Oil dashboard |
|---|---|---|
| **Setup** | What happened? | "Brent rose 98% from Dec 2025 to Apr 2026 — the highest in 28 months." |
| **Conflict** | What's at stake? | "The EIA forecasts a $20/bbl decline — every month you wait costs leverage." |
| **Resolution** | What should they do? | "Budget $108/bbl, move on contracts in May, address the spread differential." |

Never end on conflict without a resolution. Never open with resolution without first establishing the stakes.

---

### Rule 9 — The 3-minute story test

Before publishing, answer: *"If you had 3 minutes to brief a senior stakeholder, what would you say?"*

Write it out. That story becomes:
1. The dashboard **headline** (Big Idea)
2. The **chart action titles**
3. The **planning brief** (3 cards: setup / conflict / resolution)

If you can't write the 3-minute story, the dashboard isn't ready.

---

### Rule 10 — Visuals to use and avoid

| ✅ Use | ❌ Avoid |
|---|---|
| Line chart — time series trends | 3D charts — distorts values |
| Vertical/horizontal bar — discrete comparisons | Pie / donut — angles are hard to compare |
| Horizontal bar — long category names | Secondary y-axis — implies false relationships |
| Heatmap — multi-dimensional tables | Spaghetti chart — >4 lines, unlabelled |
| Simple large text — 1–2 key numbers | Stacked area — middle layers are unreadable |
| Slope chart — before/after comparison | Radar / spider — almost never readable |

---

*SWD principles sourced from: Cole Nussbaumer Knaflic, Storytelling with Data (Wiley, 2015)*
