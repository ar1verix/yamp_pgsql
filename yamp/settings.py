# -*- coding: UTF-8 -*-
import os.path

SMI = {
    "FieldTypeId": 11,
    "FieldName": "SMI",
    "PositionId": 0,
    "Mandatory": True,
    "DataFormatId": 0,
    "DelOccurrence": 2,
    "StartId": "\u0002",
    "UntilEnd": False,
    "Offset": 0,
    "Length": 3,
    "LookupTableId": 0,
    "DynRoutId": 0,
    "UnitId": 0,
    "UnitMultiplier": 1.0,
    "EndOffset": 0,

}

LONG_REGISTRATION = {
    "FieldTypeId": 14,
    "FieldName": "Long registration",
    "PositionId": 2,
    "Mandatory": False,
    "DataFormatId": 0,
    "DelOccurrence": 0,
    "StartId": "AN ",
    "EndId1": "/",
    "EndId2": "\r\n",
    "EndId3": "\\",
    "UntilEnd": False,
    "Offset": 0,
    "Length": 0,
    "LookupTableId": 0,
    "DynRoutId": 0,
    "UnitId": 0,
    "UnitMultiplier": 1.0,
    "EndOffset": 0,
}

SMI_UPLINK_ANSWER = 'MAS'

FormatTypeAlphanumeric = 0
FormatTypeDatetime = 1
FormatTypeNumeric = 2
FormatTypeLatLon = 3
FormatTypeBoolean = 4

TemplateSchema = os.path.join(os.path.dirname(__file__), 'template.json')
ModelSchema = os.path.join(os.path.dirname(__file__), 'model.json')

BaseFormatDateTimeIn = '%Y-%m-%dT%H:%M:%SZ'
BaseFormatDateTimeOut = 'DDHHNN'

FileAircraftFleetsPath = os.path.join('settings', 'aircraft_fleets.json')
FileAircraftTypesPath = os.path.join('settings', 'aircraft_types.json')
FileDataFormatsPath = os.path.join('settings', 'data_formats.json')
FileFieldTypesPath = os.path.join('settings', 'field_types.json')
FileLookupTablesPath = os.path.join('settings', 'lookup_tables.json')
FileLookupItemsPath = os.path.join('settings', 'lookup_items.json')
FilePredefinedFieldsPath = os.path.join('settings', 'predefined_fields.json')
FileCustomFieldsPath = os.path.join('settings', 'custom_fields.json')


