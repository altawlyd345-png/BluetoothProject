from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.utils import platform


class SenderApp(App):

    def build(self):
        self.devices = {}

        root = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )

        root.add_widget(Label(
            text="Bluetooth Sender",
            font_size=26,
            size_hint_y=0.12
        ))

        self.status = Label(
            text="جاهز للاتصال",
            font_size=18,
            size_hint_y=0.10
        )
        root.add_widget(self.status)

        search_button = Button(
            text="البحث عن المستقبل",
            font_size=20,
            size_hint_y=0.12
        )
        search_button.bind(on_press=self.search_devices)
        root.add_widget(search_button)

        self.device_list = BoxLayout(
            orientation="vertical",
            spacing=5
        )
        root.add_widget(self.device_list)

        self.text_input = TextInput(
            hint_text="اكتب النص العربي أو الإنجليزي",
            multiline=True,
            font_size=22,
            size_hint_y=0.25
        )
        root.add_widget(self.text_input)

        self.send_button = Button(
            text="إرسال النص",
            font_size=20,
            size_hint_y=0.12
        )
        self.send_button.bind(on_press=self.send_text)
        root.add_widget(self.send_button)

        return root

    def search_devices(self, instance):
        if platform != "android":
            self.status.text = "يتطلب هاتف أندرويد"
            return

        try:
            from android.permissions import request_permissions

            self.status.text = "طلب صلاحيات البلوتوث..."

            request_permissions([
                "android.permission.BLUETOOTH",
                "android.permission.BLUETOOTH_ADMIN",
                "android.permission.ACCESS_FINE_LOCATION"
            ], self.permissions_result)

        except Exception as error:
            self.status.text = "خطأ: " + str(error)

    def permissions_result(self, permissions, grants):
        if not all(grants):
            self.status.text = "يجب السماح بالصلاحيات"
            return

        self.status.text = "تم منح الصلاحيات"

    def send_text(self, instance):
        text = self.text_input.text.strip()

        if not text:
            self.status.text = "اكتب نصاً أولاً"
            return

        self.status.text = "النص جاهز للإرسال عبر BLE"


SenderApp().run()
