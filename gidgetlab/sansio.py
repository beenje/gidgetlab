"""Code to help with HTTP requests, responses, and events from GitLab's developer API.

This code has been constructed to perform no I/O of its own. This allows you to
use any HTTP library you prefer while not having to implement common details
when working with GitLab's API (e.g. validating webhook events or specifying the
API version you want your request to work against).
"""
import cgi
import datetime
import http
import json
import re
from typing import Any, Dict, Mapping, Optional, Tuple, Type, Union
import urllib.parse

from . import (
    BadRequest,
    GitLabBroken,
    HTTPException,
    InvalidField,
    RateLimitExceeded,
    RedirectionException,
    ValidationFailure,
)


def _parse_content_type(content_type: Optional[str]) -> Tuple[Optional[str], str]:
    """Tease out the content-type and character encoding.

    A default character encoding of UTF-8 is used, so the content-type
    must be used to determine if any decoding is necessary to begin
    with.
    """
    if not content_type:
        return None, "utf-8"
    else:
        type_, parameters = cgi.parse_header(content_type)
        encoding = parameters.get("charset", "utf-8")
        return type_, encoding


def _decode_body(
    content_type: Optional[str], body: bytes, *, strict: bool = False
) -> Any:
    """Decode an HTTP body based on the specified content type.

    If 'strict' is true, then raise ValueError if the content type
    is not recognized. Otherwise simply returned the body as a decoded
    string.
    """
    type_, encoding = _parse_content_type(content_type)
    if not len(body) or not content_type:
        return None
    decoded_body = body.decode(encoding)
    if type_ == "application/json":
        return json.loads(decoded_body)
    elif type_ == "application/x-www-form-urlencoded":
        return json.loads(urllib.parse.parse_qs(decoded_body)["payload"][0])
    elif strict:
        raise ValueError(f"unrecognized content type: {type_!r}")
    return decoded_body


class Event:
    """Representation of a GitLab webhook event."""

    def __init__(self, data: Any, *, event: str, secret: Optional[str] = None) -> None:
        # https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#events
        # https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#secret-token
        #: The payload of the `event <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#events>`_
        self.data = data
        # Event is not an enum as GitLab provides the string. This allows them
        # to add new events without having to mirror them here. There's also no
        # direct worry of a user typing in the wrong event name and thus no need
        # for an enum's typing protection.
        #: The string representation of the `triggering event <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#events>`_
        self.event = event
        #: The secret token of the `webhook <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#secret-token>`_
        self.secret = secret

    @property
    def object_attributes(self) -> Union[Dict[str, Any], Any]:
        """Property to easily access the object_attributes dict from an event data"""
        return self.data.get("object_attributes", {})

    @property
    def project_id(self) -> Union[int, Any]:
        """Property to easily access the project_id from an event data"""
        try:
            return self.data["project"]["id"]
        except KeyError as exc:
            raise AttributeError(str(exc)) from None

    @classmethod
    def from_http(
        cls, headers: Mapping[str, str], body: bytes, *, secret: Optional[str] = None
    ) -> "Event":
        """Construct an :class:`Event` instance from HTTP headers and JSON body data.

        The mapping providing the *headers* is expected to support lowercase keys.

        Since this method assumes the body of the HTTP request is JSON, a check
        is performed for a content-type of "application/json".
        If the content-type does not match, :exc:`~gidgetlab.exceptions.BadRequest` is raised.

        If the appropriate headers are provided for event validation, then it
        will be performed unconditionally. Any failure in validation
        (including not providing a *secret*) will lead to :exc:`~gidgetlab.exceptions.ValidationFailure`
        being raised.
        """
        if "x-gitlab-token" in headers:
            # https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#secret-token
            if secret is None:
                raise ValidationFailure("secret not provided")
            if headers["x-gitlab-token"] != secret:
                raise ValidationFailure("invalid secret")
        elif secret is not None:
            raise ValidationFailure("x-gitlab-token is missing")

        try:
            data = _decode_body(headers["content-type"], body, strict=True)
        except (KeyError, ValueError) as exc:
            raise BadRequest(
                http.HTTPStatus(415),
                "expected a content-type of "
                "'application/json' or "
                "'application/x-www-form-urlencoded'",
            ) from exc
        return cls(data, event=headers["x-gitlab-event"], secret=secret)


def create_headers(
    requester: str, *, access_token: Optional[str] = None
) -> Dict[str, str]:
    """Create a dict representing GitLab-specific header fields.

    The user agent is set according to who the *requester* is.
    GitLab doesn't require anything specific but setting it to a username or project name
    is good practice (this is required by GitHub API).

    The *access_token* allows making an
    `authenticated request <https://docs.gitlab.com/ce/api/README.html#authentication>`_.
    Only `Personal Access Tokens <https://docs.gitlab.com/ce/api/README.html#personal-access-tokens>`_ are supported.
    Most API requests require authentication, or will only return public data when
    authentication is not provided.

    For consistency, all keys in the returned dict will be lowercased.
    """
    # Private-Token: https://docs.gitlab.com/ce/api/README.html#personal-access-tokens
    headers = {"user-agent": requester, "accept": "application/json"}
    if access_token is not None:
        headers["private-token"] = access_token
    return headers


class RateLimit:

    """The rate limit imposed upon the requester.

    The *reset_epoch* argument is expected to be UTC seconds from the epoch.
    effectively 'left' resets to 'rate'. The datetime object is timezone-aware
    and set to UTC.

    The boolean value of an instance whether another request can be made. This
    is determined based on whether there are any remaining requests or if the
    reset datetime has passed.
    """

    def __init__(self, *, limit: int, remaining: int, reset_epoch: float) -> None:
        """Instantiate a RateLimit object.

        The reset_epoch argument should be in seconds since the UTC epoch.
        """
        # Instance attribute names stem from the name GitLab uses in their
        # API documentation.
        #: The maximum limit of requests per hour the requester can make.
        self.limit = limit
        #: How many requests are left for the request until their quota is reset.
        self.remaining = remaining
        #: The :class:`datetime.datetime` object representing when the requester's
        #: quota is refreshed. The object is timezone-aware to UTC.
        self.reset_datetime = datetime.datetime.fromtimestamp(
            reset_epoch, datetime.timezone.utc
        )

    def __bool__(self) -> bool:
        """True if requests are remaining or the reset datetime has passed."""
        if self.remaining > 0:
            return True
        else:
            now = datetime.datetime.now(datetime.timezone.utc)
            return now > self.reset_datetime

    def __str__(self) -> str:
        """Provide all details in a reasonable format."""
        return f"< {self.remaining:,}/{self.limit:,} until {self.reset_datetime} >"

    @classmethod
    def from_http(cls, headers: Mapping[str, str]) -> Optional["RateLimit"]:
        """Create a :class:`RateLimit` instance from the HTTP headers of a GitLab API response.

        The mapping providing the headers is expected to support lowercase
        keys.  Returns ``None`` if ratelimit info is not found in the headers.
        """
        try:
            limit = int(headers["ratelimit-limit"])
            remaining = int(headers["ratelimit-remaining"])
            reset_epoch = float(headers["ratelimit-reset"])
        except KeyError:
            return None
        else:
            return cls(limit=limit, remaining=remaining, reset_epoch=reset_epoch)


_link_re = re.compile(
    r"\<(?P<uri>[^>]+)\>;\s*" r'(?P<param_type>\w+)="(?P<param_value>\w+)"(,\s*)?'
)


def _next_link(link: Optional[str]) -> Optional[str]:
    # https://docs.gitlab.com/ce/api/#pagination
    # https://tools.ietf.org/html/rfc5988
    if link is None:
        return None
    for match in _link_re.finditer(link):
        if match.group("param_type") == "rel":
            if match.group("param_value") == "next":
                return match.group("uri")
    else:
        return None


def decipher_response(
    status_code: int, headers: Mapping[str, str], body: bytes
) -> Tuple[Any, Optional[RateLimit], Optional[str]]:
    """Decipher an HTTP response for a GitLab API request.

    The mapping providing the headers is expected to support lowercase keys.

    The parameters of this function correspond to the three main parts
    of an HTTP response: the status code, headers, and body. Assuming
    no errors which lead to an exception being raised, a 3-item tuple
    is returned. The first item is the decoded body (typically a JSON
    object, but possibly None or a string depending on the content
    type of the body). The second item is an instance of RateLimit
    based on what the response specified.

    The last item of the tuple is the URL where to request the next
    part of results. If there are no more results then None is
    returned. Do be aware that the URL can be a URI template and so
    may need to be expanded.

    If the status code is anything other than 200, 201, 202, or 204, then
    an appropriate :exc:`~gidgetlab.exceptions.HTTPException` is raised.
    """
    data = _decode_body(headers.get("content-type"), body)
    if status_code in {200, 201, 202, 204}:
        return data, RateLimit.from_http(headers), _next_link(headers.get("link"))
    else:
        try:
            message = data["message"]
        except (TypeError, KeyError):
            message = None
        exc_type: Type[HTTPException]
        if status_code >= 500:
            exc_type = GitLabBroken
        elif status_code >= 400:
            exc_type = BadRequest
            # rate limit 429 in gitlab?
            # if status_code == 403:
            if status_code == 403:
                rate_limit = RateLimit.from_http(headers)
                if rate_limit and not rate_limit.remaining:
                    raise RateLimitExceeded(rate_limit, message)
            elif status_code == 422:
                errors = data.get("errors", None)
                if errors:
                    fields = ", ".join(repr(e["field"]) for e in errors)
                    message = f"{message} for {fields}"
                else:
                    message = data["message"]
                raise InvalidField(errors, message)
        elif status_code >= 300:
            exc_type = RedirectionException
        else:
            exc_type = HTTPException
        status_code_enum = http.HTTPStatus(status_code)
        args: Union[Tuple[http.HTTPStatus, str], Tuple[http.HTTPStatus]]
        if message:
            args = status_code_enum, message
        else:
            args = (status_code_enum,)
        raise exc_type(*args)
