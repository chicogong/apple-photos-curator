# Apple Photos Safe Organizer

A privacy-safe Codex Skill for planning and validating non-destructive organization changes in macOS Apple Photos.

## What it covers

- read-only Photos database audits with WAL/SHM preservation
- dry-run album and folder planning
- recurring-place and trip split rules
- GPS anomaly triage without guessing corrections
- hidden-media and sensitive-document boundaries
- exact duplicate gates for external storage
- post-change integrity and local sync checks
- release-time privacy scanning

## Skill payload

The installable Skill is in [`skills/apple-photos-safe-organizer-skill/`](skills/apple-photos-safe-organizer-skill/), with [`SKILL.md`](skills/apple-photos-safe-organizer-skill/SKILL.md) as its entrypoint.

## Included tools

- [`audit_photos_library.py`](skills/apple-photos-safe-organizer-skill/scripts/audit_photos_library.py) — aggregate, read-only audit from a copied Photos database
- [`scan_release_privacy.py`](skills/apple-photos-safe-organizer-skill/scripts/scan_release_privacy.py) — reject common personal-data and secret patterns
- [`validate_skill.py`](skills/apple-photos-safe-organizer-skill/scripts/validate_skill.py) — portable Skill structure check

The package intentionally contains no photos, database copies, thumbnails, OCR exports, GPS manifests, or user-specific reports.

This repository does not install or activate the Skill on the development machine; the payload is provided for explicit, user-controlled installation elsewhere.

## Safety model

Analyze first. Show a dry-run. Apply through Photos UI or PhotoKit only. Verify counts, hidden state, protected memberships, and sync status afterward. Media deletion is a separate, explicitly approved phase.

## License

MIT.
