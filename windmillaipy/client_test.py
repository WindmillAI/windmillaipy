import json
import unittest
from unittest.mock import patch
import windmillaipy


class MockResponse(object):
  def __init__(self, ok, json_data):
    self.ok = ok
    self.json_data = json_data

  def json(self):
    return self.json_data


class TestWindmillClient(unittest.TestCase):

  @patch('requests.post')
  def test_create_basic_experiment(self, mpost):
    mpost.return_value = MockResponse(True, {
        'work_units': [{
            'xid': 'asdf',
            'wid': 25,
          }]})

    wm = windmillaipy.WindmillClient('key', 'endpoint')
    wu = wm.create_experiment('some experiment')

    mpost.assert_called_once_with(
        'endpoint/api/v0/create_experiment',
        json={'api_key': 'key', 'name': 'some experiment'})

    self.assertEqual(wu.xid, 'asdf')
    self.assertEqual(wu.wid, 25)
    self.assertEqual(wu.api_key, 'key')
    self.assertEqual(wu.endpoint, 'endpoint')

  @patch('requests.post')
  def test_create_experiment_with_multiple_work_units(self, mpost):
    mpost.return_value = MockResponse(True, {
        'work_units': [{
            'xid': 'asdf',
            'wid': 1,
          }, {
            'xid': 'asdf',
            'wid': 2,
          }, {
            'xid': 'asdf',
            'wid': 3,
          }]})

    wm = windmillaipy.WindmillClient('key', 'endpoint')
    wus = wm.create_experiment('some experiment', parameters=[{}, {}, {}])

    mpost.assert_called_once_with(
        'endpoint/api/v0/create_experiment',
        json={
          'api_key': 'key',
          'name': 'some experiment',
          'parameters': [{}, {}, {}]
          })

    self.assertEqual(len(wus), 3)
    self.assertEqual(wus[0].xid, 'asdf')
    self.assertEqual(wus[0].wid, 1)
    self.assertEqual(wus[0].api_key, 'key')
    self.assertEqual(wus[0].endpoint, 'endpoint')
    self.assertEqual(wus[1].xid, 'asdf')
    self.assertEqual(wus[1].wid, 2)
    self.assertEqual(wus[1].api_key, 'key')
    self.assertEqual(wus[1].endpoint, 'endpoint')
    self.assertEqual(wus[2].xid, 'asdf')
    self.assertEqual(wus[2].wid, 3)
    self.assertEqual(wus[2].api_key, 'key')
    self.assertEqual(wus[2].endpoint, 'endpoint')


  @patch('requests.post')
  def test_create_experiment_with_tags(self, mpost):
    mpost.return_value = MockResponse(True, {
        'work_units': [{
            'xid': 'asdf',
            'wid': 25,
          }]})

    wm = windmillaipy.WindmillClient('key', 'endpoint')
    wu = wm.create_experiment('some experiment', tags=['some', 'tags'])

    mpost.assert_called_once_with(
        'endpoint/api/v0/create_experiment',
        json={'api_key': 'key', 'name': 'some experiment',
              'tags': ['some', 'tags']})

    self.assertEqual(wu.xid, 'asdf')
    self.assertEqual(wu.wid, 25)
    self.assertEqual(wu.api_key, 'key')
    self.assertEqual(wu.endpoint, 'endpoint')


  @patch('requests.get')
  def test_get_work_unit_no_remote_check(self, mget):
    wm = windmillaipy.WindmillClient('key', 'endpoint')
    wu = wm.get_work_unit('xid', 123, verify_exists=False)

    mget.assert_not_called()

    self.assertEqual(wu.xid, 'xid')
    self.assertEqual(wu.wid, 123)
    self.assertEqual(wu.api_key, 'key')
    self.assertEqual(wu.endpoint, 'endpoint')


  @patch('requests.get')
  def test_get_work_unit_where_work_unit_exists(self, mget):
    mget.return_value = MockResponse(True, {'exists': True})

    wm = windmillaipy.WindmillClient('key', 'endpoint')
    wu = wm.get_work_unit('some xid', 123)

    mget.assert_called_once_with(
        'endpoint/api/v0/verify_work_unit_exists',
        params={'api_key': 'key', 'xid': 'some xid', 'wid': 123})

    self.assertEqual(wu.xid, 'some xid')
    self.assertEqual(wu.wid, 123)
    self.assertEqual(wu.api_key, 'key')
    self.assertEqual(wu.endpoint, 'endpoint')


  @patch('requests.get')
  def test_get_work_unit_where_work_unit_does_not_exist(self, mget):
    mget.return_value = MockResponse(True, {'exists': False})

    wm = windmillaipy.WindmillClient('key', 'endpoint')
    with self.assertRaises(windmillaipy.WindmillClientError):
      wm.get_work_unit('some xid', 123)

    mget.assert_called_once_with(
        'endpoint/api/v0/verify_work_unit_exists',
        params={'api_key': 'key', 'xid': 'some xid', 'wid': 123})


  @patch('requests.get')
  def test_get_parameters_empty_parameters(self, mget):
    mget.return_value = MockResponse(True, {})

    wu = windmillaipy.WorkUnit('some xid', 123, 'key', 'endpoint')
    parameters = wu.get_parameters()

    mget.assert_called_once_with(
        'endpoint/api/v0/get_work_unit_parameters',
        params={'api_key': 'key', 'xid': 'some xid', 'wid': 123})

    self.assertEqual(parameters, {})


  @patch('requests.get')
  def test_get_parameters_some_parameters(self, mget):
    mget.return_value = MockResponse(True, {'rate': 4.32})

    wu = windmillaipy.WorkUnit('some xid', 123, 'key', 'endpoint')
    parameters = wu.get_parameters()

    mget.assert_called_once_with(
        'endpoint/api/v0/get_work_unit_parameters',
        params={'api_key': 'key', 'xid': 'some xid', 'wid': 123})

    self.assertEqual(parameters, {'rate': 4.32})


  @patch('requests.post')
  def test_complete(self, mpost):
    mpost.return_value = MockResponse(True, {})

    wu = windmillaipy.WorkUnit('xid', 123, 'key', 'endpoint')
    wu.complete()

    mpost.assert_called_once_with(
        'endpoint/api/v0/complete_experiment',
        json={'api_key': 'key', 'xid': 'xid', 'wid': 123})


if __name__ == '__main__':
  unittest.main()
