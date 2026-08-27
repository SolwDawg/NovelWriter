# Writing Profiles V2

## 1. Profile composition

```text
User/Story Rules
+ StyleProfile
+ GenreProfile
+ LanguageProfile
+ OutputProfile(TTS)
→ ResolvedWritingProfile
```

Planner, Writer and Critic use the same resolved expectations.

## 2. Alpha StyleProfile

V1 Alpha deliberately implements a compact profile:
- preset identity;
- pacing/rhythm preference;
- description/dialogue preference;
- tone;
- scoped custom rules;
- forbidden patterns.

The data model may support richer structured dimensions, but the UI/runtime should not require them.

## 3. Reference-derived style

Uploading reference texts and deriving a reusable abstract style signature is **V1.2**, not Alpha. The future analyzer should extract abstract features rather than copy recognizable prose.

## 4. GenreProfile

GenreProfile can affect:
- macro structure;
- pacing/tension;
- reveal strategy;
- ending expectations;
- QA rubric.

Alpha officially optimizes only 2–3 genres.

## 5. LanguageProfile

Language output is generated natively for the target language rather than English-first translation. Profiles may encode punctuation/dialogue, pronoun/honorific, spoken clarity and TTS conventions.

Alpha officially optimizes one language; additional languages are Beta gates.

## 6. OutputProfile

Alpha output is `TTSNarration`. TTS polishing may change expression but cannot alter StoryState/plot facts.

## 7. Authority order

1. system/safety constraints;
2. user locks/explicit story rules;
3. authoritative Story Canon/State;
4. language correctness constraints;
5. genre structural requirements;
6. style preferences;
7. model defaults.
