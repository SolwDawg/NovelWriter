import type { SceneDocumentArtifact } from "@story-platform/contracts";
import { assertSceneDocument } from "../domain/scene-document.js";
import { StoryDomainError } from "../../story/domain/errors.js";

export interface SceneDocumentRepository {
  get(sceneId: string): Promise<SceneDocumentArtifact | null>;
  save(
    sceneId: string,
    nextDocument: SceneDocumentArtifact,
    baseRevision: number,
  ): Promise<SceneDocumentArtifact>;
}

export class InMemorySceneDocumentRepository implements SceneDocumentRepository {
  private readonly documents = new Map<string, SceneDocumentArtifact>();

  constructor(initialDocuments: SceneDocumentArtifact[] = []) {
    for (const document of initialDocuments) {
      assertSceneDocument(document);
      this.documents.set(document.scene_id, structuredClone(document));
    }
  }

  async get(sceneId: string): Promise<SceneDocumentArtifact | null> {
    const document = this.documents.get(sceneId);
    return document ? structuredClone(document) : null;
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

    const currentRevision = this.documents.get(sceneId)?.revision ?? 0;
    if (currentRevision !== baseRevision) {
      throw new StoryDomainError(
        "STALE_DOCUMENT_REVISION",
        `expected document revision ${baseRevision}, current is ${currentRevision}`,
      );
    }

    const saved = structuredClone(nextDocument);
    this.documents.set(sceneId, saved);
    return structuredClone(saved);
  }
}
