import argparse
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from synology_dsm import SynologyDSM
from synology_dsm.exceptions import (SynologyDSMLogin2SAFailedException,
                                     SynologyDSMLogin2SARequiredException)

app = FastAPI()

TARGETS_PATH = 'targets.json'

def get_targets():
  """Get targets from disk."""
  path = Path(TARGETS_PATH)

  # Only parse file if exists and non-empty
  if path.is_file():
    with open(TARGETS_PATH) as f:
      f.seek(0)
      if f.read(1):
        f.seek(0)
        return json.load(f)
  
  return []

def write_targets(targets):
  """Write targets to disk."""
  with open(TARGETS_PATH, 'w') as f:
    json.dump(targets, f)

def add_host():
  """Add host to targets."""
  host = input('Host: ')
  port = input('Port [5000]: ') or 5000
  username = input('Username: ')
  password = input('Password: ')
  otp_code = None

  api = SynologyDSM(host, port, username, password)

  # Check if we need 2FA-Code
  while True:
    try:
      api.login(otp_code)
      break
    except SynologyDSMLogin2SARequiredException:
      otp_code = input('2FA code: ') or None
    except SynologyDSMLogin2SAFailedException:
      print('Wrong code. Please try again!')
      otp_code = input('2FA code: ') or None

  target = {
    'host': host,
    'port': port,
    'username': username,
    'password': password,
    'device_token': api.device_token if hasattr(api, 'device_token') else None
  }

  targets = get_targets()

  # Remove existing host (if exists)
  targets = [t for t in targets if not (t.get('host') != host)]
  targets.append(target)

  write_targets(targets)

  print('Host added.')

def get_nas_info(api: SynologyDSM):
  """Get general NAS info."""
  return ('# HELP synology_dsm_version_info DSM version\n'
          '# TYPE synology_dsm_version_info gauge\n'
          f'''dsm_version_info{{"version={api.information.version_string}"}} 1\n'''
          '# HELP synology_temperature NAS Temperature in degrees celsius\n'
          '# TYPE synology_temperature gauge\n'
          f'''synology_temperature {api.information.temperature}\n'''
          '# HELP synology_temperature_warning If NAS has temperature warning\n'
          '# TYPE synology_temperature_warning gauge\n'
          f'''synology_temperature_warning {api.information.temperature_warn}\n'''
          '# HELP synology_uptime Uptime\n'
          '# TYPE synology_uptime gauge\n'
          f'''synology_uptime {api.information.uptime}\n'''
          '# HELP synology_cpu_load CPU load in percent\n'
          '# TYPE synology_cpu_load gauge\n'
          f'''synology_cpu_load {api.utilisation.cpu_total_load}\n'''
          '# HELP synology_memory_usage Memory usage in percent\n'
          '# TYPE synology_memory_usage gauge\n'
          f'''synology_memory_usage {api.utilisation.memory_real_usage}\n'''
          '# HELP synology_network_up_bytes Network traffic upload in bytes\n'
          '# TYPE synology_network_up_bytes gauge\n'
          f'''synology_network_up_bytes {api.utilisation.network_up()}\n'''
          '# HELP synology_network_down_bytes Network traffic download in bytes\n'
          '# TYPE synology_network_down_bytes gauge\n'
          f'''synology_network_down_bytes {api.utilisation.network_down()}\n'''
          '# HELP synology_success Displays whether or not the probe was a success\n'
          '# TYPE synology_success gauge\n'
          f'''synology_success 1\n'''
  )

def get_volume_info(api: SynologyDSM):
  """Get volume info"""
  volume_info = ''

  # Add status info
  volume_info += (
    '# HELP synology_volume_status Volume status\n'
    '# TYPE synology_volume_status gauge\n'
  )

  for volume_id in api.storage.volumes_ids:
    volume_info += (
      f'''synology_volume_status{{volume="{volume_id}",status="{api.storage.volume_status(volume_id)}"}} 1\n'''
    )

  # Add used info
  volume_info += (
    '# HELP synology_volume_used Volume used percentage\n'
    '# TYPE synology_volume_used gauge\n'
  )

  for volume_id in api.storage.volumes_ids:
    volume_info += (
      f'''synology_volume_used{{volume="{volume_id}"}} {api.storage.volume_percentage_used(volume_id)}\n'''
    )

  return volume_info

def get_disk_info(api: SynologyDSM):
  """Get disk info."""
  disk_info = ''

  # Add status info
  disk_info += (
    '# HELP synology_disk_status Disk status\n'
    '# TYPE synology_disk_status gauge\n'
  )

  for disk_id in api.storage.disks_ids:
    disk_info += (
      f'''synology_disk_status{{disk="{disk_id}",status="{api.storage.disk_status(disk_id)}"}} 1\n'''
      )

  # Add temperature
  disk_info += (
    '# HELP synology_disk_temperature Disk temperature in degrees celsius\n'
    '# TYPE synology_disk_temperature gauge\n'
  )

  for disk_id in api.storage.disks_ids:
    disk_info += (
      f'''synology_disk_temperature{{disk="{disk_id}"}} {api.storage.disk_temp(disk_id)}\n'''
    )

  return disk_info

def get_success_info(success):
  """Get metrics string to determine success or failure."""
  return ('# HELP synology_success Displays whether or not the probe was a success\n'
          '# TYPE synology_success gauge\n'
          f'''synology_success {1 if success else 0}\n'''
  )

@app.get('/probe', response_class=PlainTextResponse)
async def probe(target):
  metrics = ''

  try:
    targets = get_targets()
    target_info = list(filter(lambda t: t['host'] == target, targets))
    api = SynologyDSM(target_info['host'], target_info['port'], target_info['username'], target_info['password'], device_token=target_info['device_token'])

    # Update info
    api.information.update()
    api.utilisation.update()
    api.storage.update()

    metrics = get_nas_info(api)
    metrics += get_volume_info(api)
    metrics += get_disk_info(api)
    metrics += get_success_info(True)
  except Exception as e:
    print(e)
    metrics += get_success_info(False)
  finally:
    return metrics

if __name__ == '__main__':
  # Parse arguments
  parser = argparse.ArgumentParser()
  parser.add_argument('action', type=str)
  args, _ = parser.parse_known_args()

  if args.action == 'add':
    add_host()
