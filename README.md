# yoto_ha

Home Assistant Integration for Yoto. While this currently loads and installs sensors are very limited. Readme will not always be updated as this is moving quick.

PRs are appreciated to add more.

![image](https://github.com/cdnninja/yoto_ha/assets/6373468/8ae77603-80dd-45fa-80ab-1cb040fa0112)

# Troubleshooting

You can enable logging for this integration specifically and share your logs, so I can have a deep dive investigation. To enable logging, enable via the gui or update your configuration.yaml like this, we can get more information in Configuration -> Logs page
logger:
default: warning
logs:
custom_components.yoto: debug
yoto_api: debug
