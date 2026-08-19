---
name: apple-photos-curator
description: Audit, design, and safely apply organization changes to a macOS Apple Photos library. Use for album and folder taxonomy, recurring-place or trip albums, GPS anomaly triage, screenshot and video review, hidden-media handling, exact duplicate checks, external-drive comparison, iCloud sync verification, or any request where Photos media must not be lost. Require dry-runs, read-only database analysis, PhotoKit-based writes, privacy-safe reports, and post-change integrity checks.
---

# Apple Photos Curator

Organize Apple Photos without treating metadata guesses as truth or album cleanup as permission to delete media.

## Start with the safety boundary

1. Identify the active `.photoslibrary` package and the user's requested scope.
2. Treat the Photos library as the media source of truth only when the user confirms that role.
3. Inspect databases from a temporary copy that includes WAL and SHM sidecars. Never write directly to `Photos.sqlite`.
4. Use PhotoKit or Photos UI for mutations. Do not mutate Photos databases, package contents, or iCloud state directly.
5. Keep hidden media hidden unless the user explicitly requests a reviewed round trip and completes system authentication.
6. Do not access cloud services when the user requests local-only work.

Run `scripts/audit_photos_library.py` for a privacy-safe aggregate baseline. Read [references/safety-gates.md](references/safety-gates.md) before any mutation.

## Separate analysis from mutation

Produce a dry-run before structural or batch changes. Show:

- current and proposed album paths;
- target, current, add, remove, and media-delete counts;
- selection evidence and known ambiguities;
- hidden, screenshot, recently deleted, and cloud-deleted exclusions;
- whether existing album relationships remain intact;
- rollback or recovery path.

Do not imply that adding an asset to several albums duplicates the original file. Album membership is a reference.

## Choose the workflow

### Album and folder organization

- Prefer a shallow browse structure with durable dimensions such as time/events, people, places/trips, sources, screenshots/documents, favorites, and review queues.
- Keep source/import history as provenance, not the primary browsing hierarchy.
- Use real albums only. Do not create placeholders for folder cover tiles.
- If an iOS folder has fewer than four meaningful child albums, consider removing the folder level instead of manufacturing empty albums.
- Preserve old memberships while adding a new cross-cutting view unless the user explicitly approves retirement after coverage verification.
- Read [references/album-design.md](references/album-design.md) for naming and split rules.

### Places, trips, and GPS

- Treat GPS as evidence, not authority. Validate it against time, nearby assets, visible landmarks, local reverse-location data, and the user's known travel history.
- Never rewrite GPS solely because a country or city looks implausible.
- Split recurring cities by visit period; create place-memory albums only for stable, meaningful locations.
- Merge adjacent coordinate clusters before naming a place. Exclude transit, generic streets, and one-off weak clusters.
- Keep a review queue for ambiguous locations. Do not force every asset into a named place.

### Duplicates and external storage

- A matching filename, size, duration, or visual appearance is not deletion proof.
- Require byte-exact SHA-256 identity against an accessible Photos original or another retained canonical copy.
- Verify media validity, album coverage, hidden/private status, and recovery path before deleting an external copy.
- Stage deletion candidates for review, recheck the exact target list, then delete only the verified subset.
- Never infer that an external disk is redundant as a whole.

### Hidden and private media

- Never unhide media merely to organize it.
- Do not export hidden thumbnails, OCR text, precise GPS, document contents, or asset identifiers into a public report.
- If the user requests an unhide-organize-rehide workflow, freeze an exact local manifest first, require user authentication, add the intended album relationship, verify it, rehide the same items, and confirm the hidden count and manifest match.

### Screenshots, low-quality media, and videos

- Treat low resolution and old-camera quality as review signals, not deletion criteria.
- Separate meaningful memories from low-value review candidates using local-only OCR or visual contact sheets.
- Keep sensitive documents, cards, credentials, and QR codes out of ordinary public-facing albums.
- Classify videos from content evidence when practical; do not infer theme, time, or location from filename alone.

## Apply guarded changes

Before applying:

1. Confirm database `quick_check=ok`.
2. Capture aggregate asset counts, hidden count, and a deterministic active-asset metadata fingerprint.
3. Confirm local Photos sync queues are stable when available.
4. Confirm every target exists, is active, and satisfies the visibility rules for the destination.
5. Confirm removal and media deletion counts are exactly what the user approved.

Apply the smallest reversible unit. Add memberships in bounded batches. Separate album cleanup from media deletion.

## Verify completion

After applying:

1. Wait for the library to stabilize.
2. Re-run `quick_check`, aggregate counts, hidden count, fingerprint, and sync checks.
3. Verify exact target membership and preservation of protected albums.
4. Re-run the dry-run and require zero remaining additions or unintended removals.
5. Report album changes separately from media changes.
6. Record what was changed, excluded, deleted, and left for manual review.

Stop and investigate if counts, fingerprint, hidden state, or protected memberships drift unexpectedly.

## Keep published artifacts private-safe

Run `scripts/scan_release_privacy.py <skill-or-repository-path>` before committing anything intended for sharing. Public artifacts must not contain:

- personal names, home paths, addresses, private album titles, asset UUIDs, precise GPS, OCR transcripts, or private filenames;
- credentials, tokens, email addresses, phone numbers, or cloud account identifiers;
- local reports, thumbnails, database copies, photo originals, or deletion manifests.

Publish reusable rules and generic code only. Keep task-specific evidence local and ignored by Git.
