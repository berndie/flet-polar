# flet-polar

[Flet](https://flet.dev) extension for Polar heart rate sensors and devices (H10, OH1,
Verity Sense, 360, ...). It wraps the [`polar`](https://pub.dev/packages/polar) Flutter
plugin, which is based on the official
[Polar BLE SDK](https://github.com/polarofficial/polar-ble-sdk).

This is an unofficial wrapper, not affiliated with Polar.

## Platform support

| Platform  | iOS | Android | Web | Windows | macOS | Linux |
|-----------|-----|---------|-----|---------|-------|-------|
| Supported | ✅  | ✅      | ❌  | ❌      | ❌    | ❌    |

On other platforms an app still starts, but `Polar` methods raise `RuntimeError`.

Requires Flet 1.0.5+ (Flutter 3.44+), Android 8.0+ (API 26) and iOS 14+.

> [!WARNING]
> **iOS builds are untested and will probably need extra work.** `polar` requires iOS 14,
> but the app template of `flet build` 1.0.5 targets iOS 13.0 and has no setting to change
> that. Expect a "higher minimum deployment target" error from CocoaPods. The likely fix is
> a [custom build template](https://flet.dev/docs/publish) (`flet build ipa --template ...`)
> with `platform :ios, '14.0'` in `ios/Podfile` and `IPHONEOS_DEPLOYMENT_TARGET = 14.0` in
> the Xcode project.

## Installation

Add these to the `pyproject.toml` of your Flet project.

**1. The dependency**

```toml
[project]
dependencies = [
    "flet-polar @ git+https://github.com/<your-account>/flet-polar",
    "flet>=1.0.5",
]
```

**2. Dependency overrides (required)**

```toml
[tool.flet.flutter.pubspec.dependency_overrides]
device_info_plus = "^12.3.0"
permission_handler = "12.0.1"
```

Without them, `flet build` fails. `polar` 7.12.0 asks for newer versions of both packages
than Flet 1.0.5 can use:

- `device_info_plus ^13` cannot be resolved together with Flet, which needs `^12.3`.
- `permission_handler ^13` resolves, but the Android build fails because it needs Android
  SDK platform 37.

An extension cannot declare overrides for you, because Dart only honours them in the app
itself. `polar` only uses a small, stable part of both packages, and it used
`permission_handler` 12 itself until version 7.11.0. These are also the versions that Flet's
own `flet-permission-handler` uses, so the two extensions should combine (not tested).

**3. Android settings**

The Polar BLE SDK requires Android 8.0 (API 26). Without this setting the build fails
during the manifest merge.

```toml
[tool.flet.android]
min_sdk_version = 26

[tool.flet.android.permission]
"android.permission.BLUETOOTH_SCAN" = true
"android.permission.BLUETOOTH_CONNECT" = true
"android.permission.ACCESS_FINE_LOCATION" = true
"android.permission.ACCESS_COARSE_LOCATION" = true
```

**4. iOS usage descriptions**

```toml
[tool.flet.ios.info]
NSBluetoothAlwaysUsageDescription = "Used to connect to Polar devices"
NSBluetoothPeripheralUsageDescription = "Used to connect to Polar devices"
UIBackgroundModes = ["bluetooth-central"]
```

### Run your app

The extension contains native code, so the prebuilt client behind a plain `flet run`
cannot load it. It also needs Bluetooth, so use a real phone rather than an emulator:

```bash
flet debug android -d <device-id>   # list devices with: flet debug --show-devices
flet debug ios -d <device-id>
flet build apk                      # or: flet build ipa
```

## Usage

Create the service inside your `main`: it registers itself with the page, and needs no
`page.add`. Everything else is `await polar.<method>(...)` plus `on_*` event handlers.

```python
import flet as ft
import flet_polar as fp

DEVICE_ID = "1C709B20"  # printed on the device


def main(page: ft.Page):
    heart_rate = ft.Text("-- bpm", size=48)

    async def on_ready(e: fp.PolarSdkFeaturesReadinessEvent):
        if fp.PolarSdkFeature.ONLINE_STREAMING in e.ready:
            await polar.start_streaming(e.identifier, fp.PolarDataType.HR)

    def on_hr_data(e: fp.PolarHrDataEvent):
        heart_rate.value = f"{e.samples[-1].hr} bpm"

    polar = fp.Polar(on_sdk_features_readiness=on_ready, on_hr_data=on_hr_data)

    async def connect():
        await polar.connect_to_device(DEVICE_ID)

    page.add(heart_rate, ft.Button("Connect", on_click=connect))


ft.run(main)
```

See [`examples/flet_polar_example`](examples/flet_polar_example) for an app that also
searches for devices.

### Streaming with settings

`start_streaming` uses the highest available settings by default. To choose:

```python
offered = await polar.request_stream_settings(device_id, fp.PolarDataType.ACC)
# PolarSensorSetting({PolarSettingType.SAMPLE_RATE: [25, 50, 100, 200], ...})

await polar.start_streaming(
    device_id,
    fp.PolarDataType.ACC,
    fp.PolarSensorSetting.selection(
        {
            fp.PolarSettingType.SAMPLE_RATE: 50,
            fp.PolarSettingType.RESOLUTION: 16,
            fp.PolarSettingType.RANGE: 8,
        }
    ),
)
...
await polar.stop_streaming(device_id, fp.PolarDataType.ACC)
```

A stream that ends by itself, for example when the device disconnects, fires
`on_stream_end`. If it failed, `on_error` fires first with the reason.

## API

Method and field names are the snake_case form of those in the Flutter plugin. There is
one deliberate difference: the plugin's eleven `start*Streaming` methods are combined
into `start_streaming` / `stop_streaming`, with one `on_*_data` handler per data type.

### Methods of `Polar`

All are coroutines. They raise `RuntimeError` when the SDK reports an error.

| Method | Flutter plugin |
|--------|----------------|
| `request_permissions()` | `requestPermissions` |
| `start_device_search()`, `stop_device_search()` | `searchForDevice` |
| `connect_to_device(identifier, request_permissions=True)` | `connectToDevice` |
| `disconnect_from_device(identifier)` | `disconnectFromDevice` |
| `shut_down()` | `shutDown` |
| `get_available_online_stream_data_types(identifier)` | `getAvailableOnlineStreamDataTypes` |
| `get_available_hr_service_data_types(identifier)` | `getAvailableHrServiceDataTypes` |
| `request_stream_settings(identifier, data_type)` | `requestStreamSettings` |
| `start_streaming(identifier, data_type, settings=None)`, `stop_streaming(identifier, data_type)` | `start*Streaming` |
| `start_recording(identifier, exercise_id, interval, sample_type)` | `startRecording` |
| `stop_recording(identifier)` | `stopRecording` |
| `request_recording_status(identifier)` | `requestRecordingStatus` |
| `list_exercises(identifier)` | `listExercises` |
| `fetch_exercise(identifier, entry)` | `fetchExercise` |
| `remove_exercise(identifier, entry)` | `removeExercise` |
| `set_led_config(identifier, config)` | `setLedConfig` |
| `do_factory_reset(identifier, preserve_pairing_information)` | `doFactoryReset` |
| `enable_sdk_mode(identifier)`, `disable_sdk_mode(identifier)` | `enableSdkMode`, `disableSdkMode` |
| `is_sdk_mode_enabled(identifier)` | `isSdkModeEnabled` |
| `do_first_time_use(identifier, config)` | `doFirstTimeUse` |
| `is_ftu_done(identifier)` | `isFtuDone` |

### Events of `Polar`

| Handler | Event | Flutter plugin |
|---------|-------|----------------|
| `on_ble_power_state_change` | `PolarBlePowerStateEvent` | `blePowerState` |
| `on_device_found` | `PolarDeviceEvent` | `searchForDevice` |
| `on_device_connecting`, `on_device_connected` | `PolarDeviceEvent` | `deviceConnecting`, `deviceConnected` |
| `on_device_disconnected` | `PolarDeviceDisconnectedEvent` | `deviceDisconnected` |
| `on_sdk_feature_ready` | `PolarSdkFeatureReadyEvent` | `sdkFeatureReady` |
| `on_sdk_features_readiness` | `PolarSdkFeaturesReadinessEvent` | `sdkFeaturesReadiness` |
| `on_dis_information` | `PolarDisInformationEvent` | `disInformation` |
| `on_battery_level` | `PolarBatteryLevelEvent` | `batteryLevel` |
| `on_battery_charging_status` | `PolarBatteryChargingStatusEvent` | `batteryChargingStatus` |
| `on_hr_data` | `PolarHrDataEvent` | `startHrStreaming` |
| `on_ecg_data` | `PolarEcgDataEvent` | `startEcgStreaming` |
| `on_acc_data` | `PolarAccDataEvent` | `startAccStreaming` |
| `on_gyro_data` | `PolarGyroDataEvent` | `startGyroStreaming` |
| `on_magnetometer_data` | `PolarMagnetometerDataEvent` | `startMagnetometerStreaming` |
| `on_ppg_data` | `PolarPpgDataEvent` | `startPpgStreaming` |
| `on_ppi_data` | `PolarPpiDataEvent` | `startPpiStreaming` |
| `on_temperature_data` | `PolarTemperatureDataEvent` | `startTemperatureStreaming` |
| `on_pressure_data` | `PolarPressureDataEvent` | `startPressureStreaming` |
| `on_skin_temperature_data` | `PolarTemperatureDataEvent` | `startSkinTemperatureStreaming` |
| `on_location_data` (not on iOS) | `PolarLocationDataEvent` | `startLocationStreaming` |
| `on_stream_end` | `PolarStreamEndEvent` | - |
| `on_error` | `PolarErrorEvent` | - |

All types are documented in [`types.py`](src/flet_polar/types.py).

### Good to know

- `connect_to_device` returns once the request is made. Wait for
  `on_sdk_features_readiness` before using the device.
- `start_device_search` does not request permissions: call `request_permissions` first.
- `bluetooth_scan_never_for_location` is `True` by default, which matches the
  `neverForLocation` flag the plugin recommends. Flet's `pyproject.toml` settings cannot
  set that flag on the manifest. If scans return nothing on Android 12+, create the
  service with `fp.Polar(bluetooth_scan_never_for_location=False)` so that the location
  permission is requested too.
- Flet refreshes the page after every event handler, so keep `on_*_data` handlers short
  for high-rate streams such as ECG and ACC.

## Development

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest
cd src/flutter/flet_polar && flutter test && dart analyze .
```

See [`AGENTS.md`](AGENTS.md) for the architecture and conventions.

## License

[MIT](LICENSE). The wrapped [`polar`](https://pub.dev/packages/polar) plugin and
[Polar BLE SDK](https://github.com/polarofficial/polar-ble-sdk) have their own licenses.
