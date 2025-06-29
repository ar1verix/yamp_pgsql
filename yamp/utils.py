# -*- coding: UTF-8 -*-
"""
Helper functions for the operation of modules.
"""
import copy
import datetime
import json
import os.path
import re
import shutil
from typing import List, Optional, Union

from dms2dec.dms_convert import dms2dec

from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from yamp.settings import FormatTypeAlphanumeric, FormatTypeNumeric, FormatTypeDatetime, FormatTypeLatLon


def find_all_index_substr(string: str, substring: str) -> List[int]:
    """
    This method find all substring in string and return list indexes start substring.
    :param string: String for find.
    :param substring: Substring for sinf.
    :return: list indexes start substring.
    """
    return [m.start() for m in re.finditer(re.escape(substring), string)]


def load_file(path: str, new_line: str = '\r\n') -> Union[str, List[str]]:
    """
    This method load file or files to memory.
    :param path: path to file or path to directory.
    :param new_line: separator from new line in file. Default: '\r\n'
    :return: - If file - return text from file (format - str);
             - If directory - return list texts from files (format list);
             - If not exist file or directory - return path (format str)
    """
    if not isinstance(path, str):
        raise ValueError('Parameter <path> is not string. <Path> is path to file, path to directory files or message.')
    if os.path.isdir(path):
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        ret = []
        for f in files:
            with open(
                    (os.path.join(path, f)), "r", encoding="utf-8", newline=new_line,
            ) as file_obj:
                ret.append(file_obj.read())
        return ret
    if os.path.isfile(path):
        with open(
                path, "r", encoding="utf-8", newline=new_line,
        ) as file_obj:
            return file_obj.read()
    return path


def load_json(path_file: str) -> Union[dict, List[dict]]:
    """
    Load data from JSON-file to memory to object dict.
    :param path_file: path to input file
    :return: dictionary
    """
    with open(path_file, 'r', encoding='utf-8') as file:
        result = json.load(file)
    return result


def write_json(path_file: str, data: dict):
    """
    Write dictionary to JSON.
    :param path_file: path out file.
    :param data: dictionary with data.
    """
    with open(path_file, 'w') as outfile:
        json.dump(data, outfile, indent=4)


def write_file(path_file: str, text: str):
    with open(path_file, 'w', encoding='utf-8') as file:
        file.write(text.replace('\r\n', '\n'))


def not_none_value(value_1, value_2):
    """
    Check two values on None or not None.
    :return: - If value_1 and value_2 are None - None;
             - If value_1 is not None and value_2 is None - value_1;
             - If value_2 is not None and value_1 is None - value_2;
             - If value_1 and value_2 are not None - value_1;
    """
    if value_1 is None and value_2 is None:
        return None
    return value_1 if value_2 is None else value_2


def get_hash_smi(dict_value: dict):
    """
    This method get hash templates_downlink with help smi and all subsmis.
    :param dict_value: dictionary templates_downlink.
    :return: hash.
    """
    tmp = f'{dict_value.get("SMI")}'
    # Get all SubSMI.
    fields = list(filter(lambda x: "SubSMI" in x.get("FieldName", ''), dict_value.get('Fields', [])))
    for i in fields:
        a = copy.deepcopy(i)
        smi = dict_value.get(a.get('FieldName', '').replace(" ", ""))
        a.pop('TemplateFieldId')
        a.pop("TemplateId")
        a.pop("FieldName")
        keys = sorted(list(a.keys()))
        tmp += smi
        for key in keys:
            tmp += str(a.get(key))
    return hash(tmp)


def is_69(message):
    """
    This method return message in one line if all lines have 69 simbols.
    :param message: string message.
    :return: string message one line.
    """
    try:
        te_line, free_text = message.split('-  ', 1)
    except ValueError:
        raise ValueError('Not found delimiter "-  " in file: ')
    f = '-  ' + free_text
    str_len = f.split('\r\n')
    count_row = sum([1 for i in str_len[0:-1] if len(i) == 69])
    if count_row > 1:
        return ''.join([te_line, ' '.join(str_len)]).replace('\x03', '')
    return message


def check_json_to_schema(json_data: dict, json_schema: dict):
    """
    This method check JSON to schema.
    """
    try:
        validate(json_data, json_schema)
    except ValidationError as error:
        return error.message
    return None


def remove_directory(path_dir: str):
    """
    This method removes all directories.
    :param path_dir: path to directory where removed all files.
    """
    dirs = os.listdir(path_dir)
    if dirs:
        for file in dirs:
            if os.path.isdir(os.path.join(path_dir, file)):
                shutil.rmtree(os.path.join(path_dir, file))
            else:
                os.remove(os.path.join(path_dir, file))
    return


def get_all_parent_types(id_type: int, aircraft_types: dict) -> List[int]:
    """
    Get list identifier type and subtypes aircraft.
    :param id_type: identifier aircraft type.
    :param aircraft_types: dictionary aircraft type and his parent.
    :return: list all types.
    """
    id_type_now = id_type
    result = []
    while id_type_now is not None:
        result.append(id_type_now)
        id_type_now = aircraft_types.get(id_type_now)
    return result


def dict_type_parent(aircraft_types: List[dict]) -> dict:
    return {aircraft_type.get("AircraftTypeId"): (aircraft_type.get("Parent")) for aircraft_type in aircraft_types}


def to_date(in_format: str, value: str) -> str:
    """
    Convert Aircom's formats datetime to ISO 8601.
    Example ISO 8601: 2024-08-20T09:10:41Z.
    :param in_format: format Aircom.
    :param value: value from message.
    :return: datetime to format ISO 8601.
    """
    python_in_format = in_format
    result = '%Y-%m-%dT%H:%M:%SZ'
    if "XML" in in_format:
        python_in_format = result
    else:
        if "DD" in in_format:
            python_in_format = python_in_format.replace("DD", "%d")
        else:
            result = result.replace("%d", '00')
        if "MM" in in_format and "MMM" not in in_format:
            python_in_format = python_in_format.replace("MM", "%m")
        if "MM" not in in_format:
            result = result.replace("%m", '00')
        if "MMM" in in_format:
            python_in_format = python_in_format.replace("MMM", "%b")
        if "YY" in in_format and "YYYY" not in in_format:
            python_in_format = python_in_format.replace("YY", "%y")
        if "YY" not in in_format:
            result = result.replace("%Y", '0000')
        if "YYYY" in in_format:
            python_in_format = python_in_format.replace("YYYY", "%Y")
        if "HH" in in_format:
            python_in_format = python_in_format.replace("HH", "%H")
        else:
            result = result.replace("%H", '00')
        if "NN" in in_format:
            python_in_format = python_in_format.replace("NN", "%M")
        else:
            result = result.replace("%M", '00')
        if "SS" in in_format:
            python_in_format = python_in_format.replace("SS", "%S")
        else:
            result = result.replace("%S", '00')
    date_time = datetime.datetime.strptime(value, python_in_format)
    return date_time.strftime(result)


def convert_date_format(aircom_format: str) -> str:
    """
    Method convert aircom format to python format.
    :param aircom_format: aircom format date.
    :return: python format date.
    """
    if "XML" in aircom_format:
        return '%Y-%m-%dT%H:%M:%SZ'
    return_format = aircom_format
    if "DD" in aircom_format:
        return_format = return_format.replace("DD", "%d")
    if "MM" in aircom_format and "MMM" not in aircom_format:
        return_format = return_format.replace("MM", "%m")
    if "MMM" in aircom_format:
        return_format = return_format.replace("MMM", "%b")
    if "YY" in aircom_format and "YYYY" not in aircom_format:
        return_format = return_format.replace("YY", "%y")
    if "YYYY" in aircom_format:
        return_format = return_format.replace("YYYY", "%Y")
    if "HH" in aircom_format:
        return_format = return_format.replace("HH", "%H")
    if "NN" in aircom_format:
        return_format = return_format.replace("NN", "%M")
    if "SS" in aircom_format:
        return_format = return_format.replace("SS", "%S")
    return return_format


def to_coordinate(in_format: str, value: str):
    """
    This method convert string coordinate to float value by tamplate.
    :param in_format: format Aircom.
    :param value: value from message.
    :return: coordinate to float.
    """
    python_in_format = in_format
    result = 0
    degree = ""
    minutes = ""
    seconds = ""
    format_split = in_format.split('.')
    value_split = value.split('.')
    if len(format_split) != len(value_split):
        raise ValueError("Bad format")
    for format_part, value_part in zip(format_split, value_split):
        if len(format_part) != len(value_part):
            raise ValueError("Bad format")
    if "DD.dd" in python_in_format:
        hemisphere = value[python_in_format.find("A")] if "A" in python_in_format else ''
        result = float(value.replace(hemisphere, ''))
        if result >= 90 and hemisphere in ("N", "S"):
            raise ValueError("Bad Lat.")
        if result >= 180:
            raise ValueError("Bad Lon.")
        if hemisphere in ("W", "S", "-"):
            return -1 * result
        return result
    if "A" in python_in_format:
        hemisphere = value[python_in_format.find("A")]
        if hemisphere in ("N", "E", "+"):
            result = 1
        elif hemisphere in ("W", "S", "-"):
            result = -1
    if "DD" in python_in_format:
        if "DDD" in python_in_format:
            index_start_degree = python_in_format.find("DDD")
        else:
            index_start_degree = python_in_format.find("DD")
        count_simbols = 3 if "DDD" in python_in_format else 2
        degree = value[index_start_degree:index_start_degree+count_simbols]
    if "dd" in python_in_format:
        index_start_d = python_in_format.find("dd")
        count_simbols = 3 if "ddd" in python_in_format else 2
        degree += "." + value[index_start_d:index_start_d+count_simbols]
    if "MM" in python_in_format:
        index_start_minute = python_in_format.find("MM")
        minutes = value[index_start_minute:index_start_minute+2]
    if "m" in python_in_format:
        index_start_m = python_in_format.find("m")
        count_simbols = 2 if "mm" in python_in_format else 1
        minutes += "." + value[index_start_m:index_start_m+count_simbols]
    if "SS" in python_in_format:
        index_start_sec = python_in_format.find("SS")
        count_simbols = 6 if "SSSSSS" in python_in_format else 2
        seconds = value[index_start_sec:index_start_sec+count_simbols]
    if "s" in python_in_format:
        index_start_seconds = python_in_format.find("s")
        seconds += "." + value[index_start_seconds:index_start_seconds+1]
    degree_float = float(degree)
    if hemisphere in ('N', "S") and (degree_float >= 90.0 or degree_float <= -90.0):
        raise ValueError("Bad Lat.")
    if hemisphere in ('W', "E") and (degree_float >= 180.0 or degree_float <= -180.0):
        raise ValueError("Bad Lon.")
    if minutes == '' and seconds == '':
        return result * degree_float
    result = dms2dec(f"""{degree}°{minutes}'{seconds}"{hemisphere}""")
    return result


def get_predefined_fields(name_field, format_type):
    """
    Method get default value predefined fields.
    :param name_field: name field.
    :param format_type: format field: 0, 1, 2, 3, 4
    :return: value predefined fields.
    """
    if format_type == FormatTypeAlphanumeric:
        return 'XXXX'
    if format_type == FormatTypeNumeric:
        return 123.23
    if format_type == FormatTypeDatetime:
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    if format_type == FormatTypeLatLon:
        return 34.56
    return f"<{name_field}>"


def get_custom_fields(name_field, format_type):
    """
    Method get default value custom fields.
    :param name_field: name field.
    :param format_type: format field: 0, 1, 2, 3, 4
    :return: value custom fields.
    """
    if format_type == FormatTypeAlphanumeric:
        return 'YYYY'
    if format_type == FormatTypeNumeric:
        return 123.23
    if format_type == FormatTypeDatetime:
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    if format_type == FormatTypeLatLon:
        return 34.56
    return f"[{name_field}]"


def split_length(text: str, length: int) -> List[str]:
    return [text[i:i + length] for i in range(0, len(text), length)]