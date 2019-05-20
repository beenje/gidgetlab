Changelog
=========

0.4.0 (2019-05-20)
------------------

* Add 202 as expected response from GitLab
* Fix mypy warnings about the ``Dict`` and ``Mapping`` generic types lacking
  type parameters (taken from gidgethub)
* Add /health endpoint to the bot

0.3.1 (2019-04-17)
------------------

* Allow to pass any keyword arguments to aiohttp.web.run_app()
  from bot.run() to configure port, logging...
* Improve documentation (thanks to Jon McKenzie)

0.3.0 (2018-08-21)
------------------

* Add a GitLabBot class

0.2.0 (2018-08-18)
------------------

* Replace URI template with query string params

0.1.0 (2018-07-22)
------------------

* Initial release
