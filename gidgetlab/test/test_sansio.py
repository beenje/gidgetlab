import datetime
import os
import http
import json
import pathlib
import pytest
from .. import (
    BadRequest,
    GitLabBroken,
    HTTPException,
    InvalidField,
    RateLimitExceeded,
    RedirectionException,
    ValidationFailure,
)
from .. import sansio

SAMPLES_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "samples")


def sample(directory, status_code):
    headers = {}
    headers_path = os.path.join(SAMPLES_PATH, directory, f"{status_code}.headers")
    with open(headers_path, "r") as f:
        for line in f:
            if line:
                key, _, value = line.partition(":")
                headers[key.lower().strip()] = value.strip()
    body_path = os.path.join(SAMPLES_PATH, directory, "body")
    with open(body_path, "rb") as f:
        body = f.read()
    return headers, body


class TestEvent:

    """Tests for gidgetlab.sansio.Event."""

    data = {"object_kind": "push"}
    data_bytes = '{"object_kind": "push"}'.encode("UTF-8")
    secret = "123456"
    headers = {
        "content-type": "application/json",
        "x-gitlab-event": "Push Hook",
        "x-gitlab-token": secret,
    }

    def check_event(self, event):
        """Check that an event matches the test data provided by the class."""
        assert event.event == self.headers["x-gitlab-event"]
        assert event.data == self.data
        assert event.secret == self.headers["x-gitlab-token"]

    def test_init(self):
        ins = sansio.Event(
            self.data, event=self.headers["x-gitlab-event"], secret=self.secret
        )
        self.check_event(ins)

    def test_from_http_json(self):
        """Construct an event from complete HTTP information."""
        event = sansio.Event.from_http(
            self.headers, self.data_bytes, secret=self.secret
        )
        self.check_event(event)

    def test_from_http_urlencoded(self):
        headers, body = sample("push", 200)
        event = sansio.Event.from_http(headers, body, secret="my-secret-token")
        assert event.data["object_kind"] == "push"

    def test_from_http_no_content_type(self):
        """Only accept data when content-type is application/json."""
        headers_no_content_type = self.headers.copy()
        del headers_no_content_type["content-type"]
        with pytest.raises(BadRequest):
            sansio.Event.from_http(
                headers_no_content_type, self.data_bytes, secret=self.secret
            )

    def test_from_http_unknown_content_type(self):
        headers = headers = {
            "content-type": "image/png",
            "x-gitlab-event": "Push Hook",
            "x-gitlab-token": "123456",
        }
        with pytest.raises(BadRequest):
            sansio.Event.from_http(headers, self.data_bytes, secret=self.secret)

    def test_from_http_missing_secret(self):
        """Signature but no secret raises ValidationFailure."""
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(self.headers, self.data_bytes)

    def test_from_http_missing_token(self):
        """Secret but no x-gitlab-token raises ValidationFailure."""
        headers_no_token = self.headers.copy()
        del headers_no_token["x-gitlab-token"]
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(
                headers_no_token, self.data_bytes, secret=self.secret
            )

    def test_from_http_bad_secret(self):
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(self.headers, self.data_bytes, secret="bad secret")

    def test_from_http_no_token(self):
        headers = self.headers.copy()
        del headers["x-gitlab-token"]
        event = sansio.Event.from_http(headers, self.data_bytes)
        assert event.event == self.headers["x-gitlab-event"]
        assert event.data == self.data
        assert event.secret is None

    def test_event_without_project_id(self):
        event = sansio.Event.from_http(
            self.headers, self.data_bytes, secret=self.secret
        )
        with pytest.raises(AttributeError):
            event.project_id

    def test_event_with_project_id(self):
        data_bytes = '{"object_kind": "push", "project": {"id": 42}}'.encode("UTF-8")
        event = sansio.Event.from_http(self.headers, data_bytes, secret=self.secret)
        assert event.project_id == 42


class TestCreateHeaders:

    """Tests for gidgetlab.sansio.create_headers()."""

    def test_common_case(self):
        user_agent = "brettcannon"
        access_token = "secret"
        headers = sansio.create_headers(user_agent, access_token=access_token)
        assert headers["user-agent"] == user_agent
        assert headers["accept"] == "application/json"
        assert headers["private-token"] == access_token

    def test_all_keys_lowercase(self):
        """Test all header fields are lowercase."""
        user_agent = "brettcannon"
        access_token = "secret"
        headers = sansio.create_headers(user_agent, access_token=access_token)
        assert len(headers) == 3
        for key in headers.keys():
            assert key == key.lower()


class TestRateLimit:
    def test_init(self):
        left = 42
        rate = 64
        reset = datetime.datetime.now(datetime.timezone.utc)
        rate_limit = sansio.RateLimit(
            remaining=left, limit=rate, reset_epoch=reset.timestamp()
        )
        assert rate_limit.remaining == left
        assert rate_limit.limit == rate
        assert rate_limit.reset_datetime == reset

    def test_bool(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        year_from_now = now + datetime.timedelta(365)
        year_ago = now - datetime.timedelta(365)
        # Requests left.
        rate = sansio.RateLimit(
            remaining=1, limit=1, reset_epoch=year_from_now.timestamp()
        )
        assert rate
        # Reset passed.
        rate = sansio.RateLimit(remaining=0, limit=1, reset_epoch=year_ago.timestamp())
        assert rate
        # No requests and reset not passed.
        rate = sansio.RateLimit(
            remaining=0, limit=1, reset_epoch=year_from_now.timestamp()
        )
        assert not rate

    def test_from_http(self):
        left = 42
        rate = 65
        reset = datetime.datetime.now(datetime.timezone.utc)
        headers = {
            "ratelimit-limit": str(rate),
            "ratelimit-remaining": str(left),
            "ratelimit-reset": str(reset.timestamp()),
        }
        rate_limit = sansio.RateLimit.from_http(headers)
        assert rate_limit.limit == rate
        assert rate_limit.remaining == left
        assert rate_limit.reset_datetime == reset

    def test___str__(self):
        left = 4200
        rate = 65000
        reset = datetime.datetime.now(datetime.timezone.utc)
        message = str(
            sansio.RateLimit(limit=rate, remaining=left, reset_epoch=reset.timestamp())
        )
        assert format(left, ",") in message
        assert format(rate, ",") in message
        assert str(reset) in message

    def test_from_http_no_ratelimit(self):
        headers = {}
        rate_limit = sansio.RateLimit.from_http(headers)
        assert rate_limit is None


def sample2(directory, status_code):
    # pytest doesn't set __spec__.origin :(
    sample_dir = pathlib.Path(__file__).parent / "samples" / directory
    headers_path = sample_dir / f"{status_code}.json"
    with headers_path.open("r") as file:
        headers = json.load(file)
    body = (sample_dir / "body").read_bytes()
    return headers, body


class TestDecipherResponse:

    """Tests for gidgetlab.sansio.decipher_response()."""

    def test_5XX(self):
        status_code = 502
        with pytest.raises(GitLabBroken) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_4XX_no_message(self):
        status_code = 400
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_4XX_message(self):
        status_code = 400
        message = json.dumps({"message": "it went bad"}).encode("UTF-8")
        headers = {"content-type": "application/json; charset=utf-8"}
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, headers, message)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "it went bad"

    def test_404(self):
        status_code = 404
        headers, body = sample("invalid", status_code)
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "Not Found"

    def test_403_rate_limit_exceeded(self):
        status_code = 403
        headers = {
            "content-type": "application/json; charset=utf-8",
            "ratelimit-limit": "2",
            "ratelimit-remaining": "0",
            "ratelimit-reset": "1",
        }
        body = json.dumps({"message": "oops"}).encode("UTF-8")
        with pytest.raises(RateLimitExceeded) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_403_forbidden(self):
        status_code = 403
        headers = {
            "content-type": "application/json; charset=utf-8",
            "ratelimit-limit": "2",
            "ratelimit-remaining": "1",
            "ratelimit-reset": "1",
        }
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, headers, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_422(self):
        status_code = 422
        errors = [{"resource": "Issue", "field": "title", "code": "missing_field"}]
        body = json.dumps({"message": "it went bad", "errors": errors})
        body = body.encode("utf-8")
        headers = {"content-type": "application/json; charset=utf-8"}
        with pytest.raises(InvalidField) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "it went bad for 'title'"

    def test_422_no_errors_object(self):
        status_code = 422
        body = json.dumps(
            {
                "message": "Reference does not exist",
                "documentation_url": "https://developer.github.com/v3/git/refs/#delete-a-reference",
            }
        )
        body = body.encode("utf-8")
        headers = {"content-type": "application/json; charset=utf-8"}
        with pytest.raises(InvalidField) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "Reference does not exist"

    def test_3XX(self):
        status_code = 301
        with pytest.raises(RedirectionException) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_2XX_error(self):
        status_code = 205
        with pytest.raises(HTTPException) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_200(self):
        status_code = 200
        headers, body = sample("projects_single", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 597
        assert data[0]["ssh_url_to_repo"] == "git@gitlab.com:beenje/gitlab-ce.git"

    def test_201(self):
        """Test a 201 response along with non-pagination Link header."""
        status_code = 201
        headers = {
            "ratelimit-limit": "60",
            "ratelimit-remaining": "50",
            "ratelimit-reset": "12345678",
            "content-type": "application/json; charset=utf-8",
            "link": '<http://example.com>; test="unimportant"',
        }
        data = {
            "id": 208045946,
            "url": "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab-ce/labels",
            "name": "bug",
            "color": "f29513",
        }
        body = json.dumps(data).encode("UTF-8")
        returned_data, rate_limit, more = sansio.decipher_response(
            status_code, headers, body
        )
        assert more is None
        assert rate_limit.limit == 60
        assert returned_data == data

    def test_202(self):
        """Test both a 202 response and an empty response body."""
        status_code = 202
        headers, body = sample("delete_registry_repository", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 599
        assert data is None

    def test_204(self):
        """Test both a 204 response and an empty response body."""
        status_code = 204
        headers, body = sample("delete_tag", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 594
        assert data is None

    def test_next(self):
        status_code = 200
        headers, body = sample("projects_page_1", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert (
            more
            == "https://gitlab.com/api/v4/groups/gitlab-org/projects?archived=false&id=gitlab-org&order_by=created_at&owned=false&page=2&per_page=20&simple=false&sort=desc&starred=false&with_custom_attributes=false&with_issues_enabled=false&with_merge_requests_enabled=false"
        )
        assert rate_limit.remaining == 598
        assert data[0]["name"] == "many-branches"

        headers, body = sample("projects_page_2", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert (
            more
            == "https://gitlab.com/api/v4/groups/gitlab-org/projects?archived=false&id=gitlab-org&order_by=created_at&owned=false&page=3&per_page=20&simple=false&sort=desc&starred=false&with_custom_attributes=false&with_issues_enabled=false&with_merge_requests_enabled=false"
        )
        assert rate_limit.remaining == 598
        assert data[0]["name"] == "gitlab-svgs"

        headers, body = sample("projects_page_last", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 599
        assert data[0]["name"] == "GitLab CI"

    def test_no_ratelimit(self):
        """Test no ratelimit in headers."""
        status_code = 201
        headers = {
            "content-type": "application/json; charset=utf-8",
            "link": '<http://example.com>; test="unimportant"',
        }
        data = {
            "id": 208045946,
            "url": "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab-ce/labels",
            "name": "bug",
            "color": "f29513",
        }
        body = json.dumps(data).encode("UTF-8")
        returned_data, rate_limit, more = sansio.decipher_response(
            status_code, headers, body
        )
        assert more is None
        assert rate_limit is None
        assert returned_data == data
