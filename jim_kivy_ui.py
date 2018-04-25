from kivy.app import App
from kivy.config import Config
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup

Config.set('graphics', 'resizable', '0')  # 0 being off 1 being on as in true/false
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '500')


class ChatKivyUI(BoxLayout):
    # def __init__(self, client, **kwargs):
        # self.client = client
        # self.client.run()
        # super(BoxLayout, self).__init__(**kwargs)

    def new_message(self):
        print(self.ids.text_input.text)

        self.ids.messageList.item_strings.append(self.ids.text_input.text)

        self.ids.text_input.text = ''


class ConfirmPopup(GridLayout):
    text = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        print(args)


class ChatKivyApp(App):
    client=None
    def build(self):
        # self.client=None

        content = ConfirmPopup(text='Do You Love Kivy?')
        content.bind(on_answer=self._on_answer)
        self.popup = Popup(title="Answer Question",
                           content=content,
                           size_hint=(None, None),
                           size=(200, 200),
                           auto_dismiss=False)
        # self.popup.open()

        return ChatKivyUI()

    def _on_answer(self, instance, answer):
        print("USER ANSWER: ", repr(answer))
        self.popup.dismiss()