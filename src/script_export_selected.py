# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import shutil
import sys
import imp

imp.reload(sys)
sys.setdefaultencoding('utf-8')

import scriptengine
from entrypoint import get_device_entrypoints, find_application, get_src_folder
from import_export import OBJECT_TYPE_TO_EXPORT_FUNCTION
from util import print_python_version, assert_project_open
from object_type import get_object_type

# --- GUI выбор объектов (Windows Forms) ---
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
from System.Windows.Forms import (Form, Button, CheckedListBox, DialogResult,
                                  Label, Panel, FormStartPosition, FormBorderStyle,
                                  DockStyle, AutoScaleMode)
from System.Drawing import Size, Point

def select_objects(root_objects):
    form = Form()
    form.Text = "Select Objects to Export (recursively)"
    form.Size = Size(450, 500)
    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False

    label = Label()
    label.Text = "Check objects you want to export (including all children):"
    label.Location = Point(10, 10)
    label.Size = Size(420, 25)

    clb = CheckedListBox()
    clb.Dock = DockStyle.Fill
    clb.CheckOnClick = True
    clb.Location = Point(10, 40)

    for obj in root_objects:
        clb.Items.Add(obj.get_name(), False)

    panel = Panel()
    panel.Dock = DockStyle.Bottom
    panel.Height = 40

    btn_ok = Button()
    btn_ok.Text = "OK"
    btn_ok.DialogResult = DialogResult.OK
    btn_ok.Location = Point(280, 8)
    btn_ok.Size = Size(75, 25)

    btn_cancel = Button()
    btn_cancel.Text = "Cancel"
    btn_cancel.DialogResult = DialogResult.Cancel
    btn_cancel.Location = Point(365, 8)
    btn_cancel.Size = Size(75, 25)

    panel.Controls.Add(btn_ok)
    panel.Controls.Add(btn_cancel)

    form.Controls.Add(clb)
    form.Controls.Add(label)
    form.Controls.Add(panel)
    form.AutoScaleMode = AutoScaleMode.Font

    result = form.ShowDialog()
    if result == DialogResult.OK:
        selected = []
        for i in range(clb.Items.Count):
            if clb.GetItemChecked(i):
                selected.append(root_objects[i])
        return selected
    else:
        return []

# --- Удаление старых артефактов экспорта для заданного имени ---
def remove_export_artifacts(folder, name):
    """
    Удаляет папку folder/name, а также файлы folder/name.st, folder/name.xml,
    folder/name.gvl.xml, folder/name.gvl.st, если они существуют.
    """
    # Папка
    path_dir = os.path.join(folder, name)
    if os.path.exists(path_dir):
        if os.path.isdir(path_dir):
            shutil.rmtree(path_dir)
        else:
            os.remove(path_dir)

    # Файлы с расширениями
    extensions = ['.st', '.xml', '.gvl.xml', '.gvl.st']
    for ext in extensions:
        file_path = os.path.join(folder, name + ext)
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Рекурсивный экспорт (как в script_export_to_files.py) ---
def export_child(child_obj, parent_obj, parent_folder_path):
    """Рекурсивно экспортирует объект и всех его детей, используя словарь export-функций."""
    child_obj_type = get_object_type(child_obj)
    export_fn = OBJECT_TYPE_TO_EXPORT_FUNCTION.get(child_obj_type)
    if export_fn is not None:
        export_fn(child_obj, parent_obj, parent_folder_path, export_child)

# --- Основная функция ---
def main():
    print_python_version()
    assert_project_open()

    src_folder = get_src_folder(scriptengine.projects.primary)
    print("Writing to: " + src_folder)

    # Создаём корневую папку, если её нет (не удаляем!)
    if not os.path.exists(src_folder):
        os.makedirs(src_folder)

    devices = list(get_device_entrypoints(scriptengine.projects.primary))
    if not devices:
        print("No devices found!")
        return
    device_obj = devices[0]

    device_folder = os.path.join(src_folder, device_obj.get_name())
    if not os.path.exists(device_folder):
        os.makedirs(device_folder)

    application = find_application(device_obj)
    if application is None:
        print("No Application found in device!")
        return

    application_folder = os.path.join(device_folder, "application")
    if not os.path.exists(application_folder):
        os.makedirs(application_folder)

    root_objects = list(application.get_children())
    if not root_objects:
        print("Nothing to export in Application")
        return

    selected = select_objects(root_objects)
    if not selected:
        print("No objects selected. Export cancelled.")
        return

    print("Selected {} object(s). Starting recursive export...".format(len(selected)))
    for obj in selected:
        # Удаляем старые артефакты этого объекта перед экспортом
        remove_export_artifacts(application_folder, obj.get_name())
        export_child(obj, application, application_folder)
        print("Exported: {} (and all its children)".format(obj.get_name()))

    print("Done!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        raise e