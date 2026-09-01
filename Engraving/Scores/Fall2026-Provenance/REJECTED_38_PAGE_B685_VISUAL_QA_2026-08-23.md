# Rejected 38-page b685 visual QA - 2026-08-23

## Audited snapshot

- Dorico project at audit dispatch: `FlashlightsInTheDark_Fall2026_PerformerScore_Production.dorico`
- Preserved rejected copy: `FlashlightsInTheDark_Fall2026_PerformerScore_Rejected38PageProof_2026-08-23_201928.dorico`
- Project SHA-256: `b6859f84c97c8c7003a03ca7f60d5cbb417977e6c3d5f241e0c282e7018b70d3`
- Embedded-preview SHA-256: `2a9d996a82f46e5efb7f39d1ef293fa6130b3bb1cc771c03ba44595ff9e1f127`
- Preview metadata: Dorico 5.1.60.2187; generated 2026-08-23 20:19:28 CDT; 38 US Letter portrait pages.
- Method: extracted the saved embedded preview, rendered and inspected all 38 pages at 180 dpi, and re-rendered pages 1, 13-16, 25-26, and 30-38 at 300 dpi. Every page was inspected both as a full page and in ordered spread/contact-sheet context. No live Dorico state or project content was edited during this audit.
- After the rejected proof was preserved, the production file was restored to the earlier 39-page checkpoint, SHA-256 `3ddbd1c386269850f57469e31f48f4726f44d31b7fea8158619b401ded54936e`.

## Result

**Reject - materially worse than the prior 39-page checkpoint.** The proof
retains the mechanical edition-wide improvements: all 38 pages are nonblank
Letter portrait pages; page 1 contains exactly two systems; all six staves are
five-line; the Shadow and Light choruses remain separately bracketed; and
barlines join correctly within each three-staff ensemble.

The isolated m.115-118 page is a real local improvement: the former page-33
lyric/dynamic overprint is removed and the aleatoric instruction is clear.
However, the recast collapses m.93-102 into one ten-measure system on page 25.
That system is categorically unreadable: the chord row becomes a solid block,
lyrics fuse in every ensemble, long extenders and hairpins cross text, and
notation/text collide throughout the Light staves. Page 26 still contains only
m.103, so the attempted change does not repair the `yours / too` physical turn.
The one-page net reduction also reverses later page parity and exposes new
right-page turns at m.124/125, m.134/135, and m.145/146.

The 38-page music proof is not booklet-compatible with the prepared single
colophon: 38 music pages plus the nonblank page-40 colophon would total 39
pages. The prior 39-page music checkpoint plus that colophon totals the intended
40 pages.

## Verified page map

| Page | Measures / systems | Page | Measures / systems |
| ---: | --- | ---: | --- |
| 1 | 1-3 / 4-6 | 20 | 67-70 |
| 2 | 7-8 | 21 | 71-73 |
| 3 | 9-10 | 22 | 74-76 |
| 4 | 11-12 | 23 | 77-80 |
| 5 | 13-14 | 24 | 81-83 / 84-92 |
| 6 | 15-16 | 25 | **93-102, one system** |
| 7 | 17-20 | 26 | 103 |
| 8 | 21-22 | 27 | 104-105 |
| 9 | 23-25 | 28 | 106-107 |
| 10 | 26-31 | 29 | 108-109 |
| 11 | 32-36 | 30 | 110-112 |
| 12 | 37-39 | 31 | 113-114 |
| 13 | 40-42 | 32 | 115-118 |
| 14 | 43-45 | 33 | 119-124 |
| 15 | 46-49 | 34 | 125-129 |
| 16 | 50-52 | 35 | 130-134 |
| 17 | 53-56 | 36 | 135-139 |
| 18 | 57-61 | 37 | 140-145 |
| 19 | 62-66 | 38 | 146-151 |

Page 1 and page 24 are the only two-system pages. Every other page contains one
system, including the overfull page 25.

## Publication blockers

### P0 - page 25, measures 93-102

- The chord sequence beginning with `Fm7`, `Eaug`, and `C/E` is compressed into
  literal glyph-on-glyph overprint. Most identities after the first few symbols
  cannot be read reliably even at 300 dpi.
- Shadow lyrics fuse into forms including `handsto-geth-er`, `car-ryyours`, and
  overlapping `should / hands` lines. Multiple words, extenders, and hairpins
  occupy the same vertical lanes.
- Light lyrics and notation are substantially worse: `hands grow weary`,
  `I'll carry your light`, dynamics, notes, tuplets, and extenders collide across
  the lower half of the system. Several strings read as composite words rather
  than distinguishable lyric lanes.
- This is not a local nudge problem. The ten-measure system must be split back
  into the earlier m.93-96, m.97-98, and m.99-102 systems before object cleanup.

### P0 - page 1, measures 1-6

- The title, boxed rehearsal mark 2, commission line, `Moderato`, and opening
  direction band still collide. Mark 2 remains inside the credit band and
  `Moderato` crosses the commission line.
- First-system lyrics and dynamics overlap notation in Alto S, both Light upper
  staves, and Tenor/Bass L. `Here`, `awake`, and `with` cross note/staff regions.
- The second system retains duplicate/overprinted Baritone S `-no light`, the
  nearby `f`, isolated parenthesis fragments, and multiple lyric/staff clashes.
- Required furniture is present, and the page correctly retains two systems,
  but it is still not performer-ready.

### P0 - right-page lyric/phrase turns

- Pages 13-14, m.42/43: `au- / -tumn` remains a literal mid-word turn.
- Pages 15-16, m.49/50: `pre- / -ceding` remains a literal mid-word turn.
- Pages 25-26, m.102/103: page 25 ends on `yours` or `your light`; orphan page
  26 completes `too`. The intended phrase remains divided at a physical turn.
- Pages 33-34, m.124/125: all lyric-bearing groups end page 33 on `Who`; page 34
  continues `are we?` and `Warm hearts light`. The recast creates a new exposed
  mid-question turn.
- Pages 35-36, m.134/135: the continuing `Night / Light` texture has no shared
  rest. This is a newly exposed turn requiring a performer test at minimum.
- Pages 37-38, m.145/146: all six staves continue the final `night / light` and
  `Hmm.` texture into m.146 with no shared turn window. This is a new unsafe
  final-section turn.

### P1 - page 30, measures 110-112

`Cmaj9/E` and `subito` remain fused as `Cmaj9/Esubito` above Soprano S. The
nearby `mp` is separate, but the chord and direction remain visually ambiguous.

## Late-section gain at pages 31-32

- Page 31 now contains only m.113-114. The upper Baritone S `night` lanes,
  Light `subito mp` objects, and long continuation rules are separated and
  readable, albeit extremely sparse.
- Page 32 contains only m.115-118. Boxed 115, the singular `rearticulate freely
  in aleatoric style` instruction, Shadow `pp`/`Who?`, two Baritone S lyric
  lanes, and the Light `Who are we? / Warm hearts` material are all visibly
  separated at 300 dpi. The former severe page-33 overprint is resolved by the
  split.
- The m.114/115 right-page turn is at a clearly marked sectional restart and is
  much better than an all-six tied turn, but it does not compensate for the
  catastrophic page 25 and the later parity regressions.

## Other retained cleanup issues

- Page 2 repeats `listen for primer tone` independently over all three Light
  staves instead of presenting an unambiguous ensemble-level instruction.
- Pages 3, 13-16, and several later systems retain isolated parentheses,
  system-start fragments, conspicuously long continuation rules, or unlabeled
  multi-voice lyric lanes.
- Page 17's `reversed-impact sound event` remains close to the right margin but
  is not clipped.
- No blank page, cropped system, missing staff, one-line staff, or system-on-
  system vertical collision was found outside the page-25 internal overprint.

## Comparison with the prior 39-page checkpoint

| Area | Prior 39-page checkpoint | Rejected b685 proof | Verdict |
| --- | --- | --- | --- |
| m.93-102 | Three separate systems over pages 25-27; chord spacing tight but decipherable | One ten-measure system on page 25 with pervasive literal collisions | **Much worse** |
| m.102/103 turn | `yours / too` split after right page 27 | Same phrase split after right page 25 | **No musical gain** |
| m.113-118 | Two systems on one page with severe local overprint | Separate pages 31 and 32; locally readable | **Better** |
| m.119-151 parity | Stable facing-page continuations | New physical turns after m.124, m.134, and m.145 | **Worse** |
| Page 1 | Severe furniture/lyric collisions | Unchanged | **No gain** |
| Booklet total with colophon | 39 + 1 = 40 | 38 + 1 = 39 | **Worse / fail** |

The b685 state should remain rejected. The restored 39-page `3ddbd1c...`
checkpoint is the safer production baseline. If the clean m.115 split is
reintroduced, it must be offset with a safe page elsewhere while preserving
separate systems through m.93-102 and rechecking every later right-page turn.

## Safest next casting experiment

From the restored 39-page checkpoint, the most promising proof-only experiment
is to make m.115 a frame break while converting the m.113 frame break to a
system break. The intended local map would be:

- page 32: m.110-112 / m.113-114 as two sparse systems;
- page 33: m.115-118 as one system;
- page 34 onward: unchanged from the restored checkpoint.

This would keep the all-six m.112/113 `night` continuation on one page, isolate
the collision-heavy m.115 system, preserve the 39-music-page / 40-page-with-
colophon total, and avoid changing later page parity. It is only a candidate:
the m.110-114 two-system page must be exported and checked at 100 percent before
acceptance. Pairing earlier systems such as m.104-105 / m.106-107 would be a
worse offset because it would move m.110-112 onto a right page and recreate the
critical m.112/113 physical turn.
