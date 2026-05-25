"""Inverse runners for the Rollback Axis.

Each runner is the symmetric inverse of a Backup Axis runner:
  rsync_dir         <-> restore_rsync_dir
  pg_dump           <-> restore_pg_dump
  docker_volume_tar <-> restore_docker_volume
"""
