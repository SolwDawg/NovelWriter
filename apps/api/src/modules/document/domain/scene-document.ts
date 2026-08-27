import type { SceneDocumentArtifact } from "@story-platform/contracts";
import { StoryDomainError } from "../../story/domain/errors.js";

export function assertSceneDocument(document: SceneDocumentArtifact): void {
  if (document.schema_version !== 1 || document.revision < 1 || !document.scene_id) {
    throw new StoryDomainError(
      "INVALID_SCENE_COMMIT",
      "scene document has an invalid schema version, revision, or scene ID",
    );
  }

  const blockIds = document.blocks.map((block) => block.id);
  if (
    blockIds.length === 0 ||
    blockIds.some((id) => !id) ||
    new Set(blockIds).size !== blockIds.length
  ) {
    throw new StoryDomainError(
      "INVALID_SCENE_COMMIT",
      `scene ${document.scene_id} must contain unique stable block IDs`,
    );
  }
}

export function sceneText(document: SceneDocumentArtifact): string {
  assertSceneDocument(document);
  return document.blocks
    .map((block) => block.text)
    .filter(Boolean)
    .join("\n");
}
