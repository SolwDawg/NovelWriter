import { cloneStory, type Story } from "../domain/entities.js";
import { StoryDomainError } from "../domain/errors.js";
import type { ApplyValidatedSceneCommand } from "../domain/commands.js";

export interface StoryRepository {
  get(storyId: string): Promise<Story>;
  save(story: Story, expectedVersion: number): Promise<void>;
}

export interface AtomicSceneCommitRepository extends StoryRepository {
  commitValidatedScene(
    current: Story,
    next: Story,
    command: ApplyValidatedSceneCommand,
  ): Promise<Story>;
}

export class InMemoryStoryRepository implements StoryRepository {
  private readonly stories = new Map<string, Story>();

  constructor(initialStories: Story[] = []) {
    for (const story of initialStories) this.stories.set(story.id, cloneStory(story));
  }

  async get(storyId: string): Promise<Story> {
    const story = this.stories.get(storyId);
    if (!story) {
      throw new StoryDomainError("STORY_NOT_FOUND", `story not found: ${storyId}`);
    }
    return cloneStory(story);
  }

  async save(story: Story, expectedVersion: number): Promise<void> {
    const current = this.stories.get(story.id);
    if (!current) {
      throw new StoryDomainError("STORY_NOT_FOUND", `story not found: ${story.id}`);
    }
    if (current.version !== expectedVersion) {
      throw new StoryDomainError(
        "VERSION_CONFLICT",
        `expected aggregate version ${expectedVersion}, current is ${current.version}`,
      );
    }
    this.stories.set(story.id, cloneStory(story));
  }
}
