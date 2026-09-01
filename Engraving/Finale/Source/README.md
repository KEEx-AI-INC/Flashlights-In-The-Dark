# Active Finale source handoff

The active Fall 2026 SingerScore baseline is maintained in the canonical
MusicXML score:

`../../Scores/FlashlightsInTheDark_v26_NewerScoreWithFewerParts.musicxml`

This folder intentionally does not contain a competing active `.musx` score.
Historical Finale source files live in `Source_Archive/` and must remain
unchanged. When a Finale working file is needed, create it deliberately from
the approved MusicXML baseline or from a documented archival recovery, give it
a Fall 2026-specific name, and keep it outside `Source_Archive/`.

## v35 meter reference

For the currently saved v35 Finale working score, use
`FlashlightsInTheDark_v35_meter-map.musicxml` as the authoritative MusicXML
reference for meter mapping. Its documented measure boundaries are in
`METER_MAP_v35.md`. This reference supersedes older meter assumptions only; it
does not supersede the established text or layout sources.

Before changing text, read
`../../../Documentation/Project-Management/FALL_2026_WORKING_TEXT.md`. The
Fall text preserves 88 stable cue IDs; do not use this cleanup to modify
generated event recipes or runtime assets.
