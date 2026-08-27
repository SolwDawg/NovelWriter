import { and, eq } from "drizzle-orm";
import type { SceneDocumentArtifact } from "@story-platform/contracts";
import {
  sceneDocuments,
  scenes,
  sceneVersions,
} from "../../../infrastructure/database/schema.js";
import type {
  TransactionContext,
  UnitOfWork,
} from "../../../infrastructure/database/unit-of-work.js";
import { StoryDomainError } from "../../story/domain/errors.js";
import type { SceneDocumentRepository } from "../application/scene-document-repository.js";
import { assertSceneDocument } from "../domain/scene-document.js";

export class PostgresSceneDocumentRepository implements SceneDocumentRepository {
  constructor(private readonly unitOfWork: UnitOfWork) {}

  async get(sceneId: string): Promise<SceneDocumentArtifact | null> {
    return this.unitOfWork.transaction(async (tx) => {
      const rows = await tx
        .select()
        .from(sceneDocuments)
        .where(eq(sceneDocuments.sceneId, sceneId))
        .limit(1);
      return rows[0]?.documentJson as SceneDocumentArtifact | null;
    });
  }

  async save(
    sceneId: string,
    nextDocument: SceneDocumentArtifact,
    baseRevision: number,
  ): Promise<SceneDocumentArtifact> {
    assertSceneDocument(nextDocument);
    if (
      baseRevision < 0 ||
      nextDocument.scene_id !== sceneId ||
      nextDocument.revision !== baseRevision + 1
    ) {
      throw new StoryDomainError(
        "INVALID_SCENE_COMMIT",
        "document scene ID or next revision is invalid",
      );
    }

    return this.unitOfWork.transaction(async (tx) => {
      const currentRows = await tx
        .select()
        .from(sceneDocuments)
        .where(eq(sceneDocuments.sceneId, sceneId))
        .limit(1);
      const current = currentRows[0];
      const currentRevision = current?.revision ?? 0;
      if (currentRevision !== baseRevision) {
        throw new StoryDomainError(
          "STALE_DOCUMENT_REVISION",
          `expected document revision ${baseRevision}, current is ${currentRevision}`,
        );
      }

      const documentId = current?.id ?? `${nextDocument.scene_id}:document`;
      if (current) {
        const updated = await tx
          .update(sceneDocuments)
          .set({
            artifactId: nextDocument.artifact_id ?? null,
            revision: nextDocument.revision,
            documentJson: nextDocument,
            updatedAt: new Date(),
          })
          .where(
            and(
              eq(sceneDocuments.sceneId, sceneId),
              eq(sceneDocuments.revision, baseRevision),
            ),
          )
          .returning({ id: sceneDocuments.id });
        if (!updated[0]) {
          throw new StoryDomainError(
            "STALE_DOCUMENT_REVISION",
            `document changed while saving scene ${sceneId}`,
          );
        }
      } else {
        const sceneRows = await tx
          .select({ storyId: scenes.storyId })
          .from(scenes)
          .where(eq(scenes.id, sceneId))
          .limit(1);
        const scene = sceneRows[0];
        if (!scene) {
          throw new StoryDomainError(
            "INVALID_SCENE_COMMIT",
            `scene must exist before its first document save: ${sceneId}`,
          );
        }
        await tx.insert(sceneDocuments).values({
          id: documentId,
          storyId: scene.storyId,
          sceneId,
          artifactId: nextDocument.artifact_id ?? null,
          revision: nextDocument.revision,
          documentJson: nextDocument,
        });
      }

      await tx
        .insert(sceneVersions)
        .values({
          id: `${documentId}:revision:${nextDocument.revision}`,
          storyId: current?.storyId ?? (await this.storyIdForScene(tx, sceneId)),
          sceneId,
          revision: nextDocument.revision,
          source: "MANUAL",
          documentJson: nextDocument,
          metadataJson: { baseRevision },
        })
        .onConflictDoNothing();
      return structuredClone(nextDocument);
    });
  }

  private async storyIdForScene(tx: TransactionContext, sceneId: string): Promise<string> {
    const rows = await tx
      .select({ storyId: scenes.storyId })
      .from(scenes)
      .where(eq(scenes.id, sceneId))
      .limit(1);
    const storyId = rows[0]?.storyId;
    if (!storyId) {
      throw new StoryDomainError(
        "INVALID_SCENE_COMMIT",
        `scene must exist before its first document version: ${sceneId}`,
      );
    }
    return storyId;
  }
}
