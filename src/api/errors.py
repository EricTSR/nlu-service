import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.nlu.errors import (
    NluProviderRateLimitError,
    NluProviderResponseError,
    NluProviderTimeoutError,
    NluProviderUnavailableError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(NluProviderTimeoutError, _provider_timeout)
    application.add_exception_handler(NluProviderRateLimitError, _provider_rate_limited)
    application.add_exception_handler(NluProviderUnavailableError, _provider_unavailable)
    application.add_exception_handler(NluProviderResponseError, _provider_invalid_response)


async def _provider_timeout(_: Request, _exception: Exception) -> JSONResponse:
    logger.warning("NLU provider timed out")
    return JSONResponse(status_code=504, content={"code": "NLU_PROVIDER_TIMEOUT"})


async def _provider_rate_limited(_: Request, _exception: Exception) -> JSONResponse:
    logger.warning("NLU provider rate limited the request")
    return JSONResponse(status_code=429, content={"code": "NLU_PROVIDER_RATE_LIMITED"})


async def _provider_unavailable(_: Request, _exception: Exception) -> JSONResponse:
    logger.warning("NLU provider is unavailable")
    return JSONResponse(status_code=503, content={"code": "NLU_PROVIDER_UNAVAILABLE"})


async def _provider_invalid_response(_: Request, _exception: Exception) -> JSONResponse:
    logger.warning("NLU provider returned an invalid response")
    return JSONResponse(status_code=502, content={"code": "NLU_PROVIDER_INVALID_RESPONSE"})
