class NluProviderError(RuntimeError):
    """Base exception for safe, public provider error mapping."""


class NluProviderTimeoutError(NluProviderError):
    pass


class NluProviderRateLimitError(NluProviderError):
    pass


class NluProviderUnavailableError(NluProviderError):
    pass


class NluProviderResponseError(NluProviderError):
    pass
