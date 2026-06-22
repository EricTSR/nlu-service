import logging

from fastapi import APIRouter

from src.services.extraction_service import ExtractionService
from src.services.question_service import QuestionService
from src.schemas.nlu import NluExtractRequest, LlmExtractResponse, NextQuestionRequest, NextQuestionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nlu", tags=["NLU"])

extraction_service = ExtractionService()
question_service = QuestionService()


@router.post(
    "/extract",
    summary="Extract NLU intent via Mistral LLM",
    response_model=LlmExtractResponse,
)
def extract_nlu(request: NluExtractRequest) -> LlmExtractResponse:
    logger.debug("Incoming request: %s", request.model_dump())
    result = extraction_service.extract(
        message=request.message,
        dialog_context=request.dialogContext,
        preferences=request.preferences,
    )
    logger.debug("Response: %s", result.model_dump_json(indent=2))
    return result


@router.post(
    "/next-question",
    summary="Generate next conversational question for a missing slot",
    response_model=NextQuestionResponse,
)
def next_question(request: NextQuestionRequest) -> NextQuestionResponse:
    logger.debug("Next question request: missingField=%s", request.missingField)
    result = question_service.generate_next_question(
        missing_field=request.missingField,
        message=request.message,
        ready_for_search=request.readyForSearch,
        preferences=request.preferences,
        dialog_context=request.dialogContext,
    )
    logger.debug("Next question response: %s", result.model_dump_json(indent=2))
    return result
