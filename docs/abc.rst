:mod:`gidgethub.abc` --- Abstract base class for simplified requests
====================================================================

.. module:: gidgethub.abc

While :mod:`gidgethub.sansio` provides all of the building blocks
necessary to make a request to the GitHub API, it still requires you
to pull together all the requisite parts of a request for the HTTP
library you prefer to use. As that can be repetitive and mostly
boilerplate between HTTP libraries, this module was created to
abstract out the HTTP library being used so all boilerplate could
be taken care.

Users should instantiate an appropriate subclass once for any single
set of calls to the GitHub API. Then one can use the appropriate method
to make requests simply, e.g.::

    # Assume `gh` has an implementation of GitHubAPI.
    data = await gh.getitem("/rate_limit")

This allows one to use the GitHub API directly without dealing with
lower-level details. Most importantly, any changes to the GitHub API
does not require an update to the library, allowing one to use
experimental APIs without issue.


.. class:: GitHubAPI(requester, *, oauth_token=None, cache=None)

    Provide an :py:term:`abstract base class` which abstracts out the
    HTTP library being used to send requests to GitHub. The class is
    initialized with the requester's name and optionally their
    OAuth token and a cache object.

    To allow for
    `conditional requests <https://developer.github.com/v3/#conditional-requests>`_,
    one can provide a :class:`collections.abc.MutableMapping` object
    for the *cache* argument to cache requests. It is up to the
    caching object to provide any caching scheme that is desired
    (e.g. the ``Cache`` classes provided by the
    `cachetools package <https://pypi.org/project/cachetools/>`_).

    There are common arguments across methods that make requests to
    GitHub. The *url_vars* argument is used to perform
    `URI template expansion <https://developer.github.com/v3/#hypermedia>`_
    via :func:`gidgethub.sansio.format_url`.The *accept* argument
    specifies what response format is acceptable and can be
    constructed by using :func:`gidgethub.sansio.accept_format`. For
    methods that send data to GitHub, there is a *data* argument which
    accepts an object which can be serialized to JSON (because
    ``None`` is a legitimate JSON value, ``""`` is used to represent
    no data).

    The returned value for GitHub requests is the decoded body of the
    response according to :func:`gidgethub.sansio.decipher_response`.
    If the status code returned by the HTTP request is anything other
    than ``200``, ``201``, or ``204``, then an appropriate
    :exc:`~gidgethub.HTTPException` is raised.

    .. versionchanged:: 2.0
        Methods no longer automatically sleep when there is a chance
        of exceeding the
        `rate limit <https://developer.github.com/v3/#rate-limiting>`_.
        This leads to :exc:`~gidgethub.RateLimitExceeded` being raised
        when the rate limit has been execeeded.

    .. versionchanged:: 2.3
        Introduced the *cache* argument to the constructor.


    .. attribute:: requester

        The requester's name (typically a GitHub username or project
        name).


    .. attribute:: oauth_token

        The provided OAuth token (if any).


    .. attribute:: rate_limit

        An instance of :class:`gidgethub.sansio.RateLimit`
        representing the last known rate limit imposed upon the user.
        This attribute is automatically updated after every successful
        HTTP request.


    .. abstractcoroutine:: _request(method, url, headers, body=b'')

        An abstract :term:`coroutine` to make an HTTP request. The
        given *headers* will have lower-case keys and include not only
        GitHub-specific fields but also ``content-length`` (and
        ``content-type`` if appropriate).

        The expected return value is a tuple consisting of the status
        code, headers, and the body of the HTTP response. The headers
        dictionary is expected to work with lower-case keys.


    .. abstractcoroutine:: sleep(seconds)

        An abstract :term:`coroutine` which causes the coroutine to
        sleep for the specified number of seconds. This is provided to
        help prevent from going over one's
        `rate limit <https://developer.github.com/v3/#rate-limiting>`_.

        .. versionchanged:: 2.0

            Renamed from ``_sleep()``.


    .. coroutine:: getitem(url, url_vars={}, *, accept=sansio.accept_format())

        Get a single item from GitHub.

        .. note::
            For ``GET`` calls that can return multiple values and
            potentially require pagination, see ``getiter()``.


    .. coroutine:: getiter(url, url_vars={}, *, accept=sansio.accept_format())

        Get all items from a GitHub API endpoint.

        An asynchronous iterable is returned which will yield all items
        from the endpoint (i.e. use ``async for`` on the result). Any
        `pagination <https://developer.github.com/v3/#pagination>`_
        will automatically be followed.

        .. note::
            For ``GET`` calls that return only a single item, see
            :meth:`getitem`.

    .. coroutine:: post(url, url_vars={}, *, data, accept=sansio.accept_format())

        Send a ``POST`` request to GitHub.


    .. coroutine:: patch(url, url_vars={}, *, data, accept=sansio.accept_format())

        Send a ``PATCH`` request to GitHub.


    .. coroutine:: put(url, url_vars={}, *, data=b"", accept=sansio.accept_format())

        Send a ``PUT`` request to GitHub.

        Be aware that some ``PUT`` endpoints such as
        `locking an issue <https://developer.github.com/v3/issues/#lock-an-issue>`_
        will return no content, leading to ``None`` being returned.


    .. coroutine:: delete(url, url_vars={}, *, data=b"", accept=sansio.accept_format())

        Send a ``DELETE`` request to GitHub.
