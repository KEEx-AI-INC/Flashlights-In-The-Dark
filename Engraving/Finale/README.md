# Finale sources

`Source/` is the active authored-score handoff folder. `Source/Source_Archive/` preserves the recovered historical Finale `.musx` lineage, and `Backups/` preserves the corresponding automatic/manual Finale backup files. Filenames—including dated edition and score identifiers—are intentionally unchanged.

On 2026-08-08, the personal Finale inventory scanned 55 `.musx` files. Metadata and filename review identified 39 Flashlights/FITD files: 24 source files and 15 backups. Each was copied into this directory, byte-compared with its original, and only then removed from its prior personal location. No unrelated Finale files were moved.

## Fall 2026 baseline

`../Scores/FlashlightsInTheDark_v26_NewerScoreWithFewerParts.musicxml` is the
active authored baseline for the Fall 2026 SingerScore update. Begin score and
libretto work from that canonical score source, using the Fall 2026 working
text and its stable 88-cue map as the editorial input.

The archived `.musx` files are historical references, not competing active
sources. In particular, `Source_Archive/FlashlightsInTheDark_v11.musx` is
preserved for provenance only. Do not modify an archived file in place; copy it
to a clearly named working file only when a deliberate recovery or comparison
pass requires it.

Create MusicXML/PDF delivery artifacts in `../Scores/`; do not edit the
software runtime copies directly. After an intentional score change, regenerate
the show-control and runtime outputs through `Operations/Scripts/`.

`Source/FlashlightsInTheDark_v26_NewerScoreWithFewerParts.musicxml` is a verified copy of the canonical MusicXML source currently named by the score-reactive light-show recipe. It is retained here for engraving-side reference; `../Scores/` remains the canonical runtime source.
