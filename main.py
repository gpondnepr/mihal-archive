import requests, webbrowser
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Rectangle, Color
from urllib.parse import quote

SERVER_URL = "http://192.168.1.217:5001"

# # ### ФУНКЦІЯ ПРАВИЛЬНОГО ФОНУ ### #
def add_bg(screen, source_file):
    with screen.canvas.before:
        Color(1, 1, 1, 1)
        screen.bg_rect = Rectangle(source=source_file, pos=screen.pos, size=screen.size)
    
    # Ця функція миттєво оновлює розмір картинки при зміні вікна
    def _update_bg(instance, value):
        instance.bg_rect.pos = instance.pos
        instance.bg_rect.size = instance.size
        
    screen.bind(pos=_update_bg, size=_update_bg)

class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        add_bg(self, 'bg.jpg')
        
        l = BoxLayout(orientation='vertical', padding=50, spacing=20)
        l.add_widget(Label(text="АРХІВ MIHAL", font_size=40, color=(1,0.8,0,1), bold=True))
        
        self.ph = TextInput(hint_text="Телефон", multiline=False, size_hint_y=None, height=50, write_tab=False)
        self.ps = TextInput(hint_text="Пароль", password=True, multiline=False, size_hint_y=None, height=50, write_tab=False)
        
        btn = Button(text="УВІЙТИ", size_hint_y=None, height=60, background_color=(0,0.7,0.3,1), bold=True)
        btn.bind(on_press=self.login)
        
        self.err = Label(text="", color=(1,0,0,1), bold=True)
        
        l.add_widget(self.ph); l.add_widget(self.ps); l.add_widget(btn); l.add_widget(self.err)
        self.add_widget(l)

    def login(self, inst):
        try:
            res = requests.post(f"{SERVER_URL}/api/search", json={"phone":self.ph.text, "password":self.ps.text, "query":""}, timeout=5)
            if res.status_code == 200:
                app = App.get_running_app()
                app.my_phone = self.ph.text
                app.my_pass = self.ps.text
                self.manager.current = 'search'
            else: self.err.text = "Помилка входу"
        except: self.err.text = "Немає зв'язку"

class SearchScreen(Screen):
    last_results = None

    def on_enter(self):
        self.render_ui(results=self.last_results)

    def render_ui(self, results=None, message=None):
        self.clear_widgets()
        add_bg(self, 'bg.jpg') # Фон для екрану пошуку
        
        if results is not None:
            self.last_results = results

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Пошук
        search_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.i = TextInput(hint_text="Введіть адресу...", multiline=False, font_size=20, write_tab=False)
        btn_search = Button(text="ЗНАЙТИ", width=120, size_hint_x=None, background_color=(0,0.5,1,1), bold=True)
        btn_search.bind(on_press=self.perform_search)
        search_box.add_widget(self.i); search_box.add_widget(btn_search)
        main_layout.add_widget(search_box)

        # Результати
        self.gr = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.gr.bind(minimum_height=self.gr.setter('height'))
        
        display_results = results if results is not None else self.last_results

        if display_results:
            for item in display_results:
                f_name = item['folder']
                display = f_name.split('_', 1)[-1] if '_' in f_name else f_name
                btn = Button(text=f"[b]{display}[/b]", markup=True, size_hint_y=None, height=80, 
                             background_color=(0.1, 0.2, 0.3, 0.8)) 
                btn.bind(on_press=lambda inst, f=f_name: self.show_files(f))
                self.gr.add_widget(btn)
        elif message:
            self.gr.add_widget(Label(text=message, color=(1, 0, 0, 1), size_hint_y=None, height=100, font_size=20, bold=True))
        
        sc = ScrollView(); sc.add_widget(self.gr); main_layout.add_widget(sc)

        # Підпис
        footer = Label(text="Создатель: MIHAL", size_hint_y=None, height=30, color=(1, 0.8, 0, 1), font_size=16, bold=True)
        main_layout.add_widget(footer)
        self.add_widget(main_layout)

    def perform_search(self, inst):
        app = App.get_running_app()
        query_text = self.i.text.strip()
        if not query_text: return
        try:
            r = requests.post(f"{SERVER_URL}/api/search", json={"phone":app.my_phone, "password":app.my_pass, "query":query_text}, timeout=10)
            if r.status_code == 200:
                res_data = r.json().get('results', [])
                if not res_data:
                    self.last_results = None
                    self.render_ui(message=f"'{query_text}' не знайдено")
                else: self.render_ui(results=res_data)
        except: self.render_ui(message="Немає зв'язку")

    def show_files(self, folder_name):
        self.clear_widgets()
        add_bg(self, 'bg.jpg') # Фон для екрану файлів
        
        l = BoxLayout(orientation='vertical', padding=15, spacing=10)
        top = BoxLayout(size_hint_y=None, height=50, spacing=10)
        back = Button(text="<-- НАЗАД", size_hint_x=None, width=120, background_color=(1,0,0,1), bold=True)
        back.bind(on_press=lambda x: self.render_ui())
        
        top.add_widget(back)
        clean_title = folder_name.split('_', 1)[-1] if '_' in folder_name else folder_name
        top.add_widget(Label(text=f"Об'єкт: {clean_title}", bold=True, font_size=18))
        l.add_widget(top)

        gr_files = GridLayout(cols=1, spacing=7, size_hint_y=None)
        gr_files.bind(minimum_height=gr_files.setter('height'))
        
        try:
            r = requests.post(f"{SERVER_URL}/api/folder_files", json={"folder": folder_name}, timeout=10)
            files = r.json().get('files', [])
            for f in files:
                fb = Button(text=f, size_hint_y=None, height=70, background_color=(0, 0.6, 0.2, 0.8), halign='left', padding=(15,0))
                fb.bind(size=fb.setter('text_size'))
                fb.bind(on_press=lambda inst, fn=f: webbrowser.open(f"{SERVER_URL}/api/view?path={quote(fn)}"))
                gr_files.add_widget(fb)
        except: pass

        sc = ScrollView(); sc.add_widget(gr_files); l.add_widget(sc)
        l.add_widget(Label(text="Создатель: MIHAL", size_hint_y=None, height=30, color=(1, 0.8, 0, 1), bold=True))
        self.add_widget(l)

class MihalApp(App):
    my_phone = ""; my_pass = ""
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(SearchScreen(name='search'))
        return sm

if __name__ == '__main__':
    MihalApp().run()
