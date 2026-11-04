import 'dart:async';

import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:polar/polar.dart';

import 'polar_codec.dart';

/// Bridges the Python `Polar` service to the polar plugin.
class PolarService extends FletService {
  PolarService({required super.control});

  /// `null` on platforms the plugin does not support.
  Polar? _polar;
  final _eventSubscriptions = <StreamSubscription>[];
  StreamSubscription? _searchSubscription;
  final _dataSubscriptions = <String, StreamSubscription>{};

  static bool get _isSupported =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
    if (!_isSupported) return;

    final polar = Polar(
      bluetoothScanNeverForLocation:
          control.getBool("bluetooth_scan_never_for_location", true)!,
    );
    _polar = polar;
    _eventSubscriptions.addAll([
      _forward(polar.blePowerState, "ble_power_state_change",
          (enabled) => {"enabled": enabled}),
      _forward(polar.deviceConnecting, "device_connecting",
          (info) => {"info": encodeDeviceInfo(info)}),
      _forward(polar.deviceConnected, "device_connected",
          (info) => {"info": encodeDeviceInfo(info)}),
      _forward(
          polar.deviceDisconnected,
          "device_disconnected",
          (e) => {
                "info": encodeDeviceInfo(e.info),
                "pairing_error": e.pairingError,
              }),
      _forward(
          polar.sdkFeatureReady,
          "sdk_feature_ready",
          (e) => {"identifier": e.identifier, "feature": e.feature.name}),
      _forward(
          polar.sdkFeaturesReadiness,
          "sdk_features_readiness",
          (e) => {
                "identifier": e.identifier,
                "ready": encodeNames(e.ready),
                "unavailable": encodeNames(e.unavailable),
              }),
      _forward(
          polar.disInformation,
          "dis_information",
          (e) => {"identifier": e.identifier, "uuid": e.uuid, "info": e.info}),
      _forward(polar.batteryLevel, "battery_level",
          (e) => {"identifier": e.identifier, "level": e.level}),
      _forward(
          polar.batteryChargingStatus,
          "battery_charging_status",
          (e) => {
                "identifier": e.identifier,
                "charging_status": e.chargingStatus.name,
              }),
    ]);
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(_invokeMethod);
    // The plugin is a process-wide singleton, so it is left running here:
    // releasing it is an explicit `shut_down` call.
    for (final subscription in _eventSubscriptions) {
      subscription.cancel();
    }
    _cancelSearchAndStreams();
    super.dispose();
  }

  StreamSubscription<T> _forward<T>(
    Stream<T> stream,
    String event,
    Json Function(T) encode,
  ) =>
      stream.listen(
        (value) => control.triggerEvent(event, encode(value)),
        onError: (Object error) => _triggerError("events", error),
      );

  void _triggerError(
    String source,
    Object error, {
    String? identifier,
    PolarDataType? dataType,
  }) {
    control.triggerEvent("error", {
      "source": source,
      "message": _describe(error),
      "identifier": identifier,
      "data_type": dataType?.name,
    });
  }

  static String _describe(Object error) => error is PlatformException
      ? error.message ?? error.code
      : error.toString();

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    final polar = _polar;
    if (polar == null) {
      throw _PolarException("Polar is only supported on Android and iOS");
    }
    try {
      return await _dispatch(polar, name, args);
    } catch (error) {
      throw _PolarException(_describe(error));
    }
  }

  Future<dynamic> _dispatch(Polar polar, String name, dynamic args) async {
    final String identifier = args?["identifier"] ?? "";
    switch (name) {
      case "request_permissions":
        await polar.requestPermissions();
      case "start_device_search":
        await _startSearch(polar);
      case "stop_device_search":
        await _searchSubscription?.cancel();
        _searchSubscription = null;
      case "connect_to_device":
        await polar.connectToDevice(
          identifier,
          requestPermissions: args["request_permissions"],
        );
      case "disconnect_from_device":
        await polar.disconnectFromDevice(identifier);
      case "shut_down":
        await _cancelSearchAndStreams();
        await polar.shutDown();
      case "get_available_online_stream_data_types":
        return encodeNames(
            await polar.getAvailableOnlineStreamDataTypes(identifier));
      case "get_available_hr_service_data_types":
        return encodeNames(
            await polar.getAvailableHrServiceDataTypes(identifier));
      case "request_stream_settings":
        return encodeSensorSetting(
            await polar.requestStreamSettings(identifier, _dataType(args)));
      case "start_streaming":
        final settings = args["settings"];
        await _startStream(polar, identifier, _dataType(args),
            settings == null ? null : decodeSensorSetting(settings));
      case "stop_streaming":
        await _dataSubscriptions
            .remove(_streamKey(identifier, _dataType(args)))
            ?.cancel();
      case "start_recording":
        await polar.startRecording(
          identifier,
          exerciseId: args["exercise_id"],
          interval: RecordingInterval.values.byName(args["interval"]),
          sampleType: SampleType.values.byName(args["sample_type"]),
        );
      case "stop_recording":
        await polar.stopRecording(identifier);
      case "request_recording_status":
        return encodeRecordingStatus(
            await polar.requestRecordingStatus(identifier));
      case "list_exercises":
        final entries = await polar.listExercises(identifier);
        return [for (final entry in entries) encodeExerciseEntry(entry)];
      case "fetch_exercise":
        return encodeExerciseData(await polar.fetchExercise(
            identifier, decodeExerciseEntry(args["entry"])));
      case "remove_exercise":
        await polar.removeExercise(
            identifier, decodeExerciseEntry(args["entry"]));
      case "set_led_config":
        await polar.setLedConfig(identifier, decodeLedConfig(args["config"]));
      case "do_factory_reset":
        await polar.doFactoryReset(
            identifier, args["preserve_pairing_information"]);
      case "enable_sdk_mode":
        await polar.enableSdkMode(identifier);
      case "disable_sdk_mode":
        await polar.disableSdkMode(identifier);
      case "is_sdk_mode_enabled":
        return await polar.isSdkModeEnabled(identifier);
      case "do_first_time_use":
        await polar.doFirstTimeUse(
            identifier, decodeFirstTimeUseConfig(args["config"]));
      case "is_ftu_done":
        return await polar.isFtuDone(identifier);
      default:
        throw UnsupportedError("Unknown Polar method: $name");
    }
    return null;
  }

  static PolarDataType _dataType(dynamic args) =>
      PolarDataType.values.byName(args["data_type"]);

  static String _streamKey(String identifier, PolarDataType type) =>
      "$identifier/${type.name}";

  Future<void> _startSearch(Polar polar) async {
    await _searchSubscription?.cancel();
    _searchSubscription = polar.searchForDevice().listen(
      (info) =>
          control.triggerEvent("device_found", {"info": encodeDeviceInfo(info)}),
      onError: (Object error) => _triggerError("search", error),
    );
  }

  Future<void> _startStream(
    Polar polar,
    String identifier,
    PolarDataType type,
    PolarSensorSetting? settings,
  ) async {
    final key = _streamKey(identifier, type);
    await _dataSubscriptions.remove(key)?.cancel();

    final event = dataEventName(type);
    late final StreamSubscription<Json> subscription;

    void ended() {
      // A stale subscription must not take a restarted stream down with it.
      if (_dataSubscriptions[key] != subscription) return;
      _dataSubscriptions.remove(key);
      control.triggerEvent("stream_end", {
        "identifier": identifier,
        "data_type": type.name,
      });
    }

    subscription = openDataStream(polar, type, identifier, settings).listen(
      (data) =>
          control.triggerEvent(event, {"identifier": identifier, ...data}),
      onError: (Object error) {
        _triggerError("streaming", error,
            identifier: identifier, dataType: type);
        ended();
      },
      onDone: ended,
      cancelOnError: true,
    );
    _dataSubscriptions[key] = subscription;
  }

  Future<void> _cancelSearchAndStreams() async {
    final subscriptions = [
      ?_searchSubscription,
      ..._dataSubscriptions.values,
    ];
    _searchSubscription = null;
    _dataSubscriptions.clear();
    await Future.wait([for (final s in subscriptions) s.cancel()]);
  }
}

class _PolarException implements Exception {
  final String message;
  const _PolarException(this.message);

  @override
  String toString() => message;
}
