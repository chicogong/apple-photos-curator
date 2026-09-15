---
name: apple-photos-curator
description: Use when users need a safe macOS Apple Photos audit, album design, trip grouping, GPS triage, hidden-media handling, duplicate checks, or sync verification. Require copied-database baselines, explicit approval before writes, privacy-safe evidence, and post-change integrity checks.
---

# Apple Photos Curator

Organize Apple Photos without treating metadata guesses as truth or album cleanup as permission to delete media.

## Route the request

1. Confirm the active `.photoslibrary`, requested scope, and whether the task is audit-only or includes approved changes.
2. For audit-only work, inspect a temporary database copy with its WAL/SHM sidecars and emit aggregate evidence only.
3. Before any change, read [references/safety-gates.md](references/safety-gates.md), capture its baseline, and present a dry-run.
4. For album structure or place grouping, also read [references/album-design.md](references/album-design.md).
5. Apply only the approved, smallest reversible batch through Photos UI or an entitled PhotoKit application.
6. Re-audit, verify the exact intended relationships, and report unresolved drift.

Run `scripts/audit_photos_library.py` for a privacy-safe aggregate baseline. It must operate on a copied database, not original media or the live database.

## Preserve hard boundaries

- Never write `Photos.sqlite`, Photos package contents, or iCloud state directly.
- Do not access cloud services when the user requests local-only work.
- Keep hidden media hidden unless the user explicitly approves the bounded workflow and completes system authentication.
- Treat GPS, filenames, timestamps, and visual similarity as evidence, not authority.
- Do not rewrite GPS from one weak signal or infer a video's subject from its filename.
- Do not delete media or external-drive files without separate approval and a recorded recovery path.
- Require SHA-256 plus byte equality before calling files exact duplicates. Keep grouped, protected, sidecar, or uncertain cases on HOLD.
- Preserve existing album relationships until retirement is explicitly approved after coverage verification.

## Make the dry-run reviewable

Report:

- current and proposed album paths;
- target, current, add, remove, and media-delete counts;
- selection evidence and ambiguities;
- hidden, screenshot, recently deleted, and cloud-deleted exclusions;
- protected relationships and recovery path;
- database integrity, aggregate counts, metadata fingerprint, and relevant sync state.

Adding an asset to an album adds a reference; it does not duplicate the original media. Keep album-reference changes separate from media deletion.

## Verify completion

After an approved batch:

1. Wait for the library to stabilize.
2. Re-run integrity, count, hidden-state, fingerprint, protected-membership, and sync checks.
3. Re-run the dry-run and require no unintended remaining changes.
4. Report album changes separately from media changes, including exclusions and manual-review items.

Stop when any count, fingerprint, hidden state, protected relationship, or sync drift cannot be explained. Keep personal evidence and generated audit artifacts local; publish generic rules and code only.
