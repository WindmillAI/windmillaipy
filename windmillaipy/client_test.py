import unittest

from client import WindmillClient


class TestWindmillClient(unittest.TestCase):

  def test_get_work_unit(self):
    wm = WindmillClient('key', 'endpoint')
    wu = wm.get_work_unit('xid', 123)

    self.assertEqual(wu.xid, 'xid')
    self.assertEqual(wu.wid, 123)
    self.assertEqual(wu.api_key, 'key')
    self.assertEqual(wu.endpoint, 'endpoint')


if __name__ == '__main__':
  unittest.main()
