# REMEMBER: this is python 2.7
from object_type import ObjectType, get_object_type
from util import *

LIBRARY_EXTENSION = ".library"


def get_src_folder(project):
    working_dir = os.path.dirname(project.path)
    project_name, project_extension = os.path.splitext(os.path.basename(project.path))
    src_folder = os.path.join(working_dir, project_name)

    return src_folder


def get_device_entrypoints(project):
    children = project.get_children()
    for child in children:
        if len(child.get_children()) < 1:
            continue

        if get_object_type(child) != ObjectType.DEVICE:
            continue

        yield child



def is_library(project):
    """A project is treated as a library if it has the .library extension, or
    (as a fallback for unusual project layouts) if it contains no devices."""
    _, ext = os.path.splitext(project.path)
    if ext.lower() == LIBRARY_EXTENSION:
        return True
    return len(list(get_device_entrypoints(project))) < 1


def find_application(device_obj):
    return first_or_error(
        device_obj.find("Application", recursive=True),
        "Couldn't find Application inside " + device_obj.get_name(),
    )


def find_communication(device_obj):
    return first_or_error(
        device_obj.find("Communication", recursive=True),
        "Couldn't find Communication inside " + device_obj.get_name(),
    )


class ContentTarget(object):
    """A single unit of work for export/import/clean operations.

    content_obj      the project object whose children are the tracked objects
    content_folder   the folder on disk those objects map to
    communication_obj the Communication node to handle, or None (libraries)
    """

    def __init__(self, content_obj, content_folder, communication_obj=None):
        self.content_obj = content_obj
        self.content_folder = content_folder
        self.communication_obj = communication_obj


def find_folder(content_obj, rel_parts):
    """Descend the folder objects named by rel_parts and return the leaf folder.
    Raises if any part is missing or is not a folder."""
    obj = content_obj
    for part in rel_parts:
        obj = first_of_type_or_error(
            obj.find(part), ObjectType.FOLDER, "Subfolder '" + part + "' not found in project"
        )
    return obj


def get_content_targets(project, src_folder):
    """Yield the ContentTargets to operate on.

    For a library the whole project root maps to the src folder. For a standard
    project each device maps to <src>/<device>/application, with its
    communication node handled alongside.
    """
    if is_library(project):
        yield ContentTarget(project, src_folder)
        return

    for device_obj in get_device_entrypoints(project):
        device_folder = os.path.join(src_folder, device_obj.get_name())
        application = find_application(device_obj)
        application_folder = os.path.join(device_folder, "application")
        communication = find_communication(device_obj)
        yield ContentTarget(application, application_folder, communication)
