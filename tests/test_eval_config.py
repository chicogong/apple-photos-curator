from __future__ import annotations

import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR_CASES = REPOSITORY_ROOT / "tests" / "apple-photos-curator.behavior.json"
BENCHMARK_CONFIG = REPOSITORY_ROOT / "evals" / "plugin-eval-benchmark.json"
RUNTIME_SMOKE_RESULT = (
    REPOSITORY_ROOT / "evals" / "results" / "2026-09-15-runtime-smoke.json"
)


class EvalConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.behavior = json.loads(BEHAVIOR_CASES.read_text(encoding="utf-8"))
        self.benchmark = json.loads(BENCHMARK_CONFIG.read_text(encoding="utf-8"))
        self.runtime_smoke = json.loads(RUNTIME_SMOKE_RESULT.read_text(encoding="utf-8"))

    def test_benchmark_covers_every_behavior_case(self) -> None:
        behavior_ids = {case["id"] for case in self.behavior["cases"]}
        benchmark_ids = {scenario["id"] for scenario in self.benchmark["scenarios"]}
        self.assertEqual(benchmark_ids, behavior_ids)

    def test_benchmark_preserves_isolation_and_read_only_policy(self) -> None:
        self.assertEqual(self.benchmark["kind"], "plugin-eval-benchmark")
        self.assertEqual(self.benchmark["schemaVersion"], 2)
        self.assertEqual(self.benchmark["targetKind"], "skill")
        self.assertEqual(self.benchmark["targetName"], self.behavior["skill"])
        self.assertEqual(self.benchmark["runner"]["type"], "codex-cli")
        self.assertEqual(self.benchmark["runner"]["sandbox"], "read-only")
        self.assertEqual(self.benchmark["runner"]["approvalPolicy"], "never")
        self.assertEqual(self.benchmark["workspace"]["setupMode"], "copy")
        self.assertEqual(self.benchmark["workspace"]["sourcePath"], ".")
        self.assertEqual(self.benchmark["targetProvisioning"]["mode"], "isolated-skill-home")

    def test_every_scenario_has_observable_semantic_checks(self) -> None:
        for scenario in self.benchmark["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                self.assertGreaterEqual(len(scenario["successChecklist"]), 3)
                self.assertGreaterEqual(len(scenario["userInput"]), 40)

    def test_runtime_smoke_result_matches_the_benchmark_matrix(self) -> None:
        self.assertEqual(self.runtime_smoke["kind"], "skill-runtime-smoke-result")
        self.assertEqual(self.runtime_smoke["schemaVersion"], 1)
        self.assertEqual(self.runtime_smoke["target"]["name"], self.behavior["skill"])
        benchmark_ids = [scenario["id"] for scenario in self.benchmark["scenarios"]]
        result_ids = [scenario["id"] for scenario in self.runtime_smoke["scenarios"]]
        self.assertEqual(result_ids, benchmark_ids)

    def test_runtime_smoke_pass_requires_complete_observed_evidence(self) -> None:
        summary = self.runtime_smoke["summary"]
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["completedScenarios"], len(self.benchmark["scenarios"]))
        self.assertEqual(summary["failedScenarios"], 0)
        self.assertEqual(summary["semanticChecksPassed"], summary["semanticChecksTotal"])
        self.assertEqual(summary["routingChecksPassed"], summary["routingChecksTotal"])
        self.assertEqual(summary["verifierFailCount"], 0)
        self.assertEqual(summary["workspaceChangedFileCount"], 0)
        self.assertGreater(summary["observedCommandExecutions"], 0)

        for scenario in self.runtime_smoke["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                self.assertEqual(
                    scenario["semanticChecksPassed"], scenario["semanticChecksTotal"]
                )
                self.assertEqual(scenario["verifiersPassed"], len(self.benchmark["verifiers"]["commands"]))
                self.assertEqual(scenario["workspaceChangedFileCount"], 0)

    def test_runtime_smoke_score_is_reproducible_from_breakdown(self) -> None:
        breakdown = self.runtime_smoke["scoreBreakdown"]
        earned = sum(dimension["earned"] for dimension in breakdown.values())
        possible = sum(dimension["possible"] for dimension in breakdown.values())
        self.assertEqual(possible, 100)
        self.assertEqual(earned, self.runtime_smoke["summary"]["score"])


if __name__ == "__main__":
    unittest.main()
