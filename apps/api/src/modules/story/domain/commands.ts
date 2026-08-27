import type { StoryState, StoryStateDelta } from "@story-platform/contracts";

export interface ApplyValidatedSceneCommand {
  storyId: string;
  sceneId: string;
  expectedStateVersion: number;
  expectedCanonVersion: number;
  documentArtifactId: string;
  delta: StoryStateDelta;
  idempotencyKey: string;
}

export interface ReconciliationResult {
  reconciledState: StoryState;
  unresolvedReasons?: string[];
}
