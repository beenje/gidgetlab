import os
import sys
import asyncio
import traceback
from typing import Any, Mapping, Tuple, Optional

import cachetools
import aiohttp
from aiohttp import web

from . import abc as gl_abc, routing, sansio


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
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Tuple[int, Mapping[str, str], bytes]:
        async with self._session.request(
            method, url, headers=headers, data=body
        ) as response:
            return response.status, response.headers, await response.read()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


class GitLabBot:
    """A GitLabBot is an aiohttp web server that handles GitLab webhooks requests

    If not given in arguments the webhook secret and access token are retrieved
    from the environment variables **GL_SECRET** and **GL_ACCESS_TOKEN**.

    If not given, the cache is set to *cachetools.LRUCache(maxsize=500)*.

    The extra *kwargs* are passed to the :class:`GitLabAPI` instance and can
    be used to set a specific **url** and **api_version**.

    Typical usage is::

        from gidgetlab.aiohttp import GitLabBot

        bot = GitLabBot("username")

        # Register a callack for a webhook event
        @bot.router.register("Issue Hook", action="open")
        async def issue_opened_event(event, gl, *args, **kwargs):
            url = f"/projects/{event.project_id}/issues/{event.object_attributes['iid']}/notes"
            message = f"Thanks for the report @{event.data['user']['username']}! I will look into it ASAP! (I'm a bot)."
            await gl.post(url, data={"body": message})

        bot.run()

    Several routers can also be registered afterwards::

        import gidgetlab.routing
        from gidgetlab.aiohttp import GitLabBot

        first_router = gidgetlab.routing.Router()
        second_router = gidgetlab.routing.Router()

        @first_router.register("Issue Hook", action="open")
        async def issue_opened_event(event, gl, *args, **kwargs):
            ...

        @second_router.register("Push Hook")
        async def push_event(event, gl, *args, **kwargs):
            ...

        bot = GitLabBot("username")
        bot.register_routers(first_router, second_router)
        bot.run()
    """

    def __init__(
        self,
        requester: str,
        *,
        secret: Optional[str] = None,
        access_token: Optional[str] = None,
        cache: Optional[gl_abc.CACHE_TYPE] = None,
        **kwargs: Any,
    ) -> None:
        self.requester = requester
        self.secret = secret or os.environ.get("GL_SECRET")
        self.access_token = access_token or os.environ.get("GL_ACCESS_TOKEN")
        self.cache = cache or cachetools.LRUCache(maxsize=500)
        # Additional keyword arguments to pass to GitLabAPI (url and api_version)
        self.kwargs = kwargs
        self.app = web.Application()
        self.app.router.add_post("/", self.webhook_handler)
        self.app.router.add_get("/health", self.health_handler)

    @property
    def router(self) -> "routing.Router":
        """The bot :class:`gidgetlab.routing.Router` instance that routes webhooks events callbacks"""
        if not hasattr(self, "_router"):
            self._router = routing.Router()
        return self._router

    def register_routers(self, *routers: "routing.Router") -> None:
        """Instantiate the bot router from the given routers"""
        if hasattr(self, "_router"):
            raise TypeError(
                "A router is already registered."
                "'register_routers' can only be called when no router is registered"
            )
        self._router = routing.Router(*routers)

    async def health_handler(self, request: "web.Request") -> "web.Response":
        """Handler to check the health of the bot

        Return 'Bot OK'
        """
        return web.Response(text="Bot OK")

    async def webhook_handler(self, request: "web.Request") -> "web.Response":
        """Handler that processes GitLab webhook requests"""
        try:
            body = await request.read()
            event = sansio.Event.from_http(request.headers, body, secret=self.secret)
            async with aiohttp.ClientSession() as session:
                gl = GitLabAPI(
                    session,
                    self.requester,
                    cache=self.cache,
                    access_token=self.access_token,
                    **self.kwargs,
                )
                # Give GitLab some time to reach internal consistency
                # (taken from bedevere and miss-islington GitHub bots)
                await asyncio.sleep(1)
                # Call the appropriate callback(s) for the event
                await self.router.dispatch(event, gl)
            return web.Response(status=200)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return web.Response(status=500)

    def run(self, **kwargs: Any) -> None:
        """Run the bot web server

        All keyword arguments are passed to the :func:`aiohttp.web.run_app` function.
        """
        web.run_app(self.app, **kwargs)
