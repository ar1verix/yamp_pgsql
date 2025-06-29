# -*- coding: UTF-8 -*-


class ParsingException(Exception):
    pass


class NotStartIdInMessageParsingException(ParsingException):
    def __init__(self, field, is_filed=False, is_record=False, is_record_block=False):
        self.name_filed = field
        self.is_field = is_filed
        self.is_record = is_record
        self.is_record_block = is_record_block

    def __str__(self):
        if self.is_field:
            return f"{self.name_filed}: Cannot find specified field start identifier characters."
        if self.is_record:
            return f"{self.name_filed}: Cannot find specified record block start identifier characters."
        if self.is_record_block:
            return f"{self.name_filed}: Cannot find specified record start identifier characters."


class NotEndIdInMessageParsingException(ParsingException):
    def __init__(self, field, is_filed=False, is_record=False):
        self.name_filed = field
        self.is_field = is_filed
        self.is_record = is_record

    def __str__(self):
        if self.is_field:
            return f"{self.name_filed}: Cannot find specified field end identifier characters."
        if self.is_record:
            return f"{self.name_filed}: Cannot find end of record block."


class NotFoundDelimiterParsingException(ParsingException):
    def __init__(self, field, is_filed=False, is_record=False):
        self.field_name = field
        self.is_field = is_filed
        self.is_record = is_record

    def __str__(self):
        if self.is_field:
            return f"{self.field_name}: Cannot find specified field data start delimiter character."
        if self.is_record:
            return f"{self.field_name}: Cannot find specified record block start delimiter character."


class NotMandatoryFieldParsingException(ParsingException):
    def __init__(self, field_name):
        self.field_name = field_name

    def __str__(self):
        return f"Not found mandatory field: <{self.field_name}> in message."


class NotFindLeastOneRecordParsingException(ParsingException):
    def __init__(self, field):
        self.field_name = field

    def __str__(self):
        return f"{self.field_name}: Cannot find at least one record occurrence."


class BadLengthParsingException(ParsingException):
    def __init__(self, field):
        self.field_name = field

    def __str__(self):
        return f"{self.field_name}: Cannot find the field because its absolute end is out of bounds."


class FormatException(Exception):
    def __init__(self, field_name, format_field, value_field):
        self.field_name = field_name
        self.format_field = format_field
        self.value_field = value_field


class DateFieldFormatException(FormatException):
    def __str__(self):
        return f"{self.field_name}: Invalid date/time. Format date/time: {self.format_field}, value: '{self.value_field}'."


class CoordinateFieldFormatException(FormatException):

    def __str__(self):
        return f"{self.field_name}: Invalid coordinate. Format coordinate: {self.format_field}, value: '{self.value_field}'."


class NumericFieldFormatException(FormatException):

    def __str__(self):
        return f"{self.field_name}: Invalid numeric. Format numeric: {self.format_field}, value: '{self.value_field}'."


class AlphanumericFieldFormatException(FormatException):

    def __str__(self):
        return f"{self.field_name}: Invalid alphanumeric. Format alphanumeric: {self.format_field}, value: '{self.value_field}'."


class BooleanFieldFormatException(FormatException):

    def __str__(self):
        return f"{self.field_name}: Invalid boolean. Format boolean: {self.format_field}, value: '{self.value_field}'."


class OutOfRangeHighException(FormatException):

    def __str__(self):
        return f"{self.field_name}: Out of range. Field\'s value more that range: {self.format_field} <= '{self.value_field}'."


class OutOfRangeLowException(FormatException):

    def __str__(self):
        return f"{self.field_name}: Out of range. Field\'s value less that range: {self.value_field} <= '{self.format_field}'."


class UnknownAircraftException(Exception):
    def __init__(self, long_reg):
        self.long_reg = long_reg

    def __str__(self):
        return f"Unknown aircraft. Aircraft with long registration {self.long_reg} unknown."


class TemplateDuplicateException(Exception):
    def __init__(self, ids):
        self.ids = ids

    def __str__(self):
        return f"The current template has similar identification settings (same identifier values and, " \
               f"if applicable, common additional identification filter criteria) to these templates. " \
               f"ID: {self.ids[0]}, {self.ids[1]}"


class DuplicateDefaultTemplateException(Exception):
    def __init__(self, id_1, id_2):
        self.id_1 = id_1
        self.id_2 = id_2

    def __str__(self):
        return f"Duplicate default template. IDs: {self.id_1}, {self.id_2}"


class ValidateTemplateToSchemaException(Exception):

    def __init__(self, template, message):
        self.template = template
        self.message = message

    def __str__(self):
        return f"Template {self.template} schema validation error. {self.message}"


class ValidateModelToSchemaException(Exception):

    def __init__(self, model, message):
        self.model = model
        self.message = message

    def __str__(self):
        return f"Model {self.model} schema validation error. {self.message}"


class DuplicateTemplateIdException(Exception):

    def __init__(self, template):
        self.template = template

    def __str__(self):
        return f'Duplicate templates with same ID={self.template}.'


class NotFoundDefaultTemplateException(Exception):
    def __str__(self):
        return "Not found default template with specificity=-1 and SMI = null."


class NotFileException(Exception):
    def __init__(self, name_file: str):
        self.name_file = name_file

    def __str__(self):
        return f"Not found file: {self.name_file}."


class NotFoundSMIException(Exception):
    def __str__(self):
        return "Not found SMI in message."


class NotFoundLongRegistrationException(Exception):
    def __str__(self):
        return "Not found Long Registration in message."


class UnknownDynamicFieldException(Exception):
    def __init__(self, name_field: str):
        self.name_field = name_field

    def __str__(self):
        return f"Unknown name custom or predefined field: {self.name_field}."


class UnknownTemplateFieldException(Exception):
    def __init__(self, name_field: str):
        self.name_field = name_field

    def __str__(self):
        return f"Unknown name template's field: {self.name_field}."


class FormatModelException(Exception):
    def __init__(self, value):
        self.value = value


class FormatDateTimeModelException(FormatModelException):
    def __init__(self, value, format_datetime):
        super().__init__(value)
        self.format_datetime = format_datetime

    def __str__(self):
        return f"Invalid date/time in model. Format date/time: {self.format_datetime}, value: '{self.value}'."


class FormatNumericModelException(FormatModelException):
    def __init__(self, value, bad_format):
        super().__init__(value)
        self.bad_format = bad_format

    def __str__(self):
        return f"Invalid numeric in model. Format numeric: {self.bad_format}, value: '{self.value}'."