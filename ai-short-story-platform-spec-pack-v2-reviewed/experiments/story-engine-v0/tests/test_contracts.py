import unittest

from story_v0.contracts import EvalCase, SystemVariant


class ContractTests(unittest.TestCase):
    def test_eval_case_requires_hard_constraints(self):
        case = EvalCase(
            id="mystery-001",
            premise="Một tài xế taxi đón một hành khách đã chết từ mười năm trước.",
            target_words=3000,
            genre="Mystery",
            hard_constraints=(
                "Danh tính hành khách chỉ được hé lộ ở phần ba cuối.",
            ),
        )
        self.assertEqual(case.target_words, 3000)
        self.assertEqual(SystemVariant.STRUCTURED_C.value, "structured_c")

    def test_eval_case_rejects_empty_hard_constraints(self):
        with self.assertRaises(ValueError):
            EvalCase(
                id="invalid",
                premise="Một ý tưởng.",
                target_words=3000,
                genre="Mystery",
                hard_constraints=(),
            )

