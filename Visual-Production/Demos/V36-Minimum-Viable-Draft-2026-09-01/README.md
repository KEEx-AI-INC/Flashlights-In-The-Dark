# V36 Minimum-Viable Light-Show Draft — September 1, 2026

This directory records the first full-duration light-show proof the composer
has designated a minimum-viable draft. It is a review and authoring milestone,
not a runtime-ready or performance-approved release.

## What the video proves

- 59 anonymous choir positions fit inside the four-row shell layout.
- The design models 30 primary musical phones and six normally dark reserves.
- Fifteen right-stage routes operate before measure 104.
- An 833.333 ms all-dark window separates the two routing phases.
- From measure 104 onward, 12 left-stage and 12 right-stage routes redistribute
  light across both halves of the ensemble.
- Light remains strictly gated by V36 note activity. Decorative texture cannot
  illuminate a routed group outside its sounding intervals.
- Shadow and Light lyric panels and role-only conductor/technology-operator
  markers remain visible.
- The audio is copied without alteration from the locally accepted normal-
  primer, piano, and electronics proof.

## Provenance

The renderer is `Operations/Scripts/render_v36_mvp_public_video.py`. Its score
and behavior inputs are:

- `Engraving/Scores/FlashlightsInTheDark_v36_FinaleExport_2026-08-29.musicxml`
- `Engraving/Score-Study/FlashlightsInTheDark_v36_LightChorusNoteActivity.json`
- `Engraving/Score-Study/FlashlightsInTheDark_v36_ShadowChorusNoteActivity.json`
- `Show-Control/Topology/FlashlightsInTheDark_v36_36PhoneTopology.json`
- the two JSON manifests in `Manifests/`

The accepted local proof displayed performer names. Repository policy prohibits
committing those identifiers, so this public-safe equivalent uses anonymous
spots while preserving timing, layout, route assignments, gating, lyrics,
audio, and decorative behavior. Exact checksums and decode evidence are stored
in the render manifest.

## Safety boundary

`runtimeEligible` is false. Nothing in this directory is copied into the
conductor or singer applications, and this milestone does not rearm either
runtime. See
`Documentation/Project-Management/V36_LIGHT_SHOW_MVP.md` for remaining gates.
