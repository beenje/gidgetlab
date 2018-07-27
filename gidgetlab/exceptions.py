"""Gidgetlab's exceptions"""

import http
from typing import Any


class GitLabException(Exception):

    """Base exception for this library."""


class ValidationFailure(GitLabException):

    """An exception representing failed validation of a webhook event."""

    # https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#secret-token


class HTTPException(GitLabException):

    """A general exception to represent HTTP responses."""

    def __init__(self, status_code: http.HTTPStatus, *args: Any) -> None:
        self.status_code = status_code
        if args:
            super().__init__(*args)
        else:
            super().__init__(status_code.phrase)


class RedirectionException(HTTPException):

    """Exception for 3XX HTTP responses."""


class BadRequest(HTTPException):
    """The request is invalid.

    Used for 4XX HTTP errors.
    """

    # https://docs.gitlab.com/ce/api/#data-validation-and-error-reporting


class RateLimitExceeded(BadRequest):

    """Request rejected due to the rate limit being exceeded."""

    # Technically rate_limit is of type gidgetlab.sansio.RateLimit, but a
    # circular import comes about if you try to properly declare it.
    def __init__(self, rate_limit: Any, *args: Any) -> None:
        self.rate_limit = rate_limit

        if not args:
            super().__init__(http.HTTPStatus.FORBIDDEN, "rate limit exceeded")
        else:
            super().__init__(http.HTTPStatus.FORBIDDEN, *args)


class InvalidField(BadRequest):

    """A field in the request is invalid.

    Represented by a 422 HTTP Response. Details of what fields were
    invalid are stored in the errors attribute.
    """

    def __init__(self, errors: Any, *args: Any) -> None:
        """Store the error details."""
        self.errors = errors
        super().__init__(http.HTTPStatus.UNPROCESSABLE_ENTITY, *args)


class GitLabBroken(HTTPException):

    """Exception for 5XX HTTP responses."""
