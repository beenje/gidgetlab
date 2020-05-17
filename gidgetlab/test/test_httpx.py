import datetime

import httpx

import pytest

from gidgetlab import httpx as gl_httpx
from gidgetlab import sansio


@pytest.mark.asyncio
async def test_sleep():
    delay = 1
    start = datetime.datetime.now()
    async with httpx.AsyncClient() as client:
        gl = gl_httpx.GitLabAPI(client, "gidgetlab")
        await gl.sleep(delay)
    stop = datetime.datetime.now()
    assert (stop - start) > datetime.timedelta(seconds=delay)


@pytest.mark.asyncio
async def test__request():
    """Make sure that that abstract method is implemented properly."""
    request_headers = sansio.create_headers("gidgetlab")
    async with httpx.AsyncClient() as client:
        gl = gl_httpx.GitLabAPI(client, "gidgetlab")
        aio_call = await gl._request(
            "GET", "https://gitlab.com/api/v4/templates/licenses/mit", request_headers,
        )
    data, rate_limit, _ = sansio.decipher_response(*aio_call)
    assert "description" in data


@pytest.mark.asyncio
async def test_get():
    """Integration test."""
    async with httpx.AsyncClient() as client:
        gl = gl_httpx.GitLabAPI(client, "gidgetlab")
        data = await gl.getitem("/templates/licenses/mit")
    assert "description" in data
