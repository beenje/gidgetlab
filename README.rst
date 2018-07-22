gidgetlab
=========

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

An asynchronous `GitLab API <https://docs.gitlab.com/ce/api/>`_ library.

This library is based on gidgethub_ from Brett Cannon,
an async GitHub API library.

I liked the concept and decided to adapt it to the GitLab API.
All credit to `Brett Cannon <https://github.com/brettcannon/>`_ for the initial library.


Installation
------------

Gidgetlab is `available on PyPI <https://pypi.org/project/gidgetlab/>`_.

::

  python3 -m pip install gidgetlab


Note that the library is still in alpha development stage.

Goals
-----

The key goal is the same as gidgethub_ (but for GitLab):
to provide a base library for the `GitLab API <https://docs.gitlab.com/ce/api/>`_
which performs no I/O of its own (a `sans-I/O <https://sans-io.readthedocs.io/>`_ library).
This allows users to choose whatever HTTP library they prefer while parceling out GitLab-specific
details to this library. This base library is then built upon to provide an
abstract base class to a cleaner API to work with. Finally, implementations of
the abstract base class are provided for asynchronous HTTP libraries for
immediate usage.


Alternative libraries
---------------------

If you think you want a different approach to the GitLab API,
`GitLab maintains a list of libraries <https://about.gitlab.com/applications/#api-clients/>`_.

.. _gidgethub: https://github.com/brettcannon/gidgethub
