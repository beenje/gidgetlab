.. gidgetlab documentation master file, created by
   sphinx-quickstart on Wed Jul 25 10:15:22 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

gidgetlab --- An async library for calling GitLab's API
=======================================================

Quick start
-----------

Here is a complete example of a server that responds to
webhooks which will greet the author and say thanks
whenever an issue is opened::

    import os
    import aiohttp
    from aiohttp import web
    from gidgetlab import routing, sansio
    from gidgetlab import aiohttp as gl_aiohttp

    router = routing.Router()

    @router.register("Issue Hook", action="open")
    async def issue_opened_event(event, gl, *args, **kwargs):
        """
        Whenever an issue is opened, greet the author and say thanks.
        """
        print(event)
        url = f"/projects/{event.project_id}/issues/{event.object_attributes['iid']}/notes"
        message = f"Thanks for the report @{event.data['user']['username']}! I will look into it ASAP! (I'm a bot)."
        await gl.post(url, data={"body": message})


    async def main(request):
        body = await request.read()
        secret = os.environ.get("GL_SECRET")
        access_token = os.environ.get("GL_TOKEN")
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        async with aiohttp.ClientSession() as session:
            gl = gl_aiohttp.GitLabAPI(session, "beenje",
                                      access_token=access_token)
            await router.dispatch(event, gl)
        return web.Response(status=200)


    if __name__ == "__main__":
        app = web.Application()
        app.router.add_post("/", main)
        port = os.environ.get("PORT")
        if port is not None:
            port = int(port)
        web.run_app(app, port=port)



Installation
------------

**This package requires Python 3.6 or above.**

`Gidgetlab is on PyPI <https://pypi.org/project/gidgetlab/>`_.

::

  python3 -m pip install gidgetlab


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
