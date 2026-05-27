# -*- coding: utf-8 -*-
from __future__ import print_function

import imp
import os
import sys

imp.reload(sys)
sys.setdefaultencoding('utf-8')

import scriptengine

from entrypoint import get_device_entrypoints, find_application, get_src_folder
from gui_export_selector import select_objects
from import_from_files import import_directory_child, import_from_files  # добавлен import_from_files
from util import print_python_version, assert_project_open


def find_path_to_object(root_obj, target_obj, current_path=None):
    """
    Возвращает список имён от root_obj (исключая root) до target_obj.
    Если target_obj == root_obj, возвращает [].
    """
    if current_path is None:
        current_path = []
    if root_obj == target_obj:
        return current_path
    for child in root_obj.get_children():
        if child == target_obj:
            return current_path + [child.get_name()]
        sub_path = find_path_to_object(child, target_obj, current_path + [child.get_name()])
        if sub_path is not None:
            return sub_path
    return None


def get_object_by_path(root_obj, path_parts):
    """Возвращает объект по списку имён потомков, начиная от root_obj."""
    current = root_obj
    for name in path_parts:
        found = None
        for child in current.get_children():
            if child.get_name() == name:
                found = child
                break
        if found is None:
            return None
        current = found
    return current


def main():
    print_python_version()
    assert_project_open()

    src_folder = get_src_folder(scriptengine.projects.primary)
    print("Source folder: " + src_folder)

    devices = list(get_device_entrypoints(scriptengine.projects.primary))
    if not devices:
        print("No devices found!")
        return
    device_obj = devices[0]
    device_name = device_obj.get_name()
    device_folder = os.path.join(src_folder, device_name)

    application = find_application(device_obj)
    if application is None:
        print("No Application found in device!")
        return

    # Подтверждение
    ui_continue = scriptengine.system.ui.prompt(
        "Import Selected Objects will overwrite chosen objects from files.\n\n"
        "Do you want to continue?",
        choice=scriptengine.PromptChoice.YesNo,
        default_result=scriptengine.PromptResult.No,
        store_description="Don't show again",
        store_key="import_selected_confirm",
    )
    if ui_continue != scriptengine.PromptResult.Yes:
        print("Import cancelled by user.")
        return

    # Выбор объектов через GUI
    selected = select_objects([application])
    if not selected:
        print("No objects selected. Import cancelled.")
        return

    # Если выбран Application — запускаем полный импорт и выходим
    if application in selected:
        print("Application selected. Performing full import using import_from_files...")
        import_from_files(scriptengine.projects.primary)
        print("Full import completed.")
        return

    # Иначе — импорт выбранных объектов по отдельности
    # Строим пути для выбранных объектов
    objects_with_path = []
    for obj in selected:
        path_parts = find_path_to_object(application, obj)
        if path_parts is None:
            print("Warning: could not determine path for '{}', skipping".format(obj.get_name()))
            continue
        objects_with_path.append((obj, path_parts))

    # Сортируем по глубине (сначала родители)
    objects_with_path.sort(key=lambda x: len(x[1]))

    # Импортируем
    for obj, path_parts in objects_with_path:
        obj_name = obj.get_name()
        print("Processing: " + obj_name)

        # Родительский путь (без последнего элемента)
        parent_path_parts = path_parts[:-1]
        parent_obj = get_object_by_path(application, parent_path_parts)
        if parent_obj is None:
            print("  ERROR: parent object not found, skipping")
            continue

        # Путь к родительской папке в файловой системе
        parent_folder_path = os.path.join(device_folder, "application", *parent_path_parts)
        if not os.path.exists(parent_folder_path):
            print("  WARNING: folder does not exist: " + parent_folder_path)

        # Удаляем старый объект
        try:
            obj.remove()
            print("  Removed existing object")
        except Exception as e:
            print("  Failed to remove object: " + str(e))
            continue

        # Импортируем заново
        try:
            import_directory_child(obj_name, parent_folder_path, parent_obj)
            print("  Imported successfully")
        except Exception as e:
            print("  Import failed: " + str(e))

    print("Done!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        raise e