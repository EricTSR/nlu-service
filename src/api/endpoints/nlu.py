import logging

from fastapi import APIRouter

from src.api.dependencies import ExtractionServiceDep, QuestionServiceDep
from src.schemas.nlu import (
    LlmExtractResponse,
    NextQuestionRequest,
    NextQuestionResponse,
    NluExtractRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nlu", tags=["NLU"])


@router.post(
    "/extract",
    summary="Extract NLU intent via Mistral LLM",
    response_model=LlmExtractResponse,
)
def extract_nlu(
    request: NluExtractRequest,
    extraction_service: ExtractionServiceDep,
) -> LlmExtractResponse:
    logger.debug("Incoming extract request with %d context entries", len(request.dialogContext))
    result = extraction_service.extract(
        message=request.message,
        dialog_context=request.dialogContext,
        preferences=request.preferences,
        locale=request.locale.value,
    )
    logger.debug("Extract response type: %s", result.messageType)
    return result


@router.post(
    "/next-question",
    summary="Generate next conversational question for a missing slot",
    response_model=NextQuestionResponse,
)
def next_question(
    request: NextQuestionRequest,
    question_service: QuestionServiceDep,
) -> NextQuestionResponse:
    logger.debug("Next question request: missingField=%s", request.missingField)
    result = question_service.generate_next_question(
        missing_field=request.missingField,
        message=request.message,
        ready_for_search=request.readyForSearch,
        preferences=request.preferences,
        dialog_context=request.dialogContext,
        locale=request.locale.value,
    )
    logger.debug("Next question generated with %d quick replies", len(result.quickReplies))
    return result
