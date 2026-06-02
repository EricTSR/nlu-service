from fastapi import APIRouter
from src.posts.models import NluExtractRequest, LlmExtractResponse, NextQuestionRequest, NextQuestionResponse
from src.services.llm_extractor import extract_with_mistral, generate_next_question

router = APIRouter(prefix="/api/v1/nlu", tags=["NLU"])


@router.post(
    "/extract",
    summary="Extract NLU intent via Mistral LLM",
    response_model=LlmExtractResponse,
)
def extract_nlu(request: NluExtractRequest) -> LlmExtractResponse:
    print("📥 Incoming request:", request.model_dump())
    result = extract_with_mistral(
        message=request.message,
        title=request.title,
        dialog_context=request.dialogContext,
        preferences=request.preferences,
    )
    print("📤 Response:", result.model_dump_json(indent=2))
    return result


@router.post(
    "/next-question",
    summary="Generate next conversational question for a missing slot",
    response_model=NextQuestionResponse,
)
def next_question(request: NextQuestionRequest) -> NextQuestionResponse:
    print(f"❓ Next question request: missingField={request.missingField}")
    result = generate_next_question(
        missing_field=request.missingField,
        message=request.message,
        ready_for_search=request.readyForSearch,
        preferences=request.preferences,
        dialog_context=request.dialogContext,
    )
    print("📤 Next question response:", result.model_dump_json(indent=2))
    return result
