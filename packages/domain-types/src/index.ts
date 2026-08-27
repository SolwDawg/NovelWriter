import type {
  SceneDocumentArtifact,
  StoryBlueprint,
  StoryIntent,
  StoryState,
} from "../../contracts/generated/index.js";

export type StoryId = string & { readonly __brand: "StoryId" };

export interface StoryRecord {
  id: StoryId;
  ownerId: string;
  intent: StoryIntent;
  blueprint?: StoryBlueprint;
  state: StoryState;
  sceneDocuments: SceneDocumentArtifact[];
  createdAt: string;
  updatedAt: string;
}
