"""Provide an abstract base class for easier requests."""
import abc
import json
import urllib.parse
from typing import Any, AsyncGenerator, Dict, Mapping, MutableMapping, Tuple
from typing import Optional as Opt

from . import sansio


# Value represents etag, last-modified, data, and next page.
CACHE_TYPE = MutableMapping[str, Tuple[Opt[str], Opt[str], Any, Opt[str]]]


class GitLabAPI(abc.ABC):
    """Provide an :py:term:`abstract base class` which abstracts out the
    HTTP library being used to send requests to GitLab. The class is
    initialized with the requester's name and optionally their
    Access token and a cache object.

    For methods that send data to GitLab, there is a *data* argument which
    accepts an object which can be serialized to JSON (because
    ``None`` is a legitimate JSON value, ``""`` is used to represent
    no data).

    The returned value for GitLab requests is the decoded body of the
    response according to :func:`gidgetlab.sansio.decipher_response`.
    If the status code returned by the HTTP request is anything other
    than ``200``, ``201``, ``202`` or ``204``, then an appropriate
    :exc:`~gidgetlab.HTTPException` is raised.
    """

    def __init__(
        self,
        requester: str,
        *,
        access_token: Opt[str] = None,
        url: str = "https://gitlab.com",
        api_version: str = "v4",
        cache: Opt[CACHE_TYPE] = None,
    ) -> None:
        self.requester = requester
        self.access_token = access_token
        self.api_url: str = urllib.parse.urljoin(url, f"/api/{api_version}/")
        self._cache = cache
        self.rate_limit: Opt[sansio.RateLimit] = None

    @abc.abstractmethod
    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Tuple[int, Mapping[str, str], bytes]:
        """An abstract :term:`coroutine` to make an HTTP request.

        The given *headers* will have lower-case keys and include not only
        GitLab-specific fields but also ``content-length`` (and ``content-type`` if appropriate).

        The expected return value is a tuple consisting of the status
        code, headers, and the body of the HTTP response. The headers
        dictionary is expected to work with lower-case keys.
        """

    @abc.abstractmethod
    async def sleep(self, seconds: float) -> None:
        """An abstract :term:`coroutine` which causes the coroutine to
        sleep for the specified number of seconds. This is provided to
        help prevent from going over one's `rate limit <https://gitlab.com/gitlab-org/gitlab-ce/issues/41308>`_.
        """

    def format_url(self, url: str, params: Mapping[str, Any]) -> str:
        """Construct a URL for the GitLab API.

        The URL may be absolute or relative. In the latter case the appropriate
        domain will be added. This is to help when copying the relative URL directly
        from the GitLab developer documentation.

        The dict provided in *params* is passed as query string.
        """
        # Works even if 'url' is fully-qualified.
        url = urllib.parse.urljoin(self.api_url, url.lstrip("/"))
        if params:
            # Pass params as query string
            url_parts = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(url_parts.query)
            query.update(params)
            url_parts_with_params = url_parts._replace(
                query=urllib.parse.urlencode(query, doseq=True)
            )
            return urllib.parse.urlunparse(url_parts_with_params)
        return url

    async def _make_request(
        self, method: str, url: str, params: Dict[str, str], data: Any
    ) -> Tuple[bytes, Opt[str]]:
        """Construct and make an HTTP request."""
        filled_url = self.format_url(url, params)
        request_headers = sansio.create_headers(
            self.requester, access_token=self.access_token
        )
        cached = cacheable = False
        # Can't use None as a "no body" sentinel as it's a legitimate JSON type.
        if data == b"":
            body = b""
            request_headers["content-length"] = "0"
            if method == "GET" and self._cache is not None:
                cacheable = True
                try:
                    etag, last_modified, data, more = self._cache[filled_url]
                    cached = True
                except KeyError:
                    pass
                else:
                    if etag is not None:
                        request_headers["if-none-match"] = etag
                    if last_modified is not None:
                        request_headers["if-modified-since"] = last_modified
        else:
            charset = "utf-8"
            body = json.dumps(data).encode(charset)
            request_headers["content-type"] = f"application/json; charset={charset}"
            request_headers["content-length"] = str(len(body))
        if self.rate_limit is not None:
            self.rate_limit.remaining -= 1
        response = await self._request(method, filled_url, request_headers, body)
        if not (response[0] == 304 and cached):
            data, self.rate_limit, more = sansio.decipher_response(*response)
            has_cache_details = "etag" in response[1] or "last-modified" in response[1]
            if self._cache is not None and cacheable and has_cache_details:
                etag = response[1].get("etag")
                last_modified = response[1].get("last-modified")
                self._cache[filled_url] = etag, last_modified, data, more
        return data, more

    async def getitem(self, url: str, params: Dict[str, str] = {}) -> Any:
        """Get a single item from GitLab.

        .. note::
            For ``GET`` calls that can return multiple values and
            potentially require pagination, see ``getiter()``.
        """
        data, _ = await self._make_request("GET", url, params, b"")
        return data

    async def getiter(
        self, url: str, params: Dict[str, str] = {}
    ) -> AsyncGenerator[Any, None]:
        """Get all items from a GitLab API endpoint.

        An asynchronous iterable is returned which will yield all items
        from the endpoint (i.e. use ``async for`` on the result). Any
        `pagination <https://docs.gitlab.com/ee/api/README.html#pagination>`_
        will automatically be followed.

        .. note::
            For ``GET`` calls that return only a single item, see
            :meth:`getitem`.
        """
        data, more = await self._make_request("GET", url, params, b"")
        for item in data:
            yield item
        if more:
            # `yield from` is not supported in coroutines.
            async for item in self.getiter(more, params):
                yield item

    async def post(self, url: str, params: Dict[str, str] = {}, *, data: Any) -> Any:
        """Send a ``POST`` request to GitLab."""
        data, _ = await self._make_request("POST", url, params, data)
        return data

    async def patch(self, url: str, params: Dict[str, str] = {}, *, data: Any) -> Any:
        """Send a ``PATCH`` request to GitLab."""
        data, _ = await self._make_request("PATCH", url, params, data)
        return data

    async def put(
        self, url: str, params: Dict[str, str] = {}, *, data: Any = b""
    ) -> Any:
        """Send a ``PUT`` request to GitLab."""
        data, _ = await self._make_request("PUT", url, params, data)
        return data

    async def delete(
        self, url: str, params: Dict[str, str] = {}, *, data: Any = b""
    ) -> None:
        """Send a ``DELETE`` request to GitLab."""
        await self._make_request("DELETE", url, params, data)
