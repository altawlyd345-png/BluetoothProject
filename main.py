from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.utils import platform

from jnius import autoclass, PythonJavaClass, java_method


class BLEScanCallback(PythonJavaClass):
    __javainterfaces__ = ['android/bluetooth/le/ScanCallback']
    __javacontext__ = 'app'

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(ILandroid/bluetooth/le/ScanResult;)V')
    def onScanResult(self, callback_type, result):
        Clock.schedule_once(
            lambda dt: self.app.add_device(result), 0
        )

    @java_method('(ILjava/lang/String;)V')
    def onScanFailed(self, error_code):
        Clock.schedule_once(
            lambda dt: self.app.scan_failed(error_code), 0
        )


class SenderApp(App):

    def build(self):
        self.devices = {}
        self.scanner = None
        self.callback = None

        layout = BoxLayout(
            orientation='vertical',
            padding=15,
            spacing=10
        )

        layout.add_widget(Label(
            text='لوحة تحكم المرسل',
            font_size=25,
            size_hint_y=0.12
        ))

        self.status = Label(
            text='جاهز للبحث عن المستقبل',
            font_size=17,
            size_hint_y=0.10
        )
        layout.add_widget(self.status)

        search = Button(
            text='البحث عن أجهزة BLE',
            size_hint_y=0.12
        )
        search.bind(on_press=self.search_devices)
        layout.add_widget(search)

        self.device_list = BoxLayout(
            orientation='vertical',
            spacing=5
        )
        layout.add_widget(self.device_list)

        self.message = TextInput(
            hint_text='اكتب النص هنا',
            multiline=True,
            font_size=22,
            size_hint_y=0.25
        )
        layout.add_widget(self.message)

        send = Button(
            text='إرسال النص',
            size_hint_y=0.12
        )
        send.bind(on_press=self.send_text)
        layout.add_widget(send)

        return layout

    def search_devices(self, instance):
        if platform != 'android':
            self.status.text = 'البحث متاح على أندرويد فقط'
            return

        from android.permissions import request_permissions

        self.status.text = 'طلب صلاحيات البلوتوث...'

        request_permissions([
            'android.permission.BLUETOOTH_SCAN',
            'android.permission.BLUETOOTH_CONNECT'
        ], self.permission_result)

    def permission_result(self, permissions, grants):
        if not all(grants):
            self.status.text = 'يجب السماح بصلاحيات البلوتوث'
            return

        Clock.schedule_once(self.start_scan, 0)

    def start_scan(self, dt):
        try:
            BluetoothAdapter = autoclass(
                'android.bluetooth.BluetoothAdapter'
            )

            self.adapter = BluetoothAdapter.getDefaultAdapter()

            if self.adapter is None:
                self.status.text = 'البلوتوث غير مدعوم'
                return

            if not self.adapter.isEnabled():
                self.status.text = 'فعّل البلوتوث أولاً'
                return

            self.scanner = self.adapter.getBluetoothLeScanner()

            if self.scanner is None:
                self.status.text = 'تعذر تشغيل ماسح BLE'
                return

            self.devices.clear()
            self.device_list.clear_widgets()

            self.callback = BLEScanCallback(self)

            self.status.text = 'جارٍ البحث لمدة 12 ثانية...'
            self.scanner.startScan(self.callback)

            Clock.schedule_once(self.stop_scan, 12)

        except Exception as error:
            self.status.text = 'خطأ: ' + str(error)

    def add_device(self, result):
        try:
            device = result.getDevice()
            address = device.getAddress()

            if address in self.devices:
                return

            name = device.getName() or 'جهاز غير معروف'
            self.devices[address] = device

            button = Button(
                text=name + ' | ' + address,
                size_hint_y=None,
                height=60
            )

            button.bind(
                on_press=lambda instance:
                self.select_device(address, name)
            )

            self.device_list.add_widget(button)

        except Exception as error:
            print(error)

    def stop_scan(self, dt):
        try:
            if self.scanner and self.callback:
                self.scanner.stopScan(self.callback)

            if self.devices:
                self.status.text = 'اختر جهاز المستقبل من القائمة'
            else:
                self.status.text = 'لم يتم العثور على أجهزة BLE'

        except Exception as error:
            self.status.text = str(error)

    def scan_failed(self, error_code):
        self.status.text = 'فشل البحث: ' + str(error_code)

    def select_device(self, address, name):
        self.status.text = 'تم اختيار: ' + name

    def send_text(self, instance):
        if not self.message.text.strip():
            self.status.text = 'اكتب نصاً أولاً'
            return

        self.status.text = 'النص جاهز، والاتصال لم يُجهّز بعد.'


SenderApp().run()
