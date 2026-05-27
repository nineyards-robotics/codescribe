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
from gui_export_selector import select_objects


def remove_export_artifacts(folder, name):
    path_dir = os.path.join(folder, name)
    if os.path.exists(path_dir):
        if os.path.isdir(path_dir):
            shutil.rmtree(path_dir)
        else:
            os.remove(path_dir)

    extensions = ['.st', '.xml', '.gvl.xml', '.gvl.st']
    for ext in extensions:
        file_path = os.path.join(folder, name + ext)
        if os.path.exists(file_path):
            os.remove(file_path)


def export_child(child_obj, parent_obj, parent_folder_path):
    child_obj_type = get_object_type(child_obj)
    export_fn = OBJECT_TYPE_TO_EXPORT_FUNCTION.get(child_obj_type)
    if export_fn is not None:
        export_fn(child_obj, parent_obj, parent_folder_path, export_child)
    else:
        print("Skip unsupported object: {} [{}]".format(
            child_obj.get_name(), child_obj_type
        ))

def find_object_path_parts(root_obj, target_obj):
    """
    Возвращает путь от root_obj до target_obj в виде списка имён.
    root_obj в результат не включается.
    Пример: ["new_beacon", "NewBeacon"]
    """
    for child in root_obj.get_children():
        if child == target_obj:
            return [child.get_name()]

        child_path = find_object_path_parts(child, target_obj)
        if child_path is not None:
            return [child.get_name()] + child_path

    return None

def main():
    print_python_version()
    assert_project_open()

    src_folder = get_src_folder(scriptengine.projects.primary)
    print("Writing to: " + src_folder)

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

    # Передаём в GUI сам application как корень дерева
    selected = select_objects([application])

    if not selected:
        print("No objects selected. Export cancelled.")
        return

    # --- НОВАЯ ЛОГИКА ДЛЯ APPLICATION ---
    if application in selected:
        print("Application selected. Exporting all children (recursively)...")
        for child in application.get_children():
            remove_export_artifacts(application_folder, child.get_name())
            export_child(child, application, application_folder)
        print("Done!")
        return
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    print("Selected {} object(s). Starting recursive export...".format(len(selected)))
    for obj in selected:
        path_parts = find_object_path_parts(application, obj)
        if path_parts is None:
            print("Skip: could not resolve path for {}".format(obj.get_name()))
            continue

        export_parent_folder = application_folder
        if len(path_parts) > 1:
            export_parent_folder = os.path.join(application_folder, *path_parts[:-1])

        if not os.path.exists(export_parent_folder):
            os.makedirs(export_parent_folder)

        remove_export_artifacts(export_parent_folder, obj.get_name())
        export_child(obj, application, export_parent_folder)

        print("Exported: {} -> {}".format(
            obj.get_name(),
            os.path.join(export_parent_folder, obj.get_name())
        ))

    print("Done!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        raise e