"""Simple baselines used by the V0 ablation.

The baselines deliberately stay small. Their purpose is to make the structured
engine's extra planning/state work measurable, not to create a second product
engine.
"""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Iterable

from .contracts import (
    Blueprint,
    EvalCase,
    SceneBlock,
    SceneDocument,
    ScenePlan,
    StoryRun,
    StoryState,
    SystemVariant,
    Usage,
)


def scene_count_for_target(target_words: int) -> int:
    if target_words <= 3000:
        return 5
    if target_words <= 10000:
        return 8
    return 10


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def pad_to_target(seed: str, target_words: int, salt: str) -> str:
    """Create deterministic filler while preserving every seed phrase."""

    seed = seed.strip()
    if word_count(seed) >= target_words:
        return seed

    fillers = (
        "Ánh đèn rung nhẹ trên mặt bàn.",
        "Không ai nói ra điều cả nhóm đang nghĩ.",
        "Ngoài cửa sổ, thành phố tiếp tục thở trong im lặng.",
        "Nhân vật quan sát thêm một lần trước khi bước tiếp.",
        "Mỗi chi tiết nhỏ khiến câu hỏi ban đầu trở nên khó quên.",
    )
    paragraphs = [seed]
    index = 0
    while word_count(" ".join(paragraphs)) < target_words:
        paragraphs.append(fillers[(index + len(salt)) % len(fillers)])
        index += 1
    return "\n".join(paragraphs)


def document_from_text(scene_id: str, text: str, revision: int = 1) -> SceneDocument:
    """Wrap prose in a stable-ID structured document."""

    paragraphs = [paragraph.strip() for paragraph in text.split("\n") if paragraph.strip()]
    blocks = tuple(
        SceneBlock(id=f"{scene_id}-block-{index:03d}", type="narration", text=paragraph)
        for index, paragraph in enumerate(paragraphs, start=1)
    )
    return SceneDocument(scene_id=scene_id, revision=revision, blocks=blocks)


def estimate_usage(input_text: str, output_text: str) -> Usage:
    # Fixture accounting is intentionally transparent rather than pretending to
    # model provider-specific tokenization.
    input_tokens = max(1, word_count(input_text))
    output_tokens = max(1, word_count(output_text))
    return Usage(input_tokens=input_tokens, output_tokens=output_tokens, estimated_cost_usd=0.0)


def make_outline(case: EvalCase) -> Blueprint:
    return Blueprint(
        title=f"Bản nháp: {case.id}",
        logline=case.premise,
        protagonist="nhân vật trung tâm",
        central_conflict="Một bí mật buộc nhân vật phải lựa chọn dưới áp lực thời gian.",
        reversals=("manh mối đầu tiên bị đảo chiều", "động cơ thật được hé lộ"),
        climax="Nhân vật đối mặt trực tiếp với sự thật.",
        resolution="Câu hỏi chính được khép lại nhưng để lại dư âm.",
        scene_count=scene_count_for_target(case.target_words),
    )


def make_simple_plans(case: EvalCase, outline: Blueprint) -> list[ScenePlan]:
    per_scene = max(1, case.target_words // outline.scene_count)
    plans: list[ScenePlan] = []
    for index in range(1, outline.scene_count + 1):
        plans.append(
            ScenePlan(
                scene_id=f"scene-{index:03d}",
                index=index,
                purpose="đẩy câu chuyện tiến lên",
                required_outcome="một bước ngoặt xảy ra",
                required_facts=(),
                forbidden_reveals=(),
                active_threads=case.critical_threads,
                target_tension=min(10, 3 + index),
                target_words=per_scene,
                pov="ngôi thứ ba",
                location="địa điểm chính",
                participants=(),
            )
        )
    return plans


def run_baseline_a(case: EvalCase) -> StoryRun:
    """A: one-shot/long-form generation with no explicit state."""

    seed = (
        f"{case.premise} Câu chuyện được kể liền mạch theo những dấu hiệu xuất hiện "
        "trên đường đi. Nhân vật lần lượt quan sát, phỏng đoán và tiến về phía "
        "một kết thúc chưa biết trước."
    )
    text = pad_to_target(seed, case.target_words, case.id)
    document = document_from_text("one-shot-story", text)
    return StoryRun(
        variant=SystemVariant.BASELINE_A,
        documents=[document],
        final_state=StoryState(),
        extracted_event_ids=[],
        committed_scene_ids=[document.scene_id],
        schema_valid=True,
        usage=estimate_usage(case.premise, text),
        notes=["one-shot baseline; no explicit StoryState or reconciliation"],
    )


def run_baseline_b(case: EvalCase) -> StoryRun:
    """B: outline first, then generate independent long sections."""

    outline = make_outline(case)
    plans = make_simple_plans(case, outline)
    per_scene = max(1, case.target_words // len(plans))
    documents: list[SceneDocument] = []
    usage = Usage()
    for plan in plans:
        seed = (
            f"{case.premise} Phần {plan.index} mở rộng dàn ý với nhịp kể đều và "
            "một manh mối mới. Các chi tiết được nối bằng cảm giác khẩn cấp, "
            "nhưng không có sổ cái trạng thái dùng chung."
        )
        # The outline baseline gets only a single generic outcome cue. It is
        # intentionally not allowed to read the case's hidden event ledger.
        if plan.index == 1 and case.events:
            seed += f" Một dấu hiệu ban đầu xuất hiện: {case.events[0].text}."
        text = pad_to_target(seed, per_scene, f"{case.id}-{plan.index}")
        document = document_from_text(plan.scene_id, text)
        documents.append(document)
        usage = usage.add(estimate_usage(case.premise, text))

    return StoryRun(
        variant=SystemVariant.BASELINE_B,
        documents=documents,
        final_state=StoryState(),
        extracted_event_ids=[],
        committed_scene_ids=[document.scene_id for document in documents],
        schema_valid=True,
        usage=usage,
        notes=["outline baseline; sections do not reconcile structured state"],
    )


def run_baseline(case: EvalCase, variant: SystemVariant) -> StoryRun:
    if variant is SystemVariant.BASELINE_A:
        return run_baseline_a(case)
    if variant is SystemVariant.BASELINE_B:
        return run_baseline_b(case)
    raise ValueError(f"unsupported baseline variant: {variant.value}")

