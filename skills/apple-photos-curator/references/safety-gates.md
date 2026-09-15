# Safety gates

## Authority levels

| Request | Allowed by default | Requires explicit approval |
|---|---|---|
| Audit or review | Read copied databases, aggregate, render local review artifacts | Any Photos mutation |
| Organize or build | Add or move album references within the requested scope | Media deletion, metadata rewrite, unhide/rehide |
| Diagnose GPS or sync | Read local metadata and queues | GPS rewrite, library repair, cloud account changes |
| Deduplicate | Hash and stage candidates | Delete Photos, device, cloud, or external-drive copies |

## Baseline

Capture before every mutation:

- copied-database `PRAGMA quick_check`;
- total, active, inactive, hidden, screenshot, photo, and video counts when available;
- deterministic hash of active asset metadata ordered by a stable database key;
- protected album membership hashes or exact sets;
- relevant local sync queue counts;
- intended additions, removals, and media deletions.

Do not persist raw UUIDs, OCR text, precise coordinates, or original paths in a public report.

## Mutation rules

- Use Photos UI or a correctly entitled PhotoKit application.
- Never write Photos SQLite databases directly.
- Add references before considering removal of legacy album references.
- Batch large membership operations and wait for library stabilization.
- Keep media deletion in a separate, explicitly approved phase.
- Do not bypass Touch ID, password prompts, or macOS privacy controls.
- Before an approved unhide-organize-rehide operation, freeze an exact local manifest; afterward, rehide the same items and verify both the manifest and hidden count.

## Exact duplicate deletion gate

An external file becomes a deletion candidate only after:

1. SHA-256 and byte equality match an accessible retained copy;
2. media readability, type, and duration are consistent;
3. album relationships, hidden state, and protected flags are checked;
4. the retained copy and recovery location are recorded;
5. the exact deletion list is shown again and explicitly approved.

Keep grouped assets, sidecars, protected media, and any uncertain match on HOLD.

## Acceptance

Require all applicable checks:

- database integrity remains `ok`;
- media counts and metadata fingerprint remain unchanged for album-only work;
- hidden count remains unchanged unless the exact hidden workflow was approved;
- protected memberships remain equal;
- intended targets are complete;
- idempotent dry-run reports zero remaining work;
- sync queues return to stable values;
- deletion reports include exact scope and recovery location.

Any unexplained drift is a failed verification, not a cosmetic warning.
