"""Application error types used across the service and API layers."""


class ApiError(Exception):
    """Base class for errors that are surfaced to API clients.

    Subclasses define the HTTP ``status_code``, a stable machine-readable
    ``code``, and a user-safe ``message``. ``message`` must never contain
    stack traces, file-system paths, environment values, or internal details.
    """

    status_code: int = 500
    code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class NotFoundError(ApiError):
    """Base class for 404 responses."""

    status_code = 404
    code = "not_found"
    message = "The requested resource was not found."


class ProjectNotFoundError(NotFoundError):
    """Raised when a project does not exist."""

    code = "project_not_found"
    message = "Project not found."


class BadRequestError(ApiError):
    """Raised when a request is invalid (HTTP 400)."""

    status_code = 400
    code = "bad_request"
    message = "The request is invalid."


class InvalidProjectStateError(BadRequestError):
    """Raised when an operation cannot run because of the project's status."""

    code = "invalid_project_state"
    message = "The project is not in a valid state for this operation."


class EmptyDescriptionError(BadRequestError):
    """Raised when a stored project description is empty for analysis."""

    code = "empty_description"
    message = "The project must have a non-empty description before analysis."


class DuplicateClarificationAnswerError(BadRequestError):
    """Raised when a clarification question already has an answer."""

    code = "duplicate_clarification_answer"
    message = "A clarification question can only be answered once."


class ClarificationQuestionNotFoundError(NotFoundError):
    """Raised when a clarification question does not exist for a project."""

    code = "clarification_question_not_found"
    message = "Clarification question not found for this project."


class NoClarificationQuestionsError(NotFoundError):
    """Raised when no clarification questions exist for a project."""

    code = "no_clarification_questions"
    message = "No clarification questions have been generated for this project."


class ProjectContextNotFoundError(NotFoundError):
    """Raised when a project has no stored ProjectContext."""

    code = "project_context_not_found"
    message = "The project has not been analysed yet."


class LLMTimeoutError(ApiError):
    """Raised when the model takes too long to respond (HTTP 504)."""

    status_code = 504
    code = "llm_timeout"
    message = "The model took too long to respond. Please try again."


class InvalidGeneratedOutputError(ApiError):
    """Raised when LLM/provider output fails schema validation (HTTP 422).

    Maps to the documented 422 response (API_CONTRACT: "Unprocessable Entity —
    LLM output validation failure after retries"). The message references the
    validation failure without echoing raw provider content.
    """

    status_code = 422
    code = "invalid_generated_output"
    message = "The model produced an invalid response."


class SRSVersionNotFoundError(NotFoundError):
    """Raised when an SRS version does not exist for a project."""

    code = "srs_version_not_found"
    message = "SRS version not found for this project."


class NoSRSVersionError(NotFoundError):
    """Raised when a project has no SRS versions at all."""

    code = "no_srs_version"
    message = "The project has not generated any SRS versions yet."


class InvalidSRSEditError(BadRequestError):
    """Raised when an SRS edit targets an invalid section, field, or value."""

    code = "invalid_srs_edit"
    message = "The SRS edit request is invalid."


class InvalidSRSStateError(BadRequestError):
    """Raised when an SRS operation cannot run because of the SRS status."""

    code = "invalid_srs_state"
    message = "The SRS version is not in a valid state for this operation."


class BodyTooLargeError(ApiError):
    """Raised when a request body exceeds ``CYBERSRS_MAX_REQUEST_BODY_BYTES`` (SEC-011)."""

    status_code = 413
    code = "request_body_too_large"
    message = "The request body exceeds the maximum allowed size (CYBERSRS_MAX_REQUEST_BODY_BYTES)."
