import os
import datetime

import aiohttp
import pytest

from unittest.mock import Mock
from .. import aiohttp as gl_aiohttp
from .. import sansio, routing


class TestGitLabAPI:
    """Tests for gidgetlab.aiohttp.GitLabAPI."""

    @pytest.mark.asyncio
    async def test_sleep(self):
        delay = 1
        start = datetime.datetime.now()
        async with aiohttp.ClientSession() as session:
            gl = gl_aiohttp.GitLabAPI(session, "gidgetlab")
            await gl.sleep(delay)
        stop = datetime.datetime.now()
        assert (stop - start) > datetime.timedelta(seconds=delay)

    @pytest.mark.asyncio
    async def test__request(self):
        """Make sure that that abstract method is implemented properly."""
        request_headers = sansio.create_headers("gidgetlab")
        async with aiohttp.ClientSession() as session:
            gl = gl_aiohttp.GitLabAPI(session, "gidgetlab")
            aio_call = await gl._request(
                "GET",
                "https://gitlab.com/api/v4/templates/licenses/mit",
                request_headers,
            )
        data, rate_limit, _ = sansio.decipher_response(*aio_call)
        assert "description" in data

    @pytest.mark.asyncio
    async def test_get(self):
        """Integration test."""
        async with aiohttp.ClientSession() as session:
            gl = gl_aiohttp.GitLabAPI(session, "gidgetlab")
            data = await gl.getitem("/templates/licenses/mit")
        assert "description" in data


class TestGitLabBot:
    """Tests for gidgetlab.aiohttp.GitLabBot."""

    async def test_init_no_env(self):
        bot = gl_aiohttp.GitLabBot("gidgetlab")
        assert bot.secret is None
        assert bot.access_token is None

    async def test_init_from_env(self):
        os.environ["GL_SECRET"] = "secret"
        os.environ["GL_ACCESS_TOKEN"] = "token"
        bot = gl_aiohttp.GitLabBot("gidgetlab")
        assert bot.secret == "secret"
        assert bot.access_token == "token"
        # Remove the environment variables so that they are not used by other tests
        del os.environ["GL_SECRET"]
        del os.environ["GL_ACCESS_TOKEN"]

    async def test_valid_webhook_request(self, aiohttp_client):
        bot = gl_aiohttp.GitLabBot("gidgetlab")
        client = await aiohttp_client(bot.app)
        headers = {"x-gitlab-event": "Issue Hook"}
        data = {"action": "open"}
        # No event is registered, so no callback will be triggered,
        # but no error should be raised
        response = await client.post("/", headers=headers, json=data)
        assert response.status == 200

    async def test_invalid_webhook_request(self, aiohttp_client):
        """Even in the face of an exception, the server should not crash."""
        bot = gl_aiohttp.GitLabBot("gidgetlab")
        client = await aiohttp_client(bot.app)
        # Missing key headers.
        response = await client.post("/", headers={})
        assert response.status == 500

    async def test_webhook_handler_triggered(self, aiohttp_client):
        bot = gl_aiohttp.GitLabBot("gidgetlab")
        handler_mock = Mock()

        @bot.router.register("Issue Hook", action="open")
        async def issue_opened_event(event, gl, *args, **kwargs):
            handler_mock()

        client = await aiohttp_client(bot.app)

        # First send a request that should not trigger the handler
        headers = {"x-gitlab-event": "Push Hook"}
        data = {"object_kind": "push"}
        response = await client.post("/", headers=headers, json=data)
        assert response.status == 200
        assert not handler_mock.called

        # Send a request that should trigger the handler
        headers = {"x-gitlab-event": "Issue Hook"}
        data = {"object_kind": "issue", "object_attributes": {"action": "open"}}
        response = await client.post("/", headers=headers, json=data)
        assert response.status == 200
        assert handler_mock.called

    async def test_register_routers(self, aiohttp_client):
        issue_router = routing.Router()
        issue_mock = Mock()
        push_router = routing.Router()
        push_mock = Mock()

        @issue_router.register("Issue Hook", action="open")
        async def issue_opened_event(event, gl, *args, **kwargs):
            issue_mock()

        @push_router.register("Push Hook")
        async def push_event(event, gl, *args, **kwargs):
            push_mock()

        bot = gl_aiohttp.GitLabBot("gidgetlab")
        bot.register_routers(issue_router, push_router)
        client = await aiohttp_client(bot.app)

        headers = {"x-gitlab-event": "Push Hook"}
        data = {"object_kind": "push"}
        response = await client.post("/", headers=headers, json=data)
        assert response.status == 200
        assert not issue_mock.called
        assert push_mock.called

        headers = {"x-gitlab-event": "Issue Hook"}
        data = {"object_kind": "issue", "object_attributes": {"action": "open"}}
        response = await client.post("/", headers=headers, json=data)
        assert response.status == 200
        assert issue_mock.called

    async def test_health(self, aiohttp_client):
        """The server should answer 'Bot OK' on /health endpoint"""
        bot = gl_aiohttp.GitLabBot("gidgetlab")
        client = await aiohttp_client(bot.app)
        response = await client.get("/health")
        assert response.status == 200
        text = await response.text()
        assert text == "Bot OK"
