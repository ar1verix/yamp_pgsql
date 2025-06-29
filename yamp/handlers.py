import os
import datetime
from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Union

import jinja2
from jinja2 import Undefined

from yamp.models import TemplateField, TemplateInfo, TemplateRecord, ModelField, ModelInfo
from yamp.exceptions import *
import yamp.settings as s
from yamp.utils import *


class ExceptionHandler:
    exceptions = []

    def _handler_exceptions(self, exception):
        name_exception = type(exception).__name__
        bases_exception = type(exception).__bases__
        name_bases_exceptions = [i.__name__ for i in bases_exception]
        types_bases = [self.exceptions_dict.get(i) for i in name_bases_exceptions]
        type_exception = self.exceptions_dict.get(name_exception)
        if type_exception is None and not any(types_bases):
            type_exception = [-7, 'Error. ']
        elif type_exception is None and any(types_bases):
            type_exception = types_bases[0]
        message = type_exception[1] + exception.__str__()
        return {
            'code': type_exception[0],
            'dsc': message
        }

    def _return_exceptions(self):
        exceptions = deepcopy(self.exceptions)
        self.exceptions = []
        return [self._handler_exceptions(exception) for exception in exceptions]


class YampBase(ExceptionHandler):
    """
    Base class for descriptor and parser.
    """
    value_free_text = '-  '  # Separator for Free Text and CI Line.
    separator_rows = '\r\n'

    def __init__(self, db_directory_path: str = None):
        if db_directory_path is None:
            raise ValueError("Not path to directory with database's files.")
        self.path_db = db_directory_path
        self.path_db_settings = os.path.join(self.path_db, 'settings')
        self.path_db_templates = os.path.join(self.path_db, 'templates')
        self.path_db_models = os.path.join(self.path_db, 'models')
        self.files_db = [os.path.join('settings', i) for i in os.listdir(self.path_db_settings)]
        self.long_registrations = self.check_file_in_db(s.FileAircraftFleetsPath)
        self.aircraft_types = self.check_file_in_db(s.FileAircraftTypesPath)
        self.aircraft_types_dict = dict_type_parent(self.aircraft_types)
        self.schema_template = load_json(s.TemplateSchema)
        self.schema_model = load_json(s.ModelSchema)
        self.messages = None
        self.type_message = None
        self.is_aeec_620 = None
        # self.schema = load_json('yamp/template.json')\

    def _identify_aeec620(self) -> bool:
        if self.value_free_text not in self.messages:
            return False
        te_line, _ = self.messages.split(self.value_free_text, 1)
        lines_header = te_line.split(self.separator_rows)
        first_row, second_row = lines_header[0], lines_header[1]
        words_in_first_row = first_row.split()
        if len(words_in_first_row[0]) != 2 or len(words_in_first_row) < 2:
            return False
        for word in words_in_first_row[1:]:
            if len(word) != 7:
                return False
        words_in_second_row = second_row.split()
        if words_in_second_row[0][0] != '.' or len(words_in_second_row[0]) != 8:
            return False
        return True

    def _type_message(self, message) -> int:
        self.te_line, self.free_text, self.index_start_free_text = self._split_message(message)
        if not self.is_aeec_620:
            return 2
        if len(self.te_line.split(self.separator_rows)) == 6:
            return 0
        return 2

    def _split_message(self, message: str) -> Tuple[str, str, int]:
        te_line, free_text = message.split(self.value_free_text, 1) if self.is_aeec_620 else ('', message)
        index_start_free_text = len(te_line) + len(self.value_free_text) if self.is_aeec_620 else 0
        return te_line, free_text, index_start_free_text

    def check_file_in_db(self, file_name: str):
        """
        Check exist file in directory db files.
        :param file_name: name file
        :return: dict
        :exception NotFileException
        """
        if file_name in self.files_db:
            path_to_file = os.path.join(self.path_db, file_name)
            return load_json(path_to_file)
        raise NotFileException(file_name)

    @staticmethod
    def extract_field(field: TemplateField, message: str) -> dict:
        """
        This method extracts one field in message.
        :param field: Template Field.
        :param message: text, which find template.
        :return: dictionary, where keys - field name, values - value field.
        """

        result = {}
        start_index = 0
        start_value = field.start_id
        index_start_in_message = message.find(start_value) if start_value is not None else 0
        if index_start_in_message == -1:
            if field.mandatory:
                # Error if the initial character of the required field is not found.
                raise NotStartIdInMessageParsingException(field.field_name, is_filed=True)
            else:
                return result
        start_index = start_index if start_value is None else index_start_in_message + len(start_value)
        delimiter, del_occurrence = field.delimiter, field.del_occurrence
        if delimiter and del_occurrence != 0:
            all_indexes = find_all_index_substr(message[start_index:], delimiter)
            if len(all_indexes) >= del_occurrence:
                index_occurrence = all_indexes[del_occurrence - 1]
                start_index += index_occurrence + len(delimiter)
            else:
                raise NotFoundDelimiterParsingException(field=field.field_name, is_filed=True)
        # 1.2. Search for delimiters and the start of the countdown from the desired one.
        # 1.3. Add value offset.
        start_index += field.offset
        # 2. Get the ending point of the Record block.
        end_index = len(message)
        # 2.1 Check for the EndId value.
        if not field.until_end:
            end_candidates = []
            for end_value in [field.end_id_1, field.end_id_2, field.end_id_3]:
                if end_value is None:
                    continue
                idx = message.find(end_value, start_index)
                if idx != -1:
                    end_candidates.append(idx)

            if end_candidates:
                end_index = min(end_candidates)
            elif any([field.end_id_1, field.end_id_2, field.end_id_3]) and field.length == 0:
                raise NotEndIdInMessageParsingException(field=field.field_name, is_filed=True)

        # 2.3 Delete value of endOffset.
        end_index -= field.end_offset
        if start_index <= end_index:
            # Get the desired block of message text.
            block_text = message[start_index:end_index]
            # Data selection by rec_start_id.
            if field.length != 0:
                # if field.length > len(block_text):
                #     # Error if the length of the field in the template is greater than the length of the message.
                #     raise BadLengthParsingException(field.field_name)
                block_text = block_text[:field.length]
            # t = block_text.replace('\x03', '').strip()
            if field.mandatory and block_text == '':
                raise NotMandatoryFieldParsingException(field.name)
            result[field.field_name] = block_text.replace('\x03', '').replace('', '')
            result['offset'] = start_index
        else:
            raise BadLengthParsingException(field.field_name)
        return result


class TemplateMatcher:

    def _extract_smi(self, message: str) -> str:
        template_field = TemplateField(s.SMI)
        result = self.extract_field(template_field, message)
        return result

    def _extract_subsmis(self, message: str, template: TemplateInfo) -> List[Dict[str, str]]:
        fields = [field for field in template.fields if 'SubSMI' in field.field_name]
        subsmis = []
        for field in fields:
            # te_line, free_text, index_free_text = self._split_message(message)
            text = self.free_text if field.position_id == 1 else self.te_line
            result_fields = self.extract_field(field, text)
            if result_fields:
                result_fields['offset'] += self.index_start_free_text if field.position_id == 1 else 0
            subsmis.append(result_fields)
        return subsmis

    def _extract_long_registration(self, message: str) -> Optional[str]:
        template_field_reg = TemplateField(s.LONG_REGISTRATION)
        try:
            reg_number = self.extract_field(template_field_reg, message)
        except Exception as error:
            self.exceptions.append(error)
            return None
        return reg_number if reg_number else {}

    def _extract_aircraft_types(self, reg_number: str | None) -> List[int]:
        if reg_number is None:
            return []
        result_query = list(
            filter(lambda x: reg_number.get('Long registration') in (x.get('AircraftReg'), x.get("AircraftNose")), self.long_registrations))
        if not result_query:
            self.exceptions.append(UnknownAircraftException(reg_number))
            return []
        id_type = result_query[0].get('AircraftTypeId', -1)
        return get_all_parent_types(id_type, self.aircraft_types_dict)

    def _match_smi(self, template: TemplateInfo, smi: str) -> bool:
        if template.smi is None:
            return False
        if '?' in template.smi:
            return re.fullmatch(template.smi.replace('?', '.'), smi) is not None
        return smi == template.smi

    def _match_subsmis(self, template: TemplateInfo, subsmis: Dict[str, str]) -> int:
        count = 0
        for i, subsmi_value in enumerate(subsmis, start=1):
            name_field = f'SubSMI {i}'
            template_subsmi = getattr(template, f"sub_smi_{i}", None)
            if template_subsmi and template_subsmi == subsmi_value.get(name_field):
                count += len(template_subsmi)
            if template_subsmi != subsmi_value.get(name_field):
                count = -1
                break
        return count

    def _match_long_registration(self, template: TemplateInfo, long_reg: str) -> int:
        if not template.long_registration:
            return 0
        if long_reg in template.long_registration:
            return 1
        return -1

    def _match_aircraft_types(self, template: TemplateInfo, aircraft_types: List[int]) -> int:
        if not template.aircraft_types:
            return 0
        result = int(any(t in template.aircraft_types for t in aircraft_types))
        if result == 0 and template.aircraft_types:
            return -1
        return result

    def _match_user(self, template: TemplateInfo, user_id: int | None) -> bool:
        return True if not template.users or user_id in template.users else False

    def _calculate_priority(self,
                            message: str,
                            template: TemplateInfo,
                            long_reg: str | None = None,
                            aircraft_types: List[int] | None = None,
                            subsmis: Dict[str, str] | None = None,
                            user_id: int | None = None) -> tuple:
        try:
            subsmis_temp = self._extract_subsmis(message, template) if subsmis is None else subsmis
            subsmi_score = self._match_subsmis(template, subsmis_temp)
            long_reg_match = self._match_long_registration(template, long_reg)
            aircraft_types_match = self._match_aircraft_types(template, aircraft_types)
            user_match = self._match_user(template, user_id)
        except ParsingException as error:
            return (-1, 0, 0, 0, template.template_id)
        priority = (
            subsmi_score,
            long_reg_match,
            aircraft_types_match,
            user_match,
            -template.template_id
        )
        return priority

    def _check_template_or_default(self, priority_template: tuple) -> bool:
        # smi, subsmi, long_registration, aircraft_type, id_template = priority_template
        subsmi, long_registration, aircraft_type, user_match, id_template = priority_template
        return not (
                # smi == -1 or subsmi == -1 or
                subsmi == -1 or
                (long_registration == -1 and aircraft_type <= 0) or
                (aircraft_type == -1 and long_registration <= 0) or
                not user_match
        )

    def sorter_priority(self, priority_template: tuple):
        priority = priority_template[0]
        is_match_template = self._check_template_or_default(priority)
        return (1, *priority) if is_match_template else (-1, *priority)

    def _best_template(self, scored_templates):
        scored_templates.sort(key=self.sorter_priority, reverse=True)

        if scored_templates:
            best_template = scored_templates[0][1] if self._check_template_or_default(
                scored_templates[0][0]) else self.get_default_template()
        else:
            best_template = self.get_default_template()
        return best_template

    def filter_templates(self):
        templates = [template for template in self.get_templates() if template.is_620_format == self.is_aeec_620]
        # get external user or from aircraft
        templates = [template for template in templates if template.source in (0, 1)]
        return templates

    def match_template(self, message: str, user_id: int | None = None) -> TemplateInfo:
        templates = self.filter_templates()
        long_reg, aircraft_types = {}, []
        if self.is_aeec_620:
            smi = self._extract_smi(message)
            long_reg = self._extract_long_registration(message)
            aircraft_types = self._extract_aircraft_types(long_reg)
            templates = [template for template in templates if self._match_smi(template, smi.get('SMI'))]

        scored_templates = [
            (self._calculate_priority(message, template, long_reg.get('Long registration'), aircraft_types,
                                      user_id=user_id), template)
            for template in templates
        ]
        best_template = self._best_template(scored_templates)

        return best_template

    def _get_aircraft_type(self, long_reg):
        aircraft_types = self._extract_aircraft_types(long_reg)
        aircraft_type = aircraft_types[0] if aircraft_types else -1
        return aircraft_types, {'Aircraft type': aircraft_type,
                                'offset': -1}

    def _get_result(self, subsmis, smi, long_reg, aircraft_type):
        result = {}
        if self.is_aeec_620:
            result["SMI"] = smi
            result["Long registration"] = long_reg
            result["Aircraft type"] = aircraft_type
        for subsmi in subsmis:
            name_field = list(filter(lambda x: "SubSMI" in x, subsmi.keys()))[0]
            result[name_field] = subsmi
        return result

    def check_message_by_template(self, message: str, template: TemplateInfo, id_user: int | None = None) -> Tuple[bool, Dict]:
        subsmis = self._extract_subsmis(message, template)
        smi, long_reg, aircraft_types, aircraft_type = None, {}, [], None
        if self.is_aeec_620:
            smi = self._extract_smi(message)
            if not self._match_smi(template, smi.get("SMI")):
                return False, {'SMI': smi}
            long_reg = self._extract_long_registration(message)
            aircraft_types, aircraft_type = self._get_aircraft_type(long_reg)

        scored_template = self._calculate_priority(message, template, long_reg, aircraft_types, subsmis, id_user)
        is_match_template = self._check_template_or_default(scored_template)
        # Get result aircraft type's identifier.
        return is_match_template, self._get_result(subsmis, smi, long_reg, aircraft_type)


class ParserHandler(TemplateMatcher):
    FREE_TEXT = 'free text'
    TE_LINE = 'te_line'
    ALL = 'all'

    dict_place_find = {
        FREE_TEXT: 1,
        TE_LINE: 2,
        ALL: 0
    }
    filters = {
        'Long registration': 0,
        'Aircraft type': 1,
    }

    exceptions_dict = {
        'FileNotFoundError': [-7, ''],
        'ValidateTemplateToSchemaException': [-1, "Bad template. "],
        'ValidateModelToSchemaException': [-1, "Bad model. "],
        'ParsingException': [-3, "Parsing error. "],
        'OutOfRangeHighException': [-6, "Out of range. "],
        'OutOfRangeLowException': [-6, "Out of range. "],
        'FormatException': [-4, "Format field error. "],
        'UnknownAircraftException': [-5, "Bad aircraft. "],
    }

    def _convert_filters(self, filters):
        result = {}
        for key, value in filters.items():
            result[key] = {}
            result[key]['original'] = str(value.get(key)) if value.get(key) is not None else None
            result[key]['internal'] = value.get(key)
            result[key]['offset'] = value.get('offset', -1)
        return result

    def _get_fields_for_place(self, fields: List[TemplateField], place: str) -> List[TemplateField]:
        """
        This method gets field in place in message.
        :param fields: list all fields.
        :param place: place in message ("free text", "ci line" , "all")
        :return: list TemplateField with position in message.
        """
        return list(filter(lambda x: x.position_id == self.dict_place_find[place], fields))

    def _extract_records(self, records: List[TemplateRecord], message_text: str) -> dict:
        """
        This method gets all records in messages.
        :param records: all records from database.
        :param message_text: text message.
        :return: dictionary with rows data in template records.
        """
        result = {}
        offset = 0
        index_free_text = message_text.find(self.value_free_text)
        if index_free_text == -1 and self.is_aeec_620:
            # The case when there is no Free Text.
            return result
        index_free_text = index_free_text + len(self.value_free_text) if self.is_aeec_620 else 0
        offset += index_free_text
        message = message_text[index_free_text:]
        for record in records:
            # Select the blocks Records.
            # 1. Get the starting point of the Record block.
            # 1.1. Check for the startId value.
            start_value = record.block_start_id
            index_start_in_message = message.find(start_value) if start_value is not None else 0
            if index_start_in_message == -1:
                self.exceptions.append(NotStartIdInMessageParsingException(field=record.rec_name, is_record=True))
                continue
            start_index = 0 if start_value is None else index_start_in_message + len(start_value)
            # 1.2. Search for delimiters and the start of the countdown from the desired one.
            delimiter, del_occurrence = record.delimiter, record.del_occurrence
            if delimiter and del_occurrence != 0:
                all_indexes = find_all_index_substr(message[start_index:], delimiter)
                if len(all_indexes) >= del_occurrence:
                    index_occurrence = all_indexes[del_occurrence - 1]
                    start_index += index_occurrence + len(delimiter)
                else:
                    # Error if the specified separator was not found.
                    self.exceptions.append(NotFoundDelimiterParsingException(field=record.rec_name, is_record=True))
                    continue
            # 1.3. Add value offset.
            start_index += record.offset
            offset = index_free_text + start_index
            # 2. Get the ending point of the Record block.
            end_index = len(message)
            # 2.1 Check for the EndId value.
            end_value_1, end_value_2, end_value_3 = record.block_end_id_1, record.block_end_id_2, record.block_end_id_3
            end_values = [end_value_1, end_value_2, end_value_3]
            index_end_value = [[value, message[start_index:].find(value)] for value in end_values if value is not None]
            if not any(end_values) and record.length > 0:
                pass
            not_bad = list(filter(lambda x: x[1] != -1, index_end_value))
            if any(end_values) and not not_bad and not record.until_end:
                # Error if the end character is not found.
                self.exceptions.append(NotEndIdInMessageParsingException(field=record.rec_name, is_record=True))
                continue
            if not_bad:
                end_index = start_index + min(not_bad, key=lambda x: x[1])[1]
            # 2.2 Check UntilEnd.
            if record.until_end:
                end_index = len(message)
            # 2.3 Delete value of endOffset.
            end_index -= record.end_offset
            if start_index < end_index:
                # Get the desired block of message text.
                block_text = message[start_index:end_index]
                offsets = []
                if record.rec_separator is not None:
                    data = block_text.split(record.rec_separator)
                    for index, row in enumerate(data):
                        offset_row = offset if index == 0 else offsets[-1] + len(data[index-1]) + len(record.rec_separator)
                        offsets.append(offset_row)
                else:
                    data = [block_text]
                    offsets.append(offset)
                rec_occurrence = record.rec_occurrence
                if rec_occurrence != 0:
                    # Get rows after the desired occurrence of the separator.
                    data = data[:rec_occurrence + 1]
                    offsets = offsets[:rec_occurrence + 1]
                # Data selection by rec_start_id.
                if record.rec_start_id is not None:
                    offset += block_text.find(record.rec_start_id) + len(record.rec_start_id) if block_text.find(
                        record.rec_start_id) != -1 else 0
                    block_text = block_text[block_text.find(record.rec_start_id) + len(record.rec_start_id):] if block_text.find(record.rec_start_id) != -1 else block_text
                    len_rec = len(record.rec_start_id)
                    offsets = [offsets[index] + i.find(record.rec_start_id) + len_rec for index, i in enumerate(data) if i.find(record.rec_start_id) != -1]
                    data = [i[i.find(record.rec_start_id) + len_rec:] for i in data if
                            i.find(record.rec_start_id) != -1]
                    if not data:
                        self.exceptions.append(NotStartIdInMessageParsingException(field=record.rec_name, is_record_block=True))
                        continue
                if not data:
                    self.exceptions.append(
                        NotFindLeastOneRecordParsingException(field=record.rec_name))
                    continue
                if record.rec_start_id is None and record.rec_separator is None and record.length != 0:
                    if record.length > len(data[0]):
                        raise NotFindLeastOneRecordParsingException(field=record.rec_name)
                        continue
                    # data[0] = data[0][:record.length]
                if record.length != 0:
                    data = split_length(block_text, record.length)
                    offsets = [offset]
                    for i in data[1:]:
                        offsets.append(offsets[-1] + record.length)
                    # data = [row[0:record.length] for row in data]
                result[record.rec_id] = {
                    'rec_name': record.rec_name,
                    'data': data,
                    'offsets': offsets
                }
                # offset += len(block_text)
        return result

    def _extract_fields_in_text(self, fields, text):
        """
        This method extracts all field in message.
        :param fields: Templates Field.
        :param text: text, which find template.
        :return: dictionary, where keys - field name, values - value field.
        """
        result = {}
        for field in fields:
            result_field = {}
            try:
                value_field = self.extract_field(field, text)
            except ParsingException as parsing_error:
                self.exceptions.append(parsing_error)
                continue
            result_field['original'] = value_field[field.field_name]
            convert_value = self._check_format_value(field, value_field)
            value_field[field.field_name] = convert_value
            result_field['internal'] = value_field[field.field_name]
            result_field['offset'] = value_field['offset']
            convert_value_field = self._convert_by_lookup_table(field, value_field)
            if convert_value_field is not None:
                result_field['converted'] = convert_value_field[field.field_name]
            result[field.field_name] = result_field
        return result

    def _check_convert_data_type(self, field, value_field, type_data_format, data_format):
        data_format, value = data_format.get('DataFormat'), value_field.get(field.field_name)
        try:
            result = to_date(data_format, value) if type_data_format == 1 else to_coordinate(data_format, value)
        except ValueError:
            if type_data_format == 1:
                raise DateFieldFormatException(field.field_name, data_format, value)
            elif type_data_format == 3:
                raise CoordinateFieldFormatException(field.field_name, data_format, value)
            result = None
        return result

    def _check_numeric_data_type(self, field, value_field):
        try:
            value = float(value_field[field.field_name])
        except ValueError:
            if field.mandatory:
                raise NumericFieldFormatException(field.field_name, 'numeric', value_field[field.field_name])
            return None
        if field.abnormal_val_high != 0 and field.abnormal_val_high <= value:
            raise OutOfRangeHighException(field.field_name, field.abnormal_val_high, value)
        if field.abnormal_val_high != 0 and field.abnormal_val_high <= value:
            raise OutOfRangeLowException(field.field_name, field.abnormal_val_high, value)
        return value

    def _check_format_value(self, field: TemplateField, value_field: dict):
        """
        This method checked format data and converted.
        :param field: field where check field.
        :param value_field: value.
        :return: converted value.
        """
        type_data_format = self.dic_field_type_format.get(field.field_type_id)
        try:
            if type_data_format in (s.FormatTypeDatetime, s.FormatTypeLatLon):
                data_format = list(filter(lambda x: x.get("DataFormatId") == field.data_format_id, self.data_formats))
                if data_format:
                    return self._check_convert_data_type(field, value_field, type_data_format, data_format.pop())
            if type_data_format == s.FormatTypeNumeric:
                return self._check_numeric_data_type(field, value_field)
        except FormatException as format_exception:
            self.exceptions.append(format_exception)
            return None
        # if type_data_format == 0:
        #     is_good_value = value_field[field.field_name].isalnum()
        #     if not is_good_value:
        #         raise AlphanumericFieldFormatException(field.field_name, 'alphanumeric', value_field[field.field_name])
        # if type_data_format == s.FormatTypeBoolean:
        #     if value_field[field.field_name] == '0' or value_field[field.field_name] == '1':
        #         return value_field[field.field_name] == '1'
        #     else:
        #         raise BooleanFieldFormatException(field.field_name, '0 or 1', value_field[field.field_name])
        return value_field[field.field_name]

    def _extract_fields_block(self, fields: List[TemplateField], message: str, offset: int = 0):
        if message == '':
            return {}
        result = self._extract_fields_in_text(fields, message)
        for key, value in result.items():
            value['offset'] += offset
        return result

    def _extract_fields_in_record(self, records_data: Dict, fields: List[TemplateField]) -> Dict:
        result = {}
        for record_id, record_data in records_data.items():
            fields_run = list(filter(lambda x: x.rec_id == record_id, fields))  # filter those that are in records
            data = record_data.get('data')
            offsets = record_data.get('offsets')
            result_list = []
            for index, (row, offset) in enumerate(zip(data, offsets)):
                result_list.append(self._extract_fields_block(fields_run, row, offset))
            result[record_data['rec_name']] = result_list
        return result

    def _extract_fields(self, fields_all: List[TemplateField], records_data: dict, message: str):
        """
        This method gets fields in message. Fields get from records and message.
        :param fields_all: list fields for gets.
        :param records_data: list records.
        :param message: text message
        :return: dictionary result with all fields.
        """
        result = {}
        # Remove the SMI allocation rules and all Sub SMIs from all Fields.
        fields = list(filter(lambda field: field.field_name not in self.template.get_smi_values(), fields_all))
        # Search the entire message.
        result |= self._extract_fields_block(self._get_fields_for_place(fields, self.ALL), message)
        # Splitting text into te line, free text.
        message_te_line, message_free_text, index_start_free_text = self._split_message(message)
        # Search in the te line.
        result |= self._extract_fields_block(self._get_fields_for_place(fields, self.TE_LINE), message_te_line)
        # Search in the free text.
        field_run = list(filter(lambda x: x.rec_id == 0, self._get_fields_for_place(fields, self.FREE_TEXT)))
        result |= self._extract_fields_block(field_run, message_free_text, index_start_free_text)
        # Search in records.
        result |= self._extract_fields_in_record(records_data, fields)
        return result

    def _convert_by_lookup_table(self, field: TemplateField, value_field: dict):
        """
        This method converted value to lookup item from lookup table.
        :param field: field where converted lookup item.
        :param value_field: value.
        :return: converted value.
        """
        convert_result = value_field.copy()
        if field.lookup_table_id == 0:
            return None
        lookup_table = self.lookups.get(field.lookup_table_id)
        convert_value = lookup_table.get(value_field[field.field_name])
        if convert_value is not None and field.use_lookup_table_to_convert_values:
            convert_result[field.field_name] = convert_value
            return convert_result
        return convert_result

    def _create_lookup_dict(self):
        result_lookup = {}
        for table in self.lookup_tables:
            result = {}
            for item in self.lookup_items:
                if item.get("TableID") == table.get("TableID"):
                    result[item.get("Value")] = item.get("ConvertTo")
            result_lookup[table.get("TableID")] = result
        return result_lookup

    def _create_field_type_format_dict(self):
        result = {}
        for field_type in self.field_types:
            result[field_type.get('FieldTypeId')] = field_type.get('FormatType')
        return result

    def _create_vocabulary(self):
        """
        This method create vocabulary for find in dictionary aircraft.
        :return: dictionary where key   -   reg_long:
                                  value -   type_aircraft_id;
        """
        regs_aircraft = self.long_registrations
        for type_air in regs_aircraft:
            self.vocabulary[type_air.get('AircraftReg')] = type_air.get("AircraftTypeId")
            if type_air.get('AircraftReg') != type_air.get('AircraftNose'):
                self.vocabulary[type_air.get('AircraftNose')] = type_air.get("AircraftTypeId")
        return self.vocabulary

    def _create_data(self, code: int, dsc: str = None, data=None, exceptions=None):
        """
        This message create result for return from parse.
        :param code: code result.
        :param dsc: message for result.
        :param data: result converted data.
        """
        self._data.code, self._data.dsc, self._data.structure = code, dsc, data
        self._data.exceptions = exceptions
        return self._data


class DiscriminatorHandler(TemplateMatcher):

    exceptions_dict = {
        'NotFoundLongRegistrationException': [-3, 'Bad messages. '],
        'NotFoundSMIException': [-3, "Bad messages. "],
        'UnknownAircraftException': [-5, "Bad aircraft. "],
    }

    type_downlink = 0
    type_uplink = 1
    type_ground = 2

    _DEFAULT_TEMPLATES = {
        (type_downlink, True): "default_template_downlink",
        (type_uplink, True): "default_template_uplink",
        (type_ground, True): "default_template_ground",
        (type_ground, False): "default_template_ground_not_620",
    }

    def _get_models(self):
        """
        This method create dict with key template's id and value list models.
        """
        result = {}
        a = [i for i in os.listdir(self.path_db_models) if '.json' in i]
        for i in a:
            json_model = load_json(os.path.join(self.path_db_models, i))
            validate_json = check_json_to_schema(json_model, self.schema_model)
            if isinstance(validate_json, str):
                raise ValidateModelToSchemaException(os.path.join(self.path_db_models, i), validate_json)
            model = ModelInfo(json_model)
            name_aircom_file, name_aeron_file = f'{model.model_id}.txt', f'{model.model_id}.jinja'
            name_aircom_file = os.path.join(self.path_db_models, name_aircom_file)
            name_aeron_file = os.path.join(self.path_db_models, name_aeron_file)
            aircom_body, aeron_body = load_file(name_aircom_file), load_file(name_aeron_file)
            model.aircom_model_body = aircom_body if aircom_body != name_aircom_file else None
            model.aeron_model_body = aeron_body if aeron_body != name_aeron_file else None
            if model.template_id not in result:
                result[model.template_id] = [model]
            else:
                result[model.template_id].append(model)
        return result

    def _get_template_from_file(self, path_file: Path) -> TemplateInfo | None:
        if path_file.suffix != '.json':
            return None
        # Upload template files.
        json_file = load_json(path_file)
        validate_json = check_json_to_schema(json_file, self.schema_template)
        if isinstance(validate_json, str):
            raise ValidateTemplateToSchemaException(path_file, validate_json)
        template_new = TemplateInfo(json_file)
        if template_new.template_id in self._template_ids:
            # Check for repetition of the id template.
            raise DuplicateTemplateIdException(template_new.template_id)
        if not template_new.active:
            # Select only active templates_downlink.
            return None
        # A list to verify the existence of the specified template id.
        self._template_ids.append(template_new.template_id)
        # Get hash with help SMI and SubSMIs.
        hash_smi = get_hash_smi(json_file)
        # Search for duplicate templates_downlink based on a hash.
        is_duplicate, tmp = self._find_equal_templates(hash_smi, template_new)
        if is_duplicate:
            # Error if the template has already been encountered.
            raise TemplateDuplicateException([tmp.template_id, template_new.template_id])

        template_new.models = self._models.get(template_new.template_id, [])
        return template_new

    def _check_default_template(self, template: TemplateInfo) -> bool:
        if template.specificity == -1 and template.smi is None:
            target_attribute = self._DEFAULT_TEMPLATES.get((template.type, template.is_620_format))

            if target_attribute is None:
                return False
            current_default = getattr(self, target_attribute)

            if current_default is not None:
                raise DuplicateDefaultTemplateException(
                    current_default.template_id, template.template_id
                )
            # Устанавливаем новое значение
            setattr(self, target_attribute, template)
            getattr(self, target_attribute).smi = '???'
            return True
        return False

    def _get_templates(self):
        """
        This method gets all active templates_downlink.
        :return: all templates_downlink.
        """
        templates_ground = []
        templates_downlink = []
        templates_uplink = []

        if not os.path.isdir(self.path_db_templates):
            # Error if the path of the template directory is incorrect.
            raise ValueError(f'Path "{self.path_db_templates}" is not directory.')
        for path_file in Path(self.path_db_templates).iterdir():
            template_new = self._get_template_from_file(path_file)

            if template_new is None or self._check_default_template(template_new):
                continue

            if template_new.type == self.type_downlink:
                templates_downlink.append(template_new)
            elif template_new.type == self.type_uplink:
                templates_uplink.append(template_new)
            elif template_new.type == self.type_ground:
                templates_ground.append(template_new)

        del self._template_ids, self._hash_table

        if self.default_template_downlink is None:
            raise NotFoundDefaultTemplateException
        return templates_downlink, templates_uplink, templates_ground

    def _find_equal_templates(self, hash_tmp, template: TemplateInfo) -> Tuple[bool, Optional[TemplateInfo]]:
        """
        This method find equal templates_downlink with help hash.
        :param hash_tmp: template's hash.
        :param template: template.
        :return: tuple:
                    first value: True - if duplicate template;
                                 False - if not duplicate template.
                    second value: None - if not duplicate,
                                  TemplateInfo - if duplicate first template.
        """
        # Get a hash of a list of templates_downlink with suitable SMI and SubSMI.
        tmps = self._hash_table.get(hash_tmp)
        if template.smi is None:
            return False, None
        if tmps is None:
            # If there is no such thing in the list, then we create it.
            self._hash_table[hash_tmp] = [template]
            return False, None
        for tmp in tmps:
            # Checking suitable SMI and SubSMIs templates_downlink for compliance with the characteristics of the aircraft type
            # and long registration.
            l_r_now, l_r_old = template.long_registration, tmp.long_registration
            a_t_1, a_t_2 = template.aircraft_types, tmp.aircraft_types
            u_t_1, u_t_2 = template.users, tmp.users
            is_subset_lr = (set(l_r_now) <= set(l_r_old) or set(l_r_now) >= set(l_r_old)) and (l_r_now and l_r_old) or (not l_r_now and not l_r_old)
            is_subset_at = (set(a_t_1) <= set(a_t_2) or set(a_t_1) >= set(a_t_2)) and (a_t_1 and a_t_2) or (not a_t_1 and not a_t_2)
            is_subset_us = (set(u_t_1) <= set(u_t_2) or set(u_t_1) >= set(u_t_2)) and (u_t_1 and u_t_2) or (not u_t_1 and not u_t_2)
            if is_subset_lr and is_subset_at and is_subset_us:
                return True, tmp
        self._hash_table[hash_tmp].append(template)
        return False, None

    def _create_data(self,
                      code: int,
                      dsc: str,
                      template: Optional[TemplateInfo] = None,
                      id_template: Optional[int] = None,
                      exceptions: Optional[List] = None):
        self._result.code = code
        self._result.exceptions = exceptions
        self._result.dsc = dsc
        self._result.template = template
        self._result.id_template = id_template
        return self._result


class WorkerModeller:
    """
    Class for worker jinja template.
    """
    def __init__(self,
                 template: TemplateInfo,
                 model: ModelInfo,
                 fields_type_dict: dict,
                 data_format_dict: dict,
                 lookup_items: dict,
                 predefined_fields: dict,
                 custom_fields: dict):
        """
        Constructor class for template jinja.
        :param template: template.
        :param model: model.
        :param fields_type_dict: dict with fields type.
        :param data_format_dict: dict with data formats.
        :param lookup_items: dict with lookup items.
        :param predefined_fields: dict with fields predefined.
        :param custom_fields: dict with fields customs.
        """
        self.model, self.template = model, template
        self.template_fields_dict = {i.template_field_id: i for i in self.template.fields}
        self.model_fields, self.template_fields = self.model.fields, self.template.fields
        self.fields_type_dict, self.data_format_dict = fields_type_dict, data_format_dict
        self.lookup_items = lookup_items
        self.count_model_field, self.delta = 0, 0
        self.predefined_fields = predefined_fields
        self.custom_fields = custom_fields
        # Workers for value's different types data
        self.field_type_workers = {
            s.FormatTypeNumeric: self._get_value_numeric,
            s.FormatTypeAlphanumeric: self._get_value_alphanumeric,
            s.FormatTypeDatetime: self._get_value_datetime,
            s.FormatTypeLatLon: self._get_value_lat_long,
            s.FormatTypeBoolean: self._get_value_boolean
        }

    def _get_field_type_template(self, model_field: ModelField):
        """
        This method get field type template.
        :param model_field: model field.
        :return: field type id.
        """
        template_field_id = model_field.template_field_id
        field_template = self.template_fields_dict.get(template_field_id)
        return field_template.field_type_id

    def _check_length(self, model_field, value):
        """
        Check length fields and get alignment.
        :param model_field: field model.
        :param value: value.
        :return: converted value.
        """
        result = value
        if model_field.nb_char_before_sep != 0 and len(result) <= model_field.nb_char_before_sep:
            if model_field.alignment == 0:
                result = result.ljust(model_field.nb_char_before_sep, ' ')
            else:
                result = result.rjust(model_field.nb_char_before_sep, ' ')
        if model_field.nb_char_before_sep != 0 and len(result) >= model_field.nb_char_before_sep:
            result = result[:model_field.nb_char_before_sep]
        return result

    def _get_value_datetime(self, model_field: ModelField, value: str) -> str:
        """
        Convert data for datetime format.
        :param model_field: model field.
        :param value: value for convert.
        :return: convert's value by model's field.
        """
        value = value.get('internal') if isinstance(value, dict) else value
        format_id = model_field.data_format_id
        if format_id is None and model_field.template_field_id is not None:
            template_field = self.template_fields_dict.get(model_field.template_field_id)
            if template_field is not None:
                format_id = template_field.data_format_id
        data_format = self.data_format_dict.get(format_id, {}).get(
            'DataFormat') if format_id is not None else s.BaseFormatDateTimeOut
        convert = value.replace('0000', '0001').replace('-00-', '-01-').replace('-00T', '-01T')
        try:
            result = datetime.datetime.strptime(convert, s.BaseFormatDateTimeIn).strftime(convert_date_format(data_format))
        except ValueError as error:
            raise FormatDateTimeModelException(value, data_format)
        result = result.lstrip('0')
        result = self._check_length(model_field, result)
        return result

    def _get_value_numeric(self, model_field: ModelField, value: str) -> str:
        """
        Convert data for numeric format.
        :param model_field: model field.
        :param value: value for convert.
        :return: convert's value by model's field.
        """
        result = value.get('internal') if isinstance(value, dict) else value
        char_operator = model_field.operator
        if char_operator is not None:
            try:
                function = f'result {char_operator} {model_field.operand}'
                result = eval(function)
            except SyntaxError:
                raise FormatNumericModelException(value, function)
        result_str = str(result)
        split_result_str = result_str.split('.')
        if len(split_result_str) != 2:
            raise FormatNumericModelException(value, "X.Y")
        if model_field.nb_char_before_sep != 0:
            split_result_str[0] = split_result_str[0][-1 * model_field.nb_char_before_sep:]
        if model_field.nb_char_after_sep != 0:
            split_result_str[1] = split_result_str[1][0:model_field.nb_char_before_sep:]
        result = f'{model_field.dec_separator}'.join(split_result_str)
        result = result.rstrip('0').rstrip('.').rstrip(',')
        if model_field.invert_bit:
            pass
        return result

    def _get_value_boolean(self, model_field: ModelField, value: str) -> str:
        return value.get('internal') if isinstance(value, dict) else value

    def _get_value_lat_long(self, model_field: ModelField, value: str) -> str:
        result = value.get('original') if isinstance(value, dict) else value
        result = self._check_length(model_field, result)
        return result

    def _get_value_alphanumeric(self, model_field: ModelField, value: str) -> str:
        """
       Convert data for alphanumeric format.
       :param model_field: model field.
       :param value: value for convert.
       :return: convert's value by model's field.
       """
        result = value.get('original') if isinstance(value, dict) else value
        if model_field.use_lookup:
            lookup_table = self.lookup_items.get(model_field.lookup_table_id, {})
            result = lookup_table.get(result)
            if result is None:
                result = value
        if model_field.replacement:
            for i in model_field.replacement:
                result = i.get('ToStr') if result == i.get('FromStr') else result
        result = self._check_length(model_field, result)
        return result

    def get_value(self, value):
        """
        This method convert value by model.
        :param value: value
        :return: convert's value.
        """
        result = value
        if isinstance(value, Undefined):
            t = None
            records = [value[0] for key, value in value._undefined_obj.items() if isinstance(value, list)]
            for record in records:
                t = record.get(value._undefined_name)
                if t is not None:
                    break
            if t is None:
                raise UnknownTemplateFieldException(value._undefined_name)
            result = t
        model_field = self.model_fields[self.count_model_field]
        if model_field.field_type_id is not None:
            field_type_id = model_field.field_type_id
        else:
            field_type_id = self._get_field_type_template(model_field)
        field_type = self.fields_type_dict.get(field_type_id)
        format_type = field_type.get('FormatType')
        result = self.field_type_workers[format_type](model_field, result)
        self.count_model_field += 1
        return result

    def get_const_field(self, name_field):
        """
        Method get constant fields.
        :param name_field: name const field.
        :return: value field.
        """
        name = name_field.replace('@', '')
        predefined_field_type = self.predefined_fields.get(name)
        if predefined_field_type is not None:
            return get_predefined_fields(name, predefined_field_type)
        custom_field_type = self.custom_fields.get(name)
        if custom_field_type is not None:
            return get_custom_fields(name, custom_field_type)
        raise UnknownDynamicFieldException(name_field)

    def start_iter(self, first_loop):
        if first_loop:
            self.delta = self.count_model_field
        return ''

    def end_iter(self, last_loop):
        if last_loop:
            self.delta = 0
        else:
            self.count_model_field = self.delta
        return ''


class ModellerHandler(ExceptionHandler):

    exceptions_dict = {
        'UnknownDynamicFieldException': [-3, 'Bad field. '],
        'UnknownTemplateFieldException': [-3, 'Bad field. '],
        'FormatModelException': [-4, "Format field error. "],
    }

    def _create_lookup_dict(self):
        result_lookup = {}
        for table in self.lookup_tables:
            result = {}
            for item in self.lookup_items:
                if item.get("TableID") == table.get("TableID"):
                    result[item.get("Value")] = item.get("ConvertTo")
            result_lookup[table.get("TableID")] = result
        return result_lookup

    def check_file_in_db(self, file_name: str):
        """
        Check exist file in directory db files.
        :param file_name: name file
        :return: dict
        :exception NotFileException
        """
        if file_name in self.files_db:
            path_to_file = os.path.join(self.path_db, file_name)
            return load_json(path_to_file)
        raise NotFileException(file_name)

    def _run_jinja(self, structure, worker, aeron_model_body):
        """
        This method run jinja template.
        :param structure: data for convert.
        :param worker: worker for convert values.
        :param aeron_model_body: text in format aeron.
        :return: reformat text message.
        """
        environment = jinja2.Environment(keep_trailing_newline=True)
        jinja = environment.from_string(aeron_model_body)
        return jinja.render(structure, worker=worker)

    def _create_data(self, code: int, dsc: str, message: str = None):
        self._result.code = code
        self._result.dsc = dsc
        self._result.message = message
        return self._result

    def _get_templates(self, templates_directory_path: str):
        result = {}
        for template_file_name in os.listdir(templates_directory_path):
            template_body_json = load_json(os.path.join(templates_directory_path, template_file_name))
            template_body = TemplateInfo(template_body_json)
            result[template_body.template_id] = template_body
        return result

