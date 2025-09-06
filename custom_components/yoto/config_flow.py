"""Config flow for Hyundai / Kia Connect integration."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

import logging
from typing import Any

from yoto_api import YotoManager
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, SOURCE_REAUTH
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    CONF_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


class YotoOptionFlowHandler(config_entries.OptionsFlow):
    """Handle an option flow for Yoto."""

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle options init setup."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.config_entry.title, data=user_input
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=15, max=999)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yoto"""

    VERSION = 2
    login_task: asyncio.Task | None = None
    token = None
    ym: YotoManager | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> YotoOptionFlowHandler:
        """Initiate options flow instance."""
        return YotoOptionFlowHandler()

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth on credential failure."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prepare reauth."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle users reauth credentials."""

        if self.ym is None:
            _LOGGER.debug("Initiating device activation")
            self.ym = await self.hass.async_add_executor_job(
                YotoManager, "KFLTf5PCpTh0yOuDuyQ5C3LEU9PSbult"
            )
            assert self.ym is not None
            urlObject = await self.hass.async_add_executor_job(
                self.ym.device_code_flow_start
            )
            yoto_device_url = urlObject["verification_uri_complete"]

        async def _wait_for_login() -> None:
            """Wait for the user to login."""
            assert self.ym is not None
            _LOGGER.debug("Waiting for device activation")
            await self.hass.async_add_executor_job(self.ym.device_code_flow_complete)

            if self.ym.token is None:
                raise HomeAssistantError("Device activation failed")

        _LOGGER.debug("Checking login task")
        if self.login_task is None:
            _LOGGER.debug("Creating task for device activation")
            self.login_task = self.hass.async_create_task(_wait_for_login())

        if self.login_task.done():
            _LOGGER.debug("Login task is done, checking results")
            if self.login_task.exception():
                return self.async_show_progress_done(next_step_id="timeout")
            self.token = self.ym.token.refresh_token

            return self.async_show_progress_done(next_step_id="finish_login")

        return self.async_show_progress(
            step_id="user",
            progress_action="wait_for_device",
            description_placeholders={
                "url": yoto_device_url,
            },
            progress_task=self.login_task,
        )

    async def async_step_finish_login(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the finalization of reauth."""
        _LOGGER.debug("Finalizing reauth")
        assert self.ym is not None
        unique_id = next(iter(self.ym.players))

        if self.source != SOURCE_REAUTH:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=unique_id,
                data={CONF_TOKEN: self.token},
            )

        self._abort_if_unique_id_mismatch(reason="reauth_account_mismatch")
        return self.async_update_reload_and_abort(
            self._get_reauth_entry(),
            data={CONF_TOKEN: self.token},
        )

    async def async_step_timeout(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle issues that need transition await from progress step."""
        if user_input is None:
            return self.async_show_form(
                step_id="timeout",
            )
        del self.login_task
        return await self.async_step_user()


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
