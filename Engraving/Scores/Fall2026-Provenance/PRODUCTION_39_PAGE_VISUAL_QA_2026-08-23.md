# Production 39-page visual QA - 2026-08-23

## Audited snapshot

- Dorico project: `FlashlightsInTheDark_Fall2026_PerformerScore_Production.dorico`
- Project saved: 2026-08-23 03:53:56 CDT
- Project SHA-256: `ffaf6669b459e5bbdceb4361acbb8e21386e645f8033c9f01a75518187d57298`
- Embedded-preview SHA-256: `b567016fd8d956ffc0129fadac356a542216cf27570eea747bcf0c7a5ac21dbd`
- Preview metadata: Dorico 5.1.60.2187; generated 2026-08-23 03:53:55 CDT; 39 US Letter portrait pages.
- Method: extracted the saved preview, rendered and inspected all 39 pages at both 150 and 300 dpi, inspected every page at full-page scale, and rechecked the dense passages at pages 1, 13-18, and 25-33 at print resolution. Pixel-density preflight found all 39 pages nonblank.
- The requested 03:49:53 preview (`beca934341977eb53ae2439de620d2be5185b66dc5fd5cd888b7ae2e7f747b32`) was also fully rendered. The 03:53 save supersedes it and changes pages 1, 4, 7, 10, 12, 18, 28, and 33 without changing pagination.

## Result

**Fail - structurally strong, but not yet performer-ready.** The 39-page cast is
mechanically intact: page 1 contains exactly two systems, every page is
nonblank, all six staves are five-line, the Shadow and Light choruses are
bracketed separately, barlines join within each three-staff ensemble, and no
system-on-system collision occurs. Adding the prepared nonblank page-40
colophon would produce a booklet-compatible 40-page object.

The recast does not yet solve the score's critical local problems. Page 1 still
has furniture and lyric collisions; page 33 has severe lyric/dynamic
overprinting in both systems; `Cmaj9/Esubito` remains fused on page 32; and the
new page-27/28 boundary still divides `car- / -ry`, now in several Light lanes.
The older right-page mid-word turns at `au- / -tumn` and `pre- / -ceding` also
remain.

## Verified page map

| Page | Measures / systems | Page | Measures / systems |
| ---: | --- | ---: | --- |
| 1 | 1-3 / 4-6 | 21 | 71-73 |
| 2 | 7-8 | 22 | 74-76 |
| 3 | 9-10 | 23 | 77-80 |
| 4 | 11-12 | 24 | 81-83 / 84-92 |
| 5 | 13-14 | 25 | 93-96 |
| 6 | 15-16 | 26 | 97-98 |
| 7 | 17-20 | 27 | 99-100 |
| 8 | 21-22 | 28 | 101-103 |
| 9 | 23-25 | 29 | 104-105 |
| 10 | 26-31 | 30 | 106-107 |
| 11 | 32-36 | 31 | 108-109 |
| 12 | 37-39 | 32 | 110-112 |
| 13 | 40-42 | 33 | 113-114 / 115-118 |
| 14 | 43-45 | 34 | 119-124 |
| 15 | 46-49 | 35 | 125-129 |
| 16 | 50-52 | 36 | 130-134 |
| 17 | 53-56 | 37 | 135-139 |
| 18 | 57-61 | 38 | 140-145 |
| 19 | 62-66 | 39 | 146-151 |
| 20 | 67-70 |  |  |

## Publication blockers

### P0 - page 1, measures 1-6

- Boxed rehearsal mark 2 no longer strikes the title, but now sits in the
  credit band above the commission line. `Moderato` prints through the
  commission line; `Begin in darkness` is crowded directly below.
- In the first system, `Here` collides with the Alto S note/dynamic, and the
  Light Soprano and Alto lyric lines cross staff lines, notes, or dynamics.
- In the second system, Baritone S carries duplicate `-no light` text in the
  same lane, with the `f` and neighboring notation overprinted. Isolated `(`
  and `)` fragments remain in the Shadow staves.
- The restored `Set in 2076`, commission line, composer, and copyright are all
  present, and the page does retain the required two systems.

### P0 - page 33, measures 113-118

- In m.113-114, the upper Baritone S `night` prints into its note/slur/staff
  region. Light-staff `subito mp`, `night`, and long imported continuation
  rules occupy competing lanes.
- At m.115, Soprano S `pp` and `Who?` overprint. In Baritone S, the two
  `Who are we?` lines collapse on one another, and the two `Warm hearts` lines
  also overprint. This text is not reliably readable at Letter size.
- The singular aleatoric instruction is complete and clear, and the two
  systems do not collide with one another. The failure is local lyric/dynamic
  routing inside the systems, not cast-off height.

### P0 - physical mid-word turns

- Pages 13-14, m.42/43: `au- / -tumn` crosses a right-page turn. Page 14 also
  retains several isolated `-tumn`, hyphen, and continuation fragments.
- Pages 15-16, m.49/50: `pre- / -ceding` crosses a right-page turn, with
  fragmented syllable lanes on both pages.
- Pages 27-28, m.100/101: the new m.101 system move keeps Shadow `car-ry` on
  page 28, but several Light lines now end page 27 on `car-` and begin page 28
  on `-ry`. The recast therefore moves the critical split to different voices
  rather than eliminating it.

### P1 - page 32, measures 110-112

`Cmaj9/E` and `subito` remain fused as `Cmaj9/Esubito` above Soprano S. The
nearby `mp` is separated, but the chord/direction identity is still ambiguous.

### P1 - page 25, measures 93-96

The right half of the chord row remains publication-tight. The smallest gaps
are around `C(add#9)/E`, `Cm/Eb`, `Abmaj7`, `Abmaj7(add#11)`, and
`Ebaug(maj7)/Ab`; the final symbol approaches the right music margin. The
identities can be decoded at 300 dpi, but they do not yet have modern
publication spacing.

## Additional cleanup still visible

- Page 2 repeats `listen for primer tone` independently over all three Light
  staves. Decide whether it is a single ensemble instruction or three
  performer-specific instructions and encode it accordingly.
- Pages 3 and 15 retain isolated parenthesis fragments.
- Pages 13-17, 21-23, 27-28, 33, and 35 contain conspicuous empty-looking or
  page-width continuation rules and multi-voice lines whose entrance/voice
  assignment is not self-evident.
- Page 17's `reversed-impact sound event` remains very near the right edge,
  though it is unclipped.
- Additional exposed right-page continuations remain after pages 9 (`in / time`),
  11 (`Who feels / these withered trees`), 19 (`We carry on / with flashlights`),
  21 (`Our one / world`), and 33 (`Warm hearts / light`). They are less severe
  than the three mid-word turns but still need performer-turn judgment.

## Confirmed strengths

- All 39 pages are US Letter portrait, present, nonblank, and unclipped.
- Page 1 has exactly two systems. Pages 24 and 33 are the only other two-system
  pages; both retain clear separation between systems.
- All six staves are visible and five-line throughout, including the opening,
  m.89-96, and the finale.
- Shadow Chorus and Light Chorus labels, brackets, joined internal barlines,
  and the gap between ensembles are correct throughout.
- Centered running titles and outside folios are consistent on all later pages.
- The m.101-103 system fits on page 28 without horizontal clipping or a literal
  note-to-note collision. It is dense and semantically busy, but physically
  viable after local lyric cleanup.
- The m.106 frame break is clean: pages 29 and 30 are nonblank, unclipped, and
  locally readable. It shifts m.110-112 to left page 32 and m.113-118 to right
  page 33, so the former m.112/113 tied physical turn becomes a facing-page
  continuation.
- Pages 34-39 are stable overall. Both aleatoric directions, `(Db = C#)`, boxed
  m.140, `shimmering polytonal sound chandelier`, the final `ppp`/`Hmm.` lanes,
  rests, and final barlines are readable.

## Comparison with Stage M and the 38-page pre-recast proof

- **Better than Stage M structurally:** joined ensemble barlines and the label
  hierarchy now pass; the running furniture is consistent; there are no blank
  or colliding systems; and 39 music pages plus the prepared colophon gives the
  intended 40-page booklet total. The former critical m.112/113 physical turn
  is now resolved into a facing spread.
- **Not materially better than Stage M locally:** page 1 remains unusable,
  `Cmaj9/Esubito` remains fused, the m.42/43 and m.49/50 word splits remain, and
  page 33 is less readable than Stage M's separately paged m.113-114 and
  m.115-118 systems.
- **Mixed against the 02:44 38-page proof:** the m.106 break and later parity are
  genuine gains. Consolidating m.101-103 gives Shadow a complete `car-ry`, but
  introduces the split in Light voices and makes page 28 denser. The global
  collision pass improves automatic vertical clearance on several pages but
  does not override legacy local lyric positions; the duplicated Baritone S
  text on page 33 is more compressed than in the 02:44 proof.

Overall severity is lower systemically than Stage M, but the acceptance result
remains **fail** because two pages have severe local overprinting and three
right-page turns divide words.

## Required next pass

1. Finish page 1's first-page furniture band and locally rebuild both opening
   lyric/dynamic systems without changing the two-system cast.
2. Treat page 33 as the highest-priority dense-page repair: separate both
   Baritone S lyric lanes, move the Shadow dynamics, then reset/nudge the upper
   `night` and Light `subito mp` objects.
3. Revisit page parity/casting for the three mid-word turns. The m.101 move
   alone does not make the page-27/28 turn safe across all lyric-bearing voices.
4. Separate `Cmaj9/E` from `subito` on page 32 and give the page-25 chord row
   targeted horizontal breathing room.
5. Normalize orphan punctuation, system-start fragments, and long empty-looking
   continuation rules, then repeat a full 300-dpi page and spread audit.

