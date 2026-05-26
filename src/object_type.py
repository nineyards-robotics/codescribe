# -*- coding: utf-8 -*-
# REMEMBER: this is python 2.7
import inspect


class ObjectType:
    POU = "POU"
    DUT = "DUT"
    GVL = "EVL"
    EVC = "EVC"
    METHOD = "METHOD"
    PROPERTY = "PROPERTY"
    ACTION = "ACTION"
    TRANSITION = "TRANSITION"
    LIBRARY_MANAGER = "LIBRARY_MANAGER"
    TASK_CONFIGURATION = "TASK_CONFIGURATION"
    PROJECT_INFORMATION = "PROJECT_INFORMATION"
    PROJECT_SETTINGS = "PROJECT_SETTINGS"
    DEVICE = "DEVICE"
    FOLDER = "FOLDER"
    CALL_TO_POU = "CALL_TO_POU"
    VISUALISATION = "VISUALISATION"

    # Новые типы, обнаруженные в проекте
    PLC_LOGIC = "PLC_LOGIC"
    TEXT_LIST = "TEXT_LIST"
    INTERFACE_METHOD = "INTERFACE_METHOD"
    PERSISTENT = "PERSISTENT"
    IMAGE_POOL = "IMAGE_POOL"
    ALARM_GROUP = "ALARM_GROUP"
    ALARM_CLASS = "ALARM_CLASS"
    ALARM_STORAGE = "ALARM_STORAGE"
    GET_ACCESSOR = "GET_ACCESSOR"
    ABSTRACT_CLASS_METHOD = "ABSTRACT_CLASS_METHOD"
    INTERFACE_GET_ACCESSOR = "INTERFACE_GET_ACCESSOR"
    EXTERNAL_FILE = "EXTERNAL_FILE"
    ADDITIONAL_DEVICE = "ADDITIONAL_DEVICE"
    APPLICATION = "APPLICATION"
    INTERFACE = "INTERFACE"
    TASK = "TASK"
    VISUALIZATION_MANAGER = "VISUALIZATION_MANAGER"
    WEB_VISUALIZATION = "WEB_VISUALIZATION"
    ALARM_CONFIGURATION = "ALARM_CONFIGURATION"
    RESOURCE = "RESOURCE"
    VISUALIZATION_STYLE = "VISUALIZATION_STYLE"
    GLOBAL_TEXT_LIST = "GLOBAL_TEXT_LIST"

    UNKNOWN = "UNKNOWN"

    @classmethod
    def __iter__(cls):
        elements = []
        for member, value in inspect.getmembers(cls):
            if not member.startswith("_") and not inspect.ismethod(value):
                elements.append(value)
        return elements


# Other mapping lists:
# https://github.com/tkucic/codesys_workflow_automation/blob/main/src/codesysBulker.py#L9
# https://github.com/18thCentury/CodeSys/blob/master/export.py#L10

GUID_TYPE_MAPPING = {
    # Существующие GUID
    "6f9dac99-8de1-4efc-8465-68ac443b7d08": ObjectType.POU,
    "2db5746d-d284-4425-9f7f-2663a34b0ebc": ObjectType.DUT,
    "ffbfa93a-b94d-45fc-a329-229860183b1d": ObjectType.GVL,
    "327b6465-4e7f-4116-846a-8369c730fd66": ObjectType.EVC,
    "f8a58466-d7f6-439f-bbb8-d4600e41d099": ObjectType.METHOD,
    "5a3b8626-d3e9-4f37-98b5-66420063d91e": ObjectType.PROPERTY,
    "8ac092e5-3128-4e26-9e7e-11016c6684f2": ObjectType.ACTION,
    "a10c6218-cb94-436f-91c6-e1652575253d": ObjectType.TRANSITION,
    "adb5cb65-8e1d-4a00-b70a-375ea27582f3": ObjectType.LIBRARY_MANAGER,
    "ae1de277-a207-4a28-9efb-456c06bd52f3": ObjectType.TASK_CONFIGURATION,
    "085afe48-c5d8-4ea5-ab0d-b35701fa6009": ObjectType.PROJECT_INFORMATION,
    "8753fe6f-4a22-4320-8103-e553c4fc8e04": ObjectType.PROJECT_SETTINGS,
    "225bfe47-7336-4dbc-9419-4105a7c831fa": ObjectType.DEVICE,
    "738bea1e-99bb-4f04-90bb-a7a567e74e3a": ObjectType.FOLDER,
    "413e2a7d-adb1-4d2c-be29-6ae6e4fab820": ObjectType.CALL_TO_POU,
    "f18bec89-9fef-401d-9953-2f11739a6808": ObjectType.VISUALISATION,

    # Новые GUID из проекта
    "40b404f9-e5dc-42c6-907f-c89f4a517386": ObjectType.PLC_LOGIC,
    "639b491f-5557-464c-af91-1471bac9f549": ObjectType.APPLICATION,
    "6654496c-404d-479a-aad2-8551054e5f1e": ObjectType.INTERFACE,           # Моторы
    "f89f7675-27f1-46b3-8abb-b7da8e774ffd": ObjectType.INTERFACE_METHOD,    # start
    "2bef0454-1bd3-412a-ac2c-af0f31dbc40f": ObjectType.TEXT_LIST,           # Rejim_heat
    "98a2708a-9b18-4f31-82ed-a1465b24fa2d": ObjectType.TASK,                # VISU_TASK
    "261bd6e6-249c-4232-bb6f-84c2fbeef430": ObjectType.PERSISTENT,          # Pr (глобальные ссылки)
    "bb0b9044-714e-4614-ad3e-33cbdf34d16b": ObjectType.IMAGE_POOL,          # Triline
    "c0a56ce5-14a3-4757-ac56-3eab44c974b3": ObjectType.ALARM_CONFIGURATION,
    "21f4ed1d-ec95-4666-820e-4abf64d93d6b": ObjectType.ALARM_GROUP,         # Alarm_con
    "b8b46f61-c7c1-4259-87e4-26fe674798f9": ObjectType.ALARM_CLASS,         # Info
    "5bd56248-46fc-4108-be33-ed01ad87d070": ObjectType.ALARM_STORAGE,       # AlarmStorage
    "792f2eb6-721e-4e64-ba20-bc98351056db": ObjectType.GET_ACCESSOR,        # Get
    "62ebfd1c-d342-43e5-8efb-f22b6d8e4a04": ObjectType.ABSTRACT_CLASS_METHOD,   # init
    "28747452-a93d-4b34-8d05-d2c6018edd7d": ObjectType.INTERFACE_GET_ACCESSOR,  # Get (другой)
    "a56744ff-693f-4597-95f9-0e1c529fffc2": ObjectType.EXTERNAL_FILE,       # favicon
    # "8e687a04-7ca7-42d3-be06-fcbda676c5ef": ObjectType.VISUALIZATION_STYLE,
    # "4d3fdb8f-ab50-4c35-9d3a-d4bb9bb9a628": ObjectType.VISUALIZATION_MANAGER,
    # "0fdbf158-1ae0-47d9-9269-cd84be308e9d": ObjectType.WEB_VISUALIZATION,
    "085766fd-043e-4545-8e8d-d651d56d5d3b": ObjectType.ADDITIONAL_DEVICE,   # PLC210_03
    "63784cbb-9ba0-45e6-9d69-babf3f040511": ObjectType.GLOBAL_TEXT_LIST,
    "9001d745-b9c5-4d77-90b7-b29c3f77a23b": ObjectType.RESOURCE,      # изображение sun_650x450.jpg
}


def get_object_type(obj):
    return GUID_TYPE_MAPPING.get(str(obj.type), ObjectType.UNKNOWN)