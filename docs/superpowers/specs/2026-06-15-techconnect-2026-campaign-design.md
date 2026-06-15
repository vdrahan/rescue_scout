# TechConnect 2026 — AI-Generated Campaign — Design Spec

**Date:** 2026-06-15
**Author:** Vladyslav Drahan
**Course:** AI Concepts (CTAI, Howest)
**Assignment:** AI-Generated Campaign — invite people to TechConnect 2026 and showcase Project One student work.

---

## 1. Goal

Produce a phenomenal, majestic, modern marketing campaign that **invites people to TechConnect 2026** and uses **Project One student work** as proof/backdrop. Build on the earlier AI Concepts campaign work (the fictional "IRON WILL" event), but retarget it to the real student-project fair.

**Success criteria**
- Materials clearly communicate the event: what, when, where, why come.
- Visuals are bold, premium, and scroll-stopping (Direction C "Connect").
- Copy is confident and inspiring.
- Project One is present as the substance behind the event (the SAR car as a concrete example, the broader fair as the offer).
- All deliverables submittable for the assignment: invitation + social-media material, plus a documentation deck.

---

## 2. Event facts (single source of truth)

Locked into every material verbatim where it matters.

| Field | Value |
|-------|-------|
| **Event** | TechConnect 2026 — Talks & Showcase |
| **Tagline** | *"Where ideas plug in."* |
| **Host** | Howest, Campus Kortrijk Weide |
| **Date** | Wednesday, 24 June 2026 |
| **Time** | 16:30 – 20:00 |
| **Location** | The Core, Campus Kortrijk Weide, Sint-Martens-Latemlaan 2B, 8500 Kortrijk |
| **Cost** | Free admission; pre-registration recommended |
| **Parking** | Free at Parking 4, Graaf Karel de Goedelaan |
| **For** | Students, alumni, professionals |
| **Reference** | https://www.howest.be/nl/nieuws/tech-connect-2026-talks-showcase |

**Program highlights**
- Student project demonstrations + research lab discovery (16:30–19:00)
- 8 short Tech Talks, 20 min each, offered twice (17:00–19:30): autonomous drone swarms, AI-native web apps, LLMs, vehicle-to-grid, web transitions, IoT security, digital twins, practical AI.
- Brainstorm workshop: Education & AI (16:30–18:00)
- Young Talent Awards (17:00–18:00)
- Refreshments + networking (16:30–20:00)

**Programs & labs showcased:** Graduaat IoT; Graduaat Web Development & Design; Bachelor Multimedia & Creative Technology; **Bachelor Creative Technologies & AI**; Banaba Sustainable Energy Management; AI Lab, Energy Lab, HIT Lab.

**Hero Project One example (the author's):** RC CAR Search-and-Rescue system — YOLOv26 vision model detecting people in 5 poses (lying, standing, sitting, crawling, partially hidden), Raspberry Pi + Gradio ground-station dashboard, for emergency & rescue services. Story hook: *"AI that finds the missing."*

---

## 3. Strategic decisions (from brainstorming)

| Decision | Choice |
|----------|--------|
| Content framing | **Event-first** — sell the evening; student projects (incl. SAR car) are backdrop/proof. |
| Brand | **Hybrid** — Howest red `#e22a18` as anchor accent inside an original premium art system. |
| Art direction | **C "Connect"** — vibrant red→magenta→violet gradient mesh, network-node motif, glassmorphism info pill, large Inter type. |
| Tone | **Confident & inspiring** — energetic, lightly cinematic. |
| Output location | `D:\2025-2026\semester 1\AI_Concepts\EVENT_CAMPAIGN_TechConnect\` |

---

## 4. Brand system (Direction C "Connect")

- **Gradient:** radial/linear blend `#ff5a3c` (warm red) → `#e0186b` (magenta) → `#6a1fb0` (violet). Howest red `#e22a18` appears as the warm anchor.
- **Neutrals:** off-white `#f7f4ef` for text-on-gradient; near-black `#0a0b0d` for any dark panels.
- **Motif:** thin white network nodes/edges (literal "connect") + subtle dot grid texture.
- **Glass element:** translucent white pill / card (`#ffffff22`, 1px `#ffffff55` border, blur) for event essentials.
- **Type:** Inter. Display 800 weight, tight letter-spacing (-1 to -1.5px) for the wordmark; 600 for labels (uppercase, +letterspacing); 500 for body.
- **Wordmark:** "TECH CONNECT 2026" stacked, with "2026" lower-emphasis.

---

## 5. Deliverables

### D1 — Invitation (text)
Formal written invitation, styled, mirroring the structure of the previous campaign's `Invitation.png` but for TechConnect. Confident & inspiring tone. Contains: greeting/hook, what the event is, what attendees will see (talks, Project One showcase, awards, networking), full date/time/location/cost, pre-register CTA, sign-off. Saved as `Invitation.md` and rendered into a deck slide.

### D2 — Instagram post image (1080×1080)
Direction C, generated as **SVG → exported PNG**. Square. Carries: wordmark, tagline, date `24 JUN`, time `16:30`, venue `THE CORE · KORTRIJK`, `FREE` + pre-register note, Howest mark, network-node motif, glass info pill. Must be legible at thumbnail size. File: `Instagram_Post.png` (+ source `.svg`).

### D3 — Instagram post (caption)
Paste-ready caption: scroll-stopping first line, 2–3 short lines of body (event-first, Project One as the draw), CTA (pre-register), event line (date/time/place/free), hashtag block (mix of #Howest #TechConnect2026 #ProjectOne #CreativeTechnologiesAI #Kortrijk + topical tags). File: `Instagram_Caption.md`.

### D4 — Documentation deck (PPTX)
Campaign write-up built with the pptx skill. On-brand master (gradient title, clean content slides). Slides:
1. Title — TechConnect 2026 campaign, author.
2. The event — context + facts (from §2).
3. Audience & goal.
4. Strategy — event-first framing, why Project One as backdrop.
5. Brand & art direction — Direction C, palette, type, motif (with the 3 explored directions + why C).
6. The invitation — D1 rendered.
7. The Instagram post — D2 image + D3 caption mocked in a phone frame.
8. AI tools used + process.
9. Close / call to action.

File: `EVENT_CAMPAIGN_TechConnect_Documentation.pptx`.

---

## 6. Production plan

1. Build the IG image as a hand-authored SVG (1080×1080) in Direction C; render to PNG.
2. Write D1 invitation + D3 caption as markdown/text.
3. Build D4 deck via the pptx skill, embedding the PNG and rendering invitation/caption on-brand.
4. Save all four into `EVENT_CAMPAIGN_TechConnect/`.
5. Self-check legibility (thumbnail test on IG image), fact accuracy against §2, tone consistency.

**Out of scope (YAGNI):** printed poster, video/reel, multi-platform variants (LinkedIn/X), animated assets. Can be added later if wanted.

---

## 7. AI tools narrative (for the deck)

Document honestly which generative-AI tools shaped the campaign: ideation/strategy and copy via Claude (Claude Code), visual art direction explored and authored as code-generated SVG, layout/deck assembly automated. This satisfies the "use generative AI tools" requirement and is itself a talking point.
