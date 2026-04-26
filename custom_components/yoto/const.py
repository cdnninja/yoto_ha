"""Constants for the yoto integration"""

from datetime import timedelta

DOMAIN: str = "yoto"

# MQTT delivers real-time updates while a player is online but never pushes a
# disconnect event, so polling is what surfaces the online -> offline transition.
SCAN_INTERVAL = timedelta(minutes=5)

DYNAMIC_UNIT: str = "dynamic_unit"

CONF_TOKEN = "token"
