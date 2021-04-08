from __future__ import annotations

import json
import io
import os
import requests
import tarfile

from typing import List


# Hardcode the endpoint base address. Can be overwritten when creating a new
# client or via the WINDMILLAI_ENDPOINT environment variable.
WINDMILLAI_ENDPOINT = 'https://www.windmillai.com'


class WindmillClientError(Exception):
  pass


# A quick util function to give Exceptions raised from client better error
# messages.
def _raise_if_error(r):
  if not r.ok:
    raise WindmillClientError(r.text)


class WindmillClient(object):
  'A client for interfacing with WindmillAI.'

  def __init__(
      self,
      api_key: str = os.environ.get('WINDMILLAI_API_KEY'),
      endpoint: int = os.environ.get('WINDMILLAI_ENDPOINT') or WINDMILLAI_ENDPOINT):
    self.api_key = api_key
    self.endpoint = endpoint

  def create_experiment(
      self, experiment_name: str, tags: List[str]=None) -> WorkUnit:
    'Creates a new experiment with a single work unit and returns it.'

    request = {
      'api_key': self.api_key,
      'name': experiment_name,
      'tags': tags,
    }
    url = '{}/api/v0/create_experiment'.format(self.endpoint)
    response = requests.post(url, json=request)
    _raise_if_error(response)

    response = response.json()
    return WorkUnit(
        response['xid'], response['wid'], self.api_key, self.endpoint)

  def get_work_unit(self, xid: str, wid: int) -> WorkUnit:
    'Returns the work unit corresponding to an xid / wid pair.'

    # TODO: We should do a remote check here to make sure xid/wid is a valid
    # and active experiment.
    return WorkUnit(xid, wid, self.api_key, self.endpoint)


class WorkUnit(object):
  'An object corresponding to a particular xid/wid run.'

  def __init__(
      self,
      xid: str,
      wid: int,
      api_key: str = os.environ.get('WINDMILLAI_API_KEY'),
      endpoint: str = os.environ.get('WINDMILLAI_ENDPOINT') or WINDMILLAI_ENDPOINT):
    self.xid: str = xid
    self.wid: int = wid
    self.api_key: str = api_key
    self.endpoint: str = endpoint

  def add_diary_entry(self, entry: str):
    request = {
      'api_key': self.api_key,
      'xid': self.xid,
      'entry': entry
    }
    url = '{}/api/v0/add_diary_entry'.format(self.endpoint)
    _raise_if_error(requests.post(url, json=request))

  def record_measurements(self, measurements):
    request = {
      'api_key': self.api_key,
      'xid': self.xid,
      'wid': self.wid,
      'measurements': measurements,
    }
    url = '{}/api/v0/add_measurements'.format(self.endpoint)
    _raise_if_error(requests.post(url, json=request))

  def complete_experiment(self):
    request = {
      'api_key': self.api_key,
      'xid': self.xid,
    }
    url = '{}/api/v0/complete_experiment'.format(self.endpoint)
    _raise_if_error(requests.post(url, json=request))

  def register_signal(self, signal: str) -> None:
    'Registers a new signal, i.e., adds the name with the signal inactive.'

    request = {
      'api_key': self.api_key,
      'xid': self.xid,
      'wid': self.wid,
      'signal': signal,
    }
    url = '{}/api/v0/register_signal'.format(self.endpoint)
    _raise_if_error(requests.post(url, json=request))

  def activate_signal(self, signal: str) -> None:
    'Activates a signal.'

    request = {
      'api_key': self.api_key,
      'xid': self.xid,
      'wid': self.wid,
      'signal': signal,
    }
    url = '{}/api/v0/activate_signal'.format(self.endpoint)
    _raise_if_error(requests.post(url, json=request))

  def deactivate_signal(self, signal: str) -> None:
    'Deactivates a signal.'

    request = {
      'api_key': self.api_key,
      'xid': self.xid,
      'wid': self.wid,
      'signal': signal,
    }
    url = '{}/api/v0/deactivate_signal'.format(self.endpoint)
    _raise_if_error(requests.post(url, json=request))

  def check_signal_active(self, signal: str, deactivate: bool=False) -> None:
    '''Checks if the signal is active.

    If clear is True this will deactivate the signal after observing it.'''

    payload = {
      'api_key': self.api_key,
      'xid': self.xid,
      'wid': self.wid,
      'signal': signal,
      'clear': deactivate,
    }
    url = '{}/api/v0/check_signal_active'.format(self.endpoint)
    response = requests.get(url, params=payload)
    _raise_if_error(response)
    return response.json()['active']

  def create_artifact(self, filename: str, contents: str) -> None:
    '''Upload a new artifact for an experiment for raw file contents.
    '''
    url = '{}/api/v0/create_artifact?upload-type=multipart'.format(
      self.endpoint)
    meta = {
      'xid': self.xid,
      'wid': self.wid,
      'filename': filename
    }
    _raise_if_error(requests.post(url, files={
      'meta': json.dumps(meta),
      'contents': contents
    }))

  def create_artifact_from_file(
      self, filename: str, local_filepath: str) -> None:
    '''Upload a new artifact for an experiment from a file on disk.

    filename is the name the file be saved under in Beaker. local_filepath is
    the path to the file on the local machine.
    '''

    with open(local_filepath, 'rb') as f:
      self.create_artifact(filename, f.read())

  def _create_archive_from_directory(
      self, directory: str, filename: str) -> io.BytesIO:
    '''Creates a gzipped archive from a folder.

    Common usage:
      self._create_archive_from_directory('/tmp/learned', 'snapshot.tgz')'''

    f = io.BytesIO()
    with tarfile.open(fileobj=f, mode='w:gz') as tar:
      tar.add(directory, arcname='.')

    return f

  def create_artifact_from_directory(
      self, filename: str, local_directory_path: str) -> None:
    '''Upload a new artifact for an experiment from a directory on disk.

    filename is the name the tar'ed directory will be saved under in Beaker.
    local_filepath is the path to the directory on the local machine.
    '''
    f: io.BytesIO = self._create_archive_from_directory(
        local_directory_path, filename)
    data = f.getvalue()
    self.create_artifact(filename, data)
