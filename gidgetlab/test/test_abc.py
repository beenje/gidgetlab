import json
import pytest
from .. import RedirectionException
from .. import abc as gl_abc


class MockGitLabAPI(gl_abc.GitLabAPI):

    DEFAULT_HEADERS = {
        "ratelimit-limit": "2",
        "ratelimit-remaining": "1",
        "ratelimit-reset": "0",
        "content-type": "application/json",
    }

    def __init__(
        self,
        status_code=200,
        headers=DEFAULT_HEADERS,
        body=b"",
        *,
        url="https://gitlab.com",
        api_version="v4",
        cache=None,
    ):
        self.response_code = status_code
        self.response_headers = headers
        self.response_body = body
        super().__init__(
            "test_abc",
            access_token="access token",
            url=url,
            api_version=api_version,
            cache=cache,
        )

    async def _request(self, method, url, headers, body=b""):
        """Make an HTTP request."""
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        response_headers = self.response_headers.copy()
        try:
            # Don't loop forever.
            del self.response_headers["link"]
        except KeyError:
            pass
        return self.response_code, response_headers, self.response_body

    async def sleep(self, seconds):  # pragma: no cover
        """Sleep for the specified number of seconds."""
        self.slept = seconds


@pytest.mark.asyncio
async def test_url_formatted():
    """The URL is appropriately formatted."""
    gl = MockGitLabAPI()
    await gl._make_request("GET", "/groups/gitlab-org/projects", {}, "")
    assert gl.url == "https://gitlab.com/api/v4/groups/gitlab-org/projects"


@pytest.mark.asyncio
async def test_headers():
    """Appropriate headers are created."""
    gl = MockGitLabAPI()
    await gl._make_request("GET", "/version", {}, "")
    assert gl.headers["user-agent"] == "test_abc"
    assert gl.headers["accept"] == "application/json"
    assert gl.headers["private-token"] == "access token"


@pytest.mark.asyncio
async def test_rate_limit_set():
    """The rate limit is updated after receiving a response."""
    rate_headers = {
        "ratelimit-limit": "42",
        "ratelimit-remaining": "1",
        "ratelimit-reset": "0",
    }
    gl = MockGitLabAPI(headers=rate_headers)
    await gl._make_request("GET", "/rate_limit", {}, "")
    assert gl.rate_limit.limit == 42


@pytest.mark.asyncio
async def test_decoding():
    """Test that appropriate decoding occurs."""
    original_data = {"hello": "world"}
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["content-type"] = "application/json; charset=utf-8"
    gl = MockGitLabAPI(headers=headers, body=json.dumps(original_data).encode("utf8"))
    data, _ = await gl._make_request("GET", "/rate_limit", {}, "")
    assert data == original_data


@pytest.mark.asyncio
async def test_more():
    """The 'next' link is returned appropriately."""
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["link"] = "<https://gitlab.com/api/v4/fake?page=2>; " 'rel="next"'
    gl = MockGitLabAPI(headers=headers)
    _, more = await gl._make_request("GET", "/fake", {}, "")
    assert more == "https://gitlab.com/api/v4/fake?page=2"


@pytest.mark.asyncio
async def test_getitem():
    original_data = {"hello": "world"}
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["content-type"] = "application/json; charset=UTF-8"
    gl = MockGitLabAPI(headers=headers, body=json.dumps(original_data).encode("utf8"))
    data = await gl.getitem("/fake")
    assert gl.method == "GET"
    assert data == original_data


@pytest.mark.asyncio
async def test_getiter():
    """Test that getiter() returns an async iterable as well as query string params."""
    original_data = [1, 2]
    next_url = "https://gitlab.com/api/v4/fake?page=2"
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["content-type"] = "application/json; charset=UTF-8"
    headers["link"] = f'<{next_url}>; rel="next"'
    gl = MockGitLabAPI(headers=headers, body=json.dumps(original_data).encode("utf8"))
    data = []
    async for item in gl.getiter("/fake", {"foo": "stuff"}):
        data.append(item)
    assert gl.method == "GET"
    assert gl.url == "https://gitlab.com/api/v4/fake?page=2&foo=stuff"
    assert len(data) == 4
    assert data[0] == 1
    assert data[1] == 2
    assert data[2] == 1
    assert data[3] == 2


@pytest.mark.asyncio
async def test_post():
    send = [1, 2, 3]
    send_json = json.dumps(send).encode("utf-8")
    receive = {"hello": "world"}
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["content-type"] = "application/json; charset=utf-8"
    gl = MockGitLabAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
    await gl.post("/fake", data=send)
    assert gl.method == "POST"
    assert gl.headers["content-type"] == "application/json; charset=utf-8"
    assert gl.body == send_json
    assert gl.headers["content-length"] == str(len(send_json))


@pytest.mark.asyncio
async def test_patch():
    send = [1, 2, 3]
    send_json = json.dumps(send).encode("utf-8")
    receive = {"hello": "world"}
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["content-type"] = "application/json; charset=utf-8"
    gl = MockGitLabAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
    await gl.patch("/fake", data=send)
    assert gl.method == "PATCH"
    assert gl.headers["content-type"] == "application/json; charset=utf-8"
    assert gl.body == send_json
    assert gl.headers["content-length"] == str(len(send_json))


@pytest.mark.asyncio
async def test_put():
    send = [1, 2, 3]
    send_json = json.dumps(send).encode("utf-8")
    receive = {"hello": "world"}
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["content-type"] = "application/json; charset=utf-8"
    gl = MockGitLabAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
    await gl.put("/fake", data=send)
    assert gl.method == "PUT"
    assert gl.headers["content-type"] == "application/json; charset=utf-8"
    assert gl.body == send_json
    assert gl.headers["content-length"] == str(len(send_json))


@pytest.mark.asyncio
async def test_delete():
    send = [1, 2, 3]
    send_json = json.dumps(send).encode("utf-8")
    receive = {"hello": "world"}
    headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
    headers["content-type"] = "application/json; charset=utf-8"
    gl = MockGitLabAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
    await gl.delete("/fake", data=send)
    assert gl.method == "DELETE"
    assert gl.headers["content-type"] == "application/json; charset=utf-8"
    assert gl.body == send_json
    assert gl.headers["content-length"] == str(len(send_json))


class TestCache:
    @pytest.mark.asyncio
    async def test_if_none_match_sent(self):
        etag = "12345"
        cache = {"https://gitlab.com/api/v4/fake": (etag, None, "hi", None)}
        gl = MockGitLabAPI(cache=cache)
        await gl.getitem("/fake")
        assert "if-none-match" in gl.headers
        assert gl.headers["if-none-match"] == etag

    @pytest.mark.asyncio
    async def test_etag_received(self):
        cache = {}
        etag = "12345"
        headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
        headers["etag"] = etag
        gl = MockGitLabAPI(200, headers, b"42", cache=cache)
        data = await gl.getitem("/fake")
        url = "https://gitlab.com/api/v4/fake"
        assert url in cache
        assert cache[url] == (etag, None, 42, None)
        assert data == cache[url][2]

    @pytest.mark.asyncio
    async def test_if_modified_since_sent(self):
        last_modified = "12345"
        cache = {"https://gitlab.com/api/v4/fake": (None, last_modified, "hi", None)}
        gl = MockGitLabAPI(cache=cache)
        await gl.getitem("/fake")
        assert "if-modified-since" in gl.headers
        assert gl.headers["if-modified-since"] == last_modified

    @pytest.mark.asyncio
    async def test_last_modified_received(self):
        cache = {}
        last_modified = "12345"
        headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
        headers["last-modified"] = last_modified
        gl = MockGitLabAPI(200, headers, b"42", cache=cache)
        data = await gl.getitem("/fake")
        url = "https://gitlab.com/api/v4/fake"
        assert url in cache
        assert cache[url] == (None, last_modified, 42, None)
        assert data == cache[url][2]

    @pytest.mark.asyncio
    async def test_hit(self):
        url = "https://gitlab.com/api/v4/fake"
        cache = {url: ("12345", "67890", 42, None)}
        gl = MockGitLabAPI(304, cache=cache)
        data = await gl.getitem(url)
        assert data == 42

    @pytest.mark.asyncio
    async def test_miss(self):
        url = "https://gitlab.com/api/v4/fake"
        cache = {url: ("12345", "67890", 42, None)}
        headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
        headers["etag"] = "09876"
        headers["last-modified"] = "54321"
        gl = MockGitLabAPI(200, headers, body=b"-13", cache=cache)
        data = await gl.getitem(url)
        assert data == -13
        assert cache[url] == ("09876", "54321", -13, None)

    @pytest.mark.asyncio
    async def test_ineligible(self):
        cache = {}
        gl = MockGitLabAPI(cache=cache)
        url = "https://gitlab.com/api/v4/fake"
        # Only way to force a GET request with a body.
        await gl._make_request("GET", url, {}, 42)
        assert url not in cache
        await gl.post(url, data=42)
        assert url not in cache

    @pytest.mark.asyncio
    async def test_redirect_without_cache(self):
        cache = {}
        gl = MockGitLabAPI(304, cache=cache)
        with pytest.raises(RedirectionException):
            await gl.getitem("/fake")

    @pytest.mark.asyncio
    async def test_no_cache(self):
        headers = MockGitLabAPI.DEFAULT_HEADERS.copy()
        headers["etag"] = "09876"
        headers["last-modified"] = "54321"
        gl = MockGitLabAPI(headers=headers)
        await gl.getitem("/fake")  # No exceptions raised.


class TestFormatUrl:
    def test_absolute_url(self):
        gl = MockGitLabAPI()
        original_url = "https://gitlab.example.com/api/v4/projects"
        url = gl.format_url(original_url, {})
        assert url == original_url

    def test_relative_url(self):
        gl = MockGitLabAPI()
        url = gl.format_url("/projects", {})
        assert url == "https://gitlab.com/api/v4/projects"

    def test_relative_url_non_default_url(self):
        gl = MockGitLabAPI(url="https://my.gitlab.example.org")
        url = gl.format_url("/projects", {})
        assert url == "https://my.gitlab.example.org/api/v4/projects"

    def test_relative_url_non_default_api_version(self):
        gl = MockGitLabAPI(api_version="v3")
        url = gl.format_url("/projects", {})
        assert url == "https://gitlab.com/api/v3/projects"

    def test_params(self):
        gl = MockGitLabAPI()
        url = "https://gitlab.com/api/v4/projects/9/trigger/pipeline"
        params = {"token": "TOKEN", "ref": "master"}
        # Pass params on an absolute URL.
        url = gl.format_url(url, params)
        assert (
            url
            == "https://gitlab.com/api/v4/projects/9/trigger/pipeline?token=TOKEN&ref=master"
        )
        # No parmas on an absolute URL.
        url = gl.format_url(url, {})
        assert url == url
        # Pass params on a relative URL.
        url = gl.format_url("/projects/9/trigger/pipeline", params)
        assert (
            url
            == "https://gitlab.com/api/v4/projects/9/trigger/pipeline?token=TOKEN&ref=master"
        )

    def test_params_quoting(self):
        gl = MockGitLabAPI()
        url = "https://gitlab.com/api/v4/projects/9/trigger/pipeline"
        params = {"token": "TOKEN", "ref": "my branch"}
        url = gl.format_url(url, params)
        assert (
            url
            == "https://gitlab.com/api/v4/projects/9/trigger/pipeline?token=TOKEN&ref=my+branch"
        )

    def test_params_update_existing_query_string(self):
        gl = MockGitLabAPI()
        url = "https://gitlab.com/api/v4/fake?page=1"
        params = {"key1": "value1", "key2": "value2"}
        url = gl.format_url(url, params)
        assert url == "https://gitlab.com/api/v4/fake?page=1&key1=value1&key2=value2"

    def test_params_list_of_items(self):
        gl = MockGitLabAPI()
        url = "https://gitlab.com/api/v4/fake"
        params = {"key1": "value1", "key2": ["value2", "value3"]}
        url = gl.format_url(url, params)
        assert (
            url == "https://gitlab.com/api/v4/fake?key1=value1&key2=value2&key2=value3"
        )
