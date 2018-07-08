from typing import Any, Mapping, Tuple

from twisted.internet import defer
from twisted.web.http_headers import Headers

import treq

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from twisted.internet import reactor
        self._reactor = reactor
        super().__init__(*args, **kwargs)

    async def _request(self, method: str, url: str, headers: Mapping,
                       body: bytes = b'') -> Tuple[int, Mapping, bytes]:
        # We need to encode the headers to a format that Twisted will like.
        # As a note: treq will set a content-length even if we do, so we need
        # to strip any content-length header.
        headers = Headers(
            {
                k.encode('utf-8'): [v.encode('utf-8')]
                for k, v in headers.items()
                if k.lower() != 'content-length'
            }
        )
        response = await treq.request(method, url, headers=headers, data=body)

        # We need to map the headers back now. In the future, we should fix
        # this up so that any header that appears more than once is handled
        # appropriately.
        response_headers = {
            k.decode('utf-8').lower(): v[0].decode('utf-8')
            for k, v in response.headers.getAllRawHeaders()
        }
        return response.code, response_headers, await response.content()

    async def sleep(self, seconds: float) -> None:
        d = defer.Deferred()
        self._reactor.callLater(seconds, d.callback, None)
        await d
