import type {
  SceneDocumentArtifact,
  StoryBlueprint,
  StoryIntent,
  StoryState,
  StoryStateDelta,
} from "@story-platform/contracts";
import {
  createEmptyStoryBible,
  type StoryBible,
} from "../../story-bible/domain/story-bible.js";

export type StoryConsistencyStatus =
  | "CLEAN"
  | "DIRTY"
  | "RECONCILING"
  | "NEEDS_REVIEW";

export type StoryStatus = "DRAFT" | "GENERATING" | "COMPLETE";

export interface Story {
  id: string;
  projectId: string;
  title: string;
  status: StoryStatus;
  targetWordCount: number;
  language: string;
  genre: StoryIntent["genre"];
  intent: StoryIntent;
  blueprint?: StoryBlueprint;
  state: StoryState;
  canonVersion: number;
  consistencyStatus: StoryConsistencyStatus;
  dirtyFromSceneId: string | null;
  committedSceneIds: string[];
  documentsBySceneId: Record<string, SceneDocumentArtifact>;
  deltasBySceneId: Record<string, StoryStateDelta>;
  appliedIdempotencyKeys: Record<string, string>;
  bible: StoryBible;
  version: number;
}

export interface CreateStoryInput {
  id: string;
  projectId: string;
  title: string;
  intent: StoryIntent;
}

export function createEmptyStoryState(): StoryState {
  return {
    schema_version: 1,
    version: 0,
    scene_index: 0,
    characters: {},
    facts: {},
    inventory: {},
    locations: {},
    timeline: [],
    open_threads: [],
    resolved_threads: [],
  };
}

export function createStory(input: CreateStoryInput): Story {
  return {
    id: input.id,
    projectId: input.projectId,
    title: input.title,
    status: "DRAFT",
    targetWordCount: input.intent.target_words,
    language: input.intent.language,
    genre: input.intent.genre,
    intent: structuredClone(input.intent),
    state: createEmptyStoryState(),
    canonVersion: 1,
    consistencyStatus: "CLEAN",
    dirtyFromSceneId: null,
    committedSceneIds: [],
    documentsBySceneId: {},
    deltasBySceneId: {},
    appliedIdempotencyKeys: {},
    bible: createEmptyStoryBible(),
    version: 0,
  };
}

export function cloneStory(story: Story): Story {
  return structuredClone(story);
}
