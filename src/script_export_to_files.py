# REMEMBER: this is python 2.7
from __future__ import print_function

import os
import shutil

import scriptengine  # type: ignore

from communication_import_export import export_communication
from entrypoint import find_folder, get_content_targets, get_src_folder, is_library
from import_export import OBJECT_TYPE_TO_EXPORT_FUNCTION, export_metadata
from manifest import compute_hashes, get_manifest_path, load_manifest, save_manifest
from object_type import get_object_type
from util import *


def export_child(child_obj, parent_obj, parent_folder_path):
    child_obj_type = get_object_type(child_obj)
    export_fn = OBJECT_TYPE_TO_EXPORT_FUNCTION.get(child_obj_type)
    if export_fn is not None:
        export_fn(child_obj, parent_obj, parent_folder_path, export_child)


def export_content(project, dest_root):
    """Export all tracked content (and communication) into dest_root."""
    for target in get_content_targets(project, dest_root):
        if not os.path.isdir(target.content_folder):
            os.makedirs(target.content_folder)

        for child_obj in target.content_obj.get_children():
            export_child(child_obj, target.content_obj, target.content_folder)

        if target.communication_obj is not None:
            export_communication(target.communication_obj, os.path.dirname(target.content_folder))


def _remove_empty_dirs(root):
    for dirpath, _, _ in os.walk(root, topdown=False):
        if dirpath != root and not os.listdir(dirpath):
            os.rmdir(dirpath)


def sync_folder(temp_root, dest_root):
    """Copy only changed/new files from temp_root into dest_root and remove files
    in dest_root that no longer exist in temp_root. Returns (changed, new, removed)
    where each is a sorted list of relative paths."""
    if not os.path.isdir(dest_root):
        os.makedirs(dest_root)

    new_hashes = compute_hashes(temp_root)
    old_hashes = compute_hashes(dest_root)

    changed = []
    new = []
    removed = []
    for rel, h in new_hashes.items():
        if rel not in old_hashes:
            new.append(rel)
        elif old_hashes[rel] != h:
            changed.append(rel)
        else:
            continue
        dst_path = os.path.join(dest_root, *rel.split("/"))
        dst_dir = os.path.dirname(dst_path)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        shutil.copyfile(os.path.join(temp_root, *rel.split("/")), dst_path)

    for rel in old_hashes:
        if rel not in new_hashes:
            os.remove(os.path.join(dest_root, *rel.split("/")))
            removed.append(rel)

    _remove_empty_dirs(dest_root)
    return sorted(changed), sorted(new), sorted(removed)


def _print_sync_summary(changed, new, removed):
    """Print the count summary plus the individual files in each category."""
    print("Export: %d changed, %d new, %d removed" % (len(changed), len(new), len(removed)))
    for rel in new:
        print("  + new:     " + rel)
    for rel in changed:
        print("  ~ changed: " + rel)
    for rel in removed:
        print("  - removed: " + rel)


def export_all(project, src_folder):
    """Full export: wipe the source folder and write everything fresh."""
    print("Writing to: " + src_folder)
    if os.path.exists(src_folder):
        shutil.rmtree(src_folder)
    os.mkdir(src_folder)

    export_content(project, src_folder)
    export_metadata(project, src_folder)
    save_manifest(get_manifest_path(project.path, src_folder), compute_hashes(src_folder))


def export_incremental(project, src_folder):
    """Export to a temp folder, then write only changed/new files into the source
    folder and remove files whose objects no longer exist (clean git diffs)."""
    print("Writing to: " + src_folder + " (incremental)")
    temp_root = src_folder + ".codescribe_tmp"
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)
    os.mkdir(temp_root)

    try:
        export_content(project, temp_root)
        changed, new, removed = sync_folder(temp_root, src_folder)
        _print_sync_summary(changed, new, removed)
    finally:
        shutil.rmtree(temp_root)

    export_metadata(project, src_folder)
    save_manifest(get_manifest_path(project.path, src_folder), compute_hashes(src_folder))


def export_subfolder(project, src_folder, subfolder):
    """Re-export only one subfolder of a library, leaving the rest untouched.
    The manifest is updated for just this subfolder."""
    rel_parts = subfolder.replace("\\", "/").split("/")
    folder_obj = find_folder(project, rel_parts)

    dest = os.path.join(src_folder, *rel_parts)
    print("Writing subfolder to: " + dest)

    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)

    for child_obj in folder_obj.get_children():
        export_child(child_obj, folder_obj, dest)

    manifest_path = get_manifest_path(project.path, src_folder)
    merged = load_manifest(manifest_path) or {}
    prefix = "/".join(rel_parts) + "/"
    merged = dict((k, v) for k, v in merged.items() if not k.startswith(prefix))
    merged.update(compute_hashes(src_folder, os.path.join(*rel_parts)))
    save_manifest(manifest_path, merged)


try:
    print_python_version()
    assert_project_open()

    project = scriptengine.projects.primary
    src_folder = get_src_folder(project)

    subfolder = prompt_subfolder("export") if is_library(project) else None

    if subfolder is not None:
        export_subfolder(project, src_folder, subfolder)
    elif is_library(project):
        # Libraries: only write the files that actually changed since last export.
        export_incremental(project, src_folder)
    else:
        export_all(project, src_folder)

except Exception as e:
    print(e)
    raise e

print("Done!")
