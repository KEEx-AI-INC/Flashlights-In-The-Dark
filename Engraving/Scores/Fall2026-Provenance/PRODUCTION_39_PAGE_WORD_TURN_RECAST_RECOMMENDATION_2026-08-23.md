# Production 39-page word-turn recast recommendation - 2026-08-23

## Scope and evidence

This is a read-only casting analysis of the current preserved 39-page
Production checkpoint:

- Project:
  `FlashlightsInTheDark_Fall2026_PerformerScore_BeforeWordTurnRecast_39Pages.dorico`
- Project SHA-256:
  `50981a34c93fb1e4f45f6183e4dad7490b7ef503efc4fd0ca60dd653ae3ada99`
- Embedded-preview SHA-256:
  `0ed5b6fb8b77a20740327a3487cdd9e6d00e26879bec427d1648380e2b44871b`
- Embedded proof: 39 nonblank US Letter music pages, 42 systems.
- Existing paired pages: p.1 (m.1-3 / m.4-6), p.24
  (m.81-83 / m.84-92), and p.32 (m.110-112 / m.113-114).
- Exact current m.97-103 map: p.26 = m.97-98, p.27 = m.99-102,
  and p.28 = m.103. The earlier written p.27/p.28 map of m.99-100 /
  m.101-103 was stale; the saved raster and independent embedded-model audit
  both confirm the m.103 frame break.

The preserved 3a96 checkpoint has the same late cast:
`FlashlightsInTheDark_Fall2026_PerformerScore_BeforePage1Cleanup_39Pages.dorico`,
SHA-256
`3a9615ce7cbd4a4e7b96973a954e3a6559e14deb19ec5a1a68257ec14d9c52df`.

The saved proof, its 300 dpi renders, the validated Fall MusicXML, and the
existing Stage F, Stage I, Stage J, Stage M, 35-page, 38-system, 39-page, and
40-page casting audits were compared. No Dorico project, proof, or source file
was edited for this analysis.

## Recommendation

Use a **41-system / 39-music-page cast**, followed by the existing nonblank
page-40 colophon. Preserve page 1 exactly as cast with its two systems.

Make six bounded break changes:

1. Move the frame/page break at **m.43 to m.42**.
2. Move the frame/page break at **m.50 to m.51**.
3. Convert the **m.84 system break to a frame/page break**.
4. Move the frame/page break at **m.103 to m.101**.
5. Remove the **m.106 frame/page break**, allowing m.104-107 to form one
   system. If Dorico retains an automatic division, select m.104-107 and use
   Make Into System.
6. Move the frame/page break at **m.140 to m.139**.

Retain every other current break, especially the system break at m.113 and the
frame break at m.115.

This is the preferred bounded candidate that meets all of these goals without
forcing two vertically deep lyric systems onto one page or compressing the
m.97-103 material into an unproved dense system:

- `au- / -tumn` is contained on p.14;
- `pre- / -ceding` is contained on p.15;
- every `car- / -ry` continuation is visible across the open p.28-29 spread,
  not across a physical turn;
- the all-six-staff m.139/140 turn is replaced by the materially safer
  m.138/139 turn;
- page 1 remains two systems;
- there are 39 nonblank music pages and 40 pages after one colophon.

## Exact resulting page map

| Page | Systems / measures | Turn consequence |
| ---: | --- | --- |
| 1 | 1-3 / 4-6 | Required two-system opening retained. |
| 2 | 7-8 |  |
| 3 | 9-10 | Workable turn into boxed m.11. |
| 4 | 11-12 |  |
| 5 | 13-14 | Known active Light-text turn. |
| 6 | 15-16 |  |
| 7 | 17-20 | Known active opening turn. |
| 8 | 21-22 |  |
| 9 | 23-25 | Known `in / time` continuation. |
| 10 | 26-31 |  |
| 11 | 32-36 | Known active turn into m.37. |
| 12 | 37-39 |  |
| 13 | **40-41** | New no-tie turn before m.42. |
| 14 | **42-45** | Contains every `au-tumn` lane. |
| 15 | **46-50** | Contains every Light `pre-ceding` lane. |
| 16 | **51-52** |  |
| 17 | 53-56 | Active transition turn. |
| 18 | 57-61 |  |
| 19 | 62-66 | `We carry on / with flashlights` continues. |
| 20 | 67-70 |  |
| 21 | 71-73 | `Our one / world` continues. |
| 22 | 74-76 |  |
| 23 | 77-80 | Ideal turn into the tacet/instruction span. |
| 24 | **81-83** | Intentional instruction page; nonblank. |
| 25 | **84-92** | Shadow-only sustained turn into m.93. |
| 26 | 93-96 |  |
| 27 | 97-98 | Light-specific turn before m.99; no divided word. |
| 28 | 99-100 | Light `car-` remains visible with p.29 `-ry`. |
| 29 | 101-103 | Strong complete-phrase turn after `yours too`. |
| 30 | **104-107** | Proven sparse combined system. |
| 31 | 108-109 | Workable comma articulation before m.110. |
| 32 | 110-112 / 113-114 | Existing paired page retained. |
| 33 | 115-118 | Moderate part-specific turn after m.118. |
| 34 | 119-124 |  |
| 35 | 125-129 | Complete `new home.` turn. |
| 36 | 130-134 |  |
| 37 | **135-138** | Improved turn before m.139. |
| 38 | **139-145** | Contains m.139/140 and ends on an even page. |
| 39 | 146-151 | Complete finale. |
| 40 | Nonblank colophon | Booklet-compatible total. |

Counting proof:

- The current 42-system proof has three paired pages and therefore 39 music
  pages.
- Converting m.84 from system to frame retains 42 systems but temporarily
  yields 40 music pages.
- Removing the m.106 break merges two sparse systems, yielding 41 systems on
  39 pages.
- Page 1 and page 32 are then the only two-system pages.
- Moving the m.103 frame to m.101 changes neither system count nor page count.
- The other three moved frame breaks likewise do not change the system or page
  count.

The resulting 41 system starts are:

`1, 4, 7, 9, 11, 13, 15, 17, 21, 23, 26, 32, 37, 40, 42, 46,
51, 53, 57, 62, 67, 71, 74, 77, 81, 84, 93, 97, 99, 101, 104,
108, 110, 113, 115, 119, 125, 130, 135, 139, 146`.

Only m.4 and m.113 are system-only starts; every other start after m.1 begins
a new page.

## Why each change is safe enough to prove

### M.42 instead of m.43

The revised systems are m.40-41 and m.42-45. Their source loads are:

| System | Notes | Lyric anchors | Directions |
| --- | ---: | ---: | ---: |
| 40-41 | 50 | 33 | 5 |
| 42-45 | 69 | 51 | 2 |

No part carries a tie across m.41/42. The new physical turn remains active but
does not divide a syllable. Starting at m.42 is necessary: some Light lanes
place `au-` at m.42 and `-tumn` at m.43, while another Tenor/Bass L lane places
`au-` at m.43 and `-tumn` at m.44. A later start at m.44 would therefore leave
one real mid-word turn.

### M.51 instead of m.50

The revised systems are m.46-50 and m.51-52:

| System | Notes | Lyric anchors | Directions |
| --- | ---: | ---: | ---: |
| 46-50 | 49 | 23 | 5 |
| 51-52 | 51 | 32 | 3 |

All Light `pre-ced-ing` syllables at m.49-50 remain together on p.15. Moving
the break earlier to m.49 is unsafe because the Soprano and Alto Light lanes
divide `co- / -lor` at m.48/49. At m.50/51 only the lower Tenor/Bass L tie
continues; its final `-ing` syllable is already printed on p.15, so no word is
divided.

### M.84 as a frame break

This separates the current p.24 pair into two intentional pages:

- p.24, m.81-83, contains the `musique concrète` semantic instruction and is
  therefore sparse but not blank;
- p.25, m.84-92, begins with five tacet measures and contains the first lantern
  entrance.

Both systems already pass individually. This is visually safer than pairing
the deep m.97-98 and m.99-100 lyric envelopes or forcing m.97-100 into one
unproved compressed system.

The musical trade is explicit: the new p.25 turn at m.92/93 is available to the
entire Light Chorus, which is tacet, while the three Shadow parts sustain. The
new p.27 turn at m.98/99 is available to the Shadow Chorus while the Light
texture continues. Neither turn divides a word.

### M.101 instead of m.103

This sixth operation is **not mathematically required** for the 39-page count,
and after the m.84 parity change the current m.99-102 / m.103 systems would no
longer place `car-ry` at a physical turn. It is nevertheless recommended for
publication because it replaces an isolated one-measure m.103 page with the
far better balanced m.99-100 / m.101-103 pair.

The move has direct visual evidence. The preserved 03:53 proof
`FlashlightsInTheDark_Fall2026_PerformerScore_BeforeMidwordTurnRepair_2026-08-23_035356.dorico`
(embedded-preview SHA-256
`b567016fd8d956ffc0129fadac356a542216cf27570eea747bcf0c7a5ac21dbd`)
prints exactly m.99-100 and m.101-103 as separate, unclipped, readable
full-page systems under the same 10.5 pt lyric regime. Its original problem was
page parity, not horizontal fit: those systems occupied p.27 and p.28, so Light
`car- / -ry` crossed a physical turn. Converting m.84 to a frame shifts the
same systems to p.28 and p.29, where they form a visible even-to-odd spread.

The revised system loads are:

| System | Notes | Lyric anchors | Directions |
| --- | ---: | ---: | ---: |
| 99-100 | 27 | 26 | 0 |
| 101-103 | 59 | 45 | 12 |

Light `car-` on p.28 remains simultaneously visible with `-ry` on p.29;
Shadow `car-ry` is wholly on p.29. Page 29 then ends at the strong, complete
`yours too` / m.103 boundary before m.104. Moving this break is therefore the
preferred editorial cast, even though leaving it at m.103 would still pass the
narrow physical-word-turn test.

### Remove m.106

M.104-107 contains 37 notes, 25 lyric anchors, eight directions, and three
harmonies. The one-system cast has already passed visually in Stage F, Stage I,
Stage J, and Stage M: chords, repeated `One light, though dim` entries, ties,
dynamics, and final rests remain clear. Removing this page restores the
39-page total only after every `car-ry` continuation has passed.

### M.139 instead of m.140

The revised systems are m.135-138 and m.139-145. The p.37/38 physical turn
moves from m.139/140 to m.138/139:

- current m.139/140: all six staves tie or continue into the next page;
- proposed m.138/139: only the three Shadow staves tie;
- every Light staff has rest before its late m.139 `light` entrance;
- the Light text turns between the complete words `We bring / light`, not
  inside a word;
- m.139, boxed m.140, `(Db = C#)`, and the sound-chandelier instruction remain
  together on p.38;
- m.145/146 remains an even-to-odd visible-spread boundary.

M.139-145 is a seven-measure system with mostly long sustained values. It adds
one bar to the already readable m.140-145 page and is the principal horizontal
acceptance item for the new proof.

## Rejected shortcuts

- **Do not pair m.97-98 / m.99-100 on one page.** The saved 300 dpi systems
  each use nearly the full vertical image area because of multi-voice lyric,
  extender, dynamic, and notation lanes. A system-only m.99 break is not a
  publication-safe vertical assumption.
- **Do not collapse m.93-102.** The preserved rejected proof demonstrates
  categorical chord, lyric, extender, and notation overprint.
- **Do not move the current m.103 frame to m.100.** M.100-103 is materially
  denser than the directly proved m.101-103 system, and the change gives no
  page-turn advantage after the m.84 parity shift.
- **Do not leave the current m.103 frame merely because the count already
  works.** It would be turn-safe after the parity change, but it leaves m.103
  alone on p.29 while the directly proved m.99-100 / m.101-103 balance is
  available at no pagination cost.
- **Do not fix all three words by one early global parity shift and compensate
  in the finale.** That route exposes the all-six m.145/146 texture at a
  physical turn or requires another unsafe split inside m.140-147.

## Acceptance gate

This is a proof-ready recommendation, not a visual acceptance claim. After the
six break changes:

1. Require exactly 41 systems on 39 nonblank music pages, with two systems only
   on p.1 and p.32.
2. Inspect new pages 13-16 at 300 dpi and confirm every `au-tumn`, `color`, and
   `preceding` lane remains complete and horizontally separated.
3. Inspect the p.24-29 spread sequence and confirm p.24 is intentionally
   nonblank, the new part-specific turns are readable, and every `car-ry`
   continuation is visible without a physical turn.
4. Inspect p.30 and confirm m.104-107 remains one unclipped system with readable
   chord and repeated lyric lanes.
5. Inspect p.37-39 at 100 percent and print-test p.37/38. Reject the m.139 start
   if seven measures cause a collision with boxed m.140, `(Db = C#)`, or the
   sound-chandelier instruction.
6. Append exactly one nonblank colophon and preflight the resulting 40-page
   Letter PDF for no blanks, embedded fonts, safe margins, and booklet order.
