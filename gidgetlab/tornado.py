from typing import Mapping, Tuple
from tornado import gen
from tornado import httpclient
from . import abc as gl_abc


class GitLabAPI(gl_abc.GitLabAPI):
    """An implementation of :class:`gidgetlab.abc.GitLabAPI` using
    `Tornado <http://www.tornadoweb.org/>`_.
    """

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""
        if method == "GET" and not body:
            real_body = None
        else:
            real_body = body
        request = httpclient.HTTPRequest(url, method, headers, real_body)
        # Since Tornado has designed AsyncHTTPClient to be a singleton, there's
        # no reason not to simply instantiate it every time.
        client = httpclient.AsyncHTTPClient()
        response = await client.fetch(request, raise_error=False)
        return response.code, response.headers, response.body

    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        await gen.sleep(seconds)
