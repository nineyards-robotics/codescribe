# REMEMBER: this is python 2.7
import io
import os

from communication_import_export import import_communication
from entrypoint import get_content_targets, get_src_folder, is_library
from import_export import *
from manifest import compute_hashes, diff, get_manifest_path, load_manifest, save_manifest
from object_type import ObjectType
from util import *


def first_word_of_line_iter(f):
    for line in f.readlines():
        words = line.strip().split()
        if len(words) > 0:
            yield words[0]


def import_directory(dir_path, dir_parent_obj):
    children = os.listdir(dir_path)
    # this is a naughty way to ensure parent POU's are created before their children
    for child in sorted(children, key=lambda x: x.count(".")):
        import_directory_child(child, dir_path, dir_parent_obj)


def import_directory_child(child, dir_path, dir_parent_obj):
    full_path = os.path.join(dir_path, child)
    filename, ext = os.path.splitext(child)

    if os.path.isdir(full_path):
        import_folder(child, dir_path, dir_parent_obj, import_directory)

    if filename.endswith(".gvl"):
        if ext == ".xml":
            # this is just here to point out that the xml is imported alongside the st file
            pass
        if ext == ".st":
            import_gvl(child, dir_path, dir_parent_obj, import_directory)
    elif "." in filename:
        # . means some sort of sub POU
        if ext == ".xml":
            import_sub_pou(child, dir_path, dir_parent_obj, import_directory)
        if ext == ".st":
            # currently only methods are exported as ST if possible
            import_method_st(child, dir_path, dir_parent_obj, import_directory)
    else:
        if ext == ".xml":
            import_native(child, dir_path, dir_parent_obj, import_directory)
        if ext == ".st":
            # Have to check for keywords to determine if POU or DUT
            with io.open(full_path, "r", encoding="utf-8") as f:
                for word in first_word_of_line_iter(f):
                    if word == "TYPE":
                        import_dut(child, dir_path, dir_parent_obj, import_directory)

                    if word in ["PROGRAM", "FUNCTION_BLOCK", "FUNCTION"]:
                        import_pou_st(child, dir_path, dir_parent_obj, import_directory)


# --------------------------------------------------------------------------- #
# Incremental / subfolder import helpers
# --------------------------------------------------------------------------- #


def _remove_existing(parent_obj, name):
    for obj in parent_obj.find(name):
        obj.remove()


def get_or_create_folder_chain(content_obj, dir_parts):
    """Descend (creating as needed) the folder objects named by dir_parts and
    return the leaf folder object. An empty dir_parts returns content_obj."""
    parent = content_obj
    for part in dir_parts:
        existing = first_of_type_or_none(parent.find(part), ObjectType.FOLDER)
        if existing is None:
            parent.create_folder(part)
            existing = first_of_type_or_error(
                parent.find(part), ObjectType.FOLDER, "Folder " + part + " could not be created"
            )
        parent = existing
    return parent


def _resolve_folder_chain(content_obj, dir_parts):
    """Like get_or_create_folder_chain but returns None if a folder is missing."""
    parent = content_obj
    for part in dir_parts:
        existing = first_of_type_or_none(parent.find(part), ObjectType.FOLDER)
        if existing is None:
            return None
        parent = existing
    return parent


def _remove_existing_for_child(child, dir_parent_obj):
    """Remove the project object that import_directory_child would (re)create for
    the given file name, so that an import can replace it in place."""
    filename, ext = os.path.splitext(child)

    if filename.endswith(".gvl"):
        if ext == ".st":
            _remove_existing(dir_parent_obj, filename.replace(".gvl", ""))
    elif "." in filename:
        parent_name = filename.split(".")[0]
        child_name = filename.split(".")[1] if len(filename.split(".")) > 1 else None
        parent_obj = first_of_type_or_none(dir_parent_obj.find(parent_name), ObjectType.POU)
        if parent_obj is not None and child_name is not None:
            _remove_existing(parent_obj, child_name)
    else:
        _remove_existing(dir_parent_obj, filename)


def upsert_import_file(rel_path, src_folder, content_obj):
    """Import a single file (given relative to src_folder), replacing any
    existing object of the same name. Creates parent folders as needed."""
    parts = rel_path.split("/")
    dir_parts, filename = parts[:-1], parts[-1]

    # GVL is a pair of files; the .st drives the import and pulls in the .xml.
    if filename.endswith(".gvl.xml"):
        filename = filename[: -len(".xml")] + ".st"

    parent = get_or_create_folder_chain(content_obj, dir_parts)
    dir_path = os.path.join(src_folder, *dir_parts) if dir_parts else src_folder

    _remove_existing_for_child(filename, parent)
    import_directory_child(filename, dir_path, parent)


def remove_object_for_file(rel_path, content_obj):
    """Remove the project object corresponding to a file that no longer exists."""
    parts = rel_path.split("/")
    dir_parts, filename = parts[:-1], parts[-1]

    # The .gvl.xml half of a GVL pair is removed together with the .st half.
    if filename.endswith(".gvl.xml"):
        return

    parent = _resolve_folder_chain(content_obj, dir_parts)
    if parent is None:
        return

    _remove_existing_for_child(filename, parent)


def _sort_key_parents_first(rel_path):
    # folders/parents first, then by dotted depth of the file name so that a
    # POU is created before its methods/actions
    return (rel_path.count("/"), os.path.basename(rel_path).count("."))


def incremental_import(content_obj, src_folder, subfolder, manifest_path, force_full):
    """Import a library content root using the file-hash manifest so that only
    changed/new files are imported and deleted files are removed. Falls back to a
    full import when there is no usable manifest. Returns True if handled."""
    new_hashes = compute_hashes(src_folder, subfolder)
    old_hashes = None if force_full else load_manifest(manifest_path)

    scope_prefix = None if subfolder is None else subfolder.replace(os.sep, "/").rstrip("/") + "/"

    def in_scope(rel):
        return scope_prefix is None or rel.startswith(scope_prefix)

    if old_hashes is None:
        # No baseline: do a full (re)build of the scope.
        if subfolder is None:
            remove_tracked_objects(content_obj.get_children())
            import_directory(src_folder, content_obj)
        else:
            for rel in sorted(new_hashes.keys(), key=_sort_key_parents_first):
                upsert_import_file(rel, src_folder, content_obj)
        merged = dict(load_manifest(manifest_path) or {})
        merged.update(new_hashes)
        save_manifest(manifest_path, merged)
        return

    scoped_old = dict((k, v) for k, v in old_hashes.items() if in_scope(k))
    changed, deleted = diff(scoped_old, new_hashes)

    # diff() lumps new files in with changed ones; split them apart for the log.
    new_files = sorted(rel for rel in changed if rel not in scoped_old)
    modified_files = sorted(rel for rel in changed if rel in scoped_old)

    print(
        "Incremental import: %d new, %d changed, %d deleted"
        % (len(new_files), len(modified_files), len(deleted))
    )
    for rel in new_files:
        print("  + new:     " + rel)
    for rel in modified_files:
        print("  ~ changed: " + rel)
    for rel in sorted(deleted):
        print("  - deleted: " + rel)

    for rel in sorted(deleted):
        remove_object_for_file(rel, content_obj)

    for rel in sorted(changed, key=_sort_key_parents_first):
        upsert_import_file(rel, src_folder, content_obj)

    merged = dict(old_hashes)
    for rel in deleted:
        merged.pop(rel, None)
    merged.update(new_hashes)
    save_manifest(manifest_path, merged)


def import_from_files(project, subfolder=None, force_full=False):
    src_folder = get_src_folder(project)
    print("Reading from: " + src_folder)
    assert_path_exists(src_folder)

    if subfolder is not None:
        assert_path_exists(os.path.join(src_folder, subfolder))

    if is_library(project):
        # Libraries are a single content root, so we can import incrementally and
        # optionally scope to a subfolder.
        manifest_path = get_manifest_path(project.path, src_folder)
        incremental_import(project, src_folder, subfolder, manifest_path, force_full)
        return

    # Standard projects: full import per device (existing behaviour).
    for target in get_content_targets(project, src_folder):
        assert_path_exists(target.content_folder)
        remove_tracked_objects(target.content_obj.get_children())
        import_directory(target.content_folder, target.content_obj)
        if target.communication_obj is not None:
            import_communication(target.communication_obj, os.path.dirname(target.content_folder))
