# Stage I raw-import visual QA

Audited proof: `FlashlightsInTheDark_Fall2026_PerformerScore_StageI_RawImport.pdf`

Audit date: 2026-08-22

## Result

**The 31-page music cast succeeds structurally, but the raw import is not yet
print-ready.** Dorico preserves all 36 intended systems on 31 nonblank Letter
pages, including exactly two systems on page 1. The cast removes the former
system-on-system collisions and gives the dense spans materially more room.
The remaining blockers are page-one furniture, ensemble grouping, lyric
routing/extenders, the chord row at measures 93-97, and one chord/dynamic
collision at measure 112.

The raw proof is intentionally only the 31 music pages. Append the already
prepared nonblank page-32 colophon only after the music pages are frozen.

## Audit method

- Rendered and inspected all 31 pages at 150 dpi in full-page views.
- Inspected full-resolution views of page 1 and the dense/problem spans at
  measures 21-25, 46-56, 93-103, 108-118, and 130-151.
- Cross-checked page count, Letter dimensions, text font resources, sampled
  printed text sizes, headers, page numbers, system boundaries, and page turns.
- Made no changes to the Dorico project or audited PDF.

## Global findings

### Structural pass

- 31 music pages; no blank page; 36 systems.
- Two systems appear only on pages 1, 6, 20, 21, and 27. Every other page has
  one system.
- Page 1 has the required two systems. The systems are close, but no musical
  system crosses another system.
- All six staves remain visible and five-line throughout, including pages 1
  and 20 around measures 89-97.
- The PDF is Letter portrait (612 x 792 points). No page-edge clipping was
  found. Later pages have centered running titles and outside folios.

### Blocking global defects

1. **The two choruses are not visually grouped.** Every system shows one
   continuous, unlabelled six-staff bracket. `Shadow Chorus` and `Light Chorus`
   group names, two separate primary brackets, and visibly separate three-staff
   barline joins are absent.
2. **Typography is below the approved floor.** The PDF uses the intended
   Bravura/Bravura Text and Academico families, but sampled lyrics print at
   9.5 pt and player labels at 8.5 pt. Lyrics must become 10.5 pt absolute and
   labels should be approximately 9.5-10 pt. Performance directions sampled at
   10 pt and are already readable.
3. **Lyric offsets and extenders still reflect import behavior.** Several
   pages contain long, duplicated, crossing, or empty-looking continuation
   rules. Page 21 is the print-blocking instance; pages 12, 14, 19, 23-25, and
   27-31 need verification after a global lyric-offset reset.
4. **One-system pages are visually inconsistent.** Some systems are vertically
   stretched (especially pages 2 and 24), while many are top-heavy with large
   lower white fields. This is not a collision problem, but it needs a final
   page-balance pass after typography is stable.

## Page-by-page findings

| Page | Measures / systems | Visual finding |
| ---: | --- | --- |
| 1 | 1-6 / 7-10 | **Fail.** Two systems are present, but a 20 pt title and a second 16 pt flow title are duplicated. The second title collides with `Begin in darkness:`; tempo, rehearsal mark 2, and three opening directions crowd the title field. Subtitle, commission, composer, and copyright furniture are absent. In system 1, Light lyrics/dynamics print through staves and noteheads; Shadow words such as `Who sees` / `beyond this` visibly fuse. In system 2, `listen for primer tone`, `we are connected by`, and the final Tenor/Bass text collide or fuse with notes. The inter-system clearance is dangerously small even though the systems do not directly overlap. |
| 2 | 11-12 | Cast is spacious and readable. The final Light/Tenor text visually fuses as `Here,here!`; multiple Light voice lanes and accents need local separation. |
| 3 | 13-14 | Pass structurally. `swell of robot sounds` and `rocket sounds` are clear; multi-voice Light lyrics remain readable. |
| 4 | 15-16 | Pass structurally. Dense `Look at this!` / `build as we design` texture is horizontally readable; retain this one-system width. |
| 5 | 17-20 | Pass structurally. Light multi-voice lyrics and left-edge continuation marks need routine lyric cleanup, but no collision blocks reading. |
| 6 | 21-22 / 23-25 | **Two-system split succeeds.** No system-on-system collision. Dynamics, hairpins, and `in the night` / `at last` lyrics need lane normalization, especially in the Light staves. |
| 7 | 26-31 | Pass. Rehearsal 31, Andante, the tempo equation, hairpin, and `clock ticking sounds` are close but non-colliding. |
| 8 | 32-36 | Pass. Multi-voice Light routing is legible; normalize inherited extender lengths. |
| 9 | 37-39 | Pass. No collision in the previously risky continuation; dynamics and hairpins are clear. |
| 10 | 40-42 | Pass. Dense slurs, ties, and multi-voice `bloom` / `autumn` text remain readable. |
| 11 | 43-45 | Pass. System-start `-tumn` fragments and continuation rules are visually awkward but do not collide. |
| 12 | 46-49 | Horizontal split succeeds. Empty-looking parenthesis pairs float in the Alto S and Alto L lyric regions; verify their semantic purpose and remove/reset only if they are import artifacts. |
| 13 | 50-52 | Horizontal split succeeds. `What are wonders` has adequate note/lyric spacing; long multi-voice extenders need routine normalization. |
| 14 | 53-56 | Pass with cleanup. `reversed-impact sound event` is clear. Three Light lyric lanes and their long extenders are crowded but non-colliding. |
| 15 | 57-61 | Pass. `Where sleeps the light?` and `Deep shadows` are readable; no system collision. |
| 16 | 62-66 | Pass. Upper hairpins, rehearsal 66, dynamics, and the `We carry on` entrance are clear. |
| 17 | 67-70 | Pass. Dense Light/Tenor lyric lanes are readable; verify the isolated left-edge continuation/ornament and normalize extenders. |
| 18 | 71-76 | Pass. Changing-meter material and `new world` / `Bright world` lanes are clear. |
| 19 | 77-83 | Pass structurally. The extender after `Bright,` sits so close to `shared` that it reads like a literal underscore (`Bright,_shared`); shorten or reroute the extender in all three Light staves. `musique concrète` is clear. |
| 20 | 84-92 / 93-97 | Upper system and inter-system spacing pass. **Fail locally at 93-97:** the chord-symbol row from `C(add♭9)/E` through `Cmaj9/E` runs together, with the densest collisions among `Cm/E♭`, `A♭maj7`, `A♭maj7(add11)`, and `E♭aug(maj7)/A♭`. Re-space or locally reduce/offset the chord symbols without shrinking lyrics. |
| 21 | 98-101 / 102-103 | **Fail.** The two systems themselves are separate, but lyric extenders, hairpins, and duplicated Light/Shadow lyric lanes cross or run through `hands grow weary`, `I'll carry your`, `yours`, and `too`. Reset lyric layout, then establish stable above/below/additional lanes locally. |
| 22 | 104-107 | Pass. Chord symbols, dynamics, ties, and repeated `One light` entries are clear. |
| 23 | 108-109 | Pass structurally. `with love,` is clear; long Light continuation rules need normalization. |
| 24 | 110-112 | **Fail locally.** On Soprano S, `Cmaj9/E` and `subito mp` collide and read as `Cmaj9/Emp`. Separate the chord symbol from the performance direction/dynamic. The wide staff spacing otherwise makes `can pierce ... night` readable. |
| 25 | 113-114 | Pass. Lead-in is clear and places the aleatoric instruction at the top of page 26. Verify long Light lyric extenders. |
| 26 | 115-118 | Pass structurally. `rearticulate freely in aleatoric style` appears once, complete, and clear above the ensemble. Multi-voice lyric lanes are readable. |
| 27 | 119-124 / 125-129 | Two-system cast succeeds with safe inter-system clearance. Several long or empty-looking Light continuation rules remain; reset/verify them before local placement. |
| 28 | 130-134 | Pass structurally. The second aleatoric instruction is complete and clear. Long blank-looking Light lyric rules require verification. |
| 29 | 135-139 | Pass. Final-transition lyrics and notes are readable; no collision. Long continuation rules remain visually prominent. |
| 30 | 140-145 | Pass. Rehearsal 140 and `shimmering polytonal sound chandelier` are clear and non-colliding; `night` / `light` and `Hmm.` lanes are readable. |
| 31 | 146-151 | Pass. Final system is uncompressed, final barlines are clear, header/folio are present, and nothing is clipped. Normalize the remaining long Light continuation rules. |

## Page-turn audit

The imported cast preserves the planned right-page turns. No new turn hazard is
introduced by Dorico, but the musical limitations remain:

| Turn after page | Boundary | Rating |
| ---: | --- | --- |
| 1 | m.10 / m.11 | Marginal; one Light voice ties and there is no shared rest. |
| 3 | m.14 / m.15 | Marginal; Baritone Shadow ties. |
| 5 | m.20 / m.21 | Unsafe but preferable to recompressing the densest opening span. |
| 7 | m.31 / m.32 | Strong; substantial shared clearance. |
| 9 | m.39 / m.40 | Unsafe but avoids the former colliding system pair. |
| 11 | m.45 / m.46 | Workable; no cross-bar tie. |
| 13 | m.52 / m.53 | Unsafe but protects the m.46-52 horizontal split. |
| 15 | m.61 / m.62 | Strong; shared clearance and no ties. |
| 17 | m.70 / m.71 | Workable; brief shared space and no ties. |
| 19 | m.83 / m.84 | Ideal; inside the tacet block. |
| 21 | m.103 / m.104 | Strong; complete phrase, shared breath, no ties. |
| 23 | m.109 / m.110 | Workable but fast; no tie and a textual comma. |
| 25 | m.114 / m.115 | Workable; no ties and the instruction begins on the next page. |
| 27 | m.129 / m.130 | Workable but fast; cadence complete, no ties. |
| 29 | m.139 / m.140 | Unsafe; all six parts sustain into the final texture. |
| 31 | m.151 / colophon | End of music; no live turn. |

## Priority order for the Dorico pass

1. Rebuild page 1: remove the duplicate flow title, restore subtitle,
   commission, composer, and copyright, and place opening directions in a clear
   band above system 1 while retaining exactly two systems.
2. Restore `Shadow Chorus` and `Light Chorus` as two labelled bracket/barline
   groups; enlarge full/abbreviated player labels.
3. Set lyrics to Academico 10.5 pt absolute, then run the global lyric-offset
   reset and re-export before making local lyric moves.
4. Repair page 21 lyric lanes, then page 1 lyric collisions and the continuation
   rules on pages 12, 14, 19, 23-25, and 27-31.
5. Re-space the page-20 chord row and separate `Cmaj9/E` from `subito mp` on
   page 24.
6. Balance one-system pages and recheck all right-page turns after typography
   and grouping change the vertical cast.

## Acceptance status

- **31-page system map:** pass.
- **Five-line staves / all six staves visible:** pass.
- **Page 1 exactly two systems:** pass structurally; fail typographically.
- **No blank music pages / no clipped page-edge objects:** pass.
- **Modern print-ready engraving:** fail pending the priority fixes above.
- **32-page saddle-stitch delivery:** structurally viable once the cleaned
  31-page music PDF is frozen and the nonblank colophon is appended.
