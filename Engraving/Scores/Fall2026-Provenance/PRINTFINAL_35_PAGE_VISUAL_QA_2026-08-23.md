# PrintFinal 35-page visual QA — 2026-08-23

## Audited snapshot

- Dorico project: `FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.dorico`
- Project SHA-256: `404bd65f068cb9828bb6ce32a6fc5086f2f0070814dd6355bda54b0ded0b40e4`
- Embedded-preview SHA-256: `c4f00b906bebfad58d2a63c3783e6e7efc1d506a622662f98a2e5b43f5bdcc4f`
- Preview metadata: Dorico 5.1.60.2187; generated 2026-08-22 23:55:59 CDT; 35 pages; US Letter portrait.
- Method: extracted the saved embedded preview, rendered all 35 pages at 300 dpi, and inspected every complete page plus the dense passages at measures 1–10, 43–45, 89–103, 110–118, and 130–151. No Dorico edit was made.

## Result

**Fail — materially improved cast-off, but not yet performer-ready.** The m.93
system break successfully places measures 84–92 and 93–96 as two separate
systems on page 22. The former m.101/102 mid-word turn is now a facing-page
continuation rather than a physical page turn, and measures 113–118 fit on page
29 without system-on-system contact. All six staves remain five-line and
visible, pages are nonblank, and the closing pages are clean.

The opening two pages remain unusable, several imported lyric fragments and
local collisions remain, the dense page-22 chord row still needs breathing
room, and the requested joined barlines are not present in the saved preview.
Running-title furniture is also inconsistent. The 35 music pages require the
existing nonblank page-36 colophon for saddle-stitch assembly.

## Publication blockers

| Priority | Location | Finding | Required next action |
| --- | --- | --- | --- |
| P0 | p.1, mm.1–6 | The title is struck by the boxed `1`; `Moderato`, `Begin in darkness`, the commission line, and sound directions overlap. Opening lyrics, notes, and dynamics collide in several staves. Page 1 does retain exactly two systems and the subtitle, commission, composer, and copyright text are present. | Rebuild the first-page furniture band and locally reconstruct the opening lyric/dynamic lanes without changing the two-system cast. |
| P0 | p.2, mm.7–10 | `loud;whatbinds us` is fused in the Shadow parts. The lower Light voices contain severe lyric/notation congestion, including the overlapping `Life;light;weareconnectedby` region and the closing tuplet text. | Normalize the text spacing and route each lyric-bearing voice to a stable lane. |
| P1 | p.13, mm.43–45 | `autumn` survives as isolated `-tumn`, a lone hyphen, and `as au - - - - tumn` fragments on different Light lanes. | Repair semantic syllabification and remove orphaned continuation fragments. |
| P1 | p.22, mm.93–96 | The new break works vertically, but `C(add#9)/E`, `Cm/Eb`, `Abmaj7(add#11)`, and `Ebaug(maj7)/Ab` form a cramped right-half chord row; the final symbol approaches the page edge. | Rebalance horizontal casting or make targeted chord-symbol spacing adjustments. |
| P1 | p.28, mm.110–112 | `Cmaj9/E` and `subito` still fuse as `Cmaj9/Esubito`; the nearby `mp` is cramped. | Separate the chord, instruction, and dynamic lanes. |
| P1 | p.29, mm.113–118 | `night.` presses into the Baritone S staff/slur. At m.115, dynamics collide with `Who?`/`Who` in the three Shadow staves. The aleatoric instruction itself is complete and readable. | Move the local lyric and dynamic objects after preserving the two-system page. |
| P1 | all pages | Internal measure barlines stop at each individual staff rather than joining the three staves within each chorus. The recently selected vocal-barline option is therefore not reflected in this saved preview. | Verify the global option, ensemble grouping, and saved/exported state; require group barlines within Shadow and within Light, with a gap between groups. |
| P1 | recurring | The centered running title is absent on many pages (for example pp.13, 15, 19, 21, 23, 25, 27, 29, 32, and 34) while the outside folios remain. | Remove page-template overrides or repair both left/right running-header frames. |

## Page-turn and casting notes

- **Improved:** p.24–25 now carries `car- / -ry` across a visible spread, not a
  physical page turn. The m.93 recast also removes the former right-page turn
  between `warm hands:` and `together`.
- **Unsafe:** the p.23–24 turn (m.98/99) has active sustained/hairpin material in
  the Light chorus and no shared rest. It remains the most exposed turn in the
  m.93–103 region.
- **Unsafe:** the p.27–28 turn (m.109/110) follows sustained `with love` material
  in all six staves and provides no common page-turn window.
- **Conditional:** p.29–30 (m.118/119) is part-specific rather than fully safe;
  p.31–32 (m.129/130) and p.33–34 (m.139/140) are defensible sectional turns but
  should be confirmed by a performer print test.
- Page 22 and page 29 are the only later two-system pages in this proof; both
  remain readable at Letter size after their local issues are corrected.

## Confirmed strengths

- All 35 pages were present and nonblank; no clipping was found.
- Page 1 contains exactly two systems; all other pages contain one or two.
- Six five-line staves remain visible throughout.
- `Shadow Chorus` and `Light Chorus` brackets and labels are readable.
- Core notation, lyric, direction, and label sizes are generally readable at
  print scale outside the identified local collisions.
- The m.115 and m.130 `rearticulate freely in aleatoric style` directions are
  each complete, singular, and readable.
- Pages 30–35 are stable overall. The `(Db = C#)` note, boxed m.140 and
  `shimmering polytonal sound chandelier` instruction are clear; the finale,
  `ppp`/`Hmm.` lanes, rests, and final barlines are clean.

## Recommended correction order

1. Repair pages 1–2.
2. Make the chorus group barlines and running headers systemic and verify a new
   saved preview.
3. Clean pp.13, 22, 28, and 29 locally.
4. Recheck the p.23–24 and p.27–28 turns in printed spreads.
5. Re-export and repeat the 35-page visual pass before appending/auditing the
   nonblank page-36 colophon.
