# Apple Photos Curator

[中文](README.zh-CN.md) | English

Apple Photos Curator is a Codex Skill for safe, evidence-based Apple Photos organization. It audits first, designs a dry-run plan second, and applies only approved changes in small batches. Its purpose is to organize albums and folders without guessing GPS corrections, exposing hidden media, or deleting media accidentally.

This repository is a generic, privacy-safe public package. It contains no photos, Photos databases, thumbnails, OCR exports, precise coordinates, deletion manifests, or user-specific reports.

## Use cases

Use this Skill for:

- **Album and folder design:** plan a shallow structure by place, time, people, source, media type, and review state.
- **Travel and place organization:** group recurring visits, trip batches, cities, and meaningful small places while keeping weak evidence in a review queue.
- **GPS anomaly triage:** compare country, city, timestamps, nearby assets, and visible context; never rewrite GPS just because a map label looks implausible.
- **Hidden and private media:** preserve hidden state and separate sensitive material; only consider an unhide–organize–rehide round trip after explicit authorization and system authentication.
- **Screenshots, documents, and QR codes:** separate reference material, cards, important information, interesting items, and manual-review candidates. Missing OCR or low resolution is not a deletion decision.
- **Videos and Live Photos:** classify special media using verifiable evidence instead of filenames alone.
- **External-storage deduplication:** propose deletion candidates only after byte-exact SHA-256 checks, media validity checks, album-relationship checks, visibility checks, and confirmation of a retained copy.
- **Local sync review:** inspect local Photos counts, hidden counts, and available local queues without accessing cloud services when the task is local-only.

## What it does not do automatically

These actions require separate, explicit authorization and a recoverable plan:

- modify `Photos.sqlite` or files inside the Photos Library package directly;
- rewrite GPS based only on a country, city, filename, or one photo;
- unhide media, export private thumbnails, or publish OCR text just to organize it;
- delete Photos or external-drive media based only on filename, size, duration, or visual similarity;
- bulk-remove legacy album relationships because a new view exists;
- run a batch mutation before sync stability is confirmed;
- access cloud services when the user requested local-only work.

## Recommended workflow

```text
Confirm scope
   ↓
Read-only audit (database copy + WAL/SHM)
   ↓
Dry-run organization plan (no media changes)
   ↓
User approves a specific batch
   ↓
Apply a small batch through Photos UI or PhotoKit
   ↓
Re-audit counts, hidden state, fingerprint, album relationships, and sync state
   ↓
Record changes, exclusions, deletions, and next steps
```

Report album-relationship changes separately from media changes. Adding an asset to an album adds a reference; it does not copy the original media. Media deletion is always a separate approval step.

## How to use it

### 1. Prompt Codex

After the Skill has been explicitly installed in a Codex environment, start with a request such as:

```text
Use apple-photos-curator.
Audit my Apple Photos read-only and propose an album/folder plan with a dry-run.
Do not change GPS, unhide media, or delete photos; report risks and review items first.
```

Useful staged requests include:

```text
Check only travel-place duplicates, omissions, and obvious anomalies. Preserve existing album relationships.
```

```text
Apply this approved album-reference batch without deleting media, then verify counts and hidden state.
```

```text
Find external-drive duplicate candidates. List only byte-identical files with a retained Photos copy; do not delete yet.
```

This repository does not automatically install or activate the Skill on the development machine. Installation and activation remain explicit user-controlled actions.

### 2. Run the read-only audit script

The audit script copies `Photos.sqlite` and any WAL/SHM sidecars into a temporary directory, opens the copy in read-only mode, and emits only aggregate counts and a metadata fingerprint. It does not write to the Photos Library and does not read or delete original media.

```bash
cd /path/to/apple-photos-curator
mkdir -p reports
python3 skills/apple-photos-curator/scripts/audit_photos_library.py \
  --library "/path/to/Photos Library.photoslibrary" \
  --output reports/audit.json
```

The output includes `quick_check`, total/active/inactive counts, hidden count, screenshot count, video count, and an active-asset metadata fingerprint. Keep the audit JSON local; do not commit it to a public repository.

If the machine has exactly one `*.photoslibrary` under the standard Pictures directory, `--library` may be omitted. Pass it explicitly when multiple libraries exist.

### 3. Validate before publishing

```bash
python3 scripts/validate_skill.py .

python3 skills/apple-photos-curator/scripts/validate_skill.py \
  skills/apple-photos-curator

python3 /path/to/skill-creator/scripts/quick_validate.py \
  skills/apple-photos-curator

python3 skills/apple-photos-curator/scripts/scan_release_privacy.py .
python3 -m py_compile skills/apple-photos-curator/scripts/*.py
```

The root validator enforces the shared Chicogong repository contract and the behavior-case schema. The Skill-local validator and privacy scanner remain product-owned gates. The privacy scanner rejects common local paths, email addresses, UUIDs, precise coordinates, tokens, and sensitive-file patterns. These checks do not replace human review or prove live agent behavior.

## Organization principles

### Albums and folders

- Keep primary browsing paths shallow and use durable dimensions: time/events, places/trips, people, sources, screenshots/documents, favorites, and review queues.
- Keep source and import history for provenance; do not make it the only browsing hierarchy.
- Use a folder when it owns several meaningful child albums; do not manufacture empty albums to fill an iOS four-tile cover.
- Preserve legacy albums until a new cross-cutting view has been checked; retire old structure only after coverage verification and approval.
- Split recurring cities or campuses by non-overlapping visit periods when the evidence and browseability justify it. Create a small-place album only when its photos, context, and location evidence are stable.

### Hidden, private, and low-quality media

- Treat hidden state as a privacy boundary, not an organization obstacle; keep it hidden by default.
- Treat old-camera quality, low resolution, blur, and missing OCR as review signals, not deletion criteria.
- Keep cards, identity documents, QR codes, account information, and private people photos separate from ordinary memory albums.
- For any unhide–organize–rehide plan, freeze an exact local manifest first, then verify the manifest and hidden count after the operation.

### Duplicates and external drives

An external file is only a deletion candidate after all of the following are true:

1. It has a byte-exact SHA-256 match to a retained copy;
2. The file is readable and its type and duration are consistent;
3. Photos album relationships, hidden state, and important flags are checked;
4. The retained copy is accessible and its recovery path is recorded;
5. The exact candidate list is shown again and explicitly approved before deletion.

## Repository layout

```text
.
├── README.md                         # English repository guide
├── README.zh-CN.md                   # Chinese repository guide
├── LICENSE
├── SECURITY.md                       # Private vulnerability-reporting policy
├── .skill-studio.json                # Studio-managed file boundary
├── .github/workflows/validate.yml    # Product-owned combined CI
├── scripts/validate_skill.py         # Studio-managed repository contract
├── tests/
│   └── apple-photos-curator.behavior.json  # Behavior cases, not fixed response text
└── skills/apple-photos-curator/
    ├── SKILL.md                      # Skill entrypoint and core workflow
    ├── agents/openai.yaml             # Codex UI metadata
    ├── references/
    │   ├── album-design.md            # Album naming, split, and folder-depth rules
    │   └── safety-gates.md            # Authorization, baseline, mutation, and acceptance gates
    └── scripts/
        ├── audit_photos_library.py   # Read-only aggregate audit
        ├── scan_release_privacy.py    # Release privacy scanner
        └── validate_skill.py          # Portable Skill structure validator
```

The Skill package intentionally contains no README, photos, database copies, reports, or installation scripts. Those belong to the repository guides or to the user's controlled local environment.

Skill Studio manages only the root `scripts/validate_skill.py` declared in `.skill-studio.json`. This repository owns its workflow and product-specific checks; a Studio upgrade must not overwrite them.

## Acceptance criteria

An organization round is complete only when all applicable checks pass:

- database `quick_check` is healthy;
- media counts and the active-media fingerprint match the intended album-only or approved mutation scope;
- hidden count has not changed without authorization;
- protected album relationships remain intact;
- target album references are complete and the idempotent dry-run reports no unintended work;
- local sync state is stable;
- changes, exclusions, deletions, and unresolved items are recorded clearly.

Stop and re-audit if any count, fingerprint, hidden-state, or album-relationship drift cannot be explained.

## License

MIT.
