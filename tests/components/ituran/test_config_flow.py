"""Test the Ituran config flow."""

from unittest.mock import patch

from pyituran.exceptions import IturanApiError, IturanAuthError

from homeassistant import config_entries
from homeassistant.components.ituran.const import (
    CONF_ID_OR_PASSPORT,
    CONF_MOBILE_ID,
    CONF_OTP,
    CONF_PHONE_NUMBER,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.is_authenticated",
            return_value=False,
        ),
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.request_otp",
        ),
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.authenticate",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID_OR_PASSPORT: "12345678",
                CONF_PHONE_NUMBER: "0501234567",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "otp"
        assert result["errors"] == {}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_OTP: "123456",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ID_OR_PASSPORT] == "12345678"
        assert result["data"][CONF_PHONE_NUMBER] == "0501234567"
        assert result["data"][CONF_MOBILE_ID] is not None


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.is_authenticated",
            return_value=False,
        ),
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.request_otp",
            side_effect=IturanAuthError,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID_OR_PASSPORT: "12345678",
                CONF_PHONE_NUMBER: "0501234567",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # Make sure the config flow tests continue to the next step so
    # we can show the config flow is able to recover from an error.
    with (
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.is_authenticated",
            return_value=False,
        ),
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.request_otp",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID_OR_PASSPORT: "12345678",
                CONF_PHONE_NUMBER: "0501234567",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "otp"
    assert result["errors"] == {}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.ituran.config_flow.Ituran.is_authenticated",
        side_effect=IturanApiError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID_OR_PASSPORT: "12345678",
                CONF_PHONE_NUMBER: "0501234567",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Make sure the config flow tests continue to the next step so
    # we can show the config flow is able to recover from an error.
    with (
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.is_authenticated",
            return_value=False,
        ),
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.request_otp",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID_OR_PASSPORT: "12345678",
                CONF_PHONE_NUMBER: "0501234567",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "otp"
    assert result["errors"] == {}


async def test_form_invalid_otp(hass: HomeAssistant) -> None:
    """Test we handle invalid OTP."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.is_authenticated",
            return_value=False,
        ),
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.request_otp",
        ),
        patch(
            "homeassistant.components.ituran.config_flow.Ituran.authenticate",
            side_effect=[IturanAuthError, None],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID_OR_PASSPORT: "12345678",
                CONF_PHONE_NUMBER: "0501234567",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "otp"
        assert result["errors"] == {}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_OTP: "123456",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "otp"
        assert result["errors"] == {"base": "invalid_otp"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_OTP: "123456",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ID_OR_PASSPORT] == "12345678"
        assert result["data"][CONF_PHONE_NUMBER] == "0501234567"
        assert result["data"][CONF_MOBILE_ID] is not None
