import tempfile
import unittest
from pathlib import Path

from story_v0.contracts import SystemVariant
from story_v0.eval_runner import load_cases, run_case, write_suite


class EvalRunnerTests(unittest.TestCase):
    def test_run_case_public_interface(self):
        case = load_cases()[0]
        result = run_case(case, SystemVariant.STRUCTURED_QA_D)
        self.assertEqual(result.case_id, case.id)
        self.assertEqual(result.variant, SystemVariant.STRUCTURED_QA_D)
        self.assertTrue(result.metrics["schema_valid"])
        self.assertEqual(result.metrics["required_outcome_pass_rate"], 1.0)

    def test_write_suite_emits_machine_and_blind_review_outputs(self):
        cases = load_cases()[:1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            results = write_suite(
                cases,
                [SystemVariant.BASELINE_A, SystemVariant.STRUCTURED_C],
                output,
            )
            self.assertEqual(len(results), 2)
            self.assertTrue((output / "summary.jsonl").exists())
            self.assertTrue((output / "summary.csv").exists())
            self.assertTrue((output / "aggregate.json").exists())
            review_files = [path.name for path in (output / "human-review").glob("*.txt")]
            self.assertEqual(len(review_files), 2)
            self.assertTrue(all("baseline" not in name for name in review_files))
            self.assertTrue(all("structured" not in name for name in review_files))

    def test_structured_variants_satisfy_all_fixture_hard_checks(self):
        cases = load_cases()
        for variant in (SystemVariant.STRUCTURED_C, SystemVariant.STRUCTURED_QA_D):
            with self.subTest(variant=variant):
                results = [run_case(case, variant) for case in cases]
                self.assertTrue(all(result.metrics["schema_valid"] for result in results))
                self.assertTrue(
                    all(result.metrics["locked_canon_pass"] for result in results)
                )
                self.assertTrue(
                    all(result.metrics["required_outcome_pass_rate"] == 1.0 for result in results)
                )
                self.assertTrue(
                    all(result.metrics["state_extractor_f1"] == 1.0 for result in results)
                )
