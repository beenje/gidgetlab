:mod:`gidgetlab.abc` --- Abstract base class for simplified requests
====================================================================

.. module:: gidgetlab.abc

While :mod:`gidgetlab.sansio` provides all of the building blocks
necessary to make a request to the GitLab API, it still requires you
to pull together all the requisite parts of a request for the HTTP
library you prefer to use. As that can be repetitive and mostly
boilerplate between HTTP libraries, this module was created to
abstract out the HTTP library being used so all boilerplate could
be taken care.

Users should instantiate an appropriate subclass once for any single
set of calls to the GitLab API.
By default, the official `https://gitlab.com` service is used.
It's easy to use a private GitLab instance by passing the *url*
parameter::

  gl = GitLabAPI(requester, url="https://mygitlab.example.com")

Then one can use the appropriate method to make requests simply, e.g.::

    # Assume `gl` has an implementation of GitLabAPI.
    data = await gl.getitem("/templates/licenses/MIT")

This allows one to use the GitLab API directly without dealing with
lower-level details. Most importantly, any changes to the GitLab API
does not require an update to the library, allowing one to use
experimental APIs without issue.


.. autoclass:: GitLabAPI
   :members:
   :member-order: bysource

    .. attribute:: requester

        The requester's name (typically a GitLab username or group
        name).

    .. attribute:: access_token

        The provided access token (if any).

    .. attribute:: api_url

        The GitLab API url constructed with the url and api_version optional parameters.
        Default to https://gitlab.com/api/v4.
        Can be set to a private GitLab instance by setting the **url** parameter.

    .. attribute:: rate_limit

        An instance of :class:`gidgetlab.sansio.RateLimit`
        representing the last known rate limit imposed upon the user.
        This attribute is automatically updated after every successful
        HTTP request.
