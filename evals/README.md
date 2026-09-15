# Skill runtime evaluation

This directory contains the reviewed configuration and privacy-safe results for an independent Codex CLI forward test. It follows OpenAI's `plugin-eval` pattern: real `codex exec` sessions, an isolated temporary workspace and Codex home, captured event logs, deterministic verifier commands, and a human-reviewed success checklist.

The configuration is an executable plan. A dated file under `results/` is evidence only for the exact target, runner, model, policy, and scope it records.

## Preflight

Before execution, record:

- the exact `openai/plugins` revision supplying `plugin-eval`;
- the Codex CLI and model versions;
- the command, sandbox, approval policy, workspace source, and target-provisioning mode;
- whether credentials, network, host services, or user data are reachable;
- the expected usage cost and artifact-retention policy.

The current matrix intentionally uses `read-only`, `approvalPolicy: never`, a copied workspace, an isolated temporary Codex home, and no real Photos paths or data. Do not widen those fields without a new review.

## Run shape

From the repository root, with a reviewed local checkout of OpenAI's `plugin-eval`:

```bash
node /path/to/openai-plugins/plugins/plugin-eval/scripts/plugin-eval.js \
  benchmark skills/apple-photos-curator \
  --config evals/plugin-eval-benchmark.json \
  --format json
```

Generated run artifacts live below `skills/apple-photos-curator/.plugin-eval/` and are ignored by Git. Preserve failed workspaces for diagnosis; otherwise keep only a privacy-reviewed summary if evidence needs to be recorded.

## Grade the result

For each scenario, inspect the final message and event log against every `successChecklist` item. A zero exit code and passing repository verifiers mean only that the run completed and did not break the copied workspace; they do not prove semantic success.

Record separately:

- invocation or non-invocation behavior;
- required and forbidden tool calls;
- unsupported claims or fabricated completion;
- repository verifier results;
- input, output, and total tokens when available;
- runtime, retries, and required human correction.

Only mark `runtime_smoke` passed after all five scenarios have observed evidence and no safety-boundary failure. A later quality benchmark should repeat the same prompt and configuration before and after changes rather than comparing different tasks.

The first reviewed smoke result is recorded in `results/2026-09-15-runtime-smoke.md`, with a machine-readable companion JSON file. It also documents why raw event logs must be checked independently of aggregate tool-count telemetry.

Primary references:

- <https://github.com/openai/plugins/tree/main/plugins/plugin-eval>
- <https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md>
