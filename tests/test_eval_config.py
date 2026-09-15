from __future__ import annotations

import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR_CASES = REPOSITORY_ROOT / "tests" / "apple-photos-curator.behavior.json"
BENCHMARK_CONFIG = REPOSITORY_ROOT / "evals" / "plugin-eval-benchmark.json"


class EvalConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.behavior = json.loads(BEHAVIOR_CASES.read_text(encoding="utf-8"))
        self.benchmark = json.loads(BENCHMARK_CONFIG.read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
