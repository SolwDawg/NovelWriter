export type StoryDomainErrorCode =
  | "STORY_NOT_FOUND"
  | "ONE_AUTHORITY_VIOLATION"
  | "LOCKED_CANON_MUTATION"
  | "STALE_STATE_VERSION"
  | "STALE_CANON_VERSION"
  | "DELTA_AUTHORITY_VIOLATION"
  | "STORY_NOT_CLEAN"
  | "INVALID_SCENE_COMMIT"
  | "DUPLICATE_SCENE"
  | "IDEMPOTENCY_CONFLICT"
  | "VERSION_CONFLICT"
  | "INVALID_STATE_CHANGE"
  | "RECONCILIATION_REQUIRED";

export class StoryDomainError extends Error {
  readonly code: StoryDomainErrorCode;

  constructor(code: StoryDomainErrorCode, message: string) {
    super(message);
    this.name = "StoryDomainError";
    this.code = code;
  }
}
