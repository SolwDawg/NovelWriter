import type {
  SceneDocumentArtifact,
  StoryState,
} from "@story-platform/contracts";

export interface AtomicPersistenceSnapshot {
  documents: Record<string, SceneDocumentArtifact>;
  states: Record<string, StoryState>;
  outbox: Record<string, Record<string, unknown>>;
}

export interface AtomicPersistenceTransaction {
  putDocument(id: string, document: SceneDocumentArtifact): void;
  putState(id: string, state: StoryState): void;
  putOutbox(id: string, event: Record<string, unknown>): void;
}

function cloneSnapshot(snapshot: AtomicPersistenceSnapshot): AtomicPersistenceSnapshot {
  return structuredClone(snapshot);
}

export class InMemoryAtomicPersistence {
  private committed: AtomicPersistenceSnapshot = {
    documents: {},
    states: {},
    outbox: {},
  };

  async transaction<T>(
    fn: (tx: AtomicPersistenceTransaction) => Promise<T>,
  ): Promise<T> {
    const draft = cloneSnapshot(this.committed);
    const tx: AtomicPersistenceTransaction = {
      putDocument: (id, document) => {
        draft.documents[id] = structuredClone(document);
      },
      putState: (id, state) => {
        draft.states[id] = structuredClone(state);
      },
      putOutbox: (id, event) => {
        draft.outbox[id] = structuredClone(event);
      },
    };
    const result = await fn(tx);
    this.committed = draft;
    return result;
  }

  snapshot(): AtomicPersistenceSnapshot {
    return cloneSnapshot(this.committed);
  }
}
