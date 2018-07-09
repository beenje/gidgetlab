"""Provide an abstract base class for easier requests."""
import abc
import json
import urllib.parse
import uritemplate
from typing import Any, AsyncGenerator, Dict, Mapping, MutableMapping, Tuple
from typing import Optional as Opt

from . import sansio


# Value represents etag, last-modified, data, and next page.
CACHE_TYPE = MutableMapping[str, Tuple[Opt[str], Opt[str], Any, Opt[str]]]


class GitLabAPI(abc.ABC):

    """Provide an idiomatic API for making calls to GitLab's API."""

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
        self, method: str, url: str, headers: Mapping, body: bytes = b""
    ) -> Tuple[int, Mapping, bytes]:
        """Make an HTTP request."""

    @abc.abstractmethod
    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""

    def format_url(self, url: str, url_vars: Mapping[str, Any]) -> str:
        """Construct a URL for the GitLab API.

        The URL may be absolute or relative. In the latter case the appropriate
        domain will be added. This is to help when copying the relative URL directly
        from the GitLab developer documentation.

        The dict provided in url_vars is used in URI template formatting.
        """
        # Works even if 'url' is fully-qualified.
        url = urllib.parse.urljoin(self.api_url, url.lstrip("/"))
        expanded_url: str = uritemplate.expand(url, var_dict=url_vars)
        return expanded_url

    async def _make_request(
        self, method: str, url: str, url_vars: Dict, data: Any
    ) -> Tuple[bytes, Opt[str]]:
        """Construct and make an HTTP request."""
        filled_url = self.format_url(url, url_vars)
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

    async def getitem(self, url: str, url_vars: Dict = {}) -> Any:
        """Send a GET request for a single item to the specified endpoint."""
        data, _ = await self._make_request("GET", url, url_vars, b"")
        return data

    async def getiter(self, url: str, url_vars: Dict = {}) -> AsyncGenerator[Any, None]:
        """Return an async iterable for all the items at a specified endpoint."""
        data, more = await self._make_request("GET", url, url_vars, b"")
        for item in data:
            yield item
        if more:
            # `yield from` is not supported in coroutines.
            async for item in self.getiter(more, url_vars):
                yield item

    async def post(self, url: str, url_vars: Dict = {}, *, data: Any) -> Any:
        data, _ = await self._make_request("POST", url, url_vars, data)
        return data

    async def patch(self, url: str, url_vars: Dict = {}, *, data: Any) -> Any:
        data, _ = await self._make_request("PATCH", url, url_vars, data)
        return data

    async def put(self, url: str, url_vars: Dict = {}, *, data: Any = b"") -> Any:
        data, _ = await self._make_request("PUT", url, url_vars, data)
        return data

    async def delete(self, url: str, url_vars: Dict = {}, *, data: Any = b"") -> None:
        await self._make_request("DELETE", url, url_vars, data)
