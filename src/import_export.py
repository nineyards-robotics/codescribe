# -*- coding: utf-8 -*-
# REMEMBER: this is python 2.7
import os
import re

from object_type import ObjectType, get_object_type
from util import *

IMPLEMENTATION_DELIMITER_SPLIT = "// --- BEGIN IMPLEMENTATION ---"
IMPLEMENTATION_DELIMITER_INSERT = "\n" + IMPLEMENTATION_DELIMITER_SPLIT + "\n\n"

_TIMESTAMP_PATTERNS = [
    # Pattern for Timestamp in regular XML
    re.compile(
        r'(<Single\b[^>]*\bName="Timestamp"\b[^>]*>)([^<]*)(</Single>)'
    ),
    # Pattern for LastModification in regular XML
    re.compile(
        r'(<Single\b[^>]*\bName="LastModification"\b[^>]*>)([^<]*)(</Single>)'
    ),
]

# Additional patterns for escaped XML content (like inside StructuredView)
_ESCAPED_TIMESTAMP_PATTERNS = [
    # Pattern for escaped Timestamp
    re.compile(
        r'(\\u003CSingle\\u0020[^\\]*\\bName="Timestamp"\\b[^\\]*\\u003E)(\d+)(\\u003C/Single\\u003E)'
    ),
    # Pattern for escaped LastModification
    re.compile(
        r'(\\u003CSingle\\u0020[^\\]*\\bName="LastModification"\\b[^\\]*\\u003E)(\d+)(\\u003C/Single\\u003E)'
    ),
]

def log_import_object(obj, context=""):  # DEBUG
    """Выводит в консоль информацию об импортированном объекте."""
    obj_type = get_object_type(obj)
    obj_guid = str(obj.type) if hasattr(obj, 'type') else "NO_GUID"
    print("[IMPORT] %s | Type: %s | GUID: %s | Name: %s" % (
        context, obj_type, obj_guid, obj.get_name()
    ))

def normalize_timestamps_in_xml(path):
    if not os.path.exists(path):
        print("WARNING: normalize_timestamps_in_xml called for non-existent file: %s" % path)
        return
    
    # Читаем с сохранением кодировки
    import codecs
    with codecs.open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    normalizedContent = content
    numOfReplacements = 0
    
    # Паттерны остаются те же
    timestamp_pattern = re.compile(
        r'(<Single\s+[^>]*?Name="Timestamp"[^>]*?>)(\d+)(</Single>)',
        re.DOTALL | re.IGNORECASE
    )
    normalizedContent, count1 = timestamp_pattern.subn(r'\g<1>0\g<3>', normalizedContent)
    numOfReplacements += count1
    
    lastmod_pattern = re.compile(
        r'(<Single\s+[^>]*?Name="LastModification"[^>]*?>)(\d+)(</Single>)',
        re.DOTALL | re.IGNORECASE
    )
    normalizedContent, count2 = lastmod_pattern.subn(r'\g<1>0\g<3>', normalizedContent)
    numOfReplacements += count2
    
    if numOfReplacements == 0:
        print("WARNING: No timestamps found in " + path)
        return
    
    # Записываем с явной UTF-8 кодировкой
    with codecs.open(path + ".tmp", 'w', encoding='utf-8') as f:
        f.write(normalizedContent)
    
    if os.path.exists(path):
        os.remove(path)
    os.rename(path + ".tmp", path)

def write_st(obj, f):
    f.write(obj.textual_declaration.text)
    f.write(IMPLEMENTATION_DELIMITER_INSERT)
    f.write(obj.textual_implementation.text)

def write_st_decl_only(obj, f):
    f.write(obj.textual_declaration.text)


def import_st(f, obj):
    f.seek(0)
    content = str(f.read())
    declaration, implementation = content.split(IMPLEMENTATION_DELIMITER_SPLIT)
    obj.textual_declaration.replace(declaration.strip() + "\n")
    obj.textual_implementation.replace(implementation.strip() + "\n")
    log_import_object(obj, "import_st")  # DEBUG

def import_st_decl_only(f, obj):
    f.seek(0)
    content = str(f.read())
    obj.textual_declaration.replace(content.strip() + "\n")
    log_import_object(obj, "import_st_decl_only")  # DEBUG

def write_native(obj, path, recursive=False):
    # Отладочная информация до экспорта
    obj_type = get_object_type(obj)
    obj_name = obj.get_name()
    print("[DEBUG] write_native: object='%s' type='%s' path='%s' recursive=%s" % (
        obj_name, obj_type, path, recursive))

    # Вызываем экспорт (файл должен создаться)
    obj.export_native(path, recursive=recursive)

    # Проверяем, создался ли файл
    if not os.path.exists(path):
        print("[WARNING] export_native did NOT create file: %s (object=%s, type=%s)" % (
            path, obj_name, obj_type))
        # Не пытаемся получить родителя – его может не быть или нет метода get_parent
        # Вместо этого выведем несколько свойств объекта для диагностики
        print("[DEBUG] Object details: name='%s', type='%s', has_textual_implementation=%s" % (
            obj_name, obj_type, getattr(obj, 'has_textual_implementation', 'N/A')))
        # Попробуем проверить, есть ли у объекта метод export_native
        if hasattr(obj, 'export_native'):
            print("[DEBUG] Object has export_native method")
        else:
            print("[DEBUG] Object does NOT have export_native method")
        return  # Не пытаемся нормализовать несуществующий файл

    # Файл существует – нормализуем таймстампы
    try:
        normalize_timestamps_in_xml(path)
        print("[DEBUG] normalize_timestamps_in_xml: OK for %s" % path)
    except Exception as e:
        print("WARNING: Failed to normalize timestamps in " + path + ": " + str(e))

def read_native(f, obj):
    obj.import_native(f)


def export_folder(child_obj, parent_obj, parent_folder_path, export_child_fn):
    child_obj_folder = os.path.join(parent_folder_path, child_obj.get_name())
    os.mkdir(child_obj_folder)
    for c in child_obj.get_children():
        export_child_fn(c, child_obj, child_obj_folder)


def import_folder(child, dir_path, dir_parent_obj, import_dir_fn):
    dir_parent_obj.create_folder(child)
    folder_obj = first_of_type_or_error(
        dir_parent_obj.find(child),
        ObjectType.FOLDER,
        "Folder of name " + child + " should have been created, but cannot be found",
    )
    log_import_object(folder_obj, "import_folder")  # DEBUG
    import_dir_fn(os.path.join(dir_path, child), folder_obj)


def export_pou(child_obj, parent_obj, parent_folder_path, export_child_fn):
    if child_obj.has_textual_implementation:
        with open(os.path.join(parent_folder_path, child_obj.get_name() + ".st"), "w") as f:
            write_st(child_obj, f)
    else:
        export_native(child_obj, parent_obj, parent_folder_path, export_child_fn)

    # Экспортируем дочерние элементы (включая папки интерфейсов)
    for c in child_obj.get_children():
        if get_object_type(c) == ObjectType.FOLDER:
            # Папку внутри POU экспортируем как папку
            export_folder(c, child_obj, parent_folder_path, export_child_fn)
        else:
            export_child_fn(c, child_obj, parent_folder_path)


def import_pou_st(child, dir_path, dir_parent_obj, import_dir_fn):
    filename, _ = os.path.splitext(child)
    pou_obj = dir_parent_obj.create_pou(filename)
    log_import_object(pou_obj, "import_pou_st")  # DEBUG
    with open(os.path.join(dir_path, child), "r") as f:
        import_st(f, pou_obj)


def export_gvl(child_obj, parent_obj, parent_folder_path, export_child_fn):
    """
    Exports native xml and structured text representation.
    This is because we need to support EVL and NVL as well, using this function.
    """
    write_native(child_obj, os.path.join(parent_folder_path, child_obj.get_name() + ".gvl.xml"), recursive=False)
    with open(os.path.join(parent_folder_path, child_obj.get_name() + ".gvl.st"), "w") as f:
        write_st_decl_only(child_obj, f)


def import_gvl(child, dir_path, dir_parent_obj, import_dir_fn):
    """
    Import the native xml and then overwrite the textual definition with the structured text.
    """
    name, ext = os.path.splitext(child)

    if ".gvl" not in name:
        raise ValueError(".gvl not in file name!")

    name = name.replace(".gvl", "")

    if ext != ".st":
        raise ValueError("Expected GVL st file!")

    gvl_xml_path = os.path.join(dir_path, name + ".gvl.xml")
    if os.path.exists(gvl_xml_path):
        import_native(gvl_xml_path, dir_path, dir_parent_obj, import_dir_fn)
        imported_obj = first_of_type_or_error(
            dir_parent_obj.find(name), ObjectType.GVL, name + " GVL should have been created, but cannot be found"
        )
        log_import_object(imported_obj, "import_gvl (from xml)")  # DEBUG
    else:
        imported_obj = dir_parent_obj.create_gvl(name)
        log_import_object(imported_obj, "import_gvl (new)")  # DEBUG

    with open(os.path.join(dir_path, child), "r") as f:
        import_st_decl_only(f, imported_obj)


def export_native(child_obj, parent_obj, parent_folder_path, export_child_fn):
    write_native(child_obj, os.path.join(parent_folder_path, child_obj.get_name() + ".xml"), recursive=False)


def export_native_recursive(child_obj, parent_obj, parent_folder_path, export_child_fn):
    write_native(child_obj, os.path.join(parent_folder_path, child_obj.get_name() + ".xml"), recursive=True)


def import_native(child, dir_path, dir_parent_obj, import_dir_fn):
    full_path = os.path.join(dir_path, child)
    name_without_ext = os.path.splitext(child)[0]
    before = set([obj.get_name() for obj in dir_parent_obj.get_children()])
    print("DEBUG: Before import of %s, children: %s" % (child, before))
    read_native(full_path, dir_parent_obj)
    after = [obj for obj in dir_parent_obj.get_children() if obj.get_name() not in before]
    print("DEBUG: After import, new children: %s" % ([obj.get_name() for obj in after]))
    if after:
        for obj in after:
            log_import_object(obj, "import_native (%s)" % child)
    else:
        existing = first_of_type_or_none(dir_parent_obj.find(name_without_ext), None)
        if existing:
            log_import_object(existing, "import_native (%s) already existed" % child)
        else:
            print("WARNING: No new object created for %s" % child)
            # Дополнительно: вывести всех детей с их типами
            for obj in dir_parent_obj.get_children():
                print("  - %s : %s" % (obj.get_name(), get_object_type(obj)))


def export_dut(child_obj, parent_obj, parent_folder_path, export_child_fn):
    with open(os.path.join(parent_folder_path, child_obj.get_name() + ".st"), "w") as f:
        f.write(child_obj.textual_declaration.text)


def import_dut(child, dir_path, dir_parent_obj, import_dir_fn):
    filename, _ = os.path.splitext(child)
    dut_obj = dir_parent_obj.create_dut(filename)
    log_import_object(dut_obj, "import_dut")  # DEBUG
    with open(os.path.join(dir_path, child), "r") as f:
        f.seek(0)
        dut_obj.textual_declaration.replace(str(f.read()))


def export_method(child_obj, parent_obj, parent_folder_path, export_child_fn):
    if child_obj.has_textual_implementation:
        with open(
            os.path.join(parent_folder_path, parent_obj.get_name() + "." + child_obj.get_name() + ".st"), "w"
        ) as f:
            write_st(child_obj, f)
    else:
        write_native(
            child_obj,
            os.path.join(parent_folder_path, parent_obj.get_name() + "." + child_obj.get_name() + ".xml"),
            recursive=False,
        )


def import_method_st(child, dir_path, dir_parent_obj, import_dir_fn):
    full_path = os.path.join(dir_path, child)
    filename, _ = os.path.splitext(child)
    parent_name, method_name = filename.split(".")
    
    parent_obj = first_of_type_or_none(dir_parent_obj.find(parent_name), ObjectType.POU)
    if parent_obj is None:
        parent_obj = first_of_type_or_none(dir_parent_obj.find(parent_name), ObjectType.INTERFACE)
    
    if parent_obj is None:
        raise ValueError(parent_name + " should have been created, but cannot be found")
    
    method_obj = parent_obj.create_method(method_name)
    log_import_object(method_obj, "import_method_st")
    with open(full_path, "r") as f:
        import_st(f, method_obj)


def export_sub_pou(child_obj, parent_obj, parent_folder_path, export_child_fn):
    write_native(
        child_obj,
        os.path.join(parent_folder_path, parent_obj.get_name() + "." + child_obj.get_name() + ".xml"),
        recursive=True,
    )


def import_sub_pou(child, dir_path, dir_parent_obj, import_dir_fn):
    full_path = os.path.join(dir_path, child)
    filename, _ = os.path.splitext(child)
    parent_name = filename.split(".")[0]
    print("DEBUG: import_sub_pou for %s, looking for parent '%s' in %s" % (child, parent_name, dir_parent_obj.get_name()))
    # Вывести всех детей dir_parent_obj с типами
    for obj in dir_parent_obj.get_children():
        print("  child: %s (%s)" % (obj.get_name(), get_object_type(obj)))
    
    parent_obj = None
    # Ищем родителя среди POU, FOLDER, INTERFACE
    parent_obj = first_of_type_or_none(dir_parent_obj.find(parent_name), ObjectType.POU)
    if parent_obj is None:
        parent_obj = first_of_type_or_none(dir_parent_obj.find(parent_name), ObjectType.FOLDER)
    if parent_obj is None:
        parent_obj = first_of_type_or_none(dir_parent_obj.find(parent_name), ObjectType.INTERFACE)
    
    if parent_obj is None:
        # Попробуем найти рекурсивно, возможно интерфейс лежит глубже
        all_children = []
        def collect(obj):
            for c in obj.get_children():
                all_children.append(c)
                collect(c)
        collect(dir_parent_obj)
        for c in all_children:
            if c.get_name() == parent_name and get_object_type(c) == ObjectType.INTERFACE:
                parent_obj = c
                break
    
    if parent_obj is None:
        # Старый поиск внутри POU для интерфейсов-папок
        for obj in dir_parent_obj.get_children():
            if get_object_type(obj) == ObjectType.POU:
                interface_folder = first_of_type_or_none(obj.find(parent_name), ObjectType.FOLDER)
                if interface_folder is not None:
                    parent_obj = interface_folder
                    break
    
    if parent_obj is None:
        raise ValueError(parent_name + " should have been created, but cannot be found")
    
    child_name = filename.split(".")[-1]
    read_native(full_path, parent_obj)
    # Логирование созданного объекта
    for obj in parent_obj.get_children():
        if obj.get_name() == child_name:
            log_import_object(obj, "import_sub_pou (%s)" % child)
            break


OBJECT_TYPE_TO_EXPORT_FUNCTION = {
    # Существующие типы
    ObjectType.FOLDER: export_folder,
    ObjectType.POU: export_pou,
    ObjectType.GVL: export_gvl,
    ObjectType.EVC: export_native,
    ObjectType.VISUALISATION: export_native_recursive,
    ObjectType.TASK_CONFIGURATION: export_native_recursive,
    ObjectType.DUT: export_dut,
    ObjectType.METHOD: export_method,
    ObjectType.PROPERTY: export_sub_pou,
    ObjectType.ACTION: export_sub_pou,
    ObjectType.TRANSITION: export_sub_pou,

    # Новые типы из обновлённого маппинга
    ObjectType.PLC_LOGIC: export_native_recursive,
    ObjectType.APPLICATION: export_native_recursive,
    ObjectType.TASK: export_native_recursive,
    ObjectType.VISUALIZATION_MANAGER: export_native_recursive,
    ObjectType.WEB_VISUALIZATION: export_native_recursive,
    ObjectType.ALARM_CONFIGURATION: export_native_recursive,
    ObjectType.ALARM_GROUP: export_native_recursive,
    ObjectType.ALARM_CLASS: export_native_recursive,
    ObjectType.ALARM_STORAGE: export_native_recursive,
    ObjectType.PERSISTENT: export_native_recursive,
    ObjectType.TEXT_LIST: export_native,
    ObjectType.IMAGE_POOL: export_native,
    ObjectType.INTERFACE: export_pou,
    ObjectType.INTERFACE_METHOD: export_method,
    ObjectType.GET_ACCESSOR: export_method,
    ObjectType.INTERFACE_GET_ACCESSOR: export_method,
    ObjectType.ABSTRACT_CLASS_METHOD: export_method,
    ObjectType.RESOURCE: export_native,
    ObjectType.EXTERNAL_FILE: export_native,
    ObjectType.ADDITIONAL_DEVICE: export_native_recursive,
    ObjectType.VISUALIZATION_STYLE: export_native,
    ObjectType.GLOBAL_TEXT_LIST: export_native,
    ObjectType.CALL_TO_POU: export_native,
}


def remove_tracked_objects(obj_list):
    for obj in obj_list:
        if get_object_type(obj) in OBJECT_TYPE_TO_EXPORT_FUNCTION:
            print("Removing " + obj.get_name())
            obj.remove()