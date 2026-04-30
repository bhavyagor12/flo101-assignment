"""Public API routes."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from flo101_api.corpus.ingest import IngestDocument, ingest_documents
from flo101_api.corpus.summary import build_corpus_summary
from flo101_api.critic.run import run_critic
from flo101_api.db.evaluations import get_evaluation, list_evaluations
from flo101_api.db.specs import get_spec, insert_spec, list_specs
from flo101_api.domain import (
    CorpusUploadResult,
    CriticException,
    Evaluation,
    SkillSpec,
    SynthesizeRequest,
)
from flo101_api.domain.artifact import ArtifactSubmission
from flo101_api.observability import get_logger
from flo101_api.synthesizer import synthesize_skill_spec

router = APIRouter()
_log = get_logger("flo101_api.api.routes")


# ─── Skill specs ────────────────────────────────────────────────────────────


@router.post(
    "/spec",
    response_model=SkillSpec,
    status_code=status.HTTP_201_CREATED,
    summary="Synthesize a SkillSpec from a natural-language goal",
    tags=["spec"],
)
async def create_spec(payload: SynthesizeRequest) -> SkillSpec:
    try:
        spec = await synthesize_skill_spec(request=payload, has_corpus=False)
    except CriticException as exc:
        raise HTTPException(status_code=502, detail=exc.to_model().model_dump()) from exc
    insert_spec(spec)
    _log.info("api.spec.created", spec_id=spec.id, score=spec.meta_critique_score)
    return spec


@router.get(
    "/spec",
    response_model=list[SkillSpec],
    summary="List all SkillSpecs",
    tags=["spec"],
)
async def list_all_specs() -> list[SkillSpec]:
    return list_specs()


@router.get(
    "/spec/{spec_id}",
    response_model=SkillSpec,
    summary="Get a SkillSpec by id",
    tags=["spec"],
)
async def get_one_spec(spec_id: str) -> SkillSpec:
    spec = get_spec(spec_id)
    if spec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "spec not found")
    return spec


# ─── Corpus ─────────────────────────────────────────────────────────────────


@router.post(
    "/spec/{spec_id}/corpus",
    response_model=CorpusUploadResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload reference materials to ground evaluation",
    tags=["corpus"],
)
async def upload_corpus(
    spec_id: str,
    files: list[UploadFile] = File(..., description="One or more text/markdown files"),
) -> CorpusUploadResult:
    if get_spec(spec_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "spec not found")
    documents: list[IngestDocument] = []
    for f in files:
        raw = await f.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"file {f.filename!r} is not utf-8 text: {exc}",
            ) from exc
        if not text.strip():
            continue
        documents.append(
            IngestDocument(
                source=f.filename or "uploaded.txt",
                content=text,
                metadata={"content_type": f.content_type or "text/plain"},
            )
        )
    if not documents:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "no usable text content in uploads"
        )
    try:
        return await ingest_documents(spec_id=spec_id, documents=documents)
    except CriticException as exc:
        raise HTTPException(status_code=502, detail=exc.to_model().model_dump()) from exc


@router.get(
    "/spec/{spec_id}/corpus/summary",
    summary="Get a representative excerpt of a spec's corpus",
    tags=["corpus"],
)
async def get_corpus_summary(spec_id: str) -> dict[str, str | None]:
    if get_spec(spec_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "spec not found")
    return {"summary": build_corpus_summary(spec_id=spec_id)}


# ─── Evaluation ─────────────────────────────────────────────────────────────


@router.post(
    "/spec/{spec_id}/evaluate",
    response_model=Evaluation,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate an artifact against a SkillSpec",
    tags=["evaluation"],
)
async def evaluate(spec_id: str, submission: ArtifactSubmission) -> Evaluation:
    if get_spec(spec_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "spec not found")
    try:
        return await run_critic(spec_id=spec_id, submission=submission)
    except CriticException as exc:
        raise HTTPException(status_code=502, detail=exc.to_model().model_dump()) from exc


@router.get(
    "/evaluation/{evaluation_id}",
    response_model=Evaluation,
    summary="Get an evaluation by id",
    tags=["evaluation"],
)
async def get_one_evaluation(evaluation_id: str) -> Evaluation:
    ev = get_evaluation(evaluation_id)
    if ev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "evaluation not found")
    return ev


@router.get(
    "/evaluation",
    response_model=list[Evaluation],
    summary="List recent evaluations",
    tags=["evaluation"],
)
async def list_recent_evaluations() -> list[Evaluation]:
    return list_evaluations()
