import { and, asc, eq } from "drizzle-orm";
import type {
  ApplyValidatedSceneCommand,
} from "../domain/commands.js";
import type {
  SceneDocumentArtifact,
  StoryBlueprint,
  StoryIntent,
  StoryState,
  StoryStateDelta,
} from "@story-platform/contracts";
import {
  canonFacts,
  characterRelationships,
  characters,
  outboxEvents,
  sceneCommitReceipts,
  sceneDocuments,
  sceneVersions,
  scenes,
  stories,
  storyStateDeltas,
  storyStates,
} from "../../../infrastructure/database/schema.js";
import type { TransactionContext, UnitOfWork } from "../../../infrastructure/database/unit-of-work.js";
import {
  type CanonFact,
  type CharacterRelationship,
  type StoryBible,
} from "../../story-bible/domain/story-bible.js";
import {
  cloneStory,
  type Story,
} from "../domain/entities.js";
import { StoryDomainError } from "../domain/errors.js";
import type { AtomicSceneCommitRepository } from "../application/story-repository.js";

function asStoryBible(
  relationshipRows: Array<typeof characterRelationships.$inferSelect>,
  canonFactRows: Array<typeof canonFacts.$inferSelect>,
): StoryBible {
  return {
    relationships: Object.fromEntries(
      relationshipRows.map((row) => [
        row.id,
        {
          id: row.id,
          subjectCharacterId: row.subjectCharacterId,
          relationType: row.relationType,
          objectCharacterId: row.objectCharacterId,
          source: row.source,
        } satisfies CharacterRelationship,
      ]),
    ),
    canonFacts: Object.fromEntries(
      canonFactRows.map((row) => [
        row.id,
        {
          id: row.id,
          subjectRef: row.subjectRef,
          predicate: row.predicate,
          value: row.valueJson as CanonFact["value"],
          locked: row.locked,
          source: row.source,
          ...(row.introducedSceneId ? { introducedSceneId: row.introducedSceneId } : {}),
        } satisfies CanonFact,
      ]),
    ),
  };
}

function sceneOrdinal(story: Story, sceneId: string, sceneIds: string[]): number {
  const committedIndex = story.committedSceneIds.indexOf(sceneId);
  if (committedIndex >= 0) return committedIndex + 1;
  return sceneIds.indexOf(sceneId) + 1;
}

export class PostgresStoryRepository implements AtomicSceneCommitRepository {
  constructor(private readonly unitOfWork: UnitOfWork) {}

  async get(storyId: string): Promise<Story> {
    return this.unitOfWork.transaction((tx) => this.readStory(tx, storyId));
  }

  async create(story: Story): Promise<void> {
    await this.unitOfWork.transaction(async (tx) => {
      await tx.insert(stories).values({
        id: story.id,
        projectId: story.projectId,
        title: story.title,
        status: story.status,
        targetWordCount: story.targetWordCount,
        language: story.language,
        genre: story.genre,
        outputMode: story.outputMode,
        intentJson: story.intent,
        blueprintJson: story.blueprint ?? null,
        currentStateVersion: story.state.version,
        canonVersion: story.canonVersion,
        consistencyStatus: story.consistencyStatus,
        dirtyFromSceneId: story.dirtyFromSceneId,
        version: story.version,
      });
      await tx.insert(storyStates).values({
        id: `${story.id}:state:${story.state.version}`,
        storyId: story.id,
        version: story.state.version,
        stateJson: story.state,
      });
      await this.persistChildren(tx, story);
    });
  }

  async save(story: Story, expectedVersion: number): Promise<void> {
    await this.unitOfWork.transaction(async (tx) => {
      await this.persistAggregate(tx, story, expectedVersion);
    });
  }

  async commitValidatedScene(
    current: Story,
    next: Story,
    command: ApplyValidatedSceneCommand,
  ): Promise<Story> {
    return this.unitOfWork.transaction(async (tx) => {
      const existingReceipt = await tx
        .select()
        .from(sceneCommitReceipts)
        .where(eq(sceneCommitReceipts.idempotencyKey, command.idempotencyKey))
        .limit(1);
      if (existingReceipt[0]) {
        return this.readStory(tx, existingReceipt[0].storyId);
      }

      await this.persistAggregate(tx, next, current.version, {
        expectedStateVersion: command.expectedStateVersion,
        expectedCanonVersion: command.expectedCanonVersion,
      });
      await tx
        .insert(outboxEvents)
        .values({
          id: `${next.id}:scene-committed:${command.idempotencyKey}`,
          aggregateType: "Story",
          aggregateId: next.id,
          eventType: "SceneCommitted",
          idempotencyKey: command.idempotencyKey,
          payloadJson: {
            storyId: next.id,
            sceneId: command.sceneId,
            documentArtifactId: command.documentArtifactId,
            resultingStateVersion: next.state.version,
            resultingStoryVersion: next.version,
          },
        })
        .onConflictDoNothing();
      return cloneStory(next);
    });
  }

  private async persistAggregate(
    tx: TransactionContext,
    story: Story,
    expectedVersion: number,
    expected?: {
      expectedStateVersion: number;
      expectedCanonVersion: number;
    },
  ): Promise<void> {
    await this.persistChildren(tx, story);
    const updated = await tx
      .update(stories)
      .set({
        title: story.title,
        status: story.status,
        targetWordCount: story.targetWordCount,
        language: story.language,
        genre: story.genre,
        outputMode: story.outputMode,
        intentJson: story.intent,
        blueprintJson: story.blueprint ?? null,
        currentStateVersion: story.state.version,
        canonVersion: story.canonVersion,
        consistencyStatus: story.consistencyStatus,
        dirtyFromSceneId: story.dirtyFromSceneId,
        version: story.version,
        updatedAt: new Date(),
      })
      .where(
        expected
          ? and(
              eq(stories.id, story.id),
              eq(stories.version, expectedVersion),
              eq(stories.currentStateVersion, expected.expectedStateVersion),
              eq(stories.canonVersion, expected.expectedCanonVersion),
            )
          : and(eq(stories.id, story.id), eq(stories.version, expectedVersion)),
      )
      .returning({ id: stories.id });

    if (!updated[0]) await this.throwConcurrencyError(tx, story.id, expected);
  }

  private async persistChildren(tx: TransactionContext, story: Story): Promise<void> {
    const sceneIds = Object.keys(story.documentsBySceneId);

    for (const [sceneId, document] of Object.entries(story.documentsBySceneId)) {
      const committed = story.committedSceneIds.includes(sceneId);
      const ordinal = sceneOrdinal(story, sceneId, sceneIds);
      await tx
        .insert(scenes)
        .values({
          id: sceneId,
          storyId: story.id,
          ordinal,
          status: committed ? "COMMITTED" : "DRAFT",
          currentDocumentRevision: document.revision,
        })
        .onConflictDoUpdate({
          target: scenes.id,
          set: {
            ordinal,
            status: committed ? "COMMITTED" : "DRAFT",
            currentDocumentRevision: document.revision,
            updatedAt: new Date(),
          },
        });

      const documentId = `${story.id}:document:${sceneId}`;
      await tx
        .insert(sceneDocuments)
        .values({
          id: documentId,
          storyId: story.id,
          sceneId,
          artifactId: document.artifact_id ?? null,
          revision: document.revision,
          documentJson: document,
        })
        .onConflictDoUpdate({
          target: sceneDocuments.sceneId,
          set: {
            artifactId: document.artifact_id ?? null,
            revision: document.revision,
            documentJson: document,
            updatedAt: new Date(),
          },
        });

      await tx
        .insert(sceneVersions)
        .values({
          id: `${story.id}:scene-version:${sceneId}:${document.revision}`,
          storyId: story.id,
          sceneId,
          revision: document.revision,
          source: committed ? "AI" : "MANUAL",
          documentJson: document,
          metadataJson: { persistedBy: "PostgresStoryRepository" },
        })
        .onConflictDoNothing();
    }

    await tx
      .insert(storyStates)
      .values({
        id: `${story.id}:state:${story.state.version}`,
        storyId: story.id,
        version: story.state.version,
        stateJson: story.state,
      })
      .onConflictDoNothing();

    for (const [sceneId, delta] of Object.entries(story.deltasBySceneId)) {
      await tx
        .insert(storyStateDeltas)
        .values({
          id: `${story.id}:delta:${sceneId}`,
          storyId: story.id,
          sceneId,
          stateVersion: Math.max(1, story.committedSceneIds.indexOf(sceneId) + 1),
          deltaJson: delta,
        })
        .onConflictDoNothing();
    }

    for (const relationship of Object.values(story.bible.relationships)) {
      for (const characterId of [
        relationship.subjectCharacterId,
        relationship.objectCharacterId,
      ]) {
        await tx
          .insert(characters)
          .values({
            id: characterId,
            storyId: story.id,
            name: characterId,
            profileJson: {},
          })
          .onConflictDoNothing();
      }
      await tx
        .insert(characterRelationships)
        .values({
          id: relationship.id,
          storyId: story.id,
          subjectCharacterId: relationship.subjectCharacterId,
          relationType: relationship.relationType,
          objectCharacterId: relationship.objectCharacterId,
          source: relationship.source,
        })
        .onConflictDoUpdate({
          target: characterRelationships.id,
          set: {
            relationType: relationship.relationType,
            source: relationship.source,
            updatedAt: new Date(),
          },
        });
    }

    for (const fact of Object.values(story.bible.canonFacts)) {
      await tx
        .insert(canonFacts)
        .values({
          id: fact.id,
          storyId: story.id,
          subjectRef: fact.subjectRef,
          predicate: fact.predicate,
          valueJson: fact.value,
          locked: fact.locked,
          source: fact.source,
          introducedSceneId: fact.introducedSceneId ?? null,
        })
        .onConflictDoUpdate({
          target: canonFacts.id,
          set: {
            valueJson: fact.value,
            locked: fact.locked,
            source: fact.source,
            introducedSceneId: fact.introducedSceneId ?? null,
            updatedAt: new Date(),
          },
        });
    }

    for (const [idempotencyKey, sceneId] of Object.entries(story.appliedIdempotencyKeys)) {
      const document = story.documentsBySceneId[sceneId];
      if (!document) {
        throw new StoryDomainError(
          "INVALID_SCENE_COMMIT",
          `idempotency receipt has no document for ${sceneId}`,
        );
      }
      await tx
        .insert(sceneCommitReceipts)
        .values({
          id: `${story.id}:receipt:${idempotencyKey}`,
          idempotencyKey,
          storyId: story.id,
          sceneId,
          documentRevision: document.revision,
          resultingStateVersion: story.state.version,
          resultingStoryVersion: story.version,
        })
        .onConflictDoNothing();
    }
  }

  private async throwConcurrencyError(
    tx: TransactionContext,
    storyId: string,
    expected?: { expectedStateVersion: number; expectedCanonVersion: number },
  ): Promise<never> {
    const currentRows = await tx
      .select({
        version: stories.version,
        stateVersion: stories.currentStateVersion,
        canonVersion: stories.canonVersion,
      })
      .from(stories)
      .where(eq(stories.id, storyId))
      .limit(1);
    const current = currentRows[0];
    if (!current) {
      throw new StoryDomainError("STORY_NOT_FOUND", `story not found: ${storyId}`);
    }
    if (expected && current.stateVersion !== expected.expectedStateVersion) {
      throw new StoryDomainError(
        "STALE_STATE_VERSION",
        `expected state ${expected.expectedStateVersion}, current state is ${current.stateVersion}`,
      );
    }
    if (expected && current.canonVersion !== expected.expectedCanonVersion) {
      throw new StoryDomainError(
        "STALE_CANON_VERSION",
        `expected canon ${expected.expectedCanonVersion}, current canon is ${current.canonVersion}`,
      );
    }
    throw new StoryDomainError(
      "VERSION_CONFLICT",
      `aggregate version changed while saving story ${storyId}`,
    );
  }

  private async readStory(tx: TransactionContext, storyId: string): Promise<Story> {
    const storyRows = await tx.select().from(stories).where(eq(stories.id, storyId)).limit(1);
    const row = storyRows[0];
    if (!row) {
      throw new StoryDomainError("STORY_NOT_FOUND", `story not found: ${storyId}`);
    }

    const stateRows = await tx
      .select()
      .from(storyStates)
      .where(
        and(
          eq(storyStates.storyId, storyId),
          eq(storyStates.version, row.currentStateVersion),
        ),
      )
      .limit(1);
    const state = stateRows[0]?.stateJson as StoryState | undefined;
    if (!state) {
      throw new StoryDomainError(
        "INVALID_SCENE_COMMIT",
        `current state snapshot is missing for story ${storyId}`,
      );
    }

    const [sceneRows, documentRows, deltaRows, relationshipRows, canonFactRows, receiptRows] =
      await Promise.all([
        tx.select().from(scenes).where(eq(scenes.storyId, storyId)).orderBy(asc(scenes.ordinal)),
        tx.select().from(sceneDocuments).where(eq(sceneDocuments.storyId, storyId)),
        tx.select().from(storyStateDeltas).where(eq(storyStateDeltas.storyId, storyId)),
        tx.select().from(characterRelationships).where(eq(characterRelationships.storyId, storyId)),
        tx.select().from(canonFacts).where(eq(canonFacts.storyId, storyId)),
        tx.select().from(sceneCommitReceipts).where(eq(sceneCommitReceipts.storyId, storyId)),
      ]);

    const committedSceneIds = sceneRows
      .filter((scene) => scene.status === "COMMITTED")
      .map((scene) => scene.id);
    const documentsBySceneId: Record<string, SceneDocumentArtifact> = {};
    for (const document of documentRows) {
      documentsBySceneId[document.sceneId] = document.documentJson as SceneDocumentArtifact;
    }
    const deltasBySceneId: Record<string, StoryStateDelta> = {};
    for (const delta of deltaRows) {
      deltasBySceneId[delta.sceneId] = delta.deltaJson as StoryStateDelta;
    }
    const appliedIdempotencyKeys: Record<string, string> = {};
    for (const receipt of receiptRows) {
      appliedIdempotencyKeys[receipt.idempotencyKey] = receipt.sceneId;
    }

    return {
      id: row.id,
      projectId: row.projectId,
      title: row.title,
      status: row.status as Story["status"],
      targetWordCount: row.targetWordCount,
      language: row.language,
      genre: row.genre as Story["genre"],
      outputMode: row.outputMode as Story["outputMode"],
      intent: row.intentJson as StoryIntent,
      blueprint: (row.blueprintJson ?? undefined) as StoryBlueprint | undefined,
      state,
      canonVersion: row.canonVersion,
      consistencyStatus: row.consistencyStatus as Story["consistencyStatus"],
      dirtyFromSceneId: row.dirtyFromSceneId,
      committedSceneIds,
      documentsBySceneId,
      deltasBySceneId,
      appliedIdempotencyKeys,
      bible: asStoryBible(relationshipRows, canonFactRows),
      version: row.version,
    };
  }
}
