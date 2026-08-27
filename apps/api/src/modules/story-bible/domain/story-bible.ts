import type { JsonValue } from "@story-platform/contracts";
import { StoryDomainError } from "../../story/domain/errors.js";

export interface CharacterRelationship {
  id: string;
  subjectCharacterId: string;
  relationType: string;
  objectCharacterId: string;
  source: string;
}

export interface CanonFact {
  id: string;
  subjectRef: string;
  predicate: string;
  value: JsonValue;
  locked: boolean;
  source: string;
  introducedSceneId?: string;
}

export interface StoryBible {
  relationships: Record<string, CharacterRelationship>;
  canonFacts: Record<string, CanonFact>;
}

export function createEmptyStoryBible(): StoryBible {
  return { relationships: {}, canonFacts: {} };
}

function relationshipMatchesFact(
  relationship: CharacterRelationship,
  fact: CanonFact,
): boolean {
  return (
    relationship.subjectCharacterId === fact.subjectRef &&
    relationship.relationType === fact.predicate &&
    typeof fact.value === "string" &&
    relationship.objectCharacterId === fact.value
  );
}

export function addCharacterRelationship(
  bible: StoryBible,
  relationship: CharacterRelationship,
): StoryBible {
  if (bible.relationships[relationship.id]) {
    throw new StoryDomainError(
      "ONE_AUTHORITY_VIOLATION",
      `relationship already exists: ${relationship.id}`,
    );
  }

  const duplicateFact = Object.values(bible.canonFacts).find((fact) =>
    relationshipMatchesFact(relationship, fact),
  );
  if (duplicateFact) {
    throw new StoryDomainError(
      "ONE_AUTHORITY_VIOLATION",
      `relationship ${relationship.id} is already owned by CanonFact ${duplicateFact.id}`,
    );
  }

  return {
    ...bible,
    relationships: { ...bible.relationships, [relationship.id]: relationship },
  };
}

export function addCanonFact(bible: StoryBible, fact: CanonFact): StoryBible {
  if (bible.canonFacts[fact.id]) {
    throw new StoryDomainError(
      "ONE_AUTHORITY_VIOLATION",
      `canon fact already exists: ${fact.id}`,
    );
  }

  const owningRelationship = Object.values(bible.relationships).find((relationship) =>
    relationshipMatchesFact(relationship, fact),
  );
  if (owningRelationship) {
    throw new StoryDomainError(
      "ONE_AUTHORITY_VIOLATION",
      `CanonFact ${fact.id} duplicates authoritative relationship ${owningRelationship.id}`,
    );
  }

  return {
    ...bible,
    canonFacts: { ...bible.canonFacts, [fact.id]: fact },
  };
}

export function updateCanonFactValue(
  bible: StoryBible,
  factId: string,
  value: JsonValue,
): StoryBible {
  const existing = bible.canonFacts[factId];
  if (!existing) {
    throw new StoryDomainError("INVALID_SCENE_COMMIT", `unknown canon fact: ${factId}`);
  }

  if (existing.locked && JSON.stringify(existing.value) !== JSON.stringify(value)) {
    throw new StoryDomainError(
      "LOCKED_CANON_MUTATION",
      `locked canon fact cannot change: ${factId}`,
    );
  }

  const candidate = { ...existing, value };
  const owningRelationship = Object.values(bible.relationships).find((relationship) =>
    relationshipMatchesFact(relationship, candidate),
  );
  if (owningRelationship) {
    throw new StoryDomainError(
      "ONE_AUTHORITY_VIOLATION",
      `CanonFact ${factId} cannot shadow authoritative relationship ${owningRelationship.id}`,
    );
  }

  return {
    ...bible,
    canonFacts: {
      ...bible.canonFacts,
      [factId]: { ...existing, value },
    },
  };
}
