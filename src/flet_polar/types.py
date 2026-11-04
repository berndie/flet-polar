"""Enums, data models and events exposed by the `Polar` service.

Enum values are the names of the matching Dart enums, which is what travels over
the wire. Models and events are plain dataclasses built by flet's `from_dict`, so
they must use `typing.Optional` and must not be frozen.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional, Union

import flet as ft

# --------------------------------------------------------------------------- enums


class PolarDataType(Enum):
    """Data types available for online streaming."""

    ECG = "ecg"
    ACC = "acc"
    PPG = "ppg"
    PPI = "ppi"
    GYRO = "gyro"
    MAGNETOMETER = "magnetometer"
    HR = "hr"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    SKIN_TEMPERATURE = "skinTemperature"
    LOCATION = "location"

    @property
    def supports_stream_settings(self) -> bool:
        """Whether this data type accepts a `PolarSensorSetting`."""
        return self not in (PolarDataType.HR, PolarDataType.PPI)


class PolarSdkFeature(Enum):
    """Features of the Polar BLE SDK."""

    HR = "hr"
    DEVICE_INFO = "deviceInfo"
    BATTERY_INFO = "batteryInfo"
    ONLINE_STREAMING = "onlineStreaming"
    OFFLINE_RECORDING = "offlineRecording"
    H10_EXERCISE_RECORDING = "h10ExerciseRecording"
    DEVICE_TIME_SETUP = "deviceTimeSetup"
    SDK_MODE = "sdkMode"
    LED_ANIMATION = "ledAnimation"
    FIRMWARE_UPDATE = "firmwareUpdate"
    ACTIVITY_DATA = "activityData"
    FILE_TRANSFER = "fileTransfer"
    HTS = "hts"
    SLEEP_DATA = "sleepData"
    TEMPERATURE_DATA = "temperatureData"
    FEATURES_CONFIGURATION_SERVICE = "featuresConfigurationService"
    OFFLINE_EXERCISE_V2 = "offlineExerciseV2"
    TRAINING_DATA = "trainingData"
    DEVICE_CONTROL = "deviceControl"


class PolarChargeState(Enum):
    """Battery charge state of a device."""

    UNKNOWN = "unknown"
    CHARGING = "charging"
    DISCHARGING_ACTIVE = "dischargingActive"
    DISCHARGING_INACTIVE = "dischargingInactive"


class PolarSettingType(Enum):
    """Kinds of sensor stream settings."""

    SAMPLE_RATE = "sampleRate"
    RESOLUTION = "resolution"
    RANGE = "range"
    RANGE_MILLIUNIT = "rangeMilliunit"
    CHANNELS = "channels"
    UNKNOWN = "unknown"


class PpgDataType(Enum):
    """Layout of the channels in a PPG sample."""

    PPG3_AMBIENT1 = "ppg3_ambient1"
    UNKNOWN = "unknown"


class RecordingInterval(Enum):
    """Sampling interval of an H10 recording."""

    INTERVAL_1S = "interval_1s"
    INTERVAL_5S = "interval_5s"


class SampleType(Enum):
    """Sample type of an H10 recording."""

    HR = "hr"
    RR = "rr"


class FtuGender(Enum):
    """Gender used in the first-time-use configuration."""

    MALE = "male"
    FEMALE = "female"


class FtuTrainingBackground(Enum):
    """Training background used in the first-time-use configuration."""

    OCCASIONAL = "occasional"
    REGULAR = "regular"
    FREQUENT = "frequent"
    HEAVY = "heavy"
    SEMI_PRO = "semiPro"
    PRO = "pro"


class FtuTypicalDay(Enum):
    """Typical daily activity used in the first-time-use configuration."""

    MOSTLY_MOVING = "mostlyMoving"
    MOSTLY_SITTING = "mostlySitting"
    MOSTLY_STANDING = "mostlyStanding"


class PolarErrorSource(Enum):
    """Which background operation a `PolarErrorEvent` comes from."""

    EVENTS = "events"
    SEARCH = "search"
    STREAMING = "streaming"


# -------------------------------------------------------------------------- models


@dataclass
class PolarDeviceInfo:
    """A Polar device, as seen in its advertisement."""

    device_id: str
    """Polar device id, or UUID for third-party sensors."""
    address: str
    """MAC address. Empty on iOS and usually on modern Android versions."""
    rssi: int
    """Received signal strength indicator of the advertisement."""
    name: str
    """Local name from the advertisement."""
    is_connectable: bool
    """Whether the advertisement is connectable."""


@dataclass
class PolarSensorSetting:
    """Sensor stream settings.

    `Polar.request_stream_settings` returns the values a device offers per setting.
    `Polar.start_streaming` takes a selection, holding exactly one value per
    setting: use `selection()` or `max_settings()` to make one.
    """

    settings: dict[PolarSettingType, list[int]]

    @classmethod
    def selection(cls, values: Mapping[PolarSettingType, int]) -> "PolarSensorSetting":
        """Create a selection with one chosen value per setting."""
        return cls({setting: [value] for setting, value in values.items()})

    @property
    def is_selection(self) -> bool:
        """Whether this holds exactly one value per setting."""
        return all(len(values) == 1 for values in self.settings.values())

    def max_settings(self) -> "PolarSensorSetting":
        """Return the selection with the highest value of every setting."""
        return PolarSensorSetting.selection(
            {setting: max(values) for setting, values in self.settings.items()}
        )


@dataclass
class LedConfig:
    """Configuration of the LEDs of a device."""

    sdk_mode_led_enabled: bool = True
    ppi_mode_led_enabled: bool = True


@dataclass
class PolarRecordingStatus:
    """Status of an H10 recording."""

    ongoing: bool
    entry_id: str


@dataclass
class PolarExerciseEntry:
    """An exercise stored on a device."""

    path: str
    """Resource location on the device."""
    date: datetime
    """Date and time of the entry. Only OH1 and Verity Sense support this."""
    entry_id: str
    """Unique identifier of the entry."""


@dataclass
class PolarExerciseData:
    """The samples of a stored exercise."""

    interval: int
    """Sampling interval in seconds."""
    samples: list[int]
    """HR (BPM) or RR samples."""


@dataclass
class PolarFirstTimeUseConfig:
    """First-time-use configuration of a device. Ranges are enforced by the SDK."""

    gender: FtuGender
    birth_date: Union[date, datetime]
    height: int
    """Height in centimeters (90-240)."""
    weight: int
    """Weight in kilograms (15-300)."""
    max_heart_rate: int
    """Maximum heart rate in BPM (100-240)."""
    vo2_max: int
    """VO2 max (10-95)."""
    resting_heart_rate: int
    """Resting heart rate in BPM (20-120)."""
    training_background: FtuTrainingBackground
    device_time: datetime
    typical_day: FtuTypicalDay
    sleep_goal_minutes: int
    """Sleep goal in minutes (300-660)."""


@dataclass
class PolarHrSample:
    """A heart rate sample."""

    hr: int
    """Heart rate in BPM."""
    ppg_quality: int
    corrected_hr: int
    """Corrected heart rate in BPM."""
    rrs_ms: list[int]
    """RR intervals in milliseconds."""
    contact_status: bool
    """Whether the device has contact with the skin."""
    contact_status_supported: bool


@dataclass
class PolarEcgSample:
    """An ECG sample."""

    time_stamp: datetime
    voltage: int
    """Voltage in microvolts."""


@dataclass
class PolarAccSample:
    """An accelerometer sample, in millig and including gravity."""

    time_stamp: datetime
    x: int
    y: int
    z: int


@dataclass
class PolarGyroSample:
    """A gyroscope sample, in degrees per second."""

    time_stamp: datetime
    x: float
    y: float
    z: float


@dataclass
class PolarMagnetometerSample:
    """A magnetometer sample, in Gauss."""

    time_stamp: datetime
    x: float
    y: float
    z: float


@dataclass
class PolarPpgSample:
    """A PPG sample."""

    time_stamp: datetime
    channel_samples: list[int]
    """Raw optical values. The channels depend on the `PpgDataType`."""
    status_bits: Optional[list[int]] = None
    """Per-sample validity (1 is valid), for frame types 7, 8, 10 and 13."""


@dataclass
class PolarPpiSample:
    """A pulse-to-pulse interval sample."""

    time_stamp: int
    """Raw device timestamp."""
    ppi: int
    """Pulse-to-pulse interval in milliseconds."""
    error_estimate: int
    """Estimated absolute error of `ppi` in milliseconds."""
    hr: int
    """Heart rate in BPM."""
    blocker_bit: bool
    """Whether the measurement was invalid, e.g. due to acceleration."""
    skin_contact_status: bool
    skin_contact_supported: bool


@dataclass
class PolarTemperatureSample:
    """A temperature sample, in degrees Celsius."""

    time_stamp: datetime
    temperature: float


@dataclass
class PolarPressureSample:
    """A pressure sample, in bar."""

    time_stamp: datetime
    pressure: float


@dataclass
class PolarLocationDataSample:
    """A location sample."""

    time_stamp: datetime
    latitude: float
    longitude: float
    time: str
    """Time in the format `yyyy-MM-dd'T'HH:mm:ss.SSS`."""
    cumulative_distance: float
    """Cumulative distance in decimeters."""
    speed: float
    """Speed in km/h."""
    used_acceleration_speed: float
    coordinate_speed: float
    acceleration_speed_factor: float
    course: float
    """Course in degrees."""
    gps_chip_speed: float
    """Speed in knots."""
    fix: bool
    speed_flag: int
    fusion_state: int


# -------------------------------------------------------------------------- events


@dataclass
class PolarBlePowerStateEvent(ft.Event["Polar"]):
    """The Bluetooth adapter was switched on or off."""

    enabled: bool


@dataclass
class PolarDeviceEvent(ft.Event["Polar"]):
    """A device was found, is being connected to or got connected."""

    info: PolarDeviceInfo


@dataclass
class PolarDeviceDisconnectedEvent(ft.Event["Polar"]):
    """The connection to a device was lost.

    The SDK reconnects by itself unless `Polar.disconnect_from_device` was called.
    """

    info: PolarDeviceInfo
    pairing_error: bool
    """Whether a pairing error caused the disconnect. iOS only."""


@dataclass
class PolarSdkFeatureReadyEvent(ft.Event["Polar"]):
    """A feature became available on a device."""

    identifier: str
    feature: PolarSdkFeature


@dataclass
class PolarSdkFeaturesReadinessEvent(ft.Event["Polar"]):
    """All features were evaluated after a device connected.

    Features in neither list timed out. They can still become ready later, in which
    case `Polar.on_sdk_feature_ready` reports them.
    """

    identifier: str
    ready: list[PolarSdkFeature]
    """Features that are confirmed ready for use."""
    unavailable: list[PolarSdkFeature]
    """Features that this device does not support."""


@dataclass
class PolarDisInformationEvent(ft.Event["Polar"]):
    """Device Information Service data was received."""

    identifier: str
    uuid: str
    """UUID of the information characteristic."""
    info: str
    """The value, e.g. the firmware version as major.minor.patch."""


@dataclass
class PolarBatteryLevelEvent(ft.Event["Polar"]):
    """A battery level was received."""

    identifier: str
    level: int
    """Battery level in percent."""


@dataclass
class PolarBatteryChargingStatusEvent(ft.Event["Polar"]):
    """A battery charging status was received."""

    identifier: str
    charging_status: PolarChargeState


@dataclass
class PolarHrDataEvent(ft.Event["Polar"]):
    """A packet of heart rate samples."""

    identifier: str
    samples: list[PolarHrSample]


@dataclass
class PolarEcgDataEvent(ft.Event["Polar"]):
    """A packet of ECG samples."""

    identifier: str
    samples: list[PolarEcgSample]


@dataclass
class PolarAccDataEvent(ft.Event["Polar"]):
    """A packet of accelerometer samples."""

    identifier: str
    samples: list[PolarAccSample]


@dataclass
class PolarGyroDataEvent(ft.Event["Polar"]):
    """A packet of gyroscope samples."""

    identifier: str
    samples: list[PolarGyroSample]


@dataclass
class PolarMagnetometerDataEvent(ft.Event["Polar"]):
    """A packet of magnetometer samples."""

    identifier: str
    samples: list[PolarMagnetometerSample]


@dataclass
class PolarPpgDataEvent(ft.Event["Polar"]):
    """A packet of PPG samples."""

    identifier: str
    type: PpgDataType
    samples: list[PolarPpgSample]


@dataclass
class PolarPpiDataEvent(ft.Event["Polar"]):
    """A packet of pulse-to-pulse interval samples."""

    identifier: str
    samples: list[PolarPpiSample]


@dataclass
class PolarTemperatureDataEvent(ft.Event["Polar"]):
    """A packet of (skin) temperature samples."""

    identifier: str
    samples: list[PolarTemperatureSample]


@dataclass
class PolarPressureDataEvent(ft.Event["Polar"]):
    """A packet of pressure samples."""

    identifier: str
    samples: list[PolarPressureSample]


@dataclass
class PolarLocationDataEvent(ft.Event["Polar"]):
    """A packet of location samples."""

    identifier: str
    samples: list[PolarLocationDataSample]


@dataclass
class PolarStreamEndEvent(ft.Event["Polar"]):
    """A stream ended without `Polar.stop_streaming` being called."""

    identifier: str
    data_type: PolarDataType


@dataclass
class PolarErrorEvent(ft.Event["Polar"]):
    """A background operation failed."""

    source: PolarErrorSource
    message: str
    identifier: Optional[str] = None
    """The device, if `source` is `STREAMING`."""
    data_type: Optional[PolarDataType] = None
    """The data type, if `source` is `STREAMING`."""
