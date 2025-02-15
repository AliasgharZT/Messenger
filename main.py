


from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.dialog import MDDialog
from AZ_MDBoxLayout import AZMDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivy.properties import ObjectProperty
from AZ_FileManager import MDFileManager
from kivymd.uix.list import IconRightWidgetWithoutTouch, OneLineRightIconListItem
from kivymd.toast import toast
from kivymd.uix.textfield import MDTextField 
import serial
import time
import threading
from kivy.clock import Clock
from collections import defaultdict

Builder.load_file('style.kv')

class Style(MDAnchorLayout):

    user_info = {'name': None, 'family': None, 'number': None}
    user_photo = ObjectProperty()
    ml = ObjectProperty()
    address_photo = None
    t = 0
    name_chat = []
    mn = ObjectProperty()
    state_msg=True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.f = MDFileManager(
            exit_manager=self.close_add_user_photo,
            icon_selection_button='content-save-check-outline',
            select_path=self.get_user_photo,
            size_hint=(0.6, 0.7),
            preview=True,
        )
        self.ser = serial.Serial(
            port='COM7',  # شماره پورت COM را بررسی کنید
            baudrate=9600,  # نرخ انتقال داده
            timeout=1.4,  # زمان انتظار برای دریافت داده
            write_timeout=2,  # زمان انتظار برای ارسال داده
            # write_buffer_size=4096,  # اندازه بافر ارسال
            # read_buffer_size=4096  # اندازه بافر دریافت
        )
#////////////////////////////////
        if self.state_msg:
            receive_thread = threading.Thread(target=self.receive)
            receive_thread.daemon = True  # Thread will close automatically after the program ends
            receive_thread.start()
        self.received_chunks = defaultdict(str)  # ذخیره بخش‌های دریافت شده
        self.current_message_id = None  # شناسه پیام فعلی

    get_user_info = '''
AZMDBoxLayout:
    orientation: 'vertical'
    spacing: 7

    name: name
    family: family
    number: number

    MDTextField:
        id: name
        helper_text: 'Enter Name'
    MDTextField:
        id: family
        helper_text: 'Enter Family'
    MDTextField:
        id: number
        helper_text: 'Enter Number'
        input_filter: 'int'
    MDAnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        MDFillRoundFlatButton:
            text: 'Rejister'
            on_press:
                root.get_user_info()
'''

    get_user_chat = '''
AZMDBoxLayout:
    orientation: 'vertical'
    spacing: 7

    namechat: namechat

    MDTextField:
        id: namechat
        helper_text: 'Enter Name'
    MDAnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        MDFillRoundFlatButton:
            text: 'Rejister'
            on_press:
                root.get_chat_info()
'''

    def about(self): 
        self.about_d = MDDialog(title='About :\n',
                              text='This program was created by Ali Asghar Zahdyan\n'+
                              '                                            < < < A . Z > > >')
        self.about_d.open()

    def add_user(self):
        self.add_user_d = MDDialog(title='Information :\n\n\n\n\n\n\n\n\n\n', type='custom',
                                 content_cls=Builder.load_string(self.get_user_info),
                                 buttons=[MDFlatButton(text='Back', on_press=self.close_add_user)])
        self.add_user_d.size_hint = 0.4, 0.63
        self.add_user_d.open()   

    def close_add_user(self, obj):
        self.add_user_d.dismiss()
        self.user_info = AZMDBoxLayout.user_info

    def add_user_photo(self):
        self.f.selection_button.on_press = self.set_user_photo
        self.f.show_disks()

    def close_add_user_photo(self, *args):
        self.f.close() 

    def get_user_photo(self, path):
        self.address_photo = path

    def set_user_photo(self, *args):
        if self.address_photo is None:
            pass
        else:
            self.user_photo.source = self.address_photo
            self.address_photo = None 
            self.close_add_user_photo()

    def new_chat(self):
        self.new_chat_d = MDDialog(title='InformationChat :\n\n\n\n\n\n\n\n\n\n', type='custom',
                                 content_cls=Builder.load_string(self.get_user_chat),
                                 buttons=[MDFlatButton(text='Back', on_press=self.close_new_chat_d)])
        self.new_chat_d.size_hint = 0.4, 0.63
        self.new_chat_d.open() 

    def close_new_chat_d(self, obj):
        self.new_chat_d.dismiss()
        if self.user_info['name'] is None:
            toast('<< Fill out UserInformation >>')
        else:
            name = AZMDBoxLayout.name_chat
            name = name['name']
            if (name == '') or (name in self.name_chat):
                pass
            else:
                self.t += 1
                if self.t == 1:
                    self.ml.clear_widgets()
                one = OneLineRightIconListItem(
                    IconRightWidgetWithoutTouch(icon='chat'),
                    text=name + ' & ' + self.user_info['name'][0] + self.user_info['family'][0],
                    on_press=self.press_new_chat,
                )
                self.ml.add_widget(one) 
                self.name_chat.append(name)

    def press_new_chat(self, instance):
        self.mn.current = 'fake'
        self.ids.lbl_chat.text = instance.text 
        
# -----------------------------------------
    def send(self, msg):
        try:
            chunk_size = 1024  # اندازه بسته 1 کیلوبایت
            chunks = [msg[i:i + chunk_size] for i in range(0, len(msg), chunk_size)]

            self.ser.write(b'START\n')
            self.ser.flush()

            for i, chunk in enumerate(chunks):
                try:
                    self.ser.write(f"{i}:{chunk}\n".encode())
                    self.ser.flush()
                    print(f"Chunk {i} sent: {chunk}")
                    time.sleep(0.2)  # افزایش تأخیر به 0.2 ثانیه
                except serial.SerialTimeoutException:
                    print(f"Timeout while sending chunk {i}. Retrying...")
                    time.sleep(1)  # تأخیر بیشتر قبل از تلاش مجدد
                    continue  # تلاش مجدد برای ارسال

            self.ser.write(b'END\n')
            self.ser.flush()
            print("Message sent successfully.")
        except Exception as e:
            print(f"Error sending data: {e}")
# --------------------------------------------------
 
    def receive(self):
        try:
            print("Listening for data...")
            while True:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if response == "START":
                        print("Start of message detected.")
                        self.current_message_id = time.time()  # استفاده از زمان به عنوان شناسه پیام
                        self.received_chunks[self.current_message_id] = ""  # شروع یک پیام جدید
                    elif response == "END":
                        print("End of message detected.")
                        if self.current_message_id:
                            full_message = self.received_chunks[self.current_message_id]
                            print(f"Full message received: {full_message}")
                            Clock.schedule_once(lambda dt: self.update_ui(full_message))
                            del self.received_chunks[self.current_message_id]  # پاک کردن پیام پردازش شده
                            self.current_message_id = None
                    else:
                        if self.current_message_id:
                            # پردازش بخش‌های پیام
                            chunk_id, chunk_data = response.split(":", 1)
                            self.received_chunks[self.current_message_id] += chunk_data
                            print(f"Chunk {chunk_id} received: {chunk_data}")
        except Exception as e:
            print(f"Error receiving data: {e}")
# ------------------------------------------------------
    def update_ui(self, msg):
        self.ids.ml2.add_widget(MDTextField(text=msg, multiline=True, readonly=True))
# ---------------------------------------------------------
    def messages(self):
        # Check if the text field is not empty, then send the message
        if self.ids.txt.text != '':
            msg = self.ids.txt.text
            # Add message to message list (to be displayed on UI)
            self.ids.ml2.add_widget(MDTextField(text=msg, multiline=True, readonly=True))
            # Change state_msg to False to avoid sending duplicate messages
            self.state_msg = False
            # Create a thread to send the message
            send_thread = threading.Thread(target=self.send, args=(msg,))
            send_thread.daemon = True  # Thread will close when the main program ends
            send_thread.start()
            # Change state_msg back to True after sending
            self.state_msg = True
            # Clear the text field
            self.ids.txt.text = ''


class MainApp(MDApp):
      
    def build(self):
        self.title = 'AZenger'
        self.icon = 'icon-app.jpg'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'BlueGray'
        self.theme_cls.primary_hue = '900'
        return Style()

MainApp().run()



