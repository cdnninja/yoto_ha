# yoto_ha

Home Assistant Integration for Yoto. While this currently loads and installs sensors are very limited. Readme will not always be updated as this is moving quick.

PRs are appreciated to add more.

![image](https://github.com/cdnninja/yoto_ha/assets/6373468/7d289b63-ba2d-4f7d-a7fa-8e498af218ea)


# Troubleshooting

You can enable logging for this integration specifically and share your logs, so I can have a deep dive investigation. To enable logging, enable via the gui or update your configuration.yaml like this, we can get more information in Configuration -> Logs page
logger:
default: warning
logs:
custom_components.yoto: debug
yoto_api: debug
