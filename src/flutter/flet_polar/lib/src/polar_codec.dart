/// Translates between the polar plugin's models and the Flet wire format.
///
/// Enums travel by their Dart name and fields by the snake_case name of the
/// Python dataclass field (see `flet_polar/types.py`). The plugin's own `toJson`
/// is not used: it yields platform-specific values and is not available on all
/// models.
library;

import 'package:polar/polar.dart';

typedef Json = Map<String, dynamic>;

Json encodeDeviceInfo(PolarDeviceInfo info) => {
      "device_id": info.deviceId,
      "address": info.address,
      "rssi": info.rssi,
      "name": info.name,
      "is_connectable": info.isConnectable,
    };

List<String> encodeNames(Iterable<Enum> values) =>
    [for (final value in values) value.name];

/// [settings] holds the available values per setting.
Json encodeSensorSetting(PolarSensorSetting settings) => {
      "settings": {
        for (final entry in settings.settings.entries)
          entry.key.name: entry.value,
      },
    };

Json encodeRecordingStatus(PolarRecordingStatus status) => {
      "ongoing": status.ongoing,
      "entry_id": status.entryId,
    };

Json encodeExerciseEntry(PolarExerciseEntry entry) => {
      "path": entry.path,
      "date": entry.date,
      "entry_id": entry.entryId,
    };

Json encodeExerciseData(PolarExerciseData data) => {
      "interval": data.interval,
      "samples": data.samples,
    };

Json encodeHrData(PolarHrData data) => _samples(
      data,
      (s) => {
        "hr": s.hr,
        "ppg_quality": s.ppgQuality,
        "corrected_hr": s.correctedHr,
        "rrs_ms": s.rrsMs,
        "contact_status": s.contactStatus,
        "contact_status_supported": s.contactStatusSupported,
      },
    );

Json encodeEcgData(PolarEcgData data) => _samples(
      data,
      (s) => {"time_stamp": s.timeStamp, "voltage": s.voltage},
    );

Json encodeAccData(PolarAccData data) => _samples(
      data,
      (s) => {"time_stamp": s.timeStamp, "x": s.x, "y": s.y, "z": s.z},
    );

Json encodeGyroData(PolarGyroData data) => _samples(
      data,
      (s) => {"time_stamp": s.timeStamp, "x": s.x, "y": s.y, "z": s.z},
    );

Json encodeMagnetometerData(PolarMagnetometerData data) => _samples(
      data,
      (s) => {"time_stamp": s.timeStamp, "x": s.x, "y": s.y, "z": s.z},
    );

Json encodePpgData(PolarPpgData data) => {
      "type": data.type.name,
      ..._samples(
        data,
        (s) => {
          "time_stamp": s.timeStamp,
          "channel_samples": s.channelSamples,
          "status_bits": s.statusBits,
        },
      ),
    };

Json encodePpiData(PolarPpiData data) => _samples(
      data,
      (s) => {
        "time_stamp": s.timeStamp,
        "ppi": s.ppi,
        "error_estimate": s.errorEstimate,
        "hr": s.hr,
        "blocker_bit": s.blockerBit,
        "skin_contact_status": s.skinContactStatus,
        "skin_contact_supported": s.skinContactSupported,
      },
    );

Json encodeTemperatureData(PolarTemperatureData data) => _samples(
      data,
      (s) => {"time_stamp": s.timeStamp, "temperature": s.temperature},
    );

Json encodePressureData(PolarPressureData data) => _samples(
      data,
      (s) => {"time_stamp": s.timeStamp, "pressure": s.pressure},
    );

Json encodeLocationData(PolarLocationData data) => _samples(
      data,
      (s) => {
        "time_stamp": s.timeStamp,
        "latitude": s.latitude,
        "longitude": s.longitude,
        "time": s.time,
        "cumulative_distance": s.cumulativeDistance,
        "speed": s.speed,
        "used_acceleration_speed": s.usedAccelerationSpeed,
        "coordinate_speed": s.coordinateSpeed,
        "acceleration_speed_factor": s.accelerationSpeedFactor,
        "course": s.course,
        "gps_chip_speed": s.gpsChipSpeed,
        "fix": s.fix,
        "speed_flag": s.speedFlag,
        "fusion_state": s.fusionState,
      },
    );

Json _samples<T>(PolarStreamingData<T> data, Json Function(T) encode) => {
      "samples": [for (final sample in data.samples) encode(sample)],
    };

/// [selection] maps setting names to the single chosen value of that setting.
PolarSensorSetting decodeSensorSetting(Map selection) => PolarSensorSetting({
      for (final entry in selection.entries)
        PolarSettingType.values.byName(entry.key as String): entry.value as int,
    });

PolarExerciseEntry decodeExerciseEntry(Map json) => PolarExerciseEntry(
      path: json["path"],
      date: json["date"],
      entryId: json["entry_id"],
    );

LedConfig decodeLedConfig(Map json) => LedConfig(
      sdkModeLedEnabled: json["sdk_mode_led_enabled"],
      ppiModeLedEnabled: json["ppi_mode_led_enabled"],
    );

PolarFirstTimeUseConfig decodeFirstTimeUseConfig(Map json) =>
    PolarFirstTimeUseConfig(
      gender: FtuGender.values.byName(json["gender"]),
      birthDate: json["birth_date"],
      height: json["height"],
      weight: json["weight"],
      maxHeartRate: json["max_heart_rate"],
      vo2Max: json["vo2_max"],
      restingHeartRate: json["resting_heart_rate"],
      trainingBackground:
          FtuTrainingBackground.values.byName(json["training_background"]),
      deviceTime: json["device_time"],
      typicalDay: FtuTypicalDay.values.byName(json["typical_day"]),
      sleepGoalMinutes: json["sleep_goal_minutes"],
    );

/// Name of the Python `on_<name>` handler receiving packets of [type].
String dataEventName(PolarDataType type) {
  final snakeCase = type.name.replaceAllMapped(
    RegExp("[A-Z]"),
    (match) => "_${match[0]!.toLowerCase()}",
  );
  return "${snakeCase}_data";
}

/// Opens the plugin's stream for [type], encoding each packet for the wire.
Stream<Json> openDataStream(
  Polar polar,
  PolarDataType type,
  String identifier,
  PolarSensorSetting? settings,
) =>
    switch (type) {
      PolarDataType.hr => polar.startHrStreaming(identifier).map(encodeHrData),
      PolarDataType.ppi =>
        polar.startPpiStreaming(identifier).map(encodePpiData),
      PolarDataType.ecg => polar
          .startEcgStreaming(identifier, settings: settings)
          .map(encodeEcgData),
      PolarDataType.acc => polar
          .startAccStreaming(identifier, settings: settings)
          .map(encodeAccData),
      PolarDataType.gyro => polar
          .startGyroStreaming(identifier, settings: settings)
          .map(encodeGyroData),
      PolarDataType.magnetometer => polar
          .startMagnetometerStreaming(identifier, settings: settings)
          .map(encodeMagnetometerData),
      PolarDataType.ppg => polar
          .startPpgStreaming(identifier, settings: settings)
          .map(encodePpgData),
      PolarDataType.temperature => polar
          .startTemperatureStreaming(identifier, settings: settings)
          .map(encodeTemperatureData),
      PolarDataType.pressure => polar
          .startPressureStreaming(identifier, settings: settings)
          .map(encodePressureData),
      PolarDataType.skinTemperature => polar
          .startSkinTemperatureStreaming(identifier, settings: settings)
          .map(encodeTemperatureData),
      PolarDataType.location => polar
          .startLocationStreaming(identifier, settings: settings)
          .map(encodeLocationData),
    };
