import csv
import os
import shutil
import datetime
import jdatetime

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty

import arabic_reshaper
from bidi.algorithm import get_display

# ماژول ارسال اعلان
from plyer import notification

Window.clearcolor = (0.95, 0.95, 0.95, 1)

ACTIVE_CSV = "active_tasks.csv"
COMPLETED_CSV = "completed_tasks.csv"
SETTINGS_FILE = "settings.txt"  # ذخیره تنظیمات روشن/خاموش
ALARM_STATE_FILE = "alarm_state.txt"  # ذخیره اینکه آیا امروز هشدار داده شده یا نه
FONT_PATH = "font.ttf"

PRIORITY_COLORS = {'High': '#FF0000', 'Normal': '#555555', 'Low': '#008800'}
PRIORITY_WEIGHT = {'High': 1, 'Normal': 2, 'Low': 3}

LANG = {
    'active_tab': {'en': 'Active Tasks', 'fa': 'کارهای فعال'},
    'completed_tab': {'en': 'Completed', 'fa': 'انجام شده'},
    'task_hint': {'en': 'Task Name...', 'fa': 'نام کار...'},
    'note_hint': {'en': 'Note (Optional)...', 'fa': 'یادداشت (اختیاری)...'},
    'start_hint': {'en': 'Start (10:00)', 'fa': 'شروع (۱۰:۰۰)'},
    'end_hint': {'en': 'End (12:00)', 'fa': 'پایان (۱۲:۰۰)'},
    'add_btn': {'en': 'Add Task', 'fa': 'افزودن کار'},
    'update_btn': {'en': 'Update Task', 'fa': 'بروزرسانی'},
    'lang_btn': {'en': 'فارسی', 'fa': 'English'},
    'done_btn': {'en': 'Done', 'fa': 'انجام شد'},
    'edit_btn': {'en': 'Edit', 'fa': 'ویرایش'},
    'restore_btn': {'en': 'Restore', 'fa': 'بازیابی'},
    'del_btn': {'en': 'Delete', 'fa': 'حذف'},
    'all_day': {'en': 'All Day', 'fa': 'کل روز'},
    'search_hint': {'en': 'Search Name or Date...', 'fa': 'جستجوی نام یا تاریخ...'},
    'apply_btn': {'en': 'Search / Sort', 'fa': 'اعمال جستجو'},
    'clear_btn': {'en': 'Clear', 'fa': 'نمایش همه'},
    'export_btn': {'en': 'Export', 'fa': 'خروجی'},
    'import_btn': {'en': 'Import', 'fa': 'ورودی'},
    
    'notify_on': {'en': 'Alarm ON', 'fa': 'هشدار روشن'},
    'notify_off': {'en': 'Alarm OFF', 'fa': 'هشدار خاموش'},
    
    'priority_vals': {'en': ['High', 'Normal', 'Low'], 'fa': ['مهم', 'عادی', 'کم اهمیت']},
    'week_days': {'en': ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                  'fa': ['شنبه', 'یکشنبه', 'دوشنبه', 'سه شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']},
    
    'sort_vals': {
        'en': ['Sort: Time -> Priority', 'Sort: Priority -> Time'],
        'fa': ['مرتب سازی: زمان -> اولویت', 'مرتب سازی: اولویت -> زمان']
    }
}

def fix_persian(text):
    if not text: return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)

KV_CODE = '''
<SpinnerOption>:
    font_name: '{font}'
    color: (1, 1, 1, 1)

<TaskManager>:
    orientation: 'vertical'
    padding: 15
    spacing: 15

    BoxLayout:
        size_hint_y: None
        height: 40
        spacing: 5
        Button:
            id: btn_active
            font_name: '{font}'
            background_color: (0.2, 0.6, 1, 1)
            on_press: root.load_tasks('active')
        Button:
            id: btn_completed
            font_name: '{font}'
            background_color: (0.2, 0.8, 0.2, 1)
            on_press: root.load_tasks('completed')
        Button:
            id: btn_notify
            font_name: '{font}'
            size_hint_x: 0.5
            on_press: root.toggle_notify()
        Button:
            id: btn_import
            font_name: '{font}'
            size_hint_x: 0.4
            background_color: (0.5, 0.2, 0.8, 1)
            on_press: root.show_import_popup()
        Button:
            id: btn_export
            font_name: '{font}'
            size_hint_x: 0.4
            background_color: (0.8, 0.2, 0.5, 1)
            on_press: root.export_data()
        Button:
            id: btn_lang
            font_name: '{font}'
            size_hint_x: 0.3
            background_color: (1, 0.6, 0.1, 1)
            on_press: root.toggle_language()

    BoxLayout:
        size_hint_y: None
        height: 40
        spacing: 5
        RelativeLayout:
            size_hint_x: 1.5
            TextInput:
                id: search_input
                font_name: '{font}'
                foreground_color: (0,0,0,0) 
                background_color: (1,1,1,1) 
                cursor_color: (0,0,0,1)
                multiline: False
                halign: 'right' if root.lang == 'fa' else 'left'
            Label:
                text: root.fix_text(search_input.text) if search_input.text else root.fix_text(root.get_hint('search_hint', root.lang))
                font_name: '{font}'
                color: (0,0,0,1) if search_input.text else (0.5,0.5,0.5,1)
                text_size: self.size
                halign: 'right' if root.lang == 'fa' else 'left'
                valign: 'center'
                padding_x: 10

        Spinner:
            id: sort_spinner
            font_name: '{font}'
            size_hint_x: 1.5
            background_color: (0.4, 0.4, 0.4, 1)
        Button:
            id: btn_apply
            font_name: '{font}'
            size_hint_x: 1
            background_color: (0.1, 0.5, 0.5, 1)
            on_press: root.refresh_ui()
        Button:
            id: btn_clear
            font_name: '{font}'
            size_hint_x: 0.5
            background_color: (0.6, 0.6, 0.6, 1)
            on_press: root.clear_search()

    BoxLayout:
        id: input_section
        orientation: 'vertical'
        size_hint_y: None
        height: 140
        spacing: 10
        
        BoxLayout:
            size_hint_y: None
            height: 40
            spacing: 5
            RelativeLayout:
                size_hint_x: 2
                TextInput:
                    id: task_input
                    font_name: '{font}'
                    foreground_color: (0,0,0,0)
                    background_color: (1,1,1,1)
                    cursor_color: (0,0,0,1)
                    multiline: False
                    halign: 'right' if root.lang == 'fa' else 'left'
                Label:
                    text: root.fix_text(task_input.text) if task_input.text else root.fix_text(root.get_hint('task_hint', root.lang))
                    font_name: '{font}'
                    color: (0,0,0,1) if task_input.text else (0.5,0.5,0.5,1)
                    text_size: self.size
                    halign: 'right' if root.lang == 'fa' else 'left'
                    valign: 'center'
                    padding_x: 10

            TextInput:
                id: shamsi_input
                multiline: False
                size_hint_x: 1
            TextInput:
                id: miladi_input
                multiline: False
                size_hint_x: 1
        
        RelativeLayout:
            size_hint_y: None
            height: 40
            TextInput:
                id: note_input
                font_name: '{font}'
                foreground_color: (0,0,0,0)
                background_color: (1,1,1,1)
                cursor_color: (0,0,0,1)
                multiline: False
                halign: 'right' if root.lang == 'fa' else 'left'
            Label:
                text: root.fix_text(note_input.text) if note_input.text else root.fix_text(root.get_hint('note_hint', root.lang))
                font_name: '{font}'
                color: (0,0,0,1) if note_input.text else (0.5,0.5,0.5,1)
                text_size: self.size
                halign: 'right' if root.lang == 'fa' else 'left'
                valign: 'center'
                padding_x: 10
            
        BoxLayout:
            size_hint_y: None
            height: 40
            spacing: 5
            Spinner:
                id: day_spinner
                font_name: '{font}'
                size_hint_x: 1
                background_color: (0.6, 0.6, 0.6, 1)
            TextInput:
                id: start_input
                font_name: '{font}'
                size_hint_x: 1
            TextInput:
                id: end_input
                font_name: '{font}'
                size_hint_x: 1
            Spinner:
                id: priority_input
                font_name: '{font}'
                size_hint_x: 1
                background_color: (0.5, 0.5, 0.5, 1)
            Button:
                id: btn_add
                font_name: '{font}'
                size_hint_x: 1
                background_color: (0.2, 0.6, 1, 1)
                on_press: root.add_task()

    ScrollView:
        BoxLayout:
            id: task_list
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: 10
'''.replace('{font}', FONT_PATH)

Builder.load_string(KV_CODE)

class TaskManager(BoxLayout):
    lang = StringProperty('fa') 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_view = 'active'
        self.all_tasks = []
        self.editing_task = None 
        
        self.ignore_updates = False
        
        # وضعیت تنظیمات
        self.notify_enabled = True
        self.last_notified_date = ""
        self.load_settings()
        
        self.update_ui_language()
        self.set_today_dates()
        
        self.ids.shamsi_input.bind(text=self.on_date_changed_shamsi)
        self.ids.miladi_input.bind(text=self.on_date_changed_miladi)
        self.ids.day_spinner.bind(text=self.on_day_spinner_changed)
        
        Clock.schedule_once(lambda dt: self.load_tasks('active'))
        
        # --- سیستم پس‌زمینه (Background Loop) ---
        # هر ۶۰ ثانیه یک بار در پس‌زمینه (مادامی که برنامه مینیمایز است) چک می‌کند
        Clock.schedule_interval(self.background_alarm_check, 60)
        
        # یک بار هم همون اول که برنامه باز میشه بعد از ۳ ثانیه چک کنه
        Clock.schedule_once(self.background_alarm_check, 3)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    self.notify_enabled = (f.read().strip() == '1')
            except: pass
            
        if os.path.exists(ALARM_STATE_FILE):
            try:
                with open(ALARM_STATE_FILE, 'r') as f:
                    self.last_notified_date = f.read().strip()
            except: pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                f.write('1' if self.notify_enabled else '0')
        except: pass

    def save_alarm_state(self, date_str):
        self.last_notified_date = date_str
        try:
            with open(ALARM_STATE_FILE, 'w') as f:
                f.write(date_str)
        except: pass

    def toggle_notify(self):
        self.notify_enabled = not self.notify_enabled
        self.save_settings()
        self.update_ui_language()

    # --- پردازش اصلی هشدار پس‌زمینه ---
    def background_alarm_check(self, dt):
        if not self.notify_enabled:
            return
            
        today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
        
        # اگر امروز قبلاً هشدار داده بودیم، دیگر تکرار نکن
        if self.last_notified_date == today_shamsi:
            return

        today_tasks_count = 0
        if os.path.exists(ACTIVE_CSV):
            with open(ACTIVE_CSV, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and len(row) >= 7 and row[1] == today_shamsi:
                        today_tasks_count += 1
        
        if today_tasks_count > 0:
            title = "یادآوری کارهای امروز" if self.lang == 'fa' else "Today's Tasks"
            msg = f"شما {today_tasks_count} کار انجام نشده برای امروز دارید!" if self.lang == 'fa' else f"You have {today_tasks_count} active tasks for today!"
            
            # ذخیره میکنیم که امروز هشدار دادیم تا اسپم نشود
            self.save_alarm_state(today_shamsi)
            
            # نمایش داخل برنامه
            self.show_message_popup(fix_persian(title), fix_persian(msg))
            
            # اعلان بومی سیستم عامل
            try:
                notification.notify(
                    title=title, 
                    message=msg, 
                    app_name="Task Manager", 
                    timeout=10
                )
            except Exception as e:
                print("Native Notification Failed:", e)


    def on_date_changed_shamsi(self, instance, value):
        if self.ignore_updates: return
        try:
            y, m, d = map(int, value.replace('-', '/').split('/'))
            shamsi_obj = jdatetime.date(y, m, d)
            day_index = shamsi_obj.weekday()
            miladi_str = shamsi_obj.togregorian().strftime("%Y-%m-%d")
            
            self.ignore_updates = True
            self.ids.miladi_input.text = miladi_str
            self.ids.day_spinner.text = fix_persian(LANG['week_days'][self.lang][day_index])
            self.ignore_updates = False
        except Exception:
            self.ignore_updates = False

    def on_date_changed_miladi(self, instance, value):
        if self.ignore_updates: return
        try:
            y, m, d = map(int, value.replace('/', '-').split('-'))
            miladi_obj = datetime.date(y, m, d)
            shamsi_obj = jdatetime.date.fromgregorian(date=miladi_obj)
            day_index = shamsi_obj.weekday()
            
            self.ignore_updates = True
            self.ids.shamsi_input.text = shamsi_obj.strftime("%Y/%m/%d")
            self.ids.day_spinner.text = fix_persian(LANG['week_days'][self.lang][day_index])
            self.ignore_updates = False
        except Exception:
            self.ignore_updates = False

    def on_day_spinner_changed(self, instance, value):
        if self.ignore_updates: return
        try:
            displayed_days = [fix_persian(d) for d in LANG['week_days'][self.lang]]
            if value not in displayed_days: return
            target_index = displayed_days.index(value)
            
            current_shamsi_text = self.ids.shamsi_input.text
            y, m, d = map(int, current_shamsi_text.replace('-', '/').split('/'))
            current_shamsi_obj = jdatetime.date(y, m, d)
            current_index = current_shamsi_obj.weekday()
            
            diff = target_index - current_index
            if diff == 0: return
            
            new_shamsi_obj = current_shamsi_obj + jdatetime.timedelta(days=diff)
            new_miladi_obj = new_shamsi_obj.togregorian()
            
            self.ignore_updates = True
            self.ids.shamsi_input.text = new_shamsi_obj.strftime("%Y/%m/%d")
            self.ids.miladi_input.text = new_miladi_obj.strftime("%Y-%m-%d")
            self.ignore_updates = False
        except Exception:
            self.ignore_updates = False

    def fix_text(self, text):
        return fix_persian(text)

    def get_hint(self, key, current_lang):
        return LANG[key][current_lang]

    def get_raw_key(self, dict_category, displayed_text):
        for l in ['en', 'fa']:
            for i, val in enumerate(LANG[dict_category][l]):
                if fix_persian(val) == displayed_text or val == displayed_text:
                    return LANG[dict_category]['en'][i]
        return displayed_text

    def toggle_language(self):
        self.lang = 'en' if self.lang == 'fa' else 'fa'
        self.update_ui_language()
        self.refresh_ui()

    def update_ui_language(self):
        l = self.lang
        self.ids.btn_active.text = fix_persian(LANG['active_tab'][l])
        self.ids.btn_completed.text = fix_persian(LANG['completed_tab'][l])
        self.ids.btn_lang.text = fix_persian(LANG['lang_btn'][l])
        self.ids.btn_apply.text = fix_persian(LANG['apply_btn'][l])
        self.ids.btn_clear.text = fix_persian(LANG['clear_btn'][l])
        self.ids.btn_export.text = fix_persian(LANG['export_btn'][l])
        self.ids.btn_import.text = fix_persian(LANG['import_btn'][l])
        
        if self.notify_enabled:
            self.ids.btn_notify.text = fix_persian(LANG['notify_on'][l])
            self.ids.btn_notify.background_color = (0.2, 0.8, 0.2, 1) 
        else:
            self.ids.btn_notify.text = fix_persian(LANG['notify_off'][l])
            self.ids.btn_notify.background_color = (0.8, 0.3, 0.3, 1) 
        
        self.ids.start_input.hint_text = fix_persian(LANG['start_hint'][l])
        self.ids.end_input.hint_text = fix_persian(LANG['end_hint'][l])
        
        btn_key = 'update_btn' if self.editing_task else 'add_btn'
        self.ids.btn_add.text = fix_persian(LANG[btn_key][l])

        self.ids.sort_spinner.values = [fix_persian(v) for v in LANG['sort_vals'][l]]
        self.ids.sort_spinner.text = fix_persian(LANG['sort_vals'][l][0])

        self.ids.priority_input.values = [fix_persian(v) for v in LANG['priority_vals'][l]]
        self.ids.priority_input.text = fix_persian(LANG['priority_vals'][l][1])
        
        self.ids.day_spinner.values = [fix_persian(d) for d in LANG['week_days'][l]]
        
        self.ignore_updates = True
        try:
            current_shamsi_text = self.ids.shamsi_input.text
            y, m, d = map(int, current_shamsi_text.replace('-', '/').split('/'))
            day_index = jdatetime.date(y, m, d).weekday()
            self.ids.day_spinner.text = fix_persian(LANG['week_days'][l][day_index])
        except: pass
        self.ignore_updates = False

    def clear_search(self):
        self.ids.search_input.text = ""
        self.refresh_ui()

    def set_today_dates(self):
        today_miladi = datetime.date.today().strftime("%Y-%m-%d")
        today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
        self.default_shamsi = today_shamsi
        self.default_miladi = today_miladi
        
        self.ignore_updates = True
        self.ids.shamsi_input.text = today_shamsi
        self.ids.miladi_input.text = today_miladi
        day_index = jdatetime.date.today().weekday()
        self.ids.day_spinner.text = fix_persian(LANG['week_days'][self.lang][day_index])
        self.ignore_updates = False

    def load_tasks(self, view_type):
        self.current_view = view_type
        self.all_tasks = []
        self.editing_task = None
        self.ids.btn_add.text = fix_persian(LANG['add_btn'][self.lang])
        self.ids.task_input.text = ""
        self.ids.note_input.text = ""

        if view_type == 'completed':
            self.ids.input_section.opacity = 0
            self.ids.input_section.disabled = True
            file_to_read = COMPLETED_CSV
        else:
            self.ids.input_section.opacity = 1
            self.ids.input_section.disabled = False
            file_to_read = ACTIVE_CSV
            self.set_today_dates()

        if os.path.exists(file_to_read):
            with open(file_to_read, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and len(row) >= 7: 
                        end_t = row[5] if len(row) > 5 else ""
                        day_n = row[6] if len(row) > 6 else ""
                        note = row[7] if len(row) > 7 else ""
                        self.all_tasks.append([row[0], row[1], row[2], row[3], row[4], end_t, day_n, note])
        
        self.refresh_ui()

    def save_current_file(self):
        file_to_write = ACTIVE_CSV if self.current_view == 'active' else COMPLETED_CSV
        with open(file_to_write, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for task in self.all_tasks:
                writer.writerow(task)

    def refresh_ui(self):
        self.ids.task_list.clear_widgets()
        search_query = self.ids.search_input.text.strip()
        filtered_tasks = []

        for task in self.all_tasks:
            if search_query == "" or search_query in task[0] or search_query in task[1] or search_query in task[2]:
                filtered_tasks.append(task)

        current_sort = self.ids.sort_spinner.text.replace(u'\u202b', '').replace(u'\u202c', '')
        l = self.lang
        
        def sort_logic(task):
            date_str = task[2]
            time_str = task[4] if task[4] else "00:00"
            raw_priority = task[3] 
            p_weight = PRIORITY_WEIGHT.get(raw_priority, 2)

            if current_sort == LANG['sort_vals'][l][0]:
                return (date_str, time_str, p_weight)
            else:
                return (p_weight, date_str, time_str)

        filtered_tasks.sort(key=sort_logic)
        for task in filtered_tasks:
            self.create_task_widget(*task)

    def export_data(self):
        export_dir = "Exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        current_file = ACTIVE_CSV if self.current_view == 'active' else COMPLETED_CSV
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = os.path.join(export_dir, f"{self.current_view}_backup_{timestamp}.csv")

        if os.path.exists(current_file):
            shutil.copy(current_file, export_filename)
            msg = f"پشتیبان‌گیری با موفقیت انجام شد:\n{export_filename}" if self.lang == 'fa' else f"Exported Successfully:\n{export_filename}"
            self.show_message_popup(fix_persian("موفقیت" if self.lang == 'fa' else "Success"), fix_persian(msg))
        else:
            msg = "هیچ داده‌ای برای خروجی گرفتن وجود ندارد!" if self.lang == 'fa' else "No data to export!"
            self.show_message_popup(fix_persian("خطا" if self.lang == 'fa' else "Error"), fix_persian(msg))

    def show_import_popup(self):
        from kivy.uix.filechooser import FileChooserListView
        
        content = BoxLayout(orientation='vertical', spacing=10)
        filechooser = FileChooserListView(filters=['*.csv'], path='.')
        content.add_widget(filechooser)
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        cancel_btn = Button(text=fix_persian('لغو' if self.lang == 'fa' else 'Cancel'), font_name=FONT_PATH)
        import_btn = Button(text=fix_persian('تایید و ورود' if self.lang == 'fa' else 'Import'), font_name=FONT_PATH, background_color=(0.2, 0.8, 0.2, 1))
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(import_btn)
        content.add_widget(btn_layout)
        
        popup_title = fix_persian('فایل CSV را انتخاب کنید' if self.lang == 'fa' else 'Select CSV')
        popup = Popup(title=popup_title, title_font=FONT_PATH, content=content, size_hint=(0.9, 0.9))
        
        cancel_btn.bind(on_release=popup.dismiss)
        import_btn.bind(on_release=lambda btn: self.process_import(filechooser.selection, popup))
        popup.open()

    def process_import(self, selection, popup):
        if not selection: return
        file_path = selection[0]
        try:
            unique_tasks = {tuple(task) for task in self.all_tasks}
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and len(row) >= 7:
                        end_t = row[5] if len(row) > 5 else ""
                        day_n = row[6] if len(row) > 6 else ""
                        note = row[7] if len(row) > 7 else ""
                        unique_tasks.add(tuple([row[0], row[1], row[2], row[3], row[4], end_t, day_n, note]))
            
            self.all_tasks = [list(t) for t in unique_tasks]
            self.save_current_file()
            self.refresh_ui()
            popup.dismiss()
            msg = "داده‌ها با موفقیت وارد شدند!" if self.lang == 'fa' else "Data Imported Successfully!"
            self.show_message_popup(fix_persian("موفقیت" if self.lang == 'fa' else "Success"), fix_persian(msg))
        except Exception as e:
            msg = f"خطا در خواندن فایل:\n{str(e)}" if self.lang == 'fa' else f"Error reading file:\n{str(e)}"
            self.show_message_popup(fix_persian("خطا" if self.lang == 'fa' else "Error"), fix_persian(msg))

    def show_message_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        msg_label = Label(text=message, font_name=FONT_PATH, halign='center', text_size=(Window.width * 0.7, None))
        close_btn = Button(text=fix_persian('بستن' if self.lang == 'fa' else 'Close'), font_name=FONT_PATH, size_hint_y=None, height=40)
        content.add_widget(msg_label)
        content.add_widget(close_btn)
        popup = Popup(title=title, title_font=FONT_PATH, content=content, size_hint=(0.8, 0.4))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def action_done(self, task_data):
        self.all_tasks.remove(task_data)
        self.save_current_file()
        with open(COMPLETED_CSV, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(task_data)
        self.refresh_ui()

    def action_delete(self, task_data):
        self.all_tasks.remove(task_data)
        self.save_current_file()
        self.refresh_ui()

    def action_edit(self, task_data):
        self.ignore_updates = True
        self.ids.task_input.text = task_data[0]
        self.ids.shamsi_input.text = task_data[1]
        self.ids.miladi_input.text = task_data[2]
        
        raw_priority = task_data[3]
        raw_day = task_data[6]
        
        p_idx = LANG['priority_vals']['en'].index(raw_priority) if raw_priority in LANG['priority_vals']['en'] else 1
        d_idx = LANG['week_days']['en'].index(raw_day) if raw_day in LANG['week_days']['en'] else 0
        
        self.ids.priority_input.text = fix_persian(LANG['priority_vals'][self.lang][p_idx])
        self.ids.day_spinner.text = fix_persian(LANG['week_days'][self.lang][d_idx])

        self.ids.start_input.text = task_data[4] if task_data[4] not in [LANG['all_day']['fa'], LANG['all_day']['en']] else ""
        self.ids.end_input.text = task_data[5]
        self.ids.note_input.text = task_data[7]

        self.editing_task = task_data
        self.ids.btn_add.text = fix_persian(LANG['update_btn'][self.lang])
        self.ignore_updates = False

    def action_restore(self, task_data):
        self.all_tasks.remove(task_data)
        self.save_current_file() 
        with open(ACTIVE_CSV, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(task_data)
        self.refresh_ui()

    def create_task_widget(self, task, shamsi, miladi, raw_priority, start_t, end_t, raw_day, note):
        task_item = BoxLayout(size_hint_y=None, height=70, spacing=10)
        task_data = [task, shamsi, miladi, raw_priority, start_t, end_t, raw_day, note]

        l = self.lang
        p_idx = LANG['priority_vals']['en'].index(raw_priority) if raw_priority in LANG['priority_vals']['en'] else 1
        d_idx = LANG['week_days']['en'].index(raw_day) if raw_day in LANG['week_days']['en'] else 0
        
        local_priority = LANG['priority_vals'][l][p_idx]
        local_day = LANG['week_days'][l][d_idx]
        p_color = PRIORITY_COLORS.get(raw_priority, '#555555')

        time_display = f"{start_t} - {end_t}" if end_t else start_t
        note_text = f"\n📝 {note}" if note.strip() != "" else ""

        if self.lang == 'fa':
            raw_text = f"[{local_priority}] {task} | {local_day} {shamsi} | ساعت: {time_display} {note_text}"
        else:
            raw_text = f"[{local_priority}] {task} | {local_day} {shamsi} | Time: {time_display} {note_text}"

        fixed_text = fix_persian(raw_text)
        display_text = f"[b][color={p_color}]{fixed_text}[/color][/b]"
        
        task_label = Label(
            text=display_text, 
            markup=True,
            font_name=FONT_PATH,
            text_size=(self.width, None),
            halign='right' if self.lang == 'fa' else 'left',
            valign='center',
            color=(0,0,0,1)
        )
        task_label.bind(size=task_label.setter('text_size'))
        task_item.add_widget(task_label)

        if self.current_view == 'active':
            edit_btn = Button(text=fix_persian(LANG['edit_btn'][self.lang]), font_name=FONT_PATH, size_hint_x=0.12, background_color=(1, 0.8, 0.2, 1))
            edit_btn.bind(on_press=lambda btn: self.action_edit(task_data))
            task_item.add_widget(edit_btn)

            done_btn = Button(text=fix_persian(LANG['done_btn'][self.lang]), font_name=FONT_PATH, size_hint_x=0.15, background_color=(0.2, 0.8, 0.2, 1))
            done_btn.bind(on_press=lambda btn: self.action_done(task_data))
            task_item.add_widget(done_btn)

        if self.current_view == 'completed':
            restore_btn = Button(text=fix_persian(LANG['restore_btn'][self.lang]), font_name=FONT_PATH, size_hint_x=0.15, background_color=(0.2, 0.6, 1, 1))
            restore_btn.bind(on_press=lambda btn: self.action_restore(task_data))
            task_item.add_widget(restore_btn)

        del_btn = Button(text=fix_persian(LANG['del_btn'][self.lang]), font_name=FONT_PATH, size_hint_x=0.12, background_color=(1, 0.3, 0.3, 1))
        del_btn.bind(on_press=lambda btn: self.action_delete(task_data))
        task_item.add_widget(del_btn)
        
        self.ids.task_list.add_widget(task_item)

    def add_task(self):
        task = self.ids.task_input.text.strip()
        shamsi_input = self.ids.shamsi_input.text.strip()
        miladi_input = self.ids.miladi_input.text.strip()
        start_input = self.ids.start_input.text.strip()
        end_input = self.ids.end_input.text.strip()
        note_input = self.ids.note_input.text.strip()
        
        raw_priority = self.get_raw_key('priority_vals', self.ids.priority_input.text)
        raw_day = self.get_raw_key('week_days', self.ids.day_spinner.text)
        
        if task == "": return
            
        start_time = start_input if start_input else (LANG['all_day']['fa'] if self.lang == 'fa' else LANG['all_day']['en'])

        try:
            if shamsi_input != self.default_shamsi:
                y, m, d = map(int, shamsi_input.replace('-', '/').split('/'))
                shamsi_obj = jdatetime.date(y, m, d)
                final_miladi = shamsi_obj.togregorian().strftime("%Y-%m-%d")
                final_shamsi = shamsi_obj.strftime("%Y/%m/%d")
            elif miladi_input != self.default_miladi:
                y, m, d = map(int, miladi_input.replace('/', '-').split('-'))
                miladi_obj = datetime.date(y, m, d)
                shamsi_obj = jdatetime.date.fromgregorian(date=miladi_obj)
                final_shamsi = shamsi_obj.strftime("%Y/%m/%d")
                final_miladi = miladi_obj.strftime("%Y-%m-%d")
            else:
                final_shamsi = self.default_shamsi
                final_miladi = self.default_miladi
        except:
            final_shamsi = self.default_shamsi
            final_miladi = self.default_miladi

        new_task = [task, final_shamsi, final_miladi, raw_priority, start_time, end_input, raw_day, note_input]

        if self.editing_task:
            index = self.all_tasks.index(self.editing_task)
            self.all_tasks[index] = new_task
            self.editing_task = None
            self.ids.btn_add.text = fix_persian(LANG['add_btn'][self.lang])
        else:
            self.all_tasks.append(new_task)
            
        self.save_current_file()
        
        self.ids.task_input.text = ""
        self.ids.note_input.text = ""
        self.ids.start_input.text = ""
        self.ids.end_input.text = ""
        self.set_today_dates()
        
        self.refresh_ui()

class TodoApp(App):
    def build(self):
        self.title = "Task Manager Pro"
        return TaskManager()

if __name__ == '__main__':
    TodoApp().run()