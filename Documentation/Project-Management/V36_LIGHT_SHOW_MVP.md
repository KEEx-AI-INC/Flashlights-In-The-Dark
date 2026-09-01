# V36 Light-Show Minimum-Viable Draft

Status: composer-designated visual MVP, September 1, 2026

Runtime eligibility: **false**

## Decision

The full-duration review in
`Visual-Production/Demos/V36-Minimum-Viable-Draft-2026-09-01/` is the first
version the composer is willing to consider a minimum-viable light-show draft.
It becomes the visual and authoring baseline for the next rehearsal iteration.
It does not supersede safety gates or install a runtime show.

## Behavioral contract

- The stage has 59 anonymous singer positions. Performer names are intentionally
  absent from Git.
- Thirty phones carry musical routes and six additional phones are connected,
  normally dark hot reserves.
- Before measure 104, 15 musical routes occupy the right half of the stage.
- The redistribution uses an 833.333 ms all-dark handoff window from
  298.627686 s through 299.461020 s on the review clock.
- After measure 104, 12 routes occupy the left half and 12 routes occupy the
  right half. The remaining primary routes are deliberately dark.
- A routed device can illuminate only while its assigned V36 chorus material is
  sounding. Decorative flicker, glitter, and glow ramps are clipped to that
  note-active interval; chords and divisi use binary OR rather than brightness
  stacking.
- Six reserve positions remain visibly identifiable but dark in this proof.
- Shadow and Light lyric modules, the established normal-primer/piano/
  electronics review mix, and the conductor and technology-operator role
  markers remain present.

## Sources and privacy boundary

The committed review is regenerated from the V36 Finale MusicXML, Light and
Shadow Chorus activity JSON, deterministic decorative-texture and lyric
manifests, and the versioned 36-phone topology. The locally accepted named
proof is retained outside Git. The committed equivalent removes real performer
identifiers in accordance with repository policy while preserving the musical,
timing, audio, topology, and lighting behavior under review.

## Remaining gates

This milestone does not claim production equivalence. Before installation:

1. approve and freeze the playback master and clock anchor;
2. validate startup all-dark and atomic route ownership in the current apps;
3. rehearse 30 primaries and six reserves on physical phones;
4. prove failure, takeover, reserve exhaustion, and safe-cue failback behavior;
5. perform network, power, sightline, accessibility, and venue acceptance;
6. explicitly approve generation and installation of runtime manifests.

Legacy v26 recipes and runtime copies remain preserved but superseded for new
V36 authoring. They are not silently remapped by this decision.
