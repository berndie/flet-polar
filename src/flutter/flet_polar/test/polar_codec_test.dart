import 'dart:io';

import 'package:flet_polar/src/polar_codec.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:polar/polar.dart';

void main() {
  final time = DateTime.utc(2026, 1, 2);

  test('data events are named after the Python handlers', () {
    expect(dataEventName(PolarDataType.hr), 'hr_data');
    expect(dataEventName(PolarDataType.skinTemperature), 'skin_temperature_data');
  });

  test('every data type has an event name', () {
    expect(PolarDataType.values.map(dataEventName).toSet(),
        hasLength(PolarDataType.values.length));
  });

  test('encodes HR samples with snake_case keys', () {
    const data = PolarHrData(samples: [
      PolarHrSample(
        hr: 60,
        ppgQuality: 1,
        correctedHr: 61,
        rrsMs: [1000],
        contactStatus: true,
        contactStatusSupported: false,
      ),
    ]);
    expect(encodeHrData(data), {
      'samples': [
        {
          'hr': 60,
          'ppg_quality': 1,
          'corrected_hr': 61,
          'rrs_ms': [1000],
          'contact_status': true,
          'contact_status_supported': false,
        },
      ],
    });
  });

  test('encodes the PPG type next to its samples', () {
    final data = PolarPpgData(type: PpgDataType.ppg3_ambient1, samples: [
      PolarPpgSample(timeStamp: time, channelSamples: const [1, 2, 3, 4]),
    ]);
    expect(encodePpgData(data), {
      'type': 'ppg3_ambient1',
      'samples': [
        {
          'time_stamp': time,
          'channel_samples': [1, 2, 3, 4],
          'status_bits': null,
        },
      ],
    });
  });

  test('sensor settings encode all values and decode a selection', () {
    final selection = decodeSensorSetting({'sampleRate': 130, 'resolution': 14});
    expect(selection.isSelection, isTrue);
    expect(encodeSensorSetting(selection), {
      'settings': {
        'sampleRate': [130],
        'resolution': [14],
      },
    });
  });

  test('exercise entries survive a round trip', () {
    final entry = PolarExerciseEntry(path: '/E/1', date: time, entryId: 'id');
    final decoded = decodeExerciseEntry(encodeExerciseEntry(entry));
    expect(decoded.path, entry.path);
    expect(decoded.date, entry.date);
    expect(decoded.entryId, entry.entryId);
  });

  test('decodes the first-time-use config', () {
    final config = decodeFirstTimeUseConfig({
      'gender': 'female',
      'birth_date': time,
      'height': 170,
      'weight': 60,
      'max_heart_rate': 180,
      'vo2_max': 40,
      'resting_heart_rate': 60,
      'training_background': 'semiPro',
      'device_time': time,
      'typical_day': 'mostlySitting',
      'sleep_goal_minutes': 480,
    });
    expect(config.gender, FtuGender.female);
    expect(config.trainingBackground, FtuTrainingBackground.semiPro);
    expect(config.typicalDay, FtuTypicalDay.mostlySitting);
  });

  test('Python enums use the names of the Dart enums', () {
    final source = File('../../flet_polar/types.py').readAsStringSync();

    Set<String> pythonValues(String enumName) {
      final body = RegExp('class $enumName\\(Enum\\):(.*?)(?=\\nclass |\\n# -)',
              dotAll: true)
          .firstMatch(source)![1]!;
      return RegExp(r'^    \w+ = "(\w+)"$', multiLine: true)
          .allMatches(body)
          .map((match) => match[1]!)
          .toSet();
    }

    const enums = <String, List<Enum>>{
      'PolarDataType': PolarDataType.values,
      'PolarSdkFeature': PolarSdkFeature.values,
      'PolarChargeState': PolarChargeState.values,
      'PolarSettingType': PolarSettingType.values,
      'PpgDataType': PpgDataType.values,
      'RecordingInterval': RecordingInterval.values,
      'SampleType': SampleType.values,
      'FtuGender': FtuGender.values,
      'FtuTrainingBackground': FtuTrainingBackground.values,
      'FtuTypicalDay': FtuTypicalDay.values,
    };
    enums.forEach((name, values) {
      expect(pythonValues(name), {for (final v in values) v.name},
          reason: name);
    });
  });
}
