# Fall 2026 40-page publication cast

## Recommendation

Use **42 musical systems on 39 nonblank music pages**, followed by the existing
nonblank page-40 colophon. Pages 1, 2, and 31 carry two systems; every other
music page carries one.

This is the smallest turn-safe 40-page profile that also gives the congested
m.7-10 opening a second system. A simpler four-page expansion of the current
35-page proof is not safe: shifting m.98/99 onto a facing spread exposes the
adjacent `car- / -ry` continuation at m.101/102 as a physical turn, and shifting
m.109/110 exposes the all-six-part tie at m.112/113. The recommended recast
removes those alternating hazards instead of merely moving them.

Evidence snapshot:

- Dorico project:
  `FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.dorico`
- Project SHA-256:
  `404bd65f068cb9828bb6ce32a6fc5086f2f0070814dd6355bda54b0ded0b40e4`
- Validated casting source:
  `FlashlightsInTheDark_Fall2026_Dorico32PageCasted.musicxml`
- Source SHA-256:
  `28eaade134594b196efd38d1d1f5a40504ba12176aaa373046ee6e0a3567b844`

## Exact page map

| Page | Systems | Measures | Turn consequence |
| ---: | ---: | --- | --- |
| 1 | 2 | 1-3; 4-6 | Required opening pair; part-specific turn after m.6. |
| 2 | 2 | 7-8; 9-10 | New readability pair; no physical turn on this even page. |
| 3 | 1 | 11-12 | Workable but fast turn after m.12. |
| 4 | 1 | 13-14 | No physical turn. |
| 5 | 1 | 15-16 | Known unsafe turn after m.16. |
| 6 | 1 | 17-20 | No physical turn. |
| 7 | 1 | 21-22 | Workable turn after m.22. |
| 8 | 1 | 23-25 | No physical turn. |
| 9 | 1 | 26-31 | Strong clock/Andante turn after m.31. |
| 10 | 1 | 32-36 | No physical turn. |
| 11 | 1 | 37-39 | Known unsafe turn after m.39. |
| 12 | 1 | 40-42 | `au- / -tumn` remains on a facing spread. |
| 13 | 1 | 43-45 | Workable breathing-arc turn after m.45. |
| 14 | 1 | 46-49 | `pre- / -ceding` remains on a facing spread. |
| 15 | 1 | 50-52 | Unsafe but not mid-word turn after m.52. |
| 16 | 1 | 53-56 | No physical turn. |
| 17 | 1 | 57-61 | Strong turn after m.61. |
| 18 | 1 | 62-66 | No physical turn. |
| 19 | 1 | 67-70 | Workable colon/formal-reset turn. |
| 20 | 1 | 71-73 | New three-measure system; no physical turn. |
| 21 | 1 | 74-76 | Good rest-supported turn before `This Brave World`. |
| 22 | 1 | 77-80 | Musical part of the musique-concrete span. |
| 23 | 1 | 81-83 | Intentional silent system with the `musique concrète` instruction; ideal turn. |
| 24 | 1 | 84-92 | Tacet-to-lantern system; no physical turn. |
| 25 | 1 | 93-96 | Part-specific turn; Light Chorus has a full-bar rest. |
| 26 | 1 | 97-100 | m.98/99 is internal; `car-` remains visible with its completion. |
| 27 | 1 | 101-103 | Strong turn after the complete `yours too` phrase. |
| 28 | 1 | 104-105 | Short chord/instruction system; no physical turn. |
| 29 | 1 | 106-107 | Good full-rest turn before m.108. |
| 30 | 1 | 108-109 | m.109/110 is a facing-page boundary. |
| 31 | 2 | 110-112; 113-114 | Tied `night` stays on one page; turn moves to the no-tie m.114/115 boundary. |
| 32 | 1 | 115-118 | Complete first aleatoric field; no physical turn. |
| 33 | 1 | 119-121 | Moderate part-specific turn after m.121. |
| 34 | 1 | 122-124 | Balanced continuation; no physical turn. |
| 35 | 1 | 125-129 | Workable complete-phrase turn at `new home.` |
| 36 | 1 | 130-134 | No physical turn. |
| 37 | 1 | 135-139 | Unsafe but explicit sectional turn into boxed m.140. |
| 38 | 1 | 140-145 | No physical turn. |
| 39 | 1 | 146-151 | End of music. |
| 40 | - | Nonblank colophon | Booklet-compatible total; no live turn. |

## Exact live break delta

From the saved 35-page / 38-system PrintFinal project:

1. Add a **system break** at m.9, keeping m.7-8 and m.9-10 together on page 2.
2. Add **frame/page breaks** at m.74 and m.81.
3. Convert the m.93 **system break to a frame/page break**.
4. Force m.97-100 into one system, eliminating Dorico's automatic start at
   m.99.
5. Move the frame/page break at m.102 to m.101, producing m.97-100 and
   m.101-103.
6. Add a **frame/page break** at m.106.
7. Convert the m.113 **frame/page break to a system break**, pairing m.110-112
   with m.113-114 on page 31.
8. Convert the m.115 **system break to a frame/page break**.
9. Add a **frame/page break** at m.122.
10. Retain every other current explicit break.

The resulting system starts are:

`1, 4, 7, 9, 11, 13, 15, 17, 21, 23, 26, 32, 37, 40, 43, 46, 50, 53, 57, 62, 67, 71, 74, 77, 81, 84, 93, 97, 101, 104, 106, 108, 110, 113, 115, 119, 122, 125, 130, 135, 140, 146`.

Only m.4, m.9, and m.113 are system-only starts. Every other start after m.1
begins a new page.

Counting proof:

- 42 systems minus three paired pages equals 39 music pages.
- Adding starts at m.9, m.74, m.81, m.106, and m.122 adds five systems.
- Suppressing the automatic m.99 start removes one system.
- Net change from the saved 38 systems is plus four, producing 42.

## Density and feasibility checks

| Revised system | Notes | Lyric anchors | Directions | Harmonies | Assessment |
| --- | ---: | ---: | ---: | ---: | --- |
| 7-8 | 36 | 25 | 12 | 0 | Light upper system on page 2. |
| 9-10 | 52 | 42 | 15 | 0 | Dense, but gains twice the horizontal space of the current m.7-10 system. |
| 71-73 | 33 | 24 | 8 | 0 | Balanced three-measure full page. |
| 74-76 | 36 | 21 | 0 | 0 | Balanced three-measure full page with a good terminal rest. |
| 77-80 | 53 | 27 | 1 | 0 | Active part of the transition. |
| 81-83 | 0 | 0 | 1 | 0 | Intentionally silent, not blank; carries the semantic instruction. |
| 97-100 | 54 | 45 | 7 | 1 | Main horizontal acceptance item; lighter than the failed m.97-101 attempt. |
| 101-103 | 59 | 45 | 12 | 0 | Three dense measures on a complete page. |
| 104-105 | 18 | 12 | 7 | 2 | Separates the chord and instruction lanes. |
| 106-107 | 19 | 13 | 1 | 1 | Short continuation ending at a strong rest boundary. |
| 110-112 | 45 | 32 | 6 | 2 | Upper system of page 31. |
| 113-114 | 25 | 18 | 0 | 1 | Sparse lower system of page 31. |
| 119-121 | 34 | 22 | 0 | 0 | Balanced half of the former six-measure system. |
| 122-124 | 34 | 23 | 0 | 0 | Balanced continuation. |

No dense system exceeds seven measures. The sole longer system is m.84-92:
its first five measures are tacet and m.89-92 contains only the light lantern
entrance.

The page-31 pair is safer than the Stage F m.108-112 / m.113-114 pair that was
already physically separated: the proposed upper system removes m.108-109.
Its remaining issues (`Cmaj9/E`, `subito`, `mp`, and the `night` lane) are local
object-routing work, not a casting incompatibility.

## Right-hand turn audit

| Turn after page | Boundary | Rating | Evidence |
| ---: | --- | --- | --- |
| 1 | m.6 / m.7 | Required, part-specific | Alto S and Baritone S tie; several other parts have usable rests. |
| 3 | m.12 / m.13 | Workable but fast | No ties, but the Light phrase continues. |
| 5 | m.16 / m.17 | Unsafe, known | Alto L1/L2 ties and Shadow text continues. |
| 7 | m.22 / m.23 | Workable | No ties; Light Chorus has a full-bar rest. |
| 9 | m.31 / m.32 | **Strong** | No ties and broad shared clearance at the clock/Andante reset. |
| 11 | m.39 / m.40 | Unsafe, known | Tenor/Bass L ties into the continuing texture. |
| 13 | m.45 / m.46 | **Workable** | No tie and useful breathing clearance. |
| 15 | m.52 / m.53 | Unsafe, not mid-word | Three Light parts tie; the former `pre-ceding` hard turn stays in the spread. |
| 17 | m.61 / m.62 | **Strong** | No ties and at least two beats of clearance in every active part. |
| 19 | m.70 / m.71 | **Workable** | No ties; colon and formal reset. |
| 21 | m.76 / m.77 | **Good** | Rests provide a usable turn before `This Brave World`. |
| 23 | m.83 / m.84 | **Ideal** | Complete tacet, with five more silent measures before m.89. |
| 25 | m.96 / m.97 | Part-specific | Soprano S and Alto S tie; all three Light staves have a full-bar rest. |
| 27 | m.103 / m.104 | **Strong** | No ties; all six voices complete `yours too`. |
| 29 | m.107 / m.108 | **Good** | Full-measure rests precede the `with love` entrance. |
| 31 | m.114 / m.115 | **Workable** | No cross-bar ties; m.115 instruction begins at the top of the next page. |
| 33 | m.121 / m.122 | Moderate, part-specific | Soprano S ties; the lower four parts have two beats and complete `Who are we?`. |
| 35 | m.129 / m.130 | **Workable but fast** | No ties; complete `new home.` phrase before the sectional restart. |
| 37 | m.139 / m.140 | Unsafe but sectional | All six parts tie; boxed m.140 makes the restart explicit. |
| 39 | End / colophon | End of music | No live turn. |

## Semantics-preservation boundary

This is a casting-only plan. Applying it authorizes changes only to Dorico
system/frame breaks and the resulting page allocation. It does **not**
authorize changes to notes, pitches, rhythms, ties, tuplets, measures, meters,
tempos, dynamics, chord symbols, cue timing, lyric anchors, lyric text,
directions, staff count, staff-line count, player/group membership, or runtime
assets.

After recasting, the MusicXML round-trip must still verify:

- six parts and 151 measures per part;
- 2,787 notes;
- 1,376 lyric anchors;
- all 388 approved Fall replacements;
- canonical musical fingerprint
  `82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111`;
- no unlogged text difference.

The p.23 `musique concrète` direction is semantic content and must remain; it is
also what makes the otherwise silent page intentionally nonblank. The page-40
colophon remains a separate preserved artifact and must not be synthesized as
an empty Dorico music page.

## Acceptance gate

After applying the delta, export and inspect all 39 music pages. Reject or
revise the cast if any of these fail:

1. Page 2: the two six-staff systems must remain vertically separate with the
   approved 10.5 pt lyrics and 9.5-10 pt directions.
2. Page 23: the silent `musique concrète` page must read as intentional and
   must not appear accidentally blank.
3. Pages 26-27: m.97-100 must remain one system without reducing text size;
   the `car- / -ry` continuation must be simultaneously visible in the open
   spread.
4. Pages 30-31: m.109/110 must be a facing boundary; page 31's two systems must
   not overlap; tied `night` must remain on that page.
5. Pages 33-34: the balanced m.119-121 / m.122-124 split must retain stable
   lyric and dynamic lanes.
6. Spread audit: `au-tumn`, `pre-ceding`, `car-ry`, m.109/110, and tied
   m.112/113 must not require a physical page turn.
