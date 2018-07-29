:mod:`gidgetlab.routing` --- A router for webhook events
========================================================

.. module:: gidgetlab.routing

When a single web service is used to perform multiple actions based on
a single
`webhook event <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#events>`_,
it is easier to do those multiple steps in some sort of routing mechanism
to make sure the right objects are called is provided. This module is
meant to provide such a router for :class:`gidgetlab.sansio.Event`
instances. This allows for individual ``async`` functions to be
written per event type to help keep logic separated and focused
instead of having to differentiate between different events manually
in user code.


.. autoclass:: gidgetlab.routing.Router
   :members:
