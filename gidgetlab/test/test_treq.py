import datetime

from twisted.internet.defer import ensureDeferred
from twisted.trial.unittest import TestCase
from .. import treq as gl_treq
from .. import sansio

import treq._utils


class TwistedPluginTestCase(TestCase):
    @staticmethod
    def create_cleanup(gl):
        def cleanup(_):
            # We do this just to shut up Twisted.
            pool = treq._utils.get_global_pool()
            pool.closeCachedConnections()

            # We need to sleep to let the connections hang up.
            return ensureDeferred(gl.sleep(0.5))

        return cleanup

    def test_sleep(self):
        delay = 1
        start = datetime.datetime.now()
        gl = gl_treq.GitLabAPI("gidgetlab")

        def test_done(ignored):
            stop = datetime.datetime.now()
            self.assertTrue((stop - start) > datetime.timedelta(seconds=delay))

        d = ensureDeferred(gl.sleep(delay))
        d.addCallback(test_done)
        return d

    def test__request(self):
        request_headers = sansio.create_headers("gidgetlab")
        gl = gl_treq.GitLabAPI("gidgetlab")
        d = ensureDeferred(
            gl._request(
                "GET",
                "https://gitlab.com/api/v4/templates/licenses/mit",
                request_headers,
            )
        )

        def test_done(response):
            data, rate_limit, _ = sansio.decipher_response(*response)
            self.assertIn("description", data)

        d.addCallback(test_done)
        d.addCallback(self.create_cleanup(gl))
        return d

    def test_get(self):
        gl = gl_treq.GitLabAPI("gidgetlab")
        d = ensureDeferred(gl.getitem("/templates/licenses/mit"))

        def test_done(response):
            self.assertIn("description", response)

        d.addCallback(test_done)
        d.addCallback(self.create_cleanup(gl))
        return d
