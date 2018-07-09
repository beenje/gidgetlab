import datetime

import pytest
import tornado

from tornado.testing import AsyncTestCase

from .. import BadRequest
from .. import sansio
from .. import tornado as gl_tornado


class TornadoTestCase(AsyncTestCase):
    @tornado.testing.gen_test
    async def test_sleep(self):
        delay = 1
        start = datetime.datetime.now()
        gl = gl_tornado.GitLabAPI("gidgetlab")
        await gl.sleep(delay)
        stop = datetime.datetime.now()
        assert (stop - start) > datetime.timedelta(seconds=delay)

    @tornado.testing.gen_test
    async def test__request(self):
        """Make sure that that abstract method is implemented properly."""
        request_headers = sansio.create_headers("gidgetlab")
        gl = gl_tornado.GitLabAPI("gidgetlab")
        tornado_call = await gl._request(
            "GET", "https://gitlab.com/api/v4/templates/licenses/mit", request_headers
        )
        data, rate_limit, _ = sansio.decipher_response(*tornado_call)
        assert "description" in data

    @tornado.testing.gen_test
    async def test__request_with_body(self):
        """Make sure that that abstract method is implemented properly."""
        request_headers = sansio.create_headers("gidgetlab")
        gl = gl_tornado.GitLabAPI("gidgetlab")
        # This leads to a 404.
        tornado_call = await gl._request(
            "POST",
            "https://gitlab.com/api/v4/templates/licenses/mit",
            request_headers,
            b"bogus",
        )
        with pytest.raises(BadRequest):
            sansio.decipher_response(*tornado_call)

    @tornado.testing.gen_test
    async def test_get(self):
        """Integration test."""
        gl = gl_tornado.GitLabAPI("gidgetlab")
        data = await gl.getitem("/templates/licenses/mit")
        assert "description" in data
