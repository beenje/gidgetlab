.. gidgetlab documentation master file, created by
   sphinx-quickstart on Wed Jul 25 10:15:22 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

gidgetlab --- An async library for calling GitLab's API
=======================================================

This library is based on gidgethub_ from Brett Cannon,
an async GitHub API library.

I liked the concept with the asynchronous and `sans-I/O <https://sans-io.readthedocs.io/>`_
approach and decided to adapt it to the GitLab's API.
All credit to `Brett Cannon <https://github.com/brettcannon/>`_ for the initial library!

The main goal is to easily write GitLab bots: applications that
run automation on GitLab, using GitLab WebHooks and API.
This was inspired by `Mariatta <https://github.com/Mariatta>`_ PyCon 2018 workshop:
`Build-a-GitHub-Bot Workshop <http://github-bot-tutorial.readthedocs.io/en/latest/index.html>`_.

This project has three primary layers to it. The base layer is
:mod:`gidgetlab.sansio` and :mod:`gidgetlab.routing` which provide the
tools necessary to work with GitLab's API. The next layer up is
:mod:`gidgetlab.abc` which provides an abstract base class for a
cleaner, unified API. Finally, the top layer is using an
implementation of the abstract base class,
e.g. :mod:`gidgetlab.aiohttp`.

The :mod:`gidgetlab.aiohttp` module even provides a :class:`~gidgetlab.aiohttp.GitLabBot` class to easily create an aiohttp web server that responds to GitLab webhooks.

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

**This package requires Python 3.6 or above.**

`Gidgetlab is on PyPI <https://pypi.org/project/gidgetlab/>`_.

::

  python3 -m pip install gidgetlab

To install web server support (e.g. for ``aiohttp``, ``treq``, or ``tornado``), specify it as an extra dependency:

::

  python3 -m pip install gidgetlab[aiohttp]


You can get the source from GitLab: https://gitlab.com/beenje/gidgetlab

::

  git clone https://gitlab.com/beenje/gidgetlab.git


Please use the navigation sidebar on the left to begin.

.. toctree::
   :hidden:
   :maxdepth: 2

   exceptions
   sansio
   routing
   abc
   aiohttp
   treq
   tornado
   changelog


.. _gidgethub: https://github.com/brettcannon/gidgethub
