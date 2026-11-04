import 'package:flet/flet.dart';

import 'polar_service.dart';

class Extension extends FletExtension {
  @override
  FletService? createService(Control control) {
    switch (control.type) {
      case "Polar":
        return PolarService(control: control);
      default:
        return null;
    }
  }
}
