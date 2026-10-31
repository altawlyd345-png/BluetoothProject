import os

from import os

from  import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.text import LabelBase

from jnius import autoclass, PythonJavaClass, java_method

import arabic_reshaper
from bidi.algorithm import get_display

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
WRITE_UUID = "12345678-1234-5678-1234-56789abcdef1"

FONT_NAME = "Roboto"

font_path = os.path.join(
os.path.dirname(file),
"NotoNaskhArabic-Regular.ttf"
)

if os.path.exists(font_path):
LabelBase.register(name="ArabicFont", fn_regular=font_path)
FONT_NAME = "ArabicFont"

def arabic_text(text):
try:
return get_display(arabic_reshaper.reshape(str(text)))
except Exception:
return str(text)

class ScanListener(PythonJavaClass):
javainterfaces = [
"org/bluetoothproject/bluetoothsender/BluetoothHelper$ScanListener"
]
javacontext = "app"

def __init__(self, app):
    super().__init__()
    self.app = app

@java_method("(Landroid/bluetooth/le/ScanResult;)V")
def onDeviceFound(self, result):
    Clock.schedule_once(
        lambda dt: self.app.add_device(result), 0
    )

@java_method("(I)V")
def onScanError(self, error):
    Clock.schedule_once(
        lambda dt: self.app.set_status(
            "فشل البحث: " + str(error)
        ), 0
    )

class GattListener(PythonJavaClass):
javainterfaces = [
"org/bluetoothproject/bluetoothsender/BluetoothHelper$GattListener"
]
javacontext = "app"

def __init__(self, app):
    super().__init__()
    self.app = app

@java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
def onConnection(self, gatt, status, state):
    Clock.schedule_once(
        lambda dt: self.app.connection_changed(
            gatt, status, state
        ), 0
    )

@java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
def onServices(self, gatt, status):
    Clock.schedule_once(
        lambda dt: self.app.services_discovered(
            gatt, status
        ), 0
    )

@java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V")
def onWrite(self, gatt, characteristic, status):
    Clock.schedule_once(
        lambda dt: self.app.write_finished(status), 0
    )

class SenderApp(App):

def build(self):
    self.devices = {}
    self.scanner = None
    self.scan_callback = None
    self.gatt_callback = None
    self.gatt = None
    self.adapter = None
    self.connected = False
    self.write_characteristic = None

    root = BoxLayout(
        orientation="vertical",
        padding=12,
        spacing=10
    )

    self.status = Label(
        text=arabic_text("التطبيق جاهز"),
        font_name=FONT_NAME,
        font_size=18,
        size_hint_y=0.12
    )
    root.add_widget(self.status)

    title = Label(
        text=arabic_text("مرسل البلوتوث"),
        font_name=FONT_NAME,
        font_size=27,
        size_hint_y=0.10
    )
    root.add_widget(title)

    search = Button(
        text=arabic_text("البحث عن أجهزة البلوتوث"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.12
    )
    search.bind(on_press=self.search_devices)
    root.add_widget(search)

    self.device_list = BoxLayout(
        orientation="vertical",
        spacing=5,
        size_hint_y=0.30
    )
    root.add_widget(self.device_list)

    self.text_input = TextInput(
        hint_text=arabic_text("اكتب النص هنا"),
        multiline=True,
        font_name=FONT_NAME,
        font_size=21,
        size_hint_y=0.25,
        halign="right"
    )
    root.add_widget(self.text_input)

    send = Button(
        text=arabic_text("إرسال النص"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.12
    )
    send.bind(on_press=self.send_text)
    root.add_widget(send)

    disconnect = Button(
        text=arabic_text("قطع الاتصال"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.09
    )
    disconnect.bind(on_press=self.disconnect)
    root.add_widget(disconnect)

    return root

def set_status(self, message):
    self.status.text = arabic_text(message)

def search_devices(self, instance):
    try:
        from android.permissions import request_permissions

        version = autoclass(
            "android.os.Build$VERSION"
        ).SDK_INT

        if version >= 31:
            permissions = [
                "android.permission.BLUETOOTH_SCAN",
                "android.permission.BLUETOOTH_CONNECT"
            ]
        else:
            permissions = [
                "android.permission.ACCESS_FINE_LOCATION"
            ]

        request_permissions(
            permissions,
            self.permission_result
        )

    except Exception as error:
        self.set_status("خطأ الصلاحيات: " + str(error))

def permission_result(self, permissions, grants):
    if not all(grants):
        self.set_status("يرجى السماح بالصلاحيات")
        return

    Clock.schedule_once(self.start_scan, 0)

def start_scan(self, dt):
    try:
        BluetoothAdapter = autoclass(
            "android.bluetooth.BluetoothAdapter"
        )

        self.adapter = BluetoothAdapter.getDefaultAdapter()

        if self.adapter is None:
            self.set_status("البلوتوث غير متاح")
            return

        if not self.adapter.isEnabled():
            self.set_status("يرجى تشغيل البلوتوث")
            return

        self.scanner = self.adapter.getBluetoothLeScanner()

        if self.scanner is None:
            self.set_status("ماسح البلوتوث غير متاح")
            return

        BluetoothHelper = autoclass(
            "org.bluetoothproject.bluetoothsender.BluetoothHelper"
        )

        self.devices.clear()
        self.device_list.clear_widgets()

        self.scan_listener = ScanListener(self)
        self.scan_callback = BluetoothHelper.createScanner(
            self.scan_listener
        )

        self.set_status("جارٍ البحث عن الأجهزة...")
        self.scanner.startScan(self.scan_callback)

        Clock.schedule_once(self.stop_scan, 12)

    except Exception as error:
        self.set_status("خطأ البحث: " + str(error))

def add_device(self, result):
    try:
        device = result.getDevice()
        address = device.getAddress()

        if address in self.devices:
            return

        name = device.getName() or "جهاز غير معروف"
        self.devices[address] = device

        button = Button(
            text=arabic_text(name + "\n" + address),
            font_name=FONT_NAME,
            size_hint_y=None,
            height=70
        )

        button.bind(
            on_press=lambda instance: self.connect_device(address)
        )

        self.device_list.add_widget(button)

    except Exception as error:
        self.set_status("خطأ الجهاز: " + str(error))

def stop_scan(self, dt):
    try:
        if self.scanner and self.scan_callback:
            self.scanner.stopScan(self.scan_callback)

        if self.devices:
            self.set_status("اختر جهاز المستقبل")
        else:
            self.set_status("لم يتم العثور على أجهزة")

    except Exception as error:
        self.set_status("خطأ إيقاف البحث: " + str(error))

def connect_device(self, address):
    try:
        if self.scanner and self.scan_callback:
            self.scanner.stopScan(self.scan_callback)

        device = self.devices[address]

        activity = autoclass(
            "org.kivy.android.PythonActivity"
        ).mActivity

        BluetoothHelper = autoclass(
            "org.bluetoothproject.bluetoothsender.BluetoothHelper"
        )

        self.gatt_listener = GattListener(self)
        self.gatt_callback = BluetoothHelper.createGattCallback(
            self.gatt_listener
        )

        self.set_status("جارٍ الاتصال...")

        self.gatt = device.connectGatt(
            activity,
            False,
            self.gatt_callback
        )

    except Exception as error:
        self.set_status("خطأ الاتصال: " + str(error))

def connection_changed(self, gatt, status, state):
    if status != 0:
        self.set_status("فشل الاتصال: " + str(status))
        return

    if state == 2:
        self.set_status("متصل، جارٍ اكتشاف الخدمات")
        gatt.discoverServices()

    elif state == 0:
        self.connected = False
        self.write_characteristic = None
        self.set_status("انقطع الاتصال")

def services_discovered(self, gatt, status):
    try:
        if status != 0:
            self.set_status("فشل اكتشاف الخدمات")
            return

        UUID = autoclass("java.util.UUID")

        service = gatt.getService(
            UUID.fromString(SERVICE_UUID)
        )

        if service is None:
            self.set_status("خدمة المستقبل غير موجودة")
            return

        self.write_characteristic = service.getCharacteristic(
            UUID.fromString(WRITE_UUID)
        )

        if self.write_characteristic is None:
            self.set_status("خاصية استقبال النص غير موجودة")
            return

        self.connected = True
        self.set_status("تم الاتصال، يمكنك إرسال النص")

    except Exception as error:
        self.set_status("خطأ الخدمات: " + str(error))

def send_text(self, instance):
    if not self.connected or self.write_characteristic is None:
        self.set_status("اتصل بالمستقبل أولاً")
        return

    text = self.text_input.text

    if not text.strip():
        self.set_status("اكتب نصاً أولاً")
        return

    try:
        data = text.encode("utf-8")

        if len(data) > 180:
            self.set_status("النص طويل، الحد الحالي 180 بايت")
            return

        self.write_characteristic.setValue(data)

        result = self.gatt.writeCharacteristic(
            self.write_characteristic
        )

        if result:
            self.set_status("تم طلب إرسال النص")
        else:
            self.set_status("تعذر بدء الإرسال")

    except Exception as error:
        self.set_status("خطأ الإرسال: " + str(error))

def write_finished(self, status):
    if status == 0:
        self.set_status("اكتمل إرسال النص")
    else:
        self.set_status("فشل إرسال النص: " + str(status))

def disconnect(self, instance):
    try:
        if self.gatt:
            self.gatt.disconnect()
            self.gatt.close()

        self.gatt = None
        self.connected = False
        self.write_characteristic = None

        self.set_status("تم قطع الاتصال")

    except Exception as error:
        self.set_status("خطأ قطع الاتصال: " + str(error))

if name == "main":
SenderApp().run() import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase

from jnius import autoclass, PythonJavaClass, java_method
import arabic_reshaper
from bidi.algorithm import get_display


SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
WRITE_UUID = "12345678-1234-5678-1234-56789abcdef1"
NOTIFY_UUID = "12345678-1234-5678-1234-56789abcdef2"

FONT_NAME = "Roboto"

font_path = os.path.join(
    os.path.dirname(__file__),
    "NotoNaskhArabic-Regular.ttf"
)

if os.path.exists(font_path):
    LabelBase.register(
        name="ArabicFont",
        fn_regular=font_path
    )
    FONT_NAME = "ArabicFont"


def arabic_text(text):
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)


class ScanCallback(PythonJavaClass):
    __javainterfaces__ = [
        "android/bluetooth/le/ScanCallback"
    ]
    __javacontext__ = "app"

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(ILandroid/bluetooth/le/ScanResult;)V")
    def onScanResult(self, callback_type, result):
        Clock.schedule_once(
            lambda dt: self.app.add_device(result), 0
        )

    @java_method("(I)V")
    def onScanFailed(self, error):
        Clock.schedule_once(
            lambda dt: self.app.set_status(
                "فشل البحث: " + str(error)
            ), 0
        )


class GattCallback(PythonJavaClass):
    __javainterfaces__ = [
        "android/bluetooth/BluetoothGattCallback"
    ]
    __javacontext__ = "app"

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
    def onConnectionStateChange(self, gatt, status, state):
        Clock.schedule_once(
            lambda dt: self.app.connection_changed(
                gatt, status, state
            ), 0
        )

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        Clock.schedule_once(
            lambda dt: self.app.services_discovered(
                gatt, status
            ), 0
        )

    @java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V")
    def onCharacteristicWrite(self, gatt, characteristic, status):
        Clock.schedule_once(
            lambda dt: self.app.write_finished(status), 0
        )


class SenderApp(App):

    def build(self):
        self.devices = {}
        self.scanner = None
        self.scan_callback = None
        self.gatt_callback = GattCallback(self)
        self.gatt = None
        self.write_characteristic = None
        self.connected = False

        root = BoxLayout(
            orientation="vertical",
            padding=12,
            spacing=10
        )

        self.title_label = Label(
            text=arabic_text("مرسل البلوتوث"),
            font_name=FONT_NAME,
            font_size=27,
            size_hint_y=0.10
        )
        root.add_widget(self.title_label)

        self.status = Label(
            text=arabic_text("التطبيق جاهز"),
            font_name=FONT_NAME,
            font_size=18,
            size_hint_y=0.12
        )
        root.add_widget(self.status)

        search = Button(
            text=arabic_text("البحث عن أجهزة البلوتوث"),
            font_name=FONT_NAME,
            font_size=20,
            size_hint_y=0.12
        )
        search.bind(on_press=self.search_devices)
        root.add_widget(search)

        self.device_list = BoxLayout(
            orientation="vertical",
            spacing=5,
            size_hint_y=0.30
        )
        root.add_widget(self.device_list)

        self.text_input = TextInput(
            hint_text="اكتب النص هنا",
            multiline=True,
            font_name=FONT_NAME,
            font_size=21,
            size_hint_y=0.25,
            halign="right"
        )
        root.add_widget(self.text_input)

        send = Button(
            text=arabic_text("إرسال النص"),
            font_name=FONT_NAME,
            font_size=20,
            size_hint_y=0.12
        )
        send.bind(on_press=self.send_text)
        root.add_widget(send)

        disconnect = Button(
            text=arabic_text("قطع الاتصال"),
            font_name=FONT_NAME,
            font_size=20,
            size_hint_y=0.09
        )
        disconnect.bind(on_press=self.disconnect)
        root.add_widget(disconnect)

        return root

    def set_status(self, message):
        self.status.text = arabic_text(message)

    def search_devices(self, instance):
        try:
            from android.permissions import request_permissions

            version = autoclass(
                "android.os.Build$VERSION"
            ).SDK_INT

            if version >= 31:
                permissions = [
                    "android.permission.BLUETOOTH_SCAN",
                    "android.permission.BLUETOOTH_CONNECT"
                ]
            else:
                permissions = [
                    "android.permission.ACCESS_FINE_LOCATION"
                ]

            request_permissions(
                permissions,
                self.permission_result
            )

        except Exception as error:
            self.set_status("خطأ الصلاحيات: " + str(error))

    def permission_result(self, permissions, grants):
        if not all(grants):
            self.set_status("يرجى السماح بالصلاحيات")
            return

        Clock.schedule_once(self.start_scan, 0)

    def start_scan(self, dt):
        try:
            BluetoothAdapter = autoclass(
                "android.bluetooth.BluetoothAdapter"
            )

            self.adapter = BluetoothAdapter.getDefaultAdapter()

            if self.adapter is None or not self.adapter.isEnabled():
                self.set_status("يرجى تشغيل البلوتوث")
                return

            self.scanner = self.adapter.getBluetoothLeScanner()

            if self.scanner is None:
                self.set_status("ماسح البلوتوث غير متاح")
                return

            self.devices.clear()
            self.device_list.clear_widgets()

            self.scan_callback = ScanCallback(self)

            self.set_status("جارٍ البحث عن الأجهزة...")

            self.scanner.startScan(self.scan_callback)

            Clock.schedule_once(self.stop_scan, 12)

        except Exception as error:
            self.set_status("خطأ البحث: " + str(error))

    def add_device(self, result):
        try:
            device = result.getDevice()
            address = device.getAddress()

            if address in self.devices:
                return

            name = device.getName() or "جهاز غير معروف"
            self.devices[address] = device

            button = Button(
                text=arabic_text(name + "\n" + address),
                font_name=FONT_NAME,
                size_hint_y=None,
                height=70
            )

            button.bind(
                on_press=lambda instance:
                self.connect_device(address)
            )

            self.device_list.add_widget(button)

        except Exception:
            pass

    def stop_scan(self, dt):
        try:
            if self.scanner and self.scan_callback:
                self.scanner.stopScan(self.scan_callback)

            if self.devices:
                self.set_status("اختر جهاز المستقبل")
            else:
                self.set_status("لم يتم العثور على أجهزة")

        except Exception as error:
            self.set_status(str(error))

    def connect_device(self, address):
        try:
            if self.scanner and self.scan_callback:
                self.scanner.stopScan(self.scan_callback)

            device = self.devices[address]

            activity = autoclass(
                "org.kivy.android.PythonActivity"
            ).mActivity

            self.set_status("جارٍ الاتصال...")

            self.gatt = device.connectGatt(
                activity,
                False,
                self.gatt_callback
            )

        except Exception as error:
            self.set_status("خطأ الاتصال: " + str(error))

    def connection_changed(self, gatt, status, state):
        if status != 0:
            self.set_status("فشل الاتصال: " + str(status))
            return

        if state == 2:
            self.set_status("متصل، جارٍ اكتشاف الخدمات")
            gatt.discoverServices()

        elif state == 0:
            self.connected = False
            self.write_characteristic = None
            self.set_status("انقطع الاتصال")

    def services_discovered(self, gatt, status):
        try:
            if status != 0:
                self.set_status("فشل اكتشاف الخدمات")
                return

            UUID = autoclass("java.util.UUID")

            service = gatt.getService(
                UUID.fromString(SERVICE_UUID)
            )

            if service is None:
                self.set_status("خدمة المستقبل غير موجودة")
                return

            self.write_characteristic = service.getCharacteristic(
                UUID.fromString(WRITE_UUID)
            )

            if self.write_characteristic is None:
                self.set_status("خاصية استقبال النص غير موجودة")
                return

            self.connected = True
            self.set_status("تimport os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.text import LabelBase

from jnius import autoclass, PythonJavaClass, java_method

import arabic_reshaper
from bidi.algorithm import get_display

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
WRITE_UUID = "12345678-1234-5678-1234-56789abcdef1"

FONT_NAME = "Roboto"

font_path = os.path.join(
os.path.dirname(file),
"NotoNaskhArabic-Regular.ttf"
)

if os.path.exists(font_path):
LabelBase.register(name="ArabicFont", fn_regular=font_path)
FONT_NAME = "ArabicFont"

def arabic_text(text):
try:
return get_display(arabic_reshaper.reshape(str(text)))
except Exception:
return str(text)

class ScanListener(PythonJavaClass):
javainterfaces = [
"org/bluetoothproject/bluetoothsender/BluetoothHelper$ScanListener"
]
javacontext = "app"

def __init__(self, app):
    super().__init__()
    self.app = app

@java_method("(Landroid/bluetooth/le/ScanResult;)V")
def onDeviceFound(self, result):
    Clock.schedule_once(
        lambda dt: self.app.add_device(result), 0
    )

@java_method("(I)V")
def onScanError(self, error):
    Clock.schedule_once(
        lambda dt: self.app.set_status(
            "فشل البحث: " + str(error)
        ), 0
    )

class GattListener(PythonJavaClass):
javainterfaces = [
"org/bluetoothproject/bluetoothsender/BluetoothHelper$GattListener"
]
javacontext = "app"

def __init__(self, app):
    super().__init__()
    self.app = app

@java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
def onConnection(self, gatt, status, state):
    Clock.schedule_once(
        lambda dt: self.app.connection_changed(
            gatt, status, state
        ), 0
    )

@java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
def onServices(self, gatt, status):
    Clock.schedule_once(
        lambda dt: self.app.services_discovered(
            gatt, status
        ), 0
    )

@java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V")
def onWrite(self, gatt, characteristic, status):
    Clock.schedule_once(
        lambda dt: self.app.write_finished(status), 0
    )

class SenderApp(App):

def build(self):
    self.devices = {}
    self.scanner = None
    self.scan_callback = None
    self.gatt_callback = None
    self.gatt = None
    self.adapter = None
    self.connected = False
    self.write_characteristic = None

    root = BoxLayout(
        orientation="vertical",
        padding=12,
        spacing=10
    )

    self.status = Label(
        text=arabic_text("التطبيق جاهز"),
        font_name=FONT_NAME,
        font_size=18,
        size_hint_y=0.12
    )
    root.add_widget(self.status)

    title = Label(
        text=arabic_text("مرسل البلوتوث"),
        font_name=FONT_NAME,
        font_size=27,
        size_hint_y=0.10
    )
    root.add_widget(title)

    search = Button(
        text=arabic_text("البحث عن أجهزة البلوتوث"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.12
    )
    search.bind(on_press=self.search_devices)
    root.add_widget(search)

    self.device_list = BoxLayout(
        orientation="vertical",
        spacing=5,
        size_hint_y=0.30
    )
    root.add_widget(self.device_list)

    self.text_input = TextInput(
        hint_text=arabic_text("اكتب النص هنا"),
        multiline=True,
        font_name=FONT_NAME,
        font_size=21,
        size_hint_y=0.25,
        halign="right"
    )
    root.add_widget(self.text_input)

    send = Button(
        text=arabic_text("إرسال النص"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.12
    )
    send.bind(on_press=self.send_text)
    root.add_widget(send)

    disconnect = Button(
        text=arabic_text("قطع الاتصال"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.09
    )
    disconnect.bind(on_press=self.disconnect)
    root.add_widget(disconnect)

    return root

def set_status(self, message):
    self.status.text = arabic_text(message)

def search_devices(self, instance):
    try:
        from android.permissions import request_permissions

        version = autoclass(
            "android.os.Build$VERSION"
        ).SDK_INT

        if version >= 31:
            permissions = [
                "android.permission.BLUETOOTH_SCAN",
                "android.permission.BLUETOOTH_CONNECT"
            ]
        else:
            permissions = [
                "android.permission.ACCESS_FINE_LOCATION"
            ]

        request_permissions(
            permissions,
            self.permission_result
        )

    except Exception as error:
        self.set_status("خطأ الصلاحيات: " + str(error))

def permission_result(self, permissions, grants):
    if not all(grants):
        self.set_status("يرجى السماح بالصلاحيات")
        return

    Clock.schedule_once(self.start_scan, 0)

def start_scan(self, dt):
    try:
        BluetoothAdapter = autoclass(
            "android.bluetooth.BluetoothAdapter"
        )

        self.adapter = BluetoothAdapter.getDefaultAdapter()

        if self.adapter is None:
            self.set_status("البلوتوث غير متاح")
            return

        if not self.adapter.isEnabled():
            self.set_status("يرجى تشغيل البلوتوث")
            return

        self.scanner = self.adapter.getBluetoothLeScanner()

        if self.scanner is None:
            self.set_status("ماسح البلوتوث غير متاح")
            return

        BluetoothHelper = autoclass(
            "org.bluetoothproject.bluetoothsender.BluetoothHelper"
        )

        self.devices.clear()
        self.device_list.clear_widgets()

        self.scan_listener = ScanListener(self)
        self.scan_callback = BluetoothHelper.createScanner(
            self.scan_listener
        )

        self.set_status("جارٍ البحث عن الأجهزة...")
        self.scanner.startScan(self.scan_callback)

        Clock.schedule_once(self.stop_scan, 12)

    except Exception as error:
        self.set_status("خطأ البحث: " + str(error))

def add_device(self, result):
    try:
        device = result.getDevice()
        address = device.getAddress()

        if address in self.devices:
            return

        name = device.getName() or "جهاز غير معروف"
        self.devices[address] = device

        button = Button(
            text=arabic_text(name + "\n" + address),
            font_name=FONT_NAME,
            size_hint_y=None,
            height=70
        )

        button.bind(
            on_press=lambda instance: self.connect_device(address)
        )

        self.device_list.add_widget(button)

    except Exception as error:
        self.set_status("خطأ الجهاز: " + str(error))

def stop_scan(self, dt):
    try:
        if self.scanner and self.scan_callback:
            self.scanner.stopScan(self.scan_callback)

        if self.devices:
            self.set_status("اختر جهاز المستقبل")
        else:
            self.set_status("لم يتم العثور على أجهزة")

    except Exception as error:
        self.set_status("خطأ إيقاف البحث: " + str(error))

def connect_device(self, address):
    try:
        if self.scanner and self.scan_callback:
            self.scanner.stopScan(self.scan_callback)

        device = self.devices[address]

        activity = autoclass(
            "org.kivy.android.PythonActivity"
        ).mActivity

        BluetoothHelper = autoclass(
            "org.bluetoothproject.bluetoothsender.BluetoothHelper"
        )

        self.gatt_listener = GattListener(self)
        self.gatt_callback = BluetoothHelper.createGattCallback(
            self.gatt_listener
        )

        self.set_status("جارٍ الاتصال...")

        self.gatt = device.connectGatt(
            activity,
            False,
            self.gatt_callback
        )

    except Exception as error:
        self.set_status("خطأ الاتصال: " + str(error))

def connection_changed(self, gatt, status, state):
    if status != 0:
        self.set_status("فشل الاتصال: " + str(status))
        return

    if state == 2:
        self.set_status("متصل، جارٍ اكتشاف الخدمات")
        gatt.discoverServices()

    elif state == 0:
        self.connected = False
        self.write_characteristic = None
        self.set_status("انقطع الاتصال")

def services_discovered(self, gatt, status):
    try:
        if status != 0:
            self.set_status("فشل اكتشاف الخدمات")
            return

        UUID = autoclass("java.util.UUID")

        service = gatt.getService(
            UUID.fromString(SERVICE_UUID)
        )

        if service is None:
            self.set_status("خدمة المستقبل غير موجودة")
            return

        self.write_characteristic = service.getCharacteristic(
            UUID.fromString(WRITE_UUID)
        )

        if self.write_characteristic is None:
            self.set_status("خاصية استقبال النص غير موجودة")
            return

        self.connected = True
        self.set_status("تم الاتصال، يمكنك إرسال النص")

    except Exception as error:
        self.set_status("خطأ الخدمات: " + str(error))

def send_text(self, instance):
    if not self.connected or self.write_characteristic is None:
        self.set_status("اتصل بالمستقبل أولاً")
        return

    text = self.text_input.text

    if not text.strip():
        self.set_status("اكتب نصاً أولاً")
        return

    try:
        data = text.encode("utf-8")

        if len(data) > 180:
            self.set_status("النص طويل، الحد الحالي 180 بايت")
            return

        self.write_characteristic.setValue(data)

        result = self.gatt.writeCharacteristic(
            self.write_characteristic
        )

        if result:
            self.set_status("تم طلب إرسال النص")
        else:
            self.set_status("تعذر بدء الإرسال")

    except Exception as error:
        self.set_status("خطأ الإرسال: " + str(error))

def write_finished(self, status):
    if status == 0:
        self.set_status("اكتمل إرسال النص")
    else:
        self.set_status("فشل إرسال النص: " + str(status))

def disconnect(self, instance):
    try:
        if self.gatt:
            self.gatt.disconnect()
            self.gatt.close()

        self.gatt = None
        self.connected = False
        self.write_characteristic = None

        self.set_status("تم قطع الاتصال")

    except Exception as error:
        self.set_status("خطأ قطع الاتصال: " + str(error))

if name == "main":
SenderApp().run()م الاتصال، يمكنك إرسال النص")

        except Exception as error:
            self.set_status("خطأ الخدمات: " + str(error))

    def send_text(self, instance):
        if not self.connected or self.write_characteristic is None:
            self.set_status("اتصل بالمستقبل أولاً")
            return

        text = self.text_input.text

        if not text.strip():
            self.set_status("اكتب نصاً أوimport os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.text import LabelBase

from jnius import autoclass, PythonJavaClass, java_method

import arabic_reshaper
from bidi.algorithm import get_display

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
WRITE_UUID = "12345678-1234-5678-1234-56789abcdef1"

FONT_NAME = "Roboto"

font_path = os.path.join(
os.path.dirname(file),
"NotoNaskhArabic-Regular.ttf"
)

if os.path.exists(font_path):
LabelBase.register(name="ArabicFont", fn_regular=font_path)
FONT_NAME = "ArabicFont"

def arabic_text(text):
try:
return get_display(arabic_reshaper.reshape(str(text)))
except Exception:
return str(text)

class ScanListener(PythonJavaClass):
javainterfaces = [
"org/bluetoothproject/bluetoothsender/BluetoothHelper$ScanListener"
]
javacontext = "app"

def __init__(self, app):
    super().__init__()
    self.app = app

@java_method("(Landroid/bluetooth/le/ScanResult;)V")
def onDeviceFound(self, result):
    Clock.schedule_once(
        lambda dt: self.app.add_device(result), 0
    )

@java_method("(I)V")
def onScanError(self, error):
    Clock.schedule_once(
        lambda dt: self.app.set_status(
            "فشل البحث: " + str(error)
        ), 0
    )

class GattListener(PythonJavaClass):
javainterfaces = [
"org/bluetoothproject/bluetoothsender/BluetoothHelper$GattListener"
]
javacontext = "app"

def __init__(self, app):
    super().__init__()
    self.app = app

@java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
def onConnection(self, gatt, status, state):
    Clock.schedule_once(
        lambda dt: self.app.connection_changed(
            gatt, status, state
        ), 0
    )

@java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
def onServices(self, gatt, status):
    Clock.schedule_once(
        lambda dt: self.app.services_discovered(
            gatt, status
        ), 0
    )

@java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V")
def onWrite(self, gatt, characteristic, status):
    Clock.schedule_once(
        lambda dt: self.app.write_finished(status), 0
    )

class SenderApp(App):

def build(self):
    self.devices = {}
    self.scanner = None
    self.scan_callback = None
    self.gatt_callback = None
    self.gatt = None
    self.adapter = None
    self.connected = False
    self.write_characteristic = None

    root = BoxLayout(
        orientation="vertical",
        padding=12,
        spacing=10
    )

    self.status = Label(
        text=arabic_text("التطبيق جاهز"),
        font_name=FONT_NAME,
        font_size=18,
        size_hint_y=0.12
    )
    root.add_widget(self.status)

    title = Label(
        text=arabic_text("مرسل البلوتوث"),
        font_name=FONT_NAME,
        font_size=27,
        size_hint_y=0.10
    )
    root.add_widget(title)

    search = Button(
        text=arabic_text("البحث عن أجهزة البلوتوث"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.12
    )
    search.bind(on_press=self.search_devices)
    root.add_widget(search)

    self.device_list = BoxLayout(
        orientation="vertical",
        spacing=5,
        size_hint_y=0.30
    )
    root.add_widget(self.device_list)

    self.text_input = TextInput(
        hint_text=arabic_text("اكتب النص هنا"),
        multiline=True,
        font_name=FONT_NAME,
        font_size=21,
        size_hint_y=0.25,
        halign="right"
    )
    root.add_widget(self.text_input)

    send = Button(
        text=arabic_text("إرسال النص"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.12
    )
    send.bind(on_press=self.send_text)
    root.add_widget(send)

    disconnect = Button(
        text=arabic_text("قطع الاتصال"),
        font_name=FONT_NAME,
        font_size=20,
        size_hint_y=0.09
    )
    disconnect.bind(on_press=self.disconnect)
    root.add_widget(disconnect)

    return root

def set_status(self, message):
    self.status.text = arabic_text(message)

def search_devices(self, instance):
    try:
        from android.permissions import request_permissions

        version = autoclass(
            "android.os.Build$VERSION"
        ).SDK_INT

        if version >= 31:
            permissions = [
                "android.permission.BLUETOOTH_SCAN",
                "android.permission.BLUETOOTH_CONNECT"
            ]
        else:
            permissions = [
                "android.permission.ACCESS_FINE_LOCATION"
            ]

        request_permissions(
            permissions,
            self.permission_result
        )

    except Exception as error:
        self.set_status("خطأ الصلاحيات: " + str(error))

def permission_result(self, permissions, grants):
    if not all(grants):
        self.set_status("يرجى السماح بالصلاحيات")
        return

    Clock.schedule_once(self.start_scan, 0)

def start_scan(self, dt):
    try:
        BluetoothAdapter = autoclass(
            "android.bluetooth.BluetoothAdapter"
        )

        self.adapter = BluetoothAdapter.getDefaultAdapter()

        if self.adapter is None:
            self.set_status("البلوتوث غير متاح")
            return

        if not self.adapter.isEnabled():
            self.set_status("يرجى تشغيل البلوتوث")
            return

        self.scanner = self.adapter.getBluetoothLeScanner()

        if self.scanner is None:
            self.set_status("ماسح البلوتوث غير متاح")
            return

        BluetoothHelper = autoclass(
            "org.bluetoothproject.bluetoothsender.BluetoothHelper"
        )

        self.devices.clear()
        self.device_list.clear_widgets()

        self.scan_listener = ScanListener(self)
        self.scan_callback = BluetoothHelper.createScanner(
            self.scan_listener
        )

        self.set_status("جارٍ البحث عن الأجهزة...")
        self.scanner.startScan(self.scan_callback)

        Clock.schedule_once(self.stop_scan, 12)

    except Exception as error:
        self.set_status("خطأ البحث: " + str(error))

def add_device(self, result):
    try:
        device = result.getDevice()
        address = device.getAddress()

        if address in self.devices:
            return

        name = device.getName() or "جهاز غير معروف"
        self.devices[address] = device

        button = Button(
            text=arabic_text(name + "\n" + address),
            font_name=FONT_NAME,
            size_hint_y=None,
            height=70
        )

        button.bind(
            on_press=lambda instance: self.connect_device(address)
        )

        self.device_list.add_widget(button)

    except Exception as error:
        self.set_status("خطأ الجهاز: " + str(error))

def stop_scan(self, dt):
    try:
        if self.scanner and self.scan_callback:
            self.scanner.stopScan(self.scan_callback)

        if self.devices:
            self.set_status("اختر جهاز المستقبل")
        else:
            self.set_status("لم يتم العثور على أجهزة")

    except Exception as error:
        self.set_status("خطأ إيقاف البحث: " + str(error))

def connect_device(self, address):
    try:
        if self.scanner and self.scan_callback:
            self.scanner.stopScan(self.scan_callback)

        device = self.devices[address]

        activity = autoclass(
            "org.kivy.android.PythonActivity"
        ).mActivity

        BluetoothHelper = autoclass(
            "org.bluetoothproject.bluetoothsender.BluetoothHelper"
        )

        self.gatt_listener = GattListener(self)
        self.gatt_callback = BluetoothHelper.createGattCallback(
            self.gatt_listener
        )

        self.set_status("جارٍ الاتصال...")

        self.gatt = device.connectGatt(
            activity,
            False,
            self.gatt_callback
        )

    except Exception as error:
        self.set_status("خطأ الاتصال: " + str(error))

def connection_changed(self, gatt, status, state):
    if status != 0:
        self.set_status("فشل الاتصال: " + str(status))
        return

    if state == 2:
        self.set_status("متصل، جارٍ اكتشاف الخدمات")
        gatt.discoverServices()

    elif state == 0:
        self.connected = False
        self.write_characteristic = None
        self.set_status("انقطع الاتصال")

def services_discovered(self, gatt, status):
    try:
        if status != 0:
            self.set_status("فشل اكتشاف الخدمات")
            return

        UUID = autoclass("java.util.UUID")

        service = gatt.getService(
            UUID.fromString(SERVICE_UUID)
        )

        if service is None:
            self.set_status("خدمة المستقبل غير موجودة")
            return

        self.write_characteristic = service.getCharacteristic(
            UUID.fromString(WRITE_UUID)
        )

        if self.write_characteristic is None:
            self.set_status("خاصية استقبال النص غير موجودة")
            return

        self.connected = True
        self.set_status("تم الاتصال، يمكنك إرسال النص")

    except Exception as error:
        self.set_status("خطأ الخدمات: " + str(error))

def send_text(self, instance):
    if not self.connected or self.write_characteristic is None:
        self.set_status("اتصل بالمستقبل أولاً")
        return

    text = self.text_input.text

    if not text.strip():
        self.set_status("اكتب نصاً أولاً")
        return

    try:
        data = text.encode("utf-8")

        if len(data) > 180:
            self.set_status("النص طويل، الحد الحالي 180 بايت")
            return

        self.write_characteristic.setValue(data)

        result = self.gatt.writeCharacteristic(
            self.write_characteristic
        )

        if result:
            self.set_status("تم طلب إرسال النص")
        else:
            self.set_status("تعذر بدء الإرسال")

    except Exception as error:
        self.set_status("خطأ الإرسال: " + str(error))

def write_finished(self, status):
    if status == 0:
        self.set_status("اكتمل إرسال النص")
    else:
        self.set_status("فشل إرسال النص: " + str(status))

def disconnect(self, instance):
    try:
        if self.gatt:
            self.gatt.disconnect()
            self.gatt.close()

        self.gatt = None
        self.connected = False
        self.write_characteristic = None

        self.set_status("تم قطع الاتصال")

    except Exception as error:
        self.set_status("خطأ قطع الاتصال: " + str(error))

if name == "main":
SenderApp().run()لاً")
            return

        try:
            data = text.encode("utf-8")

            if len(data) > 180:
                self.set_status("النص طويل، الحد الحالي 180 بايت")
                return

            self.write_characteristic.setValue(data)

            result = self.gatt.writeCharacteristic(
                self.write_characteristic
            )

            if result:
                self.set_status("تم طلب إرسال النص")
            else:
                self.set_status("تعذر بدء الإرسال")

        except Exception as error:
            self.set_status("خطأ الإرسال: " + str(error))

    def write_finished(self, status):
        if status == 0:
            self.set_status("اكتمل إرسال النص")
        else:
            self.set_status("فشل إرسال النص: " + str(status))

    def disconnect(self, instance):
        try:
            if self.gatt:
                self.gatt.disconnect()
                self.gatt.close()

            self.gatt = None
            self.connected = False
            self.write_characteristic = None

            self.set_status("تم قطع الاتصال")

        except Exception as error:
            self.set_status(str(error))


if __name__ == "__main__":
    SenderApp().run()
