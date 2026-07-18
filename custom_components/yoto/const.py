"""Constants for the yoto integration"""

from datetime import timedelta

DOMAIN: str = "yoto"

# MQTT delivers real-time updates while a player is online but never pushes a
# disconnect event, so polling is what surfaces the online -> offline transition.
SCAN_INTERVAL = timedelta(minutes=5)

# Yoto only emits a `data/status` MQTT message in response to a
# `command/status/request` publish. The lib fires one on connect and after
# writes; this heartbeat refreshes MQTT-only fields (battery, charging,
# brightness, ambient sensor...) between user actions.
STATUS_PUSH_INTERVAL = timedelta(seconds=60)

DYNAMIC_UNIT: str = "dynamic_unit"

CONF_TOKEN = "token"
