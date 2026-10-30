from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.utils import platform


SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
WRITE_UUID = "12345678-1234-5678-1234-56789abcdef1"


class SenderApp(App):

    def build(self):
        self.devices = {}

        layout = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )

        layout.add_widget(Label(
            text="لوحة تحكم المرسل",
            font_size=26,
            size_hint_y=0.12
        ))

        self.status = Label(
            text="غير متصل",
            font_size=18,
            size_hint_y=0.10
        )
        layout.add_widget(self.status)

        search = Button(
            text="البحث عن المستقبل BLE",
            size_hint_y=0.12
        )
        search.bind(on_press=self.search_devices)
        layout.add_widget(search)

        self.devices_box = BoxLayout(
            orientation="vertical",
            size_hint_y=0.25
        )
        layout.add_widget(self.devices_box)

        self.message = TextInput(
            hint_text="اكتب النص العربي أو الإنجليزي هنا",
            multiline=True,
            font_size=22,
            size_hint_y=0.25
        )
        layout.add_widget(self.message)

        send = Button(
            text="إرسال النص",
            font_size=22,
            size_hint_y=0.14
        )
        send.bind(on_press=self.send_text)
        layout.add_widget(send)

        return layout

    def search_devices(self, instance):
        if platform != "android":
            self.status.text = "يتطلب هاتف أندرويد"
            return

        try:
            from android.permissions import request_permissions

            self.status.text = "طلب صلاحيات BLE..."

            request_permissions([
                "android.permission.BLUETOOTH_SCAN",
                "android.permission.BLUETOOTH_CONNECT"
            ], self.permission_result)

        except Exception as error:
            self.status.text = str(error)

    def permission_result(self, permissions, grants):
        if not all(grants):
            self.status.text = "لم يتم منح صلاحيات البلوتوث"
            return

        Clock.schedule_once(self.start_scan, 0)

    def start_scan(self, dt):
        try:
            from jnius import autoclass

            BluetoothAdapter = autoclass(
                "android.bluetooth.BluetoothAdapter"
            )

            self.adapter = BluetoothAdapter.getDefaultAdapter()

            if self.adapter is None:
                self.status.text = "البلوتوث غير مدعوم"
                return

            if not self.adapter.isEnabled():
                self.status.text = "فعّل البلوتوث أولاً"
                return

            self.scanner = self.adapter.getBluetoothLeScanner()

            self.status.text = (
                "ماسح BLE جاهز. سنضيف مستمع البحث والاتصال في الخطوة التالية."
            )

        except Exception as error:
            self.status.text = "خطأ: " + str(error)

    def send_text(self, instance):
        text = self.message.text.strip()

        if not text:
            self.status.text = "اكتب نصاً أولاً"
            return

        self.status.text = (
            "النص جاهز بترميز UTF-8، "
            "بانتظار تجهيز اتصال المستقبل."
        )


SenderApp().run()
