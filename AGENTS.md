# AGENTS.md

Flet extension that exposes the [`polar`](https://pub.dev/packages/polar) Flutter plugin
to Python as a `Polar` service. It is a small wrapper: prefer a direct mapping onto the
plugin over new abstractions.

## Layout

```
src/flet_polar/
  polar.py          Polar(ft.Service): event handler fields and async methods
  types.py          Enums, model dataclasses and event dataclasses
src/flutter/flet_polar/
  lib/src/extension.dart      Maps control type "Polar" to PolarService
  lib/src/polar_service.dart  Lifecycle, method dispatch, subscriptions
  lib/src/polar_codec.dart    Pure model <-> wire conversion, data stream table
  test/                       Codec and Python/Dart enum sync tests
tests/              Python tests, including Python/Dart sync tests
examples/flet_polar_example/  Example app, also the reference app configuration
```

## Supported versions

Flet 1.0.4 is the oldest supported version, and what the example and the lockfiles use, so
CI tests the lower bound. Python 3.10+ can install the package, but CI only tests 3.14.

## Commands

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest

# Flutter 3.44.8 is what Flet 1.0.4 and 1.0.5 use; `flet build` installs it in ~/flutter.
cd src/flutter/flet_polar && flutter pub get && dart analyze . && flutter test

# Native compile check. No device or hardware needed. Exit status is reliable only
# without a pipe, and an APK must exist in build/apk afterwards.
cd examples/flet_polar_example && uv run flet build apk --arch arm64-v8a
```

Run ruff, pytest, `dart analyze` and `flutter test` before finishing a change. After
changing Dart code or dependencies, run the APK build as well. Behaviour against a real
device cannot be tested here: say so rather than implying it was verified.

CI (`.github/workflows/ci.yml`) runs all of this on every push and pull request. It also
offers a manually triggered iOS archive build, the only way to check iOS without a Mac.

## The wire protocol

Python and Dart must agree on these by hand:

- **Methods**: `Polar.foo()` calls `_invoke_method("foo", {...})`, handled by
  `case "foo":` in `PolarService._dispatch`. Arguments are a dict with snake_case keys.
- **Events**: `control.triggerEvent("bar", {...})` reaches `Polar.on_bar`. Payload keys
  are the field names of the event dataclass.
- **Enums**: Python enum values are the Dart enum names, converted with `.name` and
  `values.byName`.
- **Data streams**: `PolarDataType.x_y` is delivered to `on_x_y_data` (see
  `dataEventName`). The packet is an `identifier` plus the output of `encode*Data`.

Tests in `tests/test_polar.py` and `test/polar_codec_test.dart` catch most mismatches,
but not the field names of models and events.

## Constraints that are easy to break

- **Use `typing.Optional` in model and event fields, not `X | None`.** Flet's `from_dict`
  only understands `Optional` on Python below 3.14, and fails silently: values are simply
  not converted. Ruff's `UP007`/`UP045` are disabled for this reason.
- **Do not freeze the dataclasses.** Flet's `from_dict` and encoder set attributes on them.
- **Do not use the plugin's `toJson`/`fromJson`.** They yield platform-specific values
  (booleans as 0/1 on iOS, different keys per platform). `polar_codec.dart` keeps Python
  free of platform differences.
- **Do not touch `Polar()` when `_isSupported` is false.** The plugin imports `dart:io`
  and has no desktop or web implementation.
- **Do not shut the plugin down in `dispose`.** It is a process-wide singleton. Only the
  subscriptions are cancelled.
- **Do not bump `polar` casually.** It is pinned exactly and its version decides the
  settings below. Check its changelog for API additions to mirror.

## Settings every app must declare

An extension cannot set these for the app, so they live in the README and in the example's
`pyproject.toml`. All were found by running `flet build apk`; keep them in sync, and re-run
that build when bumping `flet` or `polar`.

Dart honours overrides only in the root package. The copy in this package's `pubspec.yaml`
only serves `flutter test` and `dart analyze` here.

- `device_info_plus = "^12.3.0"`: `polar` 7.12.0 requires `^13`, Flet 1.0.4 and 1.0.5 require `^12.3`.
  Overriding upwards fails, because `device_info_plus` 13 needs `win32 ^6` and Flet's
  `file_picker` needs `win32 ^5`. `polar` only reads `androidInfo.version.sdkInt`.
- `permission_handler = "12.0.1"`: `polar` 7.12.0 resolves to `permission_handler_android`
  14.1.1, whose `compileSdk = 37` fails with "Failed to find target with hash string
  'android-37'" under Flet's Android Gradle Plugin. 12.0.1 is what `flet-permission-handler`
  pins. `polar` only uses `Permission.<x>.request()`.
- `min_sdk_version = 26`: required by Polar BLE SDK 6.16.1, although the plugin's Gradle file
  says 24. Flutter's default of 24 fails the manifest merge.
- iOS is **unverified**: it needs macOS. `polar` needs iOS 14, Flet's template targets 13.0
  and has no setting for it. See the warning in the README.

The first APK build needs about 10 GB of disk space for the Android SDK, NDK and Gradle
caches. Flet gives Gradle an 8 GB heap, and the daemon died here with about 4 GB of memory
available. If that happens, lower `org.gradle.jvmargs` through
`[tool.flet.android.gradle_properties]`.

## Adding plugin functionality

1. Method: add it to `polar.py`, add a `case` in `_dispatch`, and add codec functions if
   it has new models.
2. Event: add the dataclass to `types.py`, export it from `__init__.py`, add the handler
   field to `polar.py`, and forward it in `PolarService.init`.
3. Data type: add the enum member, the sample and event dataclasses, the handler,
   an `encode*Data` function and an `openDataStream` entry.
4. Update the tables in `README.md`.

## Style

- Python: ruff with the configuration in `pyproject.toml`, docstrings on public API.
- Dart: `flutter_lints`. Follow Flet's own service extensions, such as `flet-geolocator`.
- Commit messages explain why. Do not edit `uv.lock` by hand.
