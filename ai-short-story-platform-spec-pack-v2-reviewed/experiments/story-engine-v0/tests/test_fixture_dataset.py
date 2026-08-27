import unittest

from story_v0.eval_runner import load_cases


class FixtureDatasetTests(unittest.TestCase):
    def test_dataset_has_required_bands_and_genres(self):
        cases = load_cases()
        self.assertGreaterEqual(len(cases), 30)
        self.assertEqual(
            {case.target_words for case in cases},
            {3000, 10000, 15000},
        )
        self.assertEqual(
            {case.genre for case in cases},
            {"Mystery", "Thriller", "Horror"},
        )
        for case in cases:
            self.assertGreaterEqual(len(case.continuity_traps), 2)
            self.assertTrue(case.events)
            self.assertTrue(case.required_outcomes)

