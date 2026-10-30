from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

from jnius import autoclass, PythonJavaClass, java_method

class ScanCallback(PythonJavaClass):
    __javainterfaces__ = [
        'android/bluetooth/le/ScanCallback'
    ]
    __javacontext__ = 'app'

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(Landroid/bluetooth/le/ScanResult;)V')
    def onScanResult(self, callbackType, result):
        Clock.schedule_once(
            lambda dt: self.app.add_device(result), 0
        )

    @java_method('(ILjava/lang/String;)V')
    def onScanFailed(self, errorCode):
        Clock.schedule_once(
            lambda dt: self.app.scan_failed(errorCode), 0
        )


class SenderApp(App):
    def build(self):
        self.devices = {}
        self.scanner = None
        self.callback = None

        layout = BoxLayout(
            orientation='vertical',
            padding=20,
            spacing=12
        )

        layout.add_widget(Label(
            text='لوحة تحكم المرسل',
            font_size=26,
            size_hint_y=0.15
        ))

        self.status = Label(
            text='جاهز للبحث عن المستقبل',
            font_size=18,
            size_hint_y=0.15
        )
        layout.add_widget(self.status)

        search_button = Button(
            text='البحث عن أجهزة BLE',
            font_size=20,
            size_hint_y=0.15
        )
        search_button.bind(on_press=self.start_search)
        layout.add_widget(search_button)

        self.device_list = BoxLayout(
            orientation='vertical',
            spacing=8
        )
        layout.add_widget(self.device_list)

        return layout

    def start_search(self, instance):
        if platform != 'android':
            self.status.text = 'البحث متاح على أندرويد فقط'
            return

        self.devices.clear()
        self.device_list.clear_widgets()

        from android.permissions import request_permissions

        self.status.text = 'جارٍ طلب صلاحيات البلوتوث...'

        request_permissions([
            'android.permission.BLUETOOTH_SCAN',
            'android.permission.BLUETOOTH_CONNECT'
        ], self.permissions_result)

    def permissions_result(self, permissions, grants):
        if not all(grants):
            self.status.text = 'يجب السماح بصلاحيات البلوتوث'
            return

        Clock.schedule_once(self.scan_devices, 0)

    def scan_devices(self, dt):
        try:
            BluetoothAdapter = autoclass(
                'android.bluetooth.BluetoothAdapter'
            )

            self.adapter = BluetoothAdapter.getDefaultAdapter()

            if self.adapter is None:
                self.status.text = 'الهاتف لا يدعم البلوتوث'
                return

            if not self.adapter.isEnabled():
                self.status.text = 'فعّل البلوتوث أولاً'
                return

            self.scanner = self.adapter.getBluetoothLeScanner()

            if self.scanner is None:
                self.status.text = 'تعذر تشغيل ماسح BLE'
                return

            self.callback = ScanCallback(self)

            self.status.text = 'جارٍ البحث لمدة 12 ثانية...'

            self.scanner.startScan(self.callback)

            Clock.schedule_once(self.stop_search, 12)

        except Exception as error:
            self.status.text = 'خطأ: ' + str(error)

    def add_device(self, result):
        try:
            device = result.getDevice()
            address = device.getAddress()

            if address in self.devices:
                return

            name = device.getName()

            if not name:
                name = 'جهاز غير معروف'

            self.devices[address] = device

            button = Button(
                text=f'{name} | {address}',
                size_hint_y=None,
                height=65
            )

            button.bind(
                on_press=lambda instance:
                self.select_device(address, name)
            )

            self.device_list.add_widget(button)

        except Exception:
            pass

    def scan_failed(self, error):
        self.status.text = f'فشل البحث. رمز الخطأ: {error}'

    def stop_search(self, dt):
        try:
            if self.scanner and self.callback:
                self.scanner.stopScan(self.callback)

            if self.devices:
                self.status.text = 'اختر جهاز المستقبل'
            else:
                self.status.text = 'لم يتم العثور على أجهزة'

        except Exception as error:
            self.status.text = 'خطأ في إيقاف البحث: ' + str(error)

    def select_device(self, address, name):
        self.status.text = (
            'تم اختيار الجهاز: ' + name +
            '\nسيتم تجهيز الاتصال في الخطوة التالية'
        )


SenderApp().run()
