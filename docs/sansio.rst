:mod:`gidgetlab.sansio` --- sans-I/O support
============================================

.. module:: gidgetlab.sansio

Webhook events
--------------

`Webhook events <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#events>`_
are represented by :class:`Event` objects. The expectation is that a server will receive
an HTTP request from GitLab and then use :meth:`Event.from_http` to create an
:class:`Event` instance. For example::

  import os
  import aiohttp.web

  SECRET = os.environ["GL_SECRET_TOKEN"]

  async def index(request):
      headers = request.headers
      body = await request.read()
      event = gidgetlab.Event.from_http(headers, body,
                                        secret=SECRET)

This is not required, though, as the :class:`Event` class can be constructed
in a more traditional way.

.. autoclass:: gidgetlab.sansio.Event
   :members:


Calling the GitLab API
----------------------
As well as receiving webhook events in response to actions occurring on GitLab,
you can use the `GitLab API <https://docs.gitlab.com/ee/api/>`_ to make calls
to REST endpoints. This library provides support to both construct a request to
the GitLab API as well as deciphering the response to a request.


Requests
''''''''

This module provides functions to help in the construction of a URL request
by helping to automate the GitLab-specific aspects of a REST call.

::

  import requests

  request_headers = create_headers("beenje", access_token=token)
  url = "https://gitlab.com/api/v4/groups/gitlab-org/projects"
  response = requests.get(url, headers=request_headers)

.. autofunction:: create_headers

Responses
'''''''''

Decipher a response from the GitLab API gather together all of the details
that are provided to you. Continuing from the example in the Requests_ section::

  # Assuming `response` contains a requests.Response object.
  import datetime


  status_code = response.status_code
  headers = response.headers
  body = response.content
  data, rate, more = decipher_response(status_code, headers, body)
  # Response details are in `data`.
  if more:
      if not rate.remaining:
          now = datetime.datetime.now(datetime.tzinfo.utc)
          wait = rate.reset_datetime - now
          time.sleep(wait.total_seconds())
      response_more = requests.get(more, headers=request_headers)
      # Decipher `response_more` ...


.. autofunction:: decipher_response

.. autoclass:: RateLimit

   .. classmethod:: from_http(headers)

        Create a :class:`RateLimit` instance from the HTTP headers of a GitLab API
        response.  Returns ``None`` if the ratelimit is not found in the headers.
