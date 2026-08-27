import unittest

from story_v0.contracts import (
    SceneBlock,
    SceneDocument,
    StateChange,
    StoryState,
    StoryStateDelta,
    SystemVariant,
)
from story_v0.eval_runner import load_cases
from story_v0.metrics import evaluate_case
from story_v0.structured_engine import DomainConflictError, StructuredStoryEngine


class StructuredEngineTests(unittest.TestCase):
    def setUp(self):
        self.case = load_cases()[0]
        self.engine = StructuredStoryEngine()

    def test_writer_returns_document_without_authoritative_delta(self):
        premise = self.engine.interpret_intent(self.case)
        blueprint = self.engine.architect(self.case, premise)
        plan = self.engine.plan_scenes(self.case, blueprint)[0]
        writer_result = self.engine.write_scene(self.case, plan, StoryState())
        self.assertIsInstance(writer_result.document, SceneDocument)
        self.assertFalse(hasattr(writer_result, "delta"))

    def test_structured_loop_commits_each_scene_and_extracts_events(self):
        run = self.engine.generate(self.case, SystemVariant.STRUCTURED_C)
        self.assertTrue(run.schema_valid)
        self.assertEqual(len(run.committed_scene_ids), 5)
        self.assertEqual(run.final_state.scene_index, 5)
        self.assertEqual(
            set(run.extracted_event_ids),
            {event.id for event in self.case.events},
        )
        self.assertEqual(run.final_state.resolved_threads, ["passenger-01"])
        for document in run.documents:
            self.assertEqual(
                len({block.id for block in document.blocks}),
                len(document.blocks),
            )

        metrics = evaluate_case(self.case, run)
        self.assertTrue(metrics["locked_canon_pass"])
        self.assertEqual(metrics["state_extractor_f1"], 1.0)
        self.assertEqual(metrics["required_outcome_pass_rate"], 1.0)

    def test_non_extractor_delta_is_rejected_at_domain_boundary(self):
        state = StoryState()
        delta = StoryStateDelta(
            scene_id="scene-001",
            changes=(
                StateChange(
                    path="facts.secret",
                    value="forged",
                    event_id="bad-event",
                ),
            ),
            proposed_by="scene_writer",
        )
        with self.assertRaises(DomainConflictError):
            self.engine.commit_delta(
                state,
                delta,
                expected_version=0,
                scene_index=1,
                canon_facts=(),
            )

    def test_locked_canon_contradiction_fails_validation(self):
        premise = self.engine.interpret_intent(self.case)
        blueprint = self.engine.architect(self.case, premise)
        plan = self.engine.plan_scenes(self.case, blueprint)[0]
        document = SceneDocument(
            scene_id=plan.scene_id,
            revision=1,
            blocks=(
                SceneBlock(
                    id="bad-block",
                    type="narration",
                    text="Minh giữ chiếc đồng hồ bạc.",
                ),
            ),
        )
        delta, _ = self.engine.extract_state_delta(
            self.case, plan, document, StoryState()
        )
        validation = self.engine.validate_candidate(self.case, plan, document, delta)
        self.assertFalse(validation.passed)
        self.assertIn("locked canon contradiction: watch-owner-01", validation.errors)

