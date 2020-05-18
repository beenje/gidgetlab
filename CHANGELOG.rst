Changelog
=========

0.6.0 (2020-05-18)
------------------

* Add httpx support
* Add Python 3.8 tests
* Move tests outside package to fix coverage
* Add pipeline, coverage and pre-commit badges
* Add py.typed file (PEP 561)
* Switch to RTD's default theme

0.5.0 (2019-07-08)
------------------

* Allow to pass an optional SSLContext to GitLabBot (thanks to Clément Moyroud)
* Allow the bot to not wait for consistency

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
