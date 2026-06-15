# TechConnect 2026 Campaign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the four TechConnect 2026 campaign deliverables (invitation, Instagram image, Instagram caption, documentation PPTX) in Direction C "Connect", event-first framing, confident tone.

**Architecture:** Hand-authored SVG (1080×1080) → PNG for the Instagram image; markdown for invitation + caption; pptx skill assembles the documentation deck embedding all of the above. All facts trace to spec §2 (single source of truth).

**Tech Stack:** SVG, a PNG renderer (rsvg-convert / Inkscape / headless Chrome / resvg — whichever is available), python-pptx (via the pptx skill), markdown.

**Spec:** `docs/superpowers/specs/2026-06-15-techconnect-2026-campaign-design.md`

**Output dir:** `D:\2025-2026\semester 1\AI_Concepts\EVENT_CAMPAIGN_TechConnect\`

**Verification model:** No unit tests (design artifacts). Each task verifies by (a) **fact-check** every event detail against spec §2, and (b) where visual, a **thumbnail-legibility check** — render small and confirm wordmark + date + venue readable.

---

### Task 0: Scaffold output folder + brand constants

**Files:**
- Create: `EVENT_CAMPAIGN_TechConnect/` (output dir)
- Create: `EVENT_CAMPAIGN_TechConnect/brand.md` (palette/type reference, copied from spec §4)

- [ ] **Step 1: Create the output directory**

Bash:
```bash
mkdir -p "/d/2025-2026/semester 1/AI_Concepts/EVENT_CAMPAIGN_TechConnect"
```

- [ ] **Step 2: Write `brand.md`** with the Direction C tokens verbatim from spec §4:

```markdown
# TechConnect 2026 — Brand tokens (Direction C "Connect")
Gradient: #ff5a3c → #e0186b → #6a1fb0   (Howest red #e22a18 = warm anchor)
Text-on-gradient: #f7f4ef   Dark panel: #0a0b0d
Glass: bg #ffffff22, border 1px #ffffff55, blur
Type: Inter — display 800 (-1.5px tracking), label 600 uppercase +tracking, body 500
Wordmark: TECH CONNECT 2026 (2026 lower-emphasis)
Tagline: "Where ideas plug in."
```

- [ ] **Step 3: Confirm renderer availability** (decides PNG export path for Task 2)

Bash:
```bash
command -v rsvg-convert inkscape resvg 2>/dev/null; (command -v chrome || command -v chromium || command -v msedge) 2>/dev/null; echo "---done---"
```
Expected: at least one path printed. If none, plan Task 2 Step 4 uses the visualize widget screenshot or Python `cairosvg`. Record which renderer exists.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: scaffold TechConnect campaign output + brand tokens"
```

---

### Task 1: Invitation copy (D1)

**Files:**
- Create: `EVENT_CAMPAIGN_TechConnect/Invitation.md`

- [ ] **Step 1: Draft the invitation** — confident & inspiring, event-first. Structure mirrors prev campaign's invitation but for TechConnect. Required blocks: title line, hook, what-it-is, what-you'll-see (talks + Project One showcase + Young Talent Awards + networking), full logistics, CTA, sign-off. Use only facts from spec §2. Draft:

```markdown
# You're Invited — TechConnect 2026

**TechConnect 2026 · Talks & Showcase**
**Date:** Wednesday, 24 June 2026 · 16:30 – 20:00
**Location:** The Core, Campus Kortrijk Weide, Sint-Martens-Latemlaan 2B, 8500 Kortrijk

Join us at Howest Kortrijk for one evening where ideas plug in. TechConnect 2026 brings **students, alumni and professionals** together for an electric night of **student project demos, short tech talks, and networking** — the place to see what the next generation of technology creators is building.

Walk the **Project One showcase** and meet the makers behind real working prototypes — from AI vision systems that help rescuers **find missing people**, to IoT, web, and energy-transition projects straight off the workbench. Catch **eight 20-minute Tech Talks** on autonomous drone swarms, large language models, AI-native web apps, vehicle-to-grid, IoT security and digital twins. Cheer the **Young Talent Awards**. Then stay for drinks and conversation.

This isn't a lecture. It's a room full of things that work — and the people who built them.

**Free admission · pre-registration recommended.** Free parking at Parking 4, Graaf Karel de Goedelaan.

**Be there. See what students built.**
```

- [ ] **Step 2: Fact-check** every bold logistic line against spec §2 (date, time, venue, address, free, parking, program items). Fix mismatches.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "content: TechConnect invitation copy"
```

---

### Task 2: Instagram post image (D2)

**Files:**
- Create: `EVENT_CAMPAIGN_TechConnect/Instagram_Post.svg`
- Create: `EVENT_CAMPAIGN_TechConnect/Instagram_Post.png`

- [ ] **Step 1: Author the SVG** — `viewBox="0 0 1080 1080"`, Direction C. Required elements (from spec §5 D2): gradient mesh (#ff5a3c→#e0186b→#6a1fb0), dot-grid texture, white network-node motif, wordmark "TECH CONNECT 2026" (800, tight tracking), tagline "Where ideas plug in.", glass info pill containing `WED 24 JUN · 16:30 · THE CORE, KORTRIJK · FREE`, small "HOWEST" mark, embedded Inter via `@font-face` or system fallback. Build the gradient with `<radialGradient>`/`<linearGradient>`, glass pill as `<rect rx>` with low-opacity white fill + stroke. Keep wordmark in the upper-mid, pill lower third.

- [ ] **Step 2: Visual self-check in the browser companion** — write the SVG into the companion `content/` dir as `ig-preview.html` (wrap SVG in a centered 380px box to simulate feed thumbnail), confirm wordmark + date + venue legible at small size. Iterate SVG if cramped.

- [ ] **Step 3: Render to PNG** at 1080×1080 using the renderer found in Task 0 Step 3. Examples:

```bash
# rsvg-convert
rsvg-convert -w 1080 -h 1080 "Instagram_Post.svg" -o "Instagram_Post.png"
# OR inkscape
inkscape "Instagram_Post.svg" --export-type=png -w 1080 -h 1080 -o "Instagram_Post.png"
# OR python cairosvg
python -c "import cairosvg;cairosvg.svg2png(url='Instagram_Post.svg',write_to='Instagram_Post.png',output_width=1080,output_height=1080)"
```
Expected: `Instagram_Post.png` exists, 1080×1080.

- [ ] **Step 4: Verify PNG dimensions + legibility**

Bash:
```bash
python -c "from PIL import Image;i=Image.open('Instagram_Post.png');print(i.size)"
```
Expected: `(1080, 1080)`. Open the PNG, confirm all spec §5-D2 elements present and readable.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "design: TechConnect Instagram post image (Direction C)"
```

---

### Task 3: Instagram caption (D3)

**Files:**
- Create: `EVENT_CAMPAIGN_TechConnect/Instagram_Caption.md`

- [ ] **Step 1: Write the caption** — paste-ready, event-first, confident. Blocks per spec §5-D3: scroll-stopping line 1, 2–3 body lines, CTA, event line, hashtag block. Draft:

```markdown
⚡ One evening. Every idea, plugged in.

TechConnect 2026 is where Howest students, alumni & pros collide — live project demos, 8 short tech talks, the Young Talent Awards, and real networking. Come see what students actually built: AI that finds missing people, drone swarms, IoT, AI-native web & more. 🔌

🎟️ Free entry — pre-register now (link in bio).
📅 Wed 24 June · 16:30–20:00
📍 The Core, Campus Kortrijk Weide, Kortrijk

#TechConnect2026 #Howest #ProjectOne #CreativeTechnologiesAI #Kortrijk #StudentProjects #AI #IoT #TechTalks #Innovation
```

- [ ] **Step 2: Fact-check** date/time/venue/free against spec §2; confirm ≤ 2200 chars and hashtag count ≤ 30. Fix.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "content: TechConnect Instagram caption"
```

---

### Task 4: Documentation deck (D4)

**Files:**
- Create: `EVENT_CAMPAIGN_TechConnect/EVENT_CAMPAIGN_TechConnect_Documentation.pptx`

- [ ] **Step 1: Invoke the pptx skill** to build the deck. Provide it the brand tokens (Task 0 brand.md), the invitation (Task 1), caption (Task 3), and the PNG (Task 2) for embedding.

- [ ] **Step 2: Build 9 slides** per spec §5-D4 with an on-brand master (gradient title slide, clean light content slides, Howest-red accents, Inter):
  1. Title: "TechConnect 2026 — AI-Generated Campaign", author Vladyslav Drahan, AI Concepts.
  2. The Event — facts table from spec §2.
  3. Audience & Goal.
  4. Strategy — event-first; Project One as backdrop/proof; why.
  5. Brand & Art Direction — show all 3 explored directions (A Signal / B Editorial / C Connect) + why C won; palette + type.
  6. The Invitation — D1 rendered.
  7. The Instagram Post — embed `Instagram_Post.png` in a phone frame + the caption text.
  8. AI Tools & Process — per spec §7.
  9. Close / CTA — "Be there. 24 June."

- [ ] **Step 3: Verify** the .pptx opens, has 9 slides, the PNG is embedded (not broken-linked), and every fact matches spec §2.

Bash:
```bash
python -c "from pptx import Presentation;p=Presentation('EVENT_CAMPAIGN_TechConnect/EVENT_CAMPAIGN_TechConnect_Documentation.pptx');print('slides:',len(p.slides.__iter__.__self__._sldIdLst))" 2>/dev/null || echo "open manually to verify"
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "docs: TechConnect campaign documentation deck"
```

---

### Task 5: Final review + submission bundle

**Files:**
- Modify: `EVENT_CAMPAIGN_TechConnect/` (verify completeness)

- [ ] **Step 1: Confirm all four deliverables present:** Invitation.md, Instagram_Post.png (+ .svg), Instagram_Caption.md, *_Documentation.pptx.

- [ ] **Step 2: Cross-deliverable fact consistency** — date/time/venue/free identical across all four. The single most common failure mode; check explicitly.

- [ ] **Step 3: Tone pass** — invitation + caption both confident & inspiring, no generic-flyer phrasing.

- [ ] **Step 4: Stop the brainstorm companion server** (cleanup):

```bash
bash "C:\Users\vladd\.claude\plugins\cache\superpowers-dev\superpowers\5.1.0\skills\brainstorming\scripts/stop-server.sh" "D:\Project One\2025-26-projectone-ctai-VladyslavDrahan\.superpowers\brainstorm\1857-1781502879"
```

- [ ] **Step 5: Final commit**

```bash
git add -A && git commit -m "feat: complete TechConnect 2026 campaign deliverables"
```

---

## Self-Review (done at write time)

**Spec coverage:** D1→Task1, D2→Task2, D3→Task3, D4→Task4, brand §4→Task0, AI-tools §7→Task4 slide 8, cross-fact consistency §6→Task5. All spec sections mapped.

**Placeholder scan:** Copy drafts are real (not "TODO"); renderer command has 3 concrete fallbacks; pptx slide list concrete. No TBDs.

**Consistency:** Palette hex values identical across Task0/Task2/Task4. Event facts sourced from spec §2 everywhere. Filenames match spec §5.
