<img src="https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.yoto.total">

# yoto_ha

> [!IMPORTANT]
> **This custom integration is deprecated. Yoto is now built into Home Assistant.**
>
> Starting with Home Assistant **2026.6**, Yoto ships as an official core integration: <https://www.home-assistant.io/integrations/yoto>. New features and fixes will land there, not in this repository. Please migrate using the steps below.

## Migrating to the core Yoto integration

The core integration uses the same `yoto` domain. Home Assistant always loads a custom integration in place of a core one with the same domain, so you **must remove this custom integration** before the core one will load.

1. **Update Home Assistant** to 2026.6 or newer.
2. **Note down what you use.** Make a list of the Yoto entities used in your automations, scripts and dashboards. Entity IDs and features in the core integration may differ from this one, so you may need to update them later.
3. **Delete the existing configuration.** Go to **Settings → Devices & services → Yoto**. For each Yoto entry, open the three-dot menu (⋮) and select **Delete**.
4. **Remove the custom integration files.**
   - If you installed with HACS: open **HACS**, find **Yoto**, open the three-dot menu (⋮) and select **Remove**.
   - If you installed manually: delete the `custom_components/yoto` folder from your Home Assistant configuration directory.
5. **Restart Home Assistant** (**Settings → System → ⋮ → Restart Home Assistant**). The custom integration stays loaded until you restart.
6. **Add the core integration.** Go to **Settings → Devices & services → Add integration**, search for **Yoto** and follow the prompts to sign in with your Yoto account. You can also use this button:

   [![Open your Home Assistant instance and start setting up Yoto.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=yoto)

7. **Update automations, scripts and dashboards** that refer to old entity IDs or to the `yoto` services from this custom integration.
8. (Optional) Remove the `custom_components.yoto` entry from any `logger:` settings in `configuration.yaml`.

If something doesn't work in the core integration, report it through the [Home Assistant core issue tracker](https://github.com/home-assistant/core/issues), not here.

---

Home Assistant Integration for Yoto.

PRs are appreciated to add more.

![image](https://github.com/cdnninja/yoto_ha/assets/6373468/a02dac1e-609c-4536-9588-9bf5c7bba013)

# Supported Device Features

Not all devices expose all sensors/entities. Only sensors/entities supported by your device will be available in the integration.

# Installing

The easiest way to install this integration is via HACS. https://hacs.xyz/

# Services Working

- Play/Pause
- Play Media/Card via service call (format of media id is cardid+chapterid+trackid+seconds, if you leave off chapterid/trackid/seconds will start at chapter and track 1.)
- Stop Media via service call
- Set Time for Day/Night Modes
- Set display brightness Day/Night including auto
- Set Day/Night light color, this can be any color not just in app!
- Set Day/Night max volume

# Troubleshooting

You can enable logging for this integration specifically and share your logs, so I can have a deep dive investigation. To enable logging, enable via the gui or update your configuration.yaml like this, we can get more information in Configuration -> Logs page

Debug can also be enabled via the interface.

```yaml config
logger:
  default: warning
  logs:
    custom_components.yoto: debug
    yoto_api: debug
```
