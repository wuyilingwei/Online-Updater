import toml
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import requests
import subprocess
import webbrowser

PROGRAM_VERSION = "1.0.0"

root = tk.Tk()
# 创建主窗口
root.title(f"Updater v{PROGRAM_VERSION}")
root.geometry("400x450")
root.resizable(False, False)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
root.tk.call('wm', 'iconphoto', root._w, tk.PhotoImage(file=resource_path("logo.png")))

# create a logger file
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


if os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'package.toml')):
    package = toml.load(os.path.join(os.path.dirname(sys.argv[0]), 'package.toml'))
else:
    logger.error("Package file not found.")
    messagebox.showerror("Package Error", "Package file not found. Please check the package.toml exist.\nIf you copied or download the updater, please make sure the package.toml is in the same directory.")
    sys.exit(1)

REMOTE_URL = package['common']['remote']
CURRENT_VERSION = package['common']['version']
AUTHOR = package['common'].get('author', 'Unknown')
logging.info(f'Current version: {CURRENT_VERSION}')


# download the remote version
try:
    r = requests.get(f"{REMOTE_URL}/packages.toml")
    r.raise_for_status()
except requests.RequestException as e:
    logger.error(f"Failed to get remote version. Error: {e}")
    messagebox.showerror("Network Error", "Unable to obtain from the defined remote server, please confirm the service status with the provider. Only the current version information can be viewed.")
    remote_packages = {'common': {'versions': [CURRENT_VERSION], 'recommand': CURRENT_VERSION}}  # 设置默认值
else:
    remote_packages = toml.loads(r.text)

remote_available = remote_packages['common']['versions']
remote_recommand = remote_packages['common']['recommand']
logger.info(f"Remote recommand version: {remote_recommand}")
logger.info(f"Remote support versions: {remote_available}")

def get_update_type(target_remote_version: str) -> str:
    logger.debug(f"Checking update type for {CURRENT_VERSION} -> {target_remote_version}")
    current_version = CURRENT_VERSION.split(' ')[0]
    current_version = list(map(int, current_version.split('.')))
    remote_version = target_remote_version.split(' ')[0]
    remote_version = list(map(int, remote_version.split('.')))
    if remote_version[0] > current_version[0]:
        return 'incompatible'
    elif remote_version[0] < current_version[0]:
        return 'old'
    elif remote_version[1] > current_version[1]:
        return 'force'
    elif remote_version[1] < current_version[1]:
        return 'old'
    elif remote_version[2] > current_version[2]:
        return 'optional'
    elif remote_version[2] < current_version[2]:
        return 'old'
    else:
        return 'recommand'

default_update_type = get_update_type(remote_recommand)
logger.debug(f"Default update type: {default_update_type}")

is_force_update = False

def get_accept_versions(current_version, available_versions):
    current_version_list = list(map(int, current_version.split('.')))
    accept_versions = []
    for version in available_versions:
        version_list = list(map(int, version.split('.')))
        if version_list >= current_version_list or is_force_update:
            accept_versions.append(version)
    if accept_versions == []:
        accept_versions.append("No available version")
    return accept_versions

accept_versions = get_accept_versions(CURRENT_VERSION, remote_available)

# 特殊目录
# 用户文档目录
document_dir = os.path.join(os.path.expanduser('~'), 'Documents')
# 当前用户桌面目录
desktop_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
# 当前用户下载目录
download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')

def update(target_remote_version: str):
    global package, is_force_update  # 声明 package 和 is_force_update 为全局变量
    update_type = get_update_type(target_remote_version)
    logger.info(f"Updating to {target_remote_version} with type {update_type}")
    if update_type == 'incompatible':
        if is_force_update:
            logger.warning(f"Trying to update to an incompatible version.")
            if not yes_no_message("Force Update", "The server has declared this as a disruptive update.\nUsing the updater may result in errors.\nDo you still wish to proceed?"):
                logger.warning(f"User canceled the force update.")
                return
            logger.warning(f"User confirmed the force update.")
        else:
            logger.error(f"Trying to update to an incompatible version.")
            messagebox.showerror("Incompatible Version", "The server has declared this as a disruptive update.\nPlease contact the author for further instructions.\nOr enable the force update option to proceed.")
            return
    if update_type == 'force':
        logger.info(f"Update type force. Proceeding")
    if update_type == 'optional':
        logger.info(f"Update type optional. Proceeding")
    if update_type == 'recommand':
        logger.info(f"Update type recommand. Fixing")
    if update_type == 'old':
        if is_force_update:
            logger.warning(f"Trying to update to an old version.")
            if not yes_no_message("Force Update", "The server has declared this as an old version.\nDo you still wish to proceed?"):
                logger.warning(f"User canceled the force update.")
                return
            logger.warning(f"User confirmed the force update.")
        else:
            logger.error(f"Trying to update to an old version.")
            messagebox.showerror("Old Version", "The server has declared this as an old version.\nPlease contact the author for further instructions.\nOr enable the force update option to proceed.")
            return
    if update_type == 'recommand':
        if not confirm_message("Fix Version", "The server has declared this as the using version.\nDo you want to fix it?"):
            logger.warning(f"User canceled the fix version.")
            return
    update_URL = f"{REMOTE_URL}/{target_remote_version}"
    response = requests.get(f"{update_URL}/package.toml")
    if response.status_code != 200:
        logger.error(f"Failed to download package.toml. Status code: {response.status_code}")
        messagebox.showerror("Download Error", f"Failed to download package.toml. Status code: {response.status_code}")
        return
    try:
        package_text = response.text.replace("\\", "\\\\")
        update_package = toml.loads(package_text)
    except toml.TomlDecodeError as e:
        logger.error(f"Failed to parse package.toml. Error: {e}")
        messagebox.showerror("Parse Error", f"Failed to parse package.toml. Error: {e}")
        return

    required_program_version = update_package['common'].get('program', '0.0.0')
    if compare_versions(required_program_version, PROGRAM_VERSION) > 0:
        messagebox.showerror("Update Error", f"This update requires a higher version of the updater (>= {required_program_version}). Please update your updater.")
        logger.error(f"This update requires a higher version of the updater (>= {required_program_version}).")
        return

    update_progress_bar(10)
    progress_bar_value = 10
    progress_bar_step = 80 / len(update_package.get('files', {}))
    logger.debug(f"Update package: {update_package}")
    for file_key, file in update_package.get('files', {}).items():
        action = file.get('action', 'download')
        path = file.get('dir', file['path'])
        url_path = path.replace("\\", "/")
        if path.startswith('!'):
            path = path.replace('!documents!', document_dir)
            path = path.replace('!desktop!', desktop_dir)
            path = path.replace('!downloads!', download_dir)
        else:
            path = os.path.join(os.path.dirname(sys.argv[0]), path)
        if action == 'delete':
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Deleted {path}")
            else:
                logger.info(f"File {path} does not exist. Skipping delete.")
            continue
        elif action == 'download':
            match_found = False
            if ('files' in package
                and not (is_force_update or update_type == 'recommand')):
                for local_key, local in package['files'].items():
                    if file['path'] == local['path']:
                        logger.info(f"Processing {file['path']}")
                        if file['version'] == local['version']:
                            logger.info(f"Version match. Skipping")
                            match_found = True
                            break
            if match_found:
                continue
            logger.info(f"No match found for {file['path']}. Downloading")
            r = requests.get(f"{update_URL}/{url_path}")
            if r.status_code != 200:
                logger.error(f"Failed to download {file['path']}. Status code: {r.status_code}")
                continue
            # 确保path合法且文件夹存在
            path_dir = os.path.dirname(path)
            if not os.path.exists(path_dir) and path_dir:
                os.makedirs(path_dir)
            with open(path, 'wb') as f:
                f.write(r.content)
            logger.info(f"Updated {file['path']}")
        else:
            logger.error(f"Unknown action {action} for {file['path']}. Skipping")
        progress_bar_value += progress_bar_step
        update_progress_bar(progress_bar_value)
    update_progress_bar(90)
    logger.info(f"Update finished")
    global CURRENT_VERSION
    CURRENT_VERSION = update_package['common']['version']
    package = update_package
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'package.toml'), 'w') as f:
        toml.dump(package, f)
    update_progress_bar(100)
    logger.info(f"Updated package file")
    logger.info(f"Updated version to {CURRENT_VERSION}")

    # 执行 command
    # update_package['extra']['command'] 可选包含一个命令，用于更新后的操作
    command = update_package.get('extra', {}).get('command', '')
    if command:
        logger.info(f"Executing command: {command}")
        subprocess.Popen(command, shell=True, cwd=os.path.dirname(sys.argv[0]))
    return

def compare_versions(version1: str, version2: str) -> int:
    v1 = list(map(int, version1.split('.')))
    v2 = list(map(int, version2.split('.')))
    return (v1 > v2) - (v1 < v2)

def yes_no_message(title: str, message: str) -> bool:
    return messagebox.askyesno(title, message)

def confirm_message(title: str, message: str) -> bool:
    return messagebox.askokcancel(title, message)

def update_progress_bar(progress):
    progress_var.set(progress)
    root.update_idletasks()

def start_update():
    selected_version = version_var.get()
    update(selected_version)
    try:
        update(selected_version)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        messagebox.showerror("Update Failed", f"Update failed: {e}")
        return
    update_progress_bar(100)
    if selected_version == CURRENT_VERSION:
        current_version_label_pkg.config(text=f"Current Version: {CURRENT_VERSION}")  # 更新当前版本标签
        update_link.config(text=f"{REMOTE_URL}")  # 更新链接
        default_update_type = get_update_type(CURRENT_VERSION)
        update_status_label.config(text=f"{default_update_type}")  # 更新当前状态标签
        update_button.config(text="Fix" if selected_version == CURRENT_VERSION else "Update")  # 更新按钮文本
        update_status_label.config(fg=get_update_type_color(default_update_type))  # 更新状态标签颜色
        refresh_available_versions()

def refresh_available_versions():
    global remote_packages, remote_available, remote_recommand, newer_versions
    r = requests.get(f"{REMOTE_URL}/packages.toml")
    if r.status_code != 200:
        logger.error(f"Failed to get remote version. Status code: {r.status_code}")
        raise Exception(f"Failed to get remote version. Status code: {r.status_code}")
    remote_packages = toml.loads(r.text)
    remote_available = remote_packages['common']['versions']
    remote_recommand = remote_packages['common']['recommand']
    newer_versions = get_accept_versions(CURRENT_VERSION, remote_available)
    if newer_versions == ["No available version"]:
        version_var.set("No available version")
    else:
        version_var.set(remote_recommand)
    version_menu['menu'].delete(0, 'end')
    for version in newer_versions:
        version_menu['menu'].add_command(label=version, command=tk._setit(version_var, version))

def get_update_type_color(update_type: str) -> str:
    if update_type == 'force':
        return '#FF4500'  # 深红色
    elif update_type == 'optional':
        return '#DAA520'  # 深黄色
    elif update_type == 'recommand':
        return '#7CFC00'  # 深绿色
    elif update_type == 'incompatible':
        return '#00008B'  # 深蓝色
    else:
        return 'black'

def open_url(url: str):
    webbrowser.open(url)

def on_version_change(*args):
    selected_version = version_var.get()
    update_button.config(text="Fix" if selected_version == CURRENT_VERSION else "Update")
    update_button.config(state=tk.DISABLED if selected_version == "No available version" else tk.NORMAL)

def on_force_update_change():
    global is_force_update
    is_force_update = force_update_var.get()
    logger.info(f"Force update: {is_force_update}")
    refresh_available_versions()


# 添加提示文本
info_label = tk.Label(root, text="Note: This is a general-purpose updater. By using it, you acknowledge and trust the update provider, granting it the ability to perform any actions on your computer.", wraplength=380, justify="left", font=("Helvetica", 10, "bold"))
info_label.pack(pady=10)

# 包信息 frame
package_frame = tk.LabelFrame(root, text="Package Info", relief=tk.RIDGE, borderwidth=2, font=("Helvetica", 10, "bold"))
package_frame.place(x=10, y=80, width=380, height=120)

# 包作者
author_label = tk.Label(package_frame, text=f"Author(claim): {AUTHOR}", font=("Helvetica", 10, "bold"))
author_label.place(x=0, y=0)

# 当前版本
current_version_label_pkg = tk.Label(package_frame, text=f"Current Version: {CURRENT_VERSION}", font=("Helvetica", 10, "bold"))
current_version_label_pkg.place(x=190, y=0)

# 提示文本
update_link_label = tk.Label(package_frame, text="Update Link:", font=("Helvetica", 10, "bold"))
update_link_label.place(x=0, y=25)

# 更新链接
update_link = tk.Label(package_frame, text=f"{REMOTE_URL}", wraplength=370,justify="left")  # 设置 wraplength 和 justify
update_link.place(x=0, y=45)

# 远程版本 frame
remote_frame = tk.LabelFrame(root, text="Remote Versions", relief=tk.RIDGE, borderwidth=2, font=("Helvetica", 10, "bold"))
remote_frame.place(x=10, y=210, width=380, height=120)

# 显示远程最新版本
remote_version_label = tk.Label(remote_frame, text=f"Recommand: {remote_recommand}", font=("Helvetica", 10, "bold"))
remote_version_label.place(x=0, y=0)

# 提示文本
update_type_label = tk.Label(remote_frame, text="Current Status:", font=("Helvetica", 10, "bold"))
update_type_label.place(x=180, y=0)

# 显示更新状态
update_status_label = tk.Label(remote_frame, text=f"{default_update_type}", fg=get_update_type_color(default_update_type), font=("Helvetica", 10, "bold"))
update_status_label.place(x=280, y=0)

# 添加复选框以允许强制版本切换
force_update_var = tk.BooleanVar()
force_update_check = tk.Checkbutton(remote_frame, text="Enable Force Version Change", variable=force_update_var, command=on_force_update_change, font=("Helvetica", 10, "bold"))
force_update_check.place(x=0, y=60)

# 提示文本
target_version_label = tk.Label(remote_frame, text="Update to:", font=("Helvetica", 10, "bold"))
target_version_label.place(x=0, y=30)

# 版本选择下拉列表
version_var = tk.StringVar(remote_frame)
if remote_recommand not in accept_versions:
    version_var.set(accept_versions[0])
else:
    version_var.set(remote_recommand)
version_var.trace_add("write", on_version_change)  # 使用 trace_add 监听版本选择变化

version_menu = tk.OptionMenu(remote_frame, version_var, *accept_versions)
version_menu.place(x=80, y=25, width=280, height=30)  # 设置固定大小

# 更新按钮
update_button = tk.Button(remote_frame, text="Update", command=start_update, font=("Helvetica", 10, "bold"))
update_button.place(x=240, y=55, width=120, height=30)  # 设置固定大小

# 更新进度条
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)  # 使用 ttk.Progressbar
progress_bar.place(x=10, y=350, width=380, height=20)

# 添加开源软件信息
license_label = tk.Label(root, text=f"Open-Source On\nGNU GENERAL PUBLIC LICENSE\nAuthor: Wuyilingwei\nProgram Version: v{PROGRAM_VERSION}", wraplength=380, justify="left", font=("Helvetica", 10, "bold"))
license_label.place(x=10, y=370)

# 添加Github链接
github_link = tk.Label(root, text="Github", fg="blue", cursor="hand2", font=("Helvetica", 10, "bold"))
github_link.place(x=120, y=370)
github_link.bind("<Button-1>", lambda e: open_url("https://github.com/wuyilingwei/Online-Updater"))

on_version_change()  # 初始化版本选择

root.mainloop()