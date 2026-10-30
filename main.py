from kivy.app import App
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window

class BluetoothApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.2, 0.3, 1)

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        title = Label(
            text="تطبيق البلوتوث\nمرحباً بك",
            font_size=28,
            halign="center"
        )

        button = Button(
            text="تجربة التطبيق",
            font_size=22,
            size_hint=(1, 0.25)
        )

        layout.add_widget(title)
        layout.add_widget(button)

        return layout

BluetoothApp().run()
