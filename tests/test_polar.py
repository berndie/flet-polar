"""Tests the Python side of the wire protocol, without a Flet client or a device."""

import dataclasses
import re
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from flet.controls.control_event import get_event_field_type
from flet.utils.from_dict import from_dict

import flet_polar as fp

TIME = datetime(2026, 1, 2, tzinfo=timezone.utc)
DART_LIB = Path(__file__).parents[1] / "src/flutter/flet_polar/lib/src"


@pytest.fixture
def polar():
    instance = fp.Polar()
    with patch.object(instance, "_invoke_method", AsyncMock()) as invoke:
        instance.invoke = invoke
        yield instance


def event_handler_names():
    return [f.name for f in dataclasses.fields(fp.Polar) if f.name.startswith("on_")]


def test_selection_and_max_settings():
    offered = fp.PolarSensorSetting(
        {
            fp.PolarSettingType.SAMPLE_RATE: [52, 130],
            fp.PolarSettingType.RESOLUTION: [14],
        }
    )
    assert not offered.is_selection
    assert offered.max_settings() == fp.PolarSensorSetting.selection(
        {fp.PolarSettingType.SAMPLE_RATE: 130, fp.PolarSettingType.RESOLUTION: 14}
    )


def test_only_hr_and_ppi_lack_settings():
    without = {t for t in fp.PolarDataType if not t.supports_stream_settings}
    assert without == {fp.PolarDataType.HR, fp.PolarDataType.PPI}


async def test_start_streaming_sends_selected_values(polar):
    settings = fp.PolarSensorSetting.selection({fp.PolarSettingType.SAMPLE_RATE: 130})
    await polar.start_streaming("ID", fp.PolarDataType.ECG, settings)
    polar.invoke.assert_awaited_once_with(
        "start_streaming",
        {
            "identifier": "ID",
            "data_type": fp.PolarDataType.ECG,
            "settings": {"sampleRate": 130},
        },
    )


async def test_start_streaming_defaults_to_no_settings(polar):
    await polar.start_streaming("ID", fp.PolarDataType.HR)
    assert polar.invoke.await_args.args[1]["settings"] is None


async def test_start_streaming_rejects_offered_settings(polar):
    offered = fp.PolarSensorSetting({fp.PolarSettingType.SAMPLE_RATE: [52, 130]})
    with pytest.raises(ValueError, match="one value per setting"):
        await polar.start_streaming("ID", fp.PolarDataType.ECG, offered)
    polar.invoke.assert_not_awaited()


async def test_results_are_converted(polar):
    polar.invoke.return_value = ["hr", "skinTemperature"]
    assert await polar.get_available_online_stream_data_types("ID") == {
        fp.PolarDataType.HR,
        fp.PolarDataType.SKIN_TEMPERATURE,
    }

    polar.invoke.return_value = {"settings": {"sampleRate": [52, 130]}}
    assert await polar.request_stream_settings(
        "ID", fp.PolarDataType.ECG
    ) == fp.PolarSensorSetting({fp.PolarSettingType.SAMPLE_RATE: [52, 130]})

    polar.invoke.return_value = [{"path": "/E", "date": TIME, "entry_id": "e"}]
    assert await polar.list_exercises("ID") == [fp.PolarExerciseEntry("/E", TIME, "e")]

    polar.invoke.return_value = {"interval": 1, "samples": [60]}
    entry = fp.PolarExerciseEntry("/E", TIME, "e")
    assert await polar.fetch_exercise("ID", entry) == fp.PolarExerciseData(1, [60])

    polar.invoke.return_value = {"ongoing": True, "entry_id": "e"}
    assert await polar.request_recording_status("ID") == fp.PolarRecordingStatus(
        True, "e"
    )


@pytest.mark.parametrize("name", event_handler_names())
def test_every_handler_resolves_to_an_event_type(name):
    event_type = get_event_field_type(fp.Polar(), name)
    assert dataclasses.is_dataclass(event_type)
    assert event_type.__module__ == "flet_polar.types"


def test_events_are_built_from_wire_data():
    event = from_dict(
        fp.PolarEcgDataEvent,
        {
            "name": "ecg_data",
            "control": None,
            "identifier": "ID",
            "samples": [{"time_stamp": TIME, "voltage": 5}],
        },
    )
    assert event.samples == [fp.PolarEcgSample(TIME, 5)]

    readiness = from_dict(
        fp.PolarSdkFeaturesReadinessEvent,
        {
            "name": "sdk_features_readiness",
            "control": None,
            "identifier": "ID",
            "ready": ["onlineStreaming"],
            "unavailable": ["h10ExerciseRecording"],
        },
    )
    assert readiness.ready == [fp.PolarSdkFeature.ONLINE_STREAMING]

    error = from_dict(
        fp.PolarErrorEvent,
        {
            "name": "error",
            "control": None,
            "source": "streaming",
            "message": "boom",
            "identifier": "ID",
            "data_type": "skinTemperature",
        },
    )
    assert error.data_type is fp.PolarDataType.SKIN_TEMPERATURE


def test_ppg_status_bits_may_be_null():
    event = from_dict(
        fp.PolarPpgDataEvent,
        {
            "name": "ppg_data",
            "control": None,
            "identifier": "ID",
            "type": "unknown",
            "samples": [
                {"time_stamp": TIME, "channel_samples": [1], "status_bits": None}
            ],
        },
    )
    assert event.samples[0].status_bits is None


# The tests below keep the two sides of the wire protocol in sync.


def public_python_methods():
    return {
        name
        for name, value in vars(fp.Polar).items()
        if callable(value) and not name.startswith("_")
    }


def test_python_methods_and_dart_cases_match():
    source = (DART_LIB / "polar_service.dart").read_text()
    dart_cases = set(re.findall(r'case "(\w+)":', source))
    assert public_python_methods() == dart_cases


def test_every_dart_event_has_a_python_handler():
    source = (DART_LIB / "polar_service.dart").read_text()
    events = set(re.findall(r'"(\w+)",\s*\(', source))
    events |= set(re.findall(r'triggerEvent\(\s*"(\w+)"', source))
    assert events
    handlers = {name.removeprefix("on_") for name in event_handler_names()}
    assert events <= handlers
    assert handlers - events == {
        f"{name}_data"
        for name in (
            "hr",
            "ecg",
            "acc",
            "gyro",
            "magnetometer",
            "ppg",
            "ppi",
            "temperature",
            "pressure",
            "skin_temperature",
            "location",
        )
    }
