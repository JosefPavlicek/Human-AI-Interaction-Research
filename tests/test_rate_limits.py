import unittest
from unittest.mock import patch
from email.message import Message
import urllib.error
from analyzer import _retry_seconds, groq_window, Turn

class RateLimitTests(unittest.TestCase):
    def test_retry_after_header(self):
        self.assertEqual(_retry_seconds({'Retry-After':'3'},'',1),4)

    def test_retry_hint(self):
        self.assertAlmostEqual(_retry_seconds({},'Please try again in 2.662499999s.',1),3.662499999)

    @patch('analyzer.time.sleep')
    @patch('analyzer.urllib.request.urlopen')
    def test_429_retries_then_succeeds(self, urlopen, sleep):
        headers=Message(); headers['Retry-After']='2'
        error=urllib.error.HTTPError('https://api.groq.com',429,'rate limit',headers,None)
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,*args): return b'{"choices":[{"message":{"content":"{\\"summary\\":\\"ok\\",\\"events\\":[]}"}}]}'
        urlopen.side_effect=[error,FakeResponse()]
        waits=[]
        result=groq_window([Turn(1,'User','Hello')],'fake-key','test-model',on_wait=lambda *args: waits.append(args))
        self.assertEqual(result['summary'],'ok')
        self.assertEqual(waits,[(3,1,8)])
        sleep.assert_called_once_with(3)

if __name__=='__main__': unittest.main()
