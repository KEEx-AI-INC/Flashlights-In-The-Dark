# Production 40-page 2ebc visual QA - 2026-08-23

## Audited snapshot

- Dorico project: `FlashlightsInTheDark_Fall2026_PerformerScore_Production.dorico`
- Project SHA-256: `2ebc556097ed908e613e8462cb92647d2ad18eb7c2800279ccbea84af3047d5a`
- Embedded-preview SHA-256: `0d7237d237af48886d90fd86f4ea0d8c8d831bdf426819e97fb058654d451d49`
- Preview metadata: Dorico 5.1.60.2187; generated 2026-08-23 20:34:54 CDT; 40 US Letter portrait pages.
- Comparison baseline: restored 39-page Production checkpoint, project SHA-256 `3ddbd1c386269850f57469e31f48f4726f44d31b7fea8158619b401ded54936e`.
- Method: extracted the saved embedded preview, rendered and inspected all 40 pages at 180 dpi, re-rendered pages 25-40 at 300 dpi, reviewed every odd/even spread boundary, and pixel-compared pages 1-32 against the 3dd proof. Pages 1-32 are pixel-identical to 3dd. No live Dorico state or project content was edited during this audit.

## Result

**Fail as the final performer cast, despite a major local improvement.** The
new proof safely restores the m.93-102 region and cleanly isolates m.115-118.
Pages 25-32 are pixel-identical to the good 39-page checkpoint: the catastrophic
ten-measure system from the rejected b685 proof is gone, and the m.93-96,
m.97-98, and m.99-102 systems are again separate and readable.

The isolated page 34 is successful on its own terms. Boxed 115, the aleatoric
instruction, dynamics, two Baritone S lyric lanes, and all Light lyric lanes
are separated and readable. Page 33's m.113-114 system is also clean. This
fully removes the prior severe page-33 overprint.

The new page parity is not acceptable without another cast adjustment. It
creates a serious right-page turn at pages 35-36 (`Who / are we?`), an exposed
continuous-texture turn at pages 37-38, and a final-texture turn at pages 39-40.
The last of these has a full-bar sustained-note window and may be workable after
an actual print test; the first is a clear performer-score blocker.

The music-only PDF is now 40 pages and therefore divisible by four. It cannot,
however, be combined with the prepared one-page colophon without producing a
41-page object. The delivery chain must either omit that colophon or return to
39 music pages before appending it.

## Verified page map

| Page | Measures / systems | Page | Measures / systems |
| ---: | --- | ---: | --- |
| 1 | 1-3 / 4-6 | 21 | 71-73 |
| 2 | 7-8 | 22 | 74-76 |
| 3 | 9-10 | 23 | 77-80 |
| 4 | 11-12 | 24 | 81-83 / 84-92 |
| 5 | 13-14 | 25 | 93-96 |
| 6 | 15-16 | 26 | 97-98 |
| 7 | 17-20 | 27 | 99-102 |
| 8 | 21-22 | 28 | 103 |
| 9 | 23-25 | 29 | 104-105 |
| 10 | 26-31 | 30 | 106-107 |
| 11 | 32-36 | 31 | 108-109 |
| 12 | 37-39 | 32 | 110-112 |
| 13 | 40-42 | 33 | 113-114 |
| 14 | 43-45 | 34 | 115-118 |
| 15 | 46-49 | 35 | 119-124 |
| 16 | 50-52 | 36 | 125-129 |
| 17 | 53-56 | 37 | 130-134 |
| 18 | 57-61 | 38 | 135-139 |
| 19 | 62-66 | 39 | 140-145 |
| 20 | 67-70 | 40 | 146-151 |

Page 1 and page 24 are the only two-system pages. Every other page contains one
system. All 40 pages are nonblank.

## Measures 93-118 visual result

### Pages 25-27, measures 93-102 - restored safely

- Pages 25-27 are pixel-identical to the 3dd proof.
- Page 25 contains only m.93-96. The long chord row remains publication-tight,
  especially from `C(add#9)/E` through `Ebaug(maj7)/Ab`, but the identities are
  distinguishable at 300 dpi and no literal glyph-on-glyph collision occurs.
- Page 26 contains only m.97-98. Shadow and Light lyrics, chord symbol, dynamics,
  hairpins, and notes remain separated and unclipped.
- Page 27 contains only m.99-102. Multi-voice text and long continuation rules
  remain visually heavy, but `car-ry` is complete on the page and the system is
  not horizontally overfull.

### Pages 28-32, measures 103-112 - unchanged from 3dd

- Page 28 remains the sparse m.103 completion page.
- Pages 29-31 remain clean and unclipped.
- Page 32 still fails locally because `Cmaj9/E` and `subito` fuse as
  `Cmaj9/Esubito`. This is unchanged from 3dd and needs a targeted horizontal
  or vertical separation.

### Pages 33-34, measures 113-118 - successful split

- Page 33's m.113-114 system is sparse but clear. Shadow `night`, Light
  `subito mp`, and continuation lines do not collide.
- Page 34's m.115-118 system is clear at 300 dpi. Boxed 115 and `pp` are close
  but do not touch; the system-wide instruction is complete; Shadow `Who?`,
  both Baritone S lyric lines, and all Light `Who are we? / Warm hearts` lanes
  remain distinct.
- The new m.114/115 turn is a marked sectional restart after sustained notes.
  It is a defensible right-page turn and is much safer than an all-six tied
  continuation.

## Complete right-page-turn audit

| Turn after page | Boundary | Rating | Evidence |
| ---: | --- | --- | --- |
| 1 | m.6 / m.7 | Required / part-specific | Opening cast requirement; some parts continue, while several have usable rests. |
| 3 | m.10 / m.11 | Workable | Boxed 11 and the changed texture provide a clear restart. |
| 5 | m.14 / m.15 | **Unsafe** | Light text continues `They will / build as we design`; no ensemble turn window. |
| 7 | m.20 / m.21 | **Unsafe, part-specific** | Shadow text continues into `in the night`; active material reaches the edge. |
| 9 | m.25 / m.26 | **Unsafe** | Shadow phrase divides `in / time we feel`; no shared rest. |
| 11 | m.36 / m.37 | **Unsafe** | `Who feels / these withered trees` continues across the turn. |
| 13 | m.42 / m.43 | **Critical** | Literal mid-word `au- / -tumn`. |
| 15 | m.49 / m.50 | **Critical** | Literal mid-word `pre- / -ceding`. |
| 17 | m.56 / m.57 | Unsafe / active transition | Multiple active lanes reach the boundary; no full shared rest. |
| 19 | m.66 / m.67 | **Unsafe** | `We carry on / with flashlights` continues across the turn. |
| 21 | m.73 / m.74 | **Unsafe** | Shadow continues `Our one / world`; active sustained material remains. |
| 23 | m.80 / m.81 | **Ideal** | Shared rests and the extended tacet opening of m.81-83 provide ample time. |
| 25 | m.96 / m.97 | Good | Shadow completes `together`; Light is tacet; m.97 begins a new question/entry. |
| 27 | m.102 / m.103 | **Critical** | All lyric-bearing groups move from `yours` or `your light` to `too`; no shared rest. |
| 29 | m.105 / m.106 | Marginal / workable | `One light, / though dim`; the long held m.105 notes provide a possible turn window. |
| 31 | m.109 / m.110 | Workable but fast | `with love, / can pierce`; complete held notes and comma articulation help. |
| 33 | m.114 / m.115 | **Workable sectional turn** | Long-held `night` material yields to boxed 115 and a rearticulation instruction. |
| 35 | m.124 / m.125 | **Critical, new** | Baritone S and all three Light staves divide `Who / are we?`; Shadow upper voices also continue without a rest. |
| 37 | m.134 / m.135 | **Unsafe / conditional, new** | The aleatoric `Night / Light` texture continues with no shared rest; freedom of rearticulation may help, but print testing is required. |
| 39 | m.145 / m.146 | Conditional, new | All six staves continue the final texture. A full-bar held note at m.145 offers a turn window, but no true rest or sectional reset exists. |

The first 16 turn boundaries through page 31 are unchanged from the 3dd proof.
The new m.114/115 turn is acceptable; the parity regressions after it are not.

## Other retained blockers

- Page 1 remains publication-unready: the boxed 2 / commission / `Moderato`
  furniture band collides, and both opening systems retain lyric, dynamic, and
  notation overprint. The required two systems and all furniture are present.
- Page 2 repeats `listen for primer tone` independently over all three Light
  staves.
- Orphan parentheses, system-start fragments, very long continuation rules,
  and unlabeled multi-voice lyric lanes remain on several earlier pages.
- No blank page, cropped system, missing staff, one-line staff, system-on-system
  collision, or clipped late-section object was found.

## Comparison with 3dd

| Area | 3dd 39-page proof | 2ebc 40-page proof | Verdict |
| --- | --- | --- | --- |
| Pages 1-32 | Existing state | Pixel-identical | No regression or gain |
| m.93-102 | Three safe systems | Same three safe systems | Pass |
| m.113-118 | Two systems on page 33; severe local overprint | Separate pages 33-34; clean | **Major improvement** |
| m.114/115 | Same page | Sectional right-page turn | Acceptable tradeoff |
| m.119-151 parity | Facing continuations | New physical turns after m.124, m.134, and m.145 | **Regression** |
| Music page count | 39; 40 with colophon | 40 alone; 41 with colophon | Conditional |

## Recommended acceptance gate

Do not accept 2ebc as final solely because it reaches 40 pages. Preserve the
successful m.115 split, then test a compensating cast that restores the safe
late parity without touching m.93-112. The first proof must show:

1. no `Who / are we?` right-page turn at m.124/125;
2. no exposed final-texture turn at m.145/146;
3. the m.115-118 page remains as readable as current page 34;
4. either 40 music pages with no separate colophon, or 39 music pages plus the
   prepared nonblank colophon;
5. all resulting odd-page boundaries rechecked at actual Letter size.

