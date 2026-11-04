"""The `Polar` service: the Python face of the `polar` Flutter plugin."""

from typing import Any, Optional

import flet as ft
from flet.utils.from_dict import from_dict

from flet_polar.types import (
    LedConfig,
    PolarAccDataEvent,
    PolarBatteryChargingStatusEvent,
    PolarBatteryLevelEvent,
    PolarBlePowerStateEvent,
    PolarDataType,
    PolarDeviceDisconnectedEvent,
    PolarDeviceEvent,
    PolarDisInformationEvent,
    PolarEcgDataEvent,
    PolarErrorEvent,
    PolarExerciseData,
    PolarExerciseEntry,
    PolarFirstTimeUseConfig,
    PolarGyroDataEvent,
    PolarHrDataEvent,
    PolarLocationDataEvent,
    PolarMagnetometerDataEvent,
    PolarPpgDataEvent,
    PolarPpiDataEvent,
    PolarPressureDataEvent,
    PolarRecordingStatus,
    PolarSdkFeatureReadyEvent,
    PolarSdkFeaturesReadinessEvent,
    PolarSensorSetting,
    PolarStreamEndEvent,
    PolarTemperatureDataEvent,
    RecordingInterval,
    SampleType,
)

__all__ = ["Polar"]


@ft.control("Polar")
class Polar(ft.Service):
    """Connects to Polar devices and streams their data. Android and iOS only.

    Every device method takes an `identifier`: the Polar device id printed on the
    device, or its UUID. Methods raise `RuntimeError` when the SDK reports an error
    or when the platform is not supported.
    """

    bluetooth_scan_never_for_location: bool = True
    """Set to `False` to also request the location permission on Android 12+.

    Read once: the underlying plugin is a singleton, so changing it later has no
    effect.
    """

    on_ble_power_state_change: Optional[ft.EventHandler[PolarBlePowerStateEvent]] = None
    """Fires when the Bluetooth adapter is switched on or off."""
    on_device_found: Optional[ft.EventHandler[PolarDeviceEvent]] = None
    """Fires for every device found by `start_device_search`."""
    on_device_connecting: Optional[ft.EventHandler[PolarDeviceEvent]] = None
    """Fires when a connection attempt starts."""
    on_device_connected: Optional[ft.EventHandler[PolarDeviceEvent]] = None
    """Fires when a connection is established."""
    on_device_disconnected: Optional[ft.EventHandler[PolarDeviceDisconnectedEvent]] = (
        None
    )
    """Fires when a connection is lost."""
    on_sdk_feature_ready: Optional[ft.EventHandler[PolarSdkFeatureReadyEvent]] = None
    """Fires when a single feature becomes available on a device."""
    on_sdk_features_readiness: Optional[
        ft.EventHandler[PolarSdkFeaturesReadinessEvent]
    ] = None
    """Fires once all features of a connected device have been evaluated.

    This is the simplest way to wait until a device can be used.
    """
    on_dis_information: Optional[ft.EventHandler[PolarDisInformationEvent]] = None
    """Fires when Device Information Service data is received."""
    on_battery_level: Optional[ft.EventHandler[PolarBatteryLevelEvent]] = None
    """Fires when a battery level is received."""
    on_battery_charging_status: Optional[
        ft.EventHandler[PolarBatteryChargingStatusEvent]
    ] = None
    """Fires when a battery charging status is received."""

    on_hr_data: Optional[ft.EventHandler[PolarHrDataEvent]] = None
    """Receives `PolarDataType.HR` packets."""
    on_ecg_data: Optional[ft.EventHandler[PolarEcgDataEvent]] = None
    """Receives `PolarDataType.ECG` packets."""
    on_acc_data: Optional[ft.EventHandler[PolarAccDataEvent]] = None
    """Receives `PolarDataType.ACC` packets."""
    on_gyro_data: Optional[ft.EventHandler[PolarGyroDataEvent]] = None
    """Receives `PolarDataType.GYRO` packets."""
    on_magnetometer_data: Optional[ft.EventHandler[PolarMagnetometerDataEvent]] = None
    """Receives `PolarDataType.MAGNETOMETER` packets."""
    on_ppg_data: Optional[ft.EventHandler[PolarPpgDataEvent]] = None
    """Receives `PolarDataType.PPG` packets."""
    on_ppi_data: Optional[ft.EventHandler[PolarPpiDataEvent]] = None
    """Receives `PolarDataType.PPI` packets."""
    on_temperature_data: Optional[ft.EventHandler[PolarTemperatureDataEvent]] = None
    """Receives `PolarDataType.TEMPERATURE` packets."""
    on_pressure_data: Optional[ft.EventHandler[PolarPressureDataEvent]] = None
    """Receives `PolarDataType.PRESSURE` packets."""
    on_skin_temperature_data: Optional[ft.EventHandler[PolarTemperatureDataEvent]] = (
        None
    )
    """Receives `PolarDataType.SKIN_TEMPERATURE` packets."""
    on_location_data: Optional[ft.EventHandler[PolarLocationDataEvent]] = None
    """Receives `PolarDataType.LOCATION` packets. Not supported on iOS."""

    on_stream_end: Optional[ft.EventHandler[PolarStreamEndEvent]] = None
    """Fires when a stream ends on its own, e.g. because the device disconnected."""
    on_error: Optional[ft.EventHandler[PolarErrorEvent]] = None
    """Fires when a search, a stream or the SDK event channel fails."""

    # ------------------------------------------------------------------ connection

    async def request_permissions(self) -> None:
        """Request the Bluetooth (and if needed location) permissions on Android.

        Does nothing on iOS, where the system prompts by itself.
        """
        await self._invoke_method("request_permissions")

    async def start_device_search(self) -> None:
        """Search for devices, reporting them through `on_device_found`.

        Call `request_permissions` first. A running search is restarted.
        """
        await self._invoke_method("start_device_search")

    async def stop_device_search(self) -> None:
        """Stop searching for devices."""
        await self._invoke_method("stop_device_search")

    async def connect_to_device(
        self, identifier: str, request_permissions: bool = True
    ) -> None:
        """Request a connection to a device.

        This returns as soon as the request is made: the outcome is reported through
        `on_device_connected` and `on_sdk_features_readiness`.

        Args:
            identifier: Polar device id or UUID.
            request_permissions: Whether to request the needed permissions first.

        """
        await self._invoke_method(
            "connect_to_device",
            {"identifier": identifier, "request_permissions": request_permissions},
        )

    async def disconnect_from_device(self, identifier: str) -> None:
        """Disconnect from a device and stop reconnecting to it."""
        await self._device_call("disconnect_from_device", identifier)

    async def shut_down(self) -> None:
        """Stop searches and streams and release the SDK resources."""
        await self._invoke_method("shut_down")

    # ------------------------------------------------------------------- streaming

    async def get_available_online_stream_data_types(
        self, identifier: str
    ) -> set[PolarDataType]:
        """Return the data types this device can stream."""
        result = await self._device_call(
            "get_available_online_stream_data_types", identifier
        )
        return {PolarDataType(value) for value in result}

    async def get_available_hr_service_data_types(
        self, identifier: str
    ) -> set[PolarDataType]:
        """Return the set with `HR` if the device has the HR service.

        Use this for devices without the Polar Measurement Data service, on which
        `get_available_online_stream_data_types` fails.
        """
        result = await self._device_call(
            "get_available_hr_service_data_types", identifier
        )
        return {PolarDataType(value) for value in result}

    async def request_stream_settings(
        self, identifier: str, data_type: PolarDataType
    ) -> PolarSensorSetting:
        """Return the settings the device currently offers for a data type.

        What is offered depends on the device state, e.g. on other running streams.
        """
        result = await self._invoke_method(
            "request_stream_settings",
            {"identifier": identifier, "data_type": data_type},
        )
        return from_dict(PolarSensorSetting, result)

    async def start_streaming(
        self,
        identifier: str,
        data_type: PolarDataType,
        settings: Optional[PolarSensorSetting] = None,
    ) -> None:
        """Start a data stream, delivered through the matching `on_*_data` handler.

        This returns as soon as the stream is opened: failures to start are reported
        through `on_error` and `on_stream_end`. Starting a stream that is already
        running restarts it.

        Args:
            identifier: Polar device id or address.
            data_type: The data to stream.
            settings: Settings to use, as one value per setting. Defaults to the
                highest settings available. Ignored for `HR` and `PPI`, which have
                no settings.

        Raises:
            ValueError: If `settings` offers several values for a setting.

        """
        if settings is not None and not settings.is_selection:
            raise ValueError(
                "settings must hold one value per setting: "
                "use PolarSensorSetting.selection() or max_settings()"
            )
        await self._invoke_method(
            "start_streaming",
            {
                "identifier": identifier,
                "data_type": data_type,
                "settings": settings
                and {key.value: values[0] for key, values in settings.settings.items()},
            },
        )

    async def stop_streaming(self, identifier: str, data_type: PolarDataType) -> None:
        """Stop a data stream. Does nothing if it is not running."""
        await self._invoke_method(
            "stop_streaming", {"identifier": identifier, "data_type": data_type}
        )

    # ------------------------------------------------------------------- recording

    async def start_recording(
        self,
        identifier: str,
        exercise_id: str,
        interval: RecordingInterval,
        sample_type: SampleType,
    ) -> None:
        """Start an exercise recording. Polar H10 only.

        Args:
            identifier: Polar device id or UUID.
            exercise_id: Unique identifier of the entry, 1-64 bytes long.
            interval: Recording interval. Has no effect for `SampleType.RR`.
            sample_type: Sample type to record.

        """
        await self._invoke_method(
            "start_recording",
            {
                "identifier": identifier,
                "exercise_id": exercise_id,
                "interval": interval,
                "sample_type": sample_type,
            },
        )

    async def stop_recording(self, identifier: str) -> None:
        """Stop the current exercise recording. Polar H10 only."""
        await self._device_call("stop_recording", identifier)

    async def request_recording_status(self, identifier: str) -> PolarRecordingStatus:
        """Return the status of the current recording. Polar H10 only."""
        result = await self._device_call("request_recording_status", identifier)
        return from_dict(PolarRecordingStatus, result)

    async def list_exercises(self, identifier: str) -> list[PolarExerciseEntry]:
        """List the stored exercises.

        Works on Polar H10, OH1 and Verity Sense, though recording on the latter two
        requires the sensor to be registered to a Polar Flow account.
        """
        result = await self._device_call("list_exercises", identifier)
        return [from_dict(PolarExerciseEntry, entry) for entry in result]

    async def fetch_exercise(
        self, identifier: str, entry: PolarExerciseEntry
    ) -> PolarExerciseData:
        """Fetch the samples of a stored exercise."""
        result = await self._invoke_method(
            "fetch_exercise", {"identifier": identifier, "entry": entry}
        )
        return from_dict(PolarExerciseData, result)

    async def remove_exercise(self, identifier: str, entry: PolarExerciseEntry) -> None:
        """Remove a stored exercise."""
        await self._invoke_method(
            "remove_exercise", {"identifier": identifier, "entry": entry}
        )

    # --------------------------------------------------------------- device control

    async def set_led_config(self, identifier: str, config: LedConfig) -> None:
        """Enable or disable the blinking LEDs (Verity Sense 2.2.1+)."""
        await self._invoke_method(
            "set_led_config", {"identifier": identifier, "config": config}
        )

    async def do_factory_reset(
        self, identifier: str, preserve_pairing_information: bool
    ) -> None:
        """Reset a device to its factory settings."""
        await self._invoke_method(
            "do_factory_reset",
            {
                "identifier": identifier,
                "preserve_pairing_information": preserve_pairing_information,
            },
        )

    async def enable_sdk_mode(self, identifier: str) -> None:
        """Enable SDK mode, which offers a wider range of stream settings."""
        await self._device_call("enable_sdk_mode", identifier)

    async def disable_sdk_mode(self, identifier: str) -> None:
        """Disable SDK mode."""
        await self._device_call("disable_sdk_mode", identifier)

    async def is_sdk_mode_enabled(self, identifier: str) -> bool:
        """Return whether SDK mode is enabled (Verity Sense 2.1.0+)."""
        return await self._device_call("is_sdk_mode_enabled", identifier)

    async def do_first_time_use(
        self, identifier: str, config: PolarFirstTimeUseConfig
    ) -> None:
        """Send the first-time-use configuration to a device."""
        await self._invoke_method(
            "do_first_time_use", {"identifier": identifier, "config": config}
        )

    async def is_ftu_done(self, identifier: str) -> bool:
        """Return whether the first-time use has been done."""
        return await self._device_call("is_ftu_done", identifier)

    def _device_call(self, method: str, identifier: str) -> Any:
        return self._invoke_method(method, {"identifier": identifier})
