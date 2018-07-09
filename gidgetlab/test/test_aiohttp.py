import datetime

import aiohttp
import pytest

from .. import aiohttp as gl_aiohttp
from .. import sansio


@pytest.mark.asyncio
async def test_sleep():
    delay = 1
    start = datetime.datetime.now()
    async with aiohttp.ClientSession() as session:
        gl = gl_aiohttp.GitLabAPI(session, "gidgetlab")
        await gl.sleep(delay)
    stop = datetime.datetime.now()
    assert (stop - start) > datetime.timedelta(seconds=delay)


@pytest.mark.asyncio
async def test__request():
    """Make sure that that abstract method is implemented properly."""
    request_headers = sansio.create_headers("gidgetlab")
    async with aiohttp.ClientSession() as session:
        gl = gl_aiohttp.GitLabAPI(session, "gidgetlab")
        aio_call = await gl._request(
            "GET", "https://gitlab.com/api/v4/templates/licenses/mit", request_headers
        )
    data, rate_limit, _ = sansio.decipher_response(*aio_call)
    assert "description" in data


@pytest.mark.asyncio
async def test_get():
    """Integration test."""
    async with aiohttp.ClientSession() as session:
        gl = gl_aiohttp.GitLabAPI(session, "gidgetlab")
        data = await gl.getitem("/templates/licenses/mit")
    assert "description" in data
