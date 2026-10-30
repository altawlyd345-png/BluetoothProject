[app]

title = Bluetooth Sender

package.name = bluetoothsender
package.domain = org.bluetoothproject

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,otf,json,mp3,wav,ogg,mp4,webm,txt

version = 1.0.0

requirements = python3,kivy,pyjnius,plyer,arabic-reshaper,python-bidi

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 29
android.ndk = 27b

android.archs = arm64-v8a

android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,ACCESS_FINE_LOCATION

android.allow_backup = True
android.private_storage = True
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
