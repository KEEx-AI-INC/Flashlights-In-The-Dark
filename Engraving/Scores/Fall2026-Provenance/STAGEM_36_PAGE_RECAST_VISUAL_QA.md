# Stage M 36-page-recast visual QA

Audited proof: `FlashlightsInTheDark_Fall2026_PerformerScore_StageM_36PageRecast.pdf`

Audit date: 2026-08-22

SHA-256: `26c2bcf8092f2a0c167b863f1bb78cd4fd6e6932505f183e8ddbebb150b27d94`

## Result

**Fail — Stage M is not publishable or performer-ready.** The recast removes
the two literal system-on-system collisions reported in Stage J, keeps all six
staves five-line, preserves exactly two systems on page 1, and makes the formerly
overlaid systems around measures 21-25, 93-103, and 119-129 individually
readable. The long chord row at measures 93-97 is dense but does not literally
overlap at 100 percent, the two aleatoric instructions are complete and clear,
and the finale is clean.

Those gains do not yet make a viable performer score. Page 1 remains
categorically unusable, the recast creates several new right-hand turns in the
middle of words or sustained phrases, `Cmaj9/E` and `subito` remain fused on
page 27, and the required joined group barlines and minimum player-label size
are still absent. Multi-voice lyric routing and inherited continuation rules
also remain visibly unfinished in several dense passages.

The exported PDF contains **35 music pages**, not 36. It becomes
booklet-compatible only after a nonblank page-36 colophon is appended and
audited. The present PDF by itself is not divisible by four.

## Audit method

- Rendered and inspected every one of the 35 Letter pages as a complete page at
  200 dpi.
- Re-rendered pages 18-35 at 300 dpi and inspected the dense passages at native
  render size.
- Re-inspected pages 1, 6-7, 10-16, 20-24, 27-31, and 35 at 100 percent, with
  close attention to title furniture, chords, lyrics, dynamics, long rules,
  section directions, and page-edge clearance.
- Audited every right-hand turn created by the 35-page music cast.
- Checked page count, dimensions, nonblank status, embedded font resources,
  sampled text sizes, and the final barline separately.
- Made no changes to the Dorico project or PDF during this audit.

## What Stage M fixes

- **No system-on-system collisions remain.** Splitting the former Stage J
  two-system pages removes the literal overlaps at measures 21-25 and 119-129.
- **Measures 93-103 are physically separated.** The chord system and the
  three-lane lyric system no longer collide vertically.
- **All staves remain five-line and visible** on every page, including the
  opening, measures 89-97, and the finale.
- **Grouping labels and brackets are present.** `Shadow Chorus` and
  `Light Chorus` are clearly identified as separate three-staff ensembles;
  full page-1 labels and later abbreviations are sensible.
- **Core typography is readable.** Sampled lyrics are 10.5 pt, directions are
  10 pt, and chord symbols are 9.5 pt. Academico, Academico Bold/Italic,
  Bravura, and Bravura Text are embedded.
- **Running furniture is consistent** after page 1: centered running titles
  and outside folios are clear and unclipped.
- **No blank or clipped music page was found.** Page 35 has clear final
  barlines followed by rests.

## Publication blockers

### 1. Page 1: title furniture and opening notation

Page 1 still has exactly two systems, but the title, tempo, directions, and
rehearsal furniture occupy the same vertical band. `Moderato (quarter note =
c. 102)` prints through the title; `nighttime sounds mixed with` and rehearsal
mark 2 sit inside the title area. The required `Set in 2076`, commission line,
and `Jon D. Nelson` credit are absent; only the title and copyright survive.

Both systems contain severe lyric, note, and dynamic collisions. Examples
include `Herenow`, `wake`, `with-no light`, `Who sees beyond this dark`,
`listen for primer tone`, `what binds us`, `Life, light`, `we are connected by`,
and the final `Seeing the` material. Several words fuse, duplicate lanes sit
only points apart, and dynamics print through lyric fields. This page cannot be
used in rehearsal or publication without a first-page-template rebuild and
local lyric reconstruction.

### 2. New page-turn failures caused by the recast

Splitting four former two-system pages adds four music pages and changes page
parity across long spans. This moves turns away from the deliberately chosen
Stage J boundaries and creates new mid-phrase turns. The most serious are:

- **Pages 11-12, measures 42-43:** `au- / -tumn` is split across the turn.
- **Pages 13-14, measures 49-50:** `pre- / -ceding` is split across the turn.
- **Pages 23-24, measures 101-102:** `car- / -ry` is split across the turn while
  nearly all Light voices remain active beneath long hairpins.
- **Pages 27-28, measures 112-113:** all six staves sustain `night` across the
  turn; page 28 opens with tied/continued material and no performer has a true
  turn window.

Additional newly unsafe turns occur after pages 7, 9, 15, 17, and 21. The
page-turn table below records all boundaries.

### 3. Page 27: chord/direction collision

At measures 110-112, `Cmaj9/E` and `subito` touch and read as
`Cmaj9/Esubito`; `mp` is squeezed directly below. The direction must be moved
out of the chord-symbol lane. The rest of the page is readable, but this local
ambiguity is a publication blocker.

### 4. Ensemble barlines and player-label size

The two chorus labels and brackets are correct, but internal measure barlines
remain isolated on individual staves instead of joining the three staves
within each chorus. This fails the edition-wide grouping specification.

Later-page player names remain 8.5 pt by sampled PDF geometry, below the planned
9.5-10 pt floor. These are systemic rather than page-local defects.

### 5. Multi-voice lyric routing and continuation rules

The recast gives the text more vertical room, but it does not complete the
semantic lyric rebuild. Pages 10-16 and 23-24 retain two or three unlabeled
lanes on the same staff, duplicate-looking syllables, conspicuous page-width
continuation rules, and system-start fragments. Page 31 even carries long
empty-looking rules across a rest-only Soprano L staff. The objects are often
technically separated at 100 percent, but the voice assignment is not yet
stable or self-explanatory enough for publication.

## Chord-symbol audit

- **Page 21 / measures 89-92:** `Gm`, `E-flat/G`, `E-flat-minor/G-flat`, and
  `F7sus4` are close but clear.
- **Page 22 / measures 93-97:** the long row from `Fm7` through `Cmaj9/E` is
  dense, but every identity remains separable at 100 percent. More breathing
  room would improve polish, but no literal glyph overlap was found.
- **Pages 25-26:** the chord rows are clear and unclipped.
- **Page 27 / measures 110-112:** fail locally because `Cmaj9/E` and `subito`
  fuse.
- **Page 28:** `Cm(maj7)/E-flat` is clear.

## Page-turn audit

| Turn after page | Boundary | Rating | Evidence |
| ---: | --- | --- | --- |
| 1 | m.10 / m.11 | Marginal | Required title-page turn; one Light voice ties and there is no full shared rest. |
| 3 | m.14 / m.15 | Marginal | Baritone Shadow ties; the new material is nevertheless visually distinct. |
| 5 | m.20 / m.21 | Unsafe | Existing difficult opening turn; active text/music continue. |
| 7 | m.25 / m.26 | **Unsafe, new** | Shadow text continues `in / time`; the split loses the former strong turn after m.31. |
| 9 | m.36 / m.37 | **Unsafe, new** | `Who feels / these withered trees` continues across the turn. |
| 11 | m.42 / m.43 | **Unacceptable, new** | Mid-word `au- / -tumn`. |
| 13 | m.49 / m.50 | **Unacceptable, new** | Mid-word `pre- / -ceding`. |
| 15 | m.56 / m.57 | **Unsafe, new** | Active Light material continues into the next texture. |
| 17 | m.66 / m.67 | **Unsafe, new** | `We carry on / with flashlights` continues with active parts. |
| 19 | m.76 / m.77 | Good | Rests provide a usable turn before `This Brave World`. |
| 21 | m.92 / m.93 | **Unsafe, new** | Shadow Chorus continues `warm hands: / together` without a rest. |
| 23 | m.101 / m.102 | **Critical, new** | Mid-word `car- / -ry`; dense active multi-voice texture and hairpins continue. |
| 25 | m.107 / m.108 | Good | Full-measure rests precede the `with love` entry. |
| 27 | m.112 / m.113 | **Critical, new** | All six staves sustain `night` through the turn. |
| 29 | m.118 / m.119 | Moderate | Soprano S and Alto S continue/rearticulate `who`; the other four staves have usable rests. |
| 31 | m.129 / m.130 | Conditional | Little cushion, but m.130 is a clearly labeled sectional restart with a system-wide instruction. |
| 33 | m.139 / m.140 | Unsafe but sectional | Active material reaches the edge; boxed m.140 and the final-texture instruction clarify the restart. Performer test required. |
| 35 | End / colophon | End of music | No live turn. |

## Page-by-page findings

| Page | Measures / systems | Finding |
| ---: | --- | --- |
| 1 | 1-6 / 7-10 | **Fail.** Exactly two systems, but title furniture and opening notation collide extensively; required subtitle, commission, and composer lines are missing. |
| 2 | 11-12 | Readable and unclipped. Multi-voice entrance and `(sop soloist)` placement need routine lane refinement; page is top-heavy. |
| 3 | 13-14 | Local pass. Sound directions and lyrics are clear; marginal right-hand turn remains. |
| 4 | 15-16 | Local pass. Dense text remains horizontally readable; generous lower white field. |
| 5 | 17-20 | Local pass with cleanup. Light continuation marks at the left edge remain conspicuous; difficult turn after m.20. |
| 6 | 21-22 | **Structural improvement.** Former collision is gone. Extremely sparse; dangling system-start continuation marks remain. |
| 7 | 23-25 | **Structural improvement, turn fail.** Former collision is gone and objects are readable, but the new right-page turn cuts the phrase before m.26. |
| 8 | 26-31 | Pass locally. Rehearsals 26/31, Andante, and `clock ticking sounds` are clear; multi-voice dynamics remain visually busy. |
| 9 | 32-36 | Pass locally; lyric lanes are distinct. New right-page turn cuts `Who feels / these withered trees`. |
| 10 | 37-39 | Pass locally. Rehearsal 38 and hairpins are clear; system-start text fragments remain awkward. |
| 11 | 40-42 | Local objects are separated, but the Light texture remains heavy and the page ends mid-word on `au-`. |
| 12 | 43-45 | Begins with `-tumn` and inherited continuation marks because of the failed preceding turn; otherwise readable. |
| 13 | 46-49 | Parenthetical artifacts and continuation rules remain; page ends mid-word on `pre-`. |
| 14 | 50-52 | Begins with `-ceding`; `What are wonders` is readable, but multi-lane Light text remains visually heavy. |
| 15 | 53-56 | `reversed-impact sound event` is clear. Three Light lyric lanes and long hairpins are crowded; turn into m.57 is unsafe. |
| 16 | 57-61 | Pass locally. `Where sleeps the light?` and `Deep shadows` are readable; page remains top-heavy. |
| 17 | 62-66 | Local pass. Rehearsal 66 and dynamics are clear, but the new turn cuts `We carry on / with flashlights`. |
| 18 | 67-70 | Dense but readable at 100 percent; no clipping or literal overlap. |
| 19 | 71-76 | Pass. Stacked voice dynamics remain distinct, and rests provide a good turn. |
| 20 | 77-83 | Pass with cleanup. Rehearsal 80 and `musique concrète` are clear; all three Light lines still visually read `Bright,_shared`. |
| 21 | 84-92 | Chord row is physically clear. Page is very sparse; Shadow Chorus has no safe turn into m.93. |
| 22 | 93-97 | Long chord row is dense but separated at 100 percent. Page begins mid-phrase; lyric hyphens/extenders remain prominent. |
| 23 | 98-101 | Objects are technically separated, but three lyric lanes and page-width hairpins remain heavy. **Critical mid-word turn at the end.** |
| 24 | 102-103 | Begins with `-ry`; crowded multi-voice lanes are not clipped but remain unfinished. |
| 25 | 104-107 | Pass. Chords and lyrics are clear; final full-measure rests provide a good turn. |
| 26 | 108-109 | Pass but extremely sparse. Chords and `with love` are clear. |
| 27 | 110-112 | **Fail.** `Cmaj9/Esubito` is fused, and all six parts sustain through the critical turn. |
| 28 | 113-114 | Local pass; begins with continued/tied `night` material and remains extremely sparse. |
| 29 | 115-118 | Aleatoric instruction is complete, singular, system-wide, and clear. No collision; turn remains part-specific. |
| 30 | 119-124 | Pass at native resolution. Apparent thumbnail fusions such as `light Where` and `night. Who` have adequate gaps. |
| 31 | 125-129 | No local collision. Section-boundary turn is usable but lacks cushion; empty-looking continuation rules cross the rest-only Soprano L region. |
| 32 | 130-134 | Pass. Second aleatoric instruction is complete, singular, and clear; Light entries are readable. |
| 33 | 135-139 | `(D-flat = C-sharp)` and lyrics are clear. The exposed turn into the final texture needs a performer test. |
| 34 | 140-145 | Pass. Boxed 140 and `shimmering polytonal sound chandelier` are clear; `pp`/`Hmm.` lanes are stable. |
| 35 | 146-151 | Pass. Finale is readable and unclipped; `ppp`/`Hmm.` material, concluding rests, and final barlines are clear. |

## Structural and preflight status

| Requirement | Status |
| --- | --- |
| Letter portrait | Pass: all pages are 612 x 792 points. |
| Exactly two systems on page 1 | Pass structurally; fail typographically. |
| One or two systems elsewhere as content permits | Conditional: all later pages have one system, producing excessive white space and turn regressions. |
| Six visible five-line staves | Pass throughout. |
| Separate Shadow/Light labels and brackets | Pass. |
| Joined barlines within each ensemble | **Fail throughout.** |
| Lyrics at least 10.5 pt | Pass. |
| Directions at least 9.5-10 pt | Pass. |
| Player names at least 9.5-10 pt | **Fail: 8.5 pt.** |
| No blank music pages | Pass. |
| No clipped objects | Pass in the audited proof. |
| No object collisions | **Fail on page 1 and page 27; multi-lane cleanup remains elsewhere.** |
| Booklet-compatible page count | **Fail as exported: 35 pages. Conditional pass only with an audited nonblank page 36.** |
| Embedded fonts | Pass: Academico, Academico Bold/Italic, Bravura, and Bravura Text are embedded. |
| Performer-safe right-page turns | **Fail at multiple new boundaries, critically pages 23-24 and 27-28.** |
| Final page | Pass visually. |

## Required next pass

1. Rebuild page 1 with a dedicated first-page furniture band, restore the
   subtitle, commission, composer, and copyright fields, and reconstruct the
   opening lyric lanes while retaining exactly two systems.
2. Recast with page parity as a musical constraint. Either restore carefully
   spaced two-system pages at safe locations or choose different one/two-system
   pairings so that no word is split and the strongest available rests land at
   right-hand turns. Do not preserve the current 35-page music cast merely to
   keep every later page one-system.
3. Move `subito mp` away from `Cmaj9/E` on page 27.
4. Join internal barlines within each chorus and enlarge later-page player
   labels to at least 9.5 pt.
5. Normalize multi-voice lyric placement and delete or shorten orphaned or
   empty-looking continuation rules, prioritizing pages 10-16, 20, 23-24, and
   31.
6. Re-export and repeat the complete page and spread audit before appending a
   nonblank colophon. Then print-test page 1, pages 22-24, and pages 27-29 at
   actual Letter size.

## Acceptance status

Stage M is a useful spacing diagnostic and proves that the former two-system
collisions can be removed. It is **not** a production performer score. The
next proof should preserve its clear single-system spacing where necessary,
but recover a parity-aware cast, correct page 1, complete the group-barline and
label hierarchy, and finish the multi-voice lyric cleanup before any final
semantic export or saddle-stitch assembly.
