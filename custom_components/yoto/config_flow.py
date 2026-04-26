"""Config flow for Yoto integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError
from yoto_api import YotoManager

from .const import CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yoto."""

    VERSION = 3
    login_task: asyncio.Task | None = None
    token = None
    ym: YotoManager | None = None

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
        """Handle the device code login flow."""

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
            """Wait for the user to login and validate the resulting token."""
            assert self.ym is not None
            _LOGGER.debug("Waiting for device activation")
            await self.hass.async_add_executor_job(self.ym.device_code_flow_complete)

            if self.ym.token is None:
                raise HomeAssistantError("Device activation failed")

            # Validate the token by hitting the players endpoint. Surfaces a
            # bad/expired token before the entry is created.
            await self.hass.async_add_executor_job(self.ym.update_players_status)
            if not self.ym.players:
                raise HomeAssistantError("No Yoto players found on this account")

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
        """Create or update the config entry once the login has succeeded."""
        _LOGGER.debug("Finalizing login")
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
