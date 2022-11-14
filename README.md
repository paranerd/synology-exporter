# Synology Exporter

[![build](https://github.com/paranerd/synology-exporter/actions/workflows/main.yml/badge.svg)](https://github.com/paranerd/synology-exporter/actions/workflows/main.yml)
[![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/paranerd/synology-exporter?label=Current%20Version&logo=github)](https://github.com/paranerd/synology-exporter/tags)
[![Docker Image Size (latest semver)](https://shields.api-test.nl:/docker/image-size/paranerd/synology-exporter?label=Image%20Size&logo=docker)](https://hub.docker.com/repository/docker/paranerd/synology-exporter)

Prometheus exporter for Synology NAS

## Prerequisites
Make sure the `targets.json` you're mounting already exists (otherwise Docker will create it as a directory)!

## Run with Docker Run
```
docker run -d -p 9102:80 -v "/path/to/targets.json:/app/targets.json" --name synology-exporter paranerd/synology-exporter
```

## Run with Docker Compose
```
---
version: '3'
services:
  synology-exporter:
    image: paranerd/synology-exporter
    container_name: synology-exporter
    restart: unless-stopped
    ports:
      - 9102:80
    volumes:
      - /path/to/targets.json:/app/targets.json
```

## Add new host
```
docker exec -it synology-exporter python3 /app/main.py add
```

## Query metrics
```
curl "<server_ip>:9102/probe?target=<synology_url>
```

## Example output

```
# HELP synology_dsm_version_info DSM version
# TYPE synology_dsm_version_info gauge
dsm_version_info{"version=DSM 7.1.1-42962 Update 1"} 1
# HELP synology_temperature NAS Temperature in degrees celsius
# TYPE synology_temperature gauge
synology_temperature 35
# HELP synology_temperature_warning If NAS has temperature warning
# TYPE synology_temperature_warning gauge
synology_temperature_warning False
# HELP synology_uptime Uptime
# TYPE synology_uptime gauge
synology_uptime 2593712
# HELP synology_cpu_load CPU load in percent
# TYPE synology_cpu_load gauge
synology_cpu_load 1
# HELP synology_memory_usage Memory usage in percent
# TYPE synology_memory_usage gauge
synology_memory_usage 6
# HELP synology_network_up_bytes Network traffic upload in bytes
# TYPE synology_network_up_bytes gauge
synology_network_up_bytes 543
# HELP synology_network_down_bytes Network traffic download in bytes
# TYPE synology_network_down_bytes gauge
synology_network_down_bytes 1527
# HELP synology_success Displays whether or not the probe was a success
# TYPE synology_success gauge
synology_success 1
# HELP synology_volume_status Volume status
# TYPE synology_volume_status gauge
synology_volume_status{volume="volume_1",status="normal"} 1
# HELP synology_volume_used Volume used percentage
# TYPE synology_volume_used gauge
synology_volume_used{volume="volume_1"} 57.9
# HELP synology_disk_status Disk status
# TYPE synology_disk_status gauge
synology_disk_status{disk="sata1",status="normal"} 1
synology_disk_status{disk="sata2",status="normal"} 1
# HELP synology_disk_temperature Disk temperature in degrees celsius
# TYPE synology_disk_temperature gauge
synology_disk_temperature{disk="sata1"} 30
synology_disk_temperature{disk="sata2"} 31
# HELP synology_success Displays whether or not the probe was a success
# TYPE synology_success gauge
synology_success 1
```
