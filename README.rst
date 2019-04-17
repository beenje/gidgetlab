gidgetlab
=========

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

.. image:: https://readthedocs.org/projects/gidgetlab/badge/?version=latest
    :target: https://gidgetlab.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

An asynchronous `GitLab API`_ library.

This library is based on gidgethub_ from Brett Cannon,
an async GitHub API library.

I liked the concept with the asynchronous and `sans-I/O`_
approach and decided to adapt it to the GitLab's API.
All credit to `Brett Cannon <https://github.com/brettcannon/>`_ for the initial library!

Quick start
-----------

Here is a complete example of a server that responds to
webhooks which will greet the author and say thanks
whenever an issue is opened::

    from gidgetlab.aiohttp import GitLabBot

    bot = GitLabBot("beenje")


    @bot.router.register("Issue Hook", action="open")
    async def issue_opened_event(event, gl, *args, **kwargs):
        """Whenever an issue is opened, greet the author and say thanks."""
        url = f"/projects/{event.project_id}/issues/{event.object_attributes['iid']}/notes"
        message = f"Thanks for the report @{event.data['user']['username']}! I will look into it ASAP! (I'm a bot)."
        await gl.post(url, data={"body": message})


    if __name__ == "__main__":
        bot.run()

Installation
------------

Gidgetlab is `available on PyPI <https://pypi.org/project/gidgetlab/>`_.

::

  python3 -m pip install gidgetlab

To install web server support (e.g. for ``aiohttp``, ``treq``, or ``tornado``), specify it as an extra dependency:

::

  python3 -m pip install gidgetlab[aiohttp]

Note that the library is still in alpha development stage.

Goals
-----

The key goal is the same as gidgethub_ (but for GitLab):
to provide an async base library for the `GitLab API`_
which performs no I/O of its own (a `sans-I/O`_ library).

Another goal is to easily write GitLab bots: applications that
run automation on GitLab, using GitLab WebHooks and API.
This was inspired by `Mariatta <https://github.com/Mariatta>`_ PyCon 2018 workshop:
`Build-a-GitHub-Bot Workshop <http://github-bot-tutorial.readthedocs.io/en/latest/index.html>`_.


Alternative libraries
---------------------

If you think you want a different approach to the GitLab API,
`GitLab maintains a list of libraries <https://about.gitlab.com/applications/#api-clients/>`_.

.. _gidgethub: https://github.com/brettcannon/gidgethub
.. _`GitLab API`: https://docs.gitlab.com/ce/api/
.. _`sans-I/O`: https://sans-io.readthedocs.io/
