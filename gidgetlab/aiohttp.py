import asyncio
from typing import Any, Mapping, Tuple

import aiohttp

from . import abc as gl_abc


class GitLabAPI(gl_abc.GitLabAPI):
    """An implementation of :class:`gidgetlab.abc.GitLabAPI` using
    `aiohttp <https://aiohttp.readthedocs.io>`_.

    Typical usage will be::

        import aiohttp
        import gidgetlab.aiohttp


        async with aiohttp.ClientSession() as session:
            gl = gidgetlab.aiohttp.GitLabAPI(session, requester,
                                             access_token=access_token)
            # Make your requests, e.g. ...
            data = await gl.getitem("/templates/licenses/MIT")
    """

    def __init__(
        self, session: aiohttp.ClientSession, *args: Any, **kwargs: Any
    ) -> None:
        self._session = session
        super().__init__(*args, **kwargs)

    async def _request(
        self, method: str, url: str, headers: Mapping, body: bytes = b""
    ) -> Tuple[int, Mapping, bytes]:
        async with self._session.request(
            method, url, headers=headers, data=body
        ) as response:
            return response.status, response.headers, await response.read()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
