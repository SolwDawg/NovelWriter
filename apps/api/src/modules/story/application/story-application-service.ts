import type {
  SceneDocumentArtifact,
  StoryState,
} from "@story-platform/contracts";
import {
  applyValidatedScene,
  assertGenerationAllowed,
  beginReconciliation,
  completeReconciliation,
  markScenePotentiallyChanged,
  registerSceneDocument,
} from "../domain/story-domain-service.js";
import type {
  ApplyValidatedSceneCommand,
  ReconciliationResult,
} from "../domain/commands.js";
import type { Story } from "../domain/entities.js";
import type { StoryRepository } from "./story-repository.js";

export class StoryApplicationService {
  constructor(private readonly repository: StoryRepository) {}

  async registerSceneDocument(storyId: string, document: SceneDocumentArtifact): Promise<Story> {
    const current = await this.repository.get(storyId);
    const next = registerSceneDocument(current, document);
    await this.repository.save(next, current.version);
    return next;
  }

  async applyValidatedScene(command: ApplyValidatedSceneCommand): Promise<Story> {
    const current = await this.repository.get(command.storyId);
    const next = applyValidatedScene(current, command);
    if (next.version === current.version) return next;
    await this.repository.save(next, current.version);
    return next;
  }

  async markScenePotentiallyChanged(storyId: string, sceneId: string): Promise<Story> {
    const current = await this.repository.get(storyId);
    const next = markScenePotentiallyChanged(current, sceneId);
    if (next.version === current.version) return next;
    await this.repository.save(next, current.version);
    return next;
  }

  async assertGenerationAllowed(storyId: string): Promise<void> {
    assertGenerationAllowed(await this.repository.get(storyId));
  }

  async beginReconciliation(storyId: string): Promise<Story> {
    const current = await this.repository.get(storyId);
    const next = beginReconciliation(current);
    await this.repository.save(next, current.version);
    return next;
  }

  async completeReconciliation(
    storyId: string,
    result: ReconciliationResult,
  ): Promise<Story> {
    const current = await this.repository.get(storyId);
    const next = completeReconciliation(current, result);
    await this.repository.save(next, current.version);
    return next;
  }
}
