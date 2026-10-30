from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.core.window import Window

class SenderApp(App):
    def build(self):
        Window.clearcolor = (0.08, 0.10, 0.16, 1)

        layout = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )

        title = Label(
            text="لوحة تحكم المرسل",
            font_size=26,
            size_hint=(1, 0.12)
        )
        layout.add_widget(title)

        self.status = Label(
            text="حالة البلوتوث: غير متصل",
            font_size=18,
            size_hint=(1, 0.10)
        )
        layout.add_widget(self.status)

        connect_button = Button(
            text="الاتصال بالمستقبل",
            font_size=20,
            size_hint=(1, 0.12)
        )
        connect_button.bind(on_press=self.connect_bluetooth)
        layout.add_widget(connect_button)

        layout.add_widget(Label(
            text="اكتب النص المراد عرضه:",
            font_size=18,
            size_hint=(1, 0.08)
        ))

        self.message = TextInput(
            hint_text="اكتب النص هنا...",
            multiline=True,
            font_size=22,
            size_hint=(1, 0.25)
        )
        layout.add_widget(self.message)

        self.effect = Spinner(
            text="تأثير النص",
            values=(
                "عرض فوري",
                "تمرير أفقي",
                "تمرير عمودي",
                "ظهور تدريجي"
            ),
            size_hint=(1, 0.12)
        )
        layout.add_widget(self.effect)

        send_button = Button(
            text="إرسال النص",
            font_size=22,
            size_hint=(1, 0.14)
        )
        send_button.bind(on_press=self.send_message)
        layout.add_widget(send_button)

        return layout

    def connect_bluetooth(self, instance):
        self.status.text = "سيتم تجهيز الاتصال بالبلوتوث"

    def send_message(self, instance):
        if self.message.text.strip():
            self.status.text = "النص جاهز للإرسال بعد تجهيز البلوتوث"
        else:
            self.status.text = "اكتب نصاً أولاً"

SenderApp().run()
