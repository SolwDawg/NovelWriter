from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "services" / "ai-worker" / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "contracts" / "python"))

from story_platform_contracts import (  # noqa: E402
    CONTRACT_NAMES,
    CONTRACT_SCHEMA_VERSION,
    AIArtifactRef,
    AIUsage,
    SceneDocumentArtifact,
    ScenePlan,
    StoryBlueprint,
    StoryIntent,
    StoryState,
    StoryStateDelta,
)


class ContractSmokeTests(unittest.TestCase):
    def test_generated_python_equivalent_imports_for_all_contracts(self) -> None:
        self.assertEqual(CONTRACT_SCHEMA_VERSION, 1)
        self.assertEqual(
            CONTRACT_NAMES,
            (
                "StoryIntent",
                "StoryBlueprint",
                "ScenePlan",
                "SceneDocumentArtifact",
                "StoryState",
                "StoryStateDelta",
                "AIArtifactRef",
                "AIUsage",
            ),
        )

        fixture = json.loads(
            (
                REPO_ROOT
                / "packages"
                / "contracts"
                / "fixtures"
                / "story-contracts.json"
            ).read_text(encoding="utf-8")
        )
        contract_types = (
            StoryIntent,
            StoryBlueprint,
            ScenePlan,
            SceneDocumentArtifact,
            StoryState,
            StoryStateDelta,
            AIArtifactRef,
            AIUsage,
        )
        fixture_keys = (
            "story_intent",
            "story_blueprint",
            "scene_plan",
            "scene_document_artifact",
            "story_state",
            "story_state_delta",
            "ai_artifact_ref",
            "ai_usage",
        )
        for contract_type, fixture_key in zip(contract_types, fixture_keys):
            self.assertIn("schema_version", contract_type.__annotations__)
            self.assertEqual(fixture[fixture_key]["schema_version"], 1)
