import flet as ft

import flet_polar as fp


def main(page: ft.Page):
    page.title = "Polar"

    status = ft.Text("Tap search to find a Polar device")
    heart_rate = ft.Text("-- bpm", size=48)
    battery = ft.Text()
    devices = ft.ListView(expand=True)
    disconnect_button = ft.Button("Disconnect", visible=False)
    connected_id = None

    def on_device_found(e: fp.PolarDeviceEvent):
        if any(tile.key == e.info.device_id for tile in devices.controls):
            return

        async def connect():
            await polar.stop_device_search()
            await polar.connect_to_device(e.info.device_id)

        devices.controls.append(
            ft.ListTile(
                key=e.info.device_id,
                title=e.info.name,
                subtitle=f"{e.info.rssi} dBm",
                on_click=connect,
            )
        )

    def on_device_connecting(e: fp.PolarDeviceEvent):
        status.value = f"Connecting to {e.info.name}..."

    def on_device_connected(e: fp.PolarDeviceEvent):
        nonlocal connected_id
        connected_id = e.info.device_id
        status.value = f"Connected to {e.info.name}"
        disconnect_button.visible = True

    def on_device_disconnected(e: fp.PolarDeviceDisconnectedEvent):
        status.value = f"Disconnected from {e.info.name}"
        heart_rate.value = "-- bpm"
        disconnect_button.visible = False

    async def on_sdk_features_readiness(e: fp.PolarSdkFeaturesReadinessEvent):
        if fp.PolarSdkFeature.ONLINE_STREAMING not in e.ready:
            status.value = "This device does not support online streaming"
            return
        available = await polar.get_available_online_stream_data_types(e.identifier)
        if fp.PolarDataType.HR in available:
            await polar.start_streaming(e.identifier, fp.PolarDataType.HR)

    def on_hr_data(e: fp.PolarHrDataEvent):
        heart_rate.value = f"{e.samples[-1].hr} bpm"

    def on_battery_level(e: fp.PolarBatteryLevelEvent):
        battery.value = f"Battery: {e.level}%"

    def on_error(e: fp.PolarErrorEvent):
        status.value = f"Error: {e.message}"

    polar = fp.Polar(
        on_device_found=on_device_found,
        on_device_connecting=on_device_connecting,
        on_device_connected=on_device_connected,
        on_device_disconnected=on_device_disconnected,
        on_sdk_features_readiness=on_sdk_features_readiness,
        on_hr_data=on_hr_data,
        on_battery_level=on_battery_level,
        on_error=on_error,
    )

    async def search():
        await polar.request_permissions()
        await polar.start_device_search()
        status.value = "Searching..."

    async def disconnect():
        await polar.disconnect_from_device(connected_id)

    disconnect_button.on_click = disconnect

    page.add(
        status,
        heart_rate,
        battery,
        ft.Row([ft.Button("Search", on_click=search), disconnect_button]),
        devices,
    )


ft.run(main)
