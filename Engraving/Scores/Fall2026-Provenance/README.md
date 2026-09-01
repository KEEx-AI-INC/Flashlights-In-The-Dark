# Fall 2026 Dorico engraving provenance

This folder preserves the semantic import, correction chain, casting sources,
and recoverable Dorico checkpoints for the publication-engraving pass begun on
August 22, 2026.

## Delivery status

**In progress: the final Dorico project, final Dorico MusicXML export, complete
40-page PDF, and final-delivery validation have not yet been frozen and
accepted.**

The validated 40-page MusicXML below is a layout-only casting/import source,
not the final Dorico round-trip export. The existing
`Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.dorico`
is the active working document; its filename does not make it a frozen final
deliverable. Use the explicitly named checkpoint below for recovery until the
working document has been saved, exported, visually accepted, and validated.

## Baseline files

- `FlashlightsInTheDark_Fall2026_ValidatedImport.musicxml`
  - SHA-256: `58562b931a28eb0385ba584b342bc435131104929bbe03aa83cd861cc79395ad`
  - Six parts, 151 measures per part, and 1,376 lyric coordinates.
  - Musical structure fingerprint:
    `82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111`.
- `FlashlightsInTheDark_Fall2026_ImportReport.json`
  - SHA-256: `9e3fd30e20403d4ce3122b98fc85d1b671e5c07ade14ea206b4ff09cd6b7b1dd`.
  - Records 388 matched Fall lyric replacements.
- `FlashlightsInTheDark_Fall2026_ImportValidation.json`
  - SHA-256: `6781cdc08c2f28414854b60406b95fb435abfcafa91988fafe7fcafc493f6c38`.
  - Records zero target, unchanged-lyric, or structural mismatches.
- `FlashlightsInTheDark_Fall2026_Dorico_PrePolish_2026-08-22.dorico`
  - SHA-256: `1e9be3fa52ba6e17299ffecb0286e77194170774db6b08f103330f6ef983d4c0`.
- `FlashlightsInTheDark_Fall2026_Print_PrePolish_2026-08-22.pdf`
  - SHA-256: `59c2f07311fba75ed1bd0a42938b12b28779af8e2addb81a087ff7f816c6d63d`.

## Validated Stage E semantic source

- `FlashlightsInTheDark_Fall2026_StageEClean.musicxml`
  - SHA-256: `a21c0bdce98afe6b365b641e3e5c36d45d66bbf7c222be4d325441ae2e7f06f7`.
  - Validated semantic baseline for later casting: six parts, 151 measures per
    part, 2,787 note elements, 1,376 lyric anchors, all 388 approved Fall
    replacements, and the canonical musical fingerprint
    `82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111`.
- `FlashlightsInTheDark_Fall2026_StageECleanupReport.json`
  - SHA-256: `43882f5a4bf0cadaebed85fdd4c9f6b624edcdc8e8387c39b54b1cb996e4d613`.
  - Records a passing Stage E validation, the retained provenance chain, the
    logged direction repairs, and removal of three exact duplicate ensemble
    instructions without changing musical content.

## Validated 40-page publication cast

The selected profile contains 42 systems on 39 nonblank Dorico music pages,
with two systems on pages 1, 2, and 31, followed by the preserved nonblank
page-40 colophon. This source and its reports validate the proposed cast; they
do not substitute for visual acceptance of the final Dorico engraving.

- Upstream validated source:
  `FlashlightsInTheDark_Fall2026_Dorico32PageCasted.musicxml`
  - SHA-256: `28eaade134594b196efd38d1d1f5a40504ba12176aaa373046ee6e0a3567b844`.
- Publication-cast plan: `FALL_2026_40_PAGE_PUBLICATION_CAST.md`
  - SHA-256: `51ec2011270143340067bc84790ce61df3b118fe52135449718991d9b549c2ed`.
- Validated 40-page Dorico import source:
  `FlashlightsInTheDark_Fall2026_Dorico40PageCasted.musicxml`
  - SHA-256: `13100f95f471ef52e23bee1db91784cb2d6a5794e88f73c5a621fd964bb65827`.
- Casting report: `FlashlightsInTheDark_Fall2026_40PageCastingReport.json`
  - SHA-256: `0204c63c3329058aa6c857a89766d470cc09fc72c6b46fbe4121e8637f167ebc`.
- Semantic validation:
  `FlashlightsInTheDark_Fall2026_40PageSemanticValidation.json`
  - SHA-256: `c7a048d79980e48b2dfaf0603bca8f55a7e01227e85d2b5c95194318a5464a9b`.
  - Passed exact musical, lyric/routing, five-line-staff, direction, dynamic,
    harmony, metadata, and layout-only-equivalence checks, with no unlogged
    textual difference and no runtime-asset change.
- Recoverable pre-recast Dorico checkpoint:
  `FlashlightsInTheDark_Fall2026_PerformerScore_Before40PagePublicationRecast.dorico`
  - SHA-256: `404bd65f068cb9828bb6ce32a6fc5086f2f0070814dd6355bda54b0ded0b40e4`.
  - Snapshot of the saved 35-page / 38-system working state immediately before
    the 40-page publication recast; not a final-delivery project.
- Preserved colophon: `FlashlightsInTheDark_Fall2026_Page40_Colophon.pdf`
  - SHA-256: `b0733166639d6c9f98c292d5bcd04e6be8ae147a017e7fe1593480c151cd2203`.
  - One nonblank Letter page to append after the 39 accepted music pages; do
    not synthesize it as an empty Dorico or MusicXML page.

## Correction records

- Human-readable master log:
  `Documentation/Project-Management/FALL_2026_ENGRAVING_CORRECTIONS.md`
  - SHA-256: `395fdc5ab439f2ed734d8baeac129450bfd9549434c4dd3123e1cb2762c29da5`.
  - Indexes the 60 pre-import lyric corrections and eight later direction,
    spelling, fragment, and duplicate-object corrections.
- Detailed lyric inventory:
  `Documentation/Project-Management/FALL_2026_LYRIC_CORRECTIONS.md`
  - SHA-256: `15f8de2492ff79f4f135362e682d9e90f62a96862f53b17e033eebbbc81a239b`.
- Machine-readable lyric correction report:
  `FlashlightsInTheDark_Fall2026_TextCorrectionReport.json`
  - SHA-256: `9fccf7c59a23c83286acf911b8b6546a25b8db5116b9ce4c4066fec9f80f9281`.
  - Records all 60 pre-import corrections and a passing validation that
    preserves the six-part/151-measure shape, 2,787 notes, 1,376 lyric-anchor
    locations, and musical semantics.
- The later eight corrections and their Stage E validation are recorded in the
  master log and `FlashlightsInTheDark_Fall2026_StageECleanupReport.json` above.

## Pending final outputs

These paths are reserved for the accepted delivery but are not final merely
because a working file or report template exists:

- Dorico project (pending final freeze):
  `Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.dorico`.
- MusicXML (pending final Dorico export):
  `Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.musicxml`.
- Performer-score PDF (pending assembly of 39 accepted music pages plus the
  preserved colophon):
  `Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.pdf`.
- PDF assembly audit (pending):
  `FlashlightsInTheDark_Fall2026_FinalPdfAssemblyReport.json`.
- Final semantic/PDF validation (pending):
  `FlashlightsInTheDark_Fall2026_FinalValidation.json` and
  `FlashlightsInTheDark_Fall2026_FinalValidation.md`.
- Validation report shell: `FINAL_DELIVERY_VALIDATION_TEMPLATE.md`
  - SHA-256: `3ea3da0d6f76f34194bb1347385e768e215a3c9d6a3b8678d71289786bd4c7ff`.
  - This template deliberately reports `PENDING`; replace it only with
    validator-generated results from the frozen final MusicXML and complete
    40-page PDF.

## Editorial authority

Lyrics are governed by
`Documentation/Project-Management/FALL_2026_WORKING_TEXT.md`. Notes, rhythms,
measure structure, and cue timing remain governed by the canonical v26 musical
fingerprint. Engraving-only changes must not trigger edits to show-control or
runtime assets.
