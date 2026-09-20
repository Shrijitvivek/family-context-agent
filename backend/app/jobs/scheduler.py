"""Lightweight scheduler lifecycle.

TODO:
- Configure APScheduler from environment settings.
- Register deadline checks once and shut the scheduler down cleanly.
- Prevent duplicate scheduler instances in multi-worker deployments.
"""
