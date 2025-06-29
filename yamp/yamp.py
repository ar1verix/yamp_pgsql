# -*- coding: UTF-8 -*-

__all__ = ['parser', 'discriminator', 'modeller']

from yamp.settings import *

"""
This module has name YAMP - Yet Another Message Processor.
This module has classes parser, discriminator and modeller.
    1. Class parser parse text's messages and get JSON with all fields from file.
    2. Class discriminator classification text's messages by templates_downlink.
    3. Class modeller reformat message by model's template.

1.  Class parser:
    For work class need files database with aircraft_fleets.json, aircraft_types.json, data_formats.json, 
    field_types.json, lookup_tables.json and lookup_items.json where gets data about aircraft and other.
    Return class ParserResult with four parameters:
        - result.code                -   program execution code: 0 - success, < 0 - exceptions.
        - result.dsc                 -   information's message.
        - result.original_structure  -   result's original data in format JSON.
        - result.convert_structure   -   result's convert data in format JSON.
    Example create object class:
            db_path = 'db'
            file_aircraft       = 'db/settings/aircraft_fleets.json'
            file_aircraft_type  = 'db/settings/aircraft_types.json'
            data_formats        = 'db/settings/data_formats.json'
            field_types         = 'db/settings/field_types.json'
            lookup_tables       = 'db/settings/lookup_tables.json'
            lookup_items        = 'db/settings/lookup_items.json'
            in_file             = '1.txt'
            out_file            = '1.json'
            template            = TemplateInfo(load_json('templates_downlink/1.json'))
        Template is not in database:
             p = parser(path_db=db_path)
    Example parse text's file:
        1. Template is path to file.
            parser_result = parser.parse(in_file, 'template/1.json')
        2. Template is TemplateInfo.
            parser_result = parser.parse(in_file, template)

        Exception's codes:
            -1  -  Bad template or bad model, not valid schema;
            -2  -  Message does not fit the template;
            -3  -  Parsing error;
            -4  -  Format field error;
            -5  -  Bad aircraft;
            -6  -  Out of range;
            -7  -  Errors.
2. Class discriminator:
    This class classifications messages by templates_downlink.
    Return class DescriptorResult with four parameters:
        - result.code          -   program execution code: 0 - success, < 0 - exceptions.
        - result.dsc           -   information's message.
        - result.template      -   identify template in format TemplateInfo.
        - result.id_template   -   identifier identify template.
    Example:
            db_path = 'db'
            file_aircraft       = 'db/settings/aircraft_fleets.json'
            file_aircraft_type  = 'db/settings/aircraft_types.json'
            data_formats        = 'db/settings/data_formats.json'
            field_types         = 'db/settings/field_types.json'
            lookup_tables       = 'db/settings/lookup_tables.json'
            lookup_items        = 'db/settings/lookup_items.json'
            in_file             = '1.txt'
            message = load_file(in_file)
        Templates in file JSON:
            discriminator = discriminator(path_db=db_path)
            descriptor_results = discriminator.identify_template(message) # return DescriptorResult
        If the message does not match more than one template, then return default template.
    Exception:
        - NotFileException                  -   if not found file db;
        - ValidateModelToSchemaException    -   if model not valid by schema;
        - ValidateTemplateToSchemaException -   if template not valid by schema;
        - ValueError                        -   if path_template is not directory;
        - DuplicateDefaultTemplateException -   if default template more one;
        - DuplicateTemplateIdException      -   if template's id is duplicate;
        - TemplateDuplicateException        -   if template is duplicate.

    Exception's codes:
            -3  -  Parsing error not found SMI or Long Registration;
            -5  -  Bad aircraft;
            -7  -  Errors.
3. Class modeller:
    This class convert parser's structure to file .txt.
    Return class ModellerResult with tree parameters:
        - result.code          -   program execution code: 0 - success, < 0 - exceptions.
        - result.dsc           -   information's message.
        - result.message       -   out reformat message.
    Example:
            db_path = 'db'
            file_aircraft       = 'db/settings/aircraft_fleets.json'
            file_aircraft_type  = 'db/settings/aircraft_types.json'
            data_formats        = 'db/settings/data_formats.json'
            field_types         = 'db/settings/field_types.json'
            lookup_tables       = 'db/settings/lookup_tables.json'
            lookup_items        = 'db/settings/lookup_items.json'
            dynamic_fields      = 'db/settings/dynamic_fields.json'
            template            = TemplateInfo(load_json('templates_downlink/1.json'))
        modeller = modeller(path_db=db_path)
        models = template.models
        modeller_result = modeller.reformat(results.original_structure, models[0], template)
    
    Exception:
        - NotFileException  -   if not found file db.
    
    Exception's codes:
            -3  -  Parsing error, unknown fields;
            -4  -  bad format field;
            -7  -  Errors.      
"""

from yamp.handlers import ParserHandler, DiscriminatorHandler, YampBase, ModellerHandler, WorkerModeller
from yamp.utils import *
from yamp.models import TemplateInfo, ParserResult, DescriptorResult, ModelInfo, ModellerResult


class parser(YampBase, ParserHandler):
    """
    Class parser parsing template for parse text's messages by Templates.
    YAMP - Yet Another Message Processor.
    """

    def __init__(self, db_directory_path: str = None):
        """
        Constructor class. Create objects parameters.
        :param path_db: file with data from database in format JSON.
                        Files:  -   'aircraft_fleets.json';
                                -   'aircraft_types.json';
                                -   'data_formats.json';
                                -   'field_types.json';
                                -   'lookup_tables.json';
                                -   'lookup_items.json'.
        Example:
               db_path = 'db'
            1. Template in file JSON:
                parser = parser(path_db=db_path)
                parser_result = parser.parse('test/21.txt', "21.json")
        """
        super().__init__(db_directory_path=db_directory_path)
        file_name = FileDataFormatsPath
        self.data_formats = self.check_file_in_db(file_name)
        file_name = FileFieldTypesPath
        self.field_types = self.check_file_in_db(file_name)
        file_name = FileLookupTablesPath
        self.lookup_tables = self.check_file_in_db(file_name)
        file_name = FileLookupItemsPath
        self.lookup_items = self.check_file_in_db(file_name)
        self.lookups = self._create_lookup_dict()
        self.dic_field_type_format = self._create_field_type_format_dict()
        self.vocabulary = {}
        self._create_vocabulary()
        self.template, self._result, self.messages = None, None, None
        self._data = ParserResult()
        return

    def parse(self, message: str, template: TemplateInfo, id_user: int | None = None) -> ParserResult:
        """
        Main parsing method. Parsing messages and return ParserResult with structures and code.
        :param id_user:
        :param message: data for parsing.
                     Format: text message.
        :param template: template for parsing files.
                         Format: - TemplateInfo - template in format TemplateInfo.
        :return: - object ParserResult's class - which has code, dsc, original_structure and convert_structure.
                   Exception's codes:
                        -1  -  Bad template or bad model, not valid schema;
                        -2  -  Message does not fit the template;
                        -3  -  Parsing error;
                        -4  -  Format field error;
                        -5  -  Bad aircraft;
                        -6  -  Out of range;
                        -7  -  Errors.
        """
        self._data.clear_data()
        self._data.id_template = template.template_id
        self.messages = message
        self.is_aeec_620 = self._identify_aeec620()
        self.template = template
        self.type_message = self._type_message(message)
        # self.messages = is_69(self.messages)

        # Get information about the template in dict format.
        try:
            # self.template = self._get_template_or_except(template)
            is_match_template, result = self.check_message_by_template(self.messages, self.template, id_user)
            if not is_match_template:
                id_tmp = self.template.template_id
                return self._create_data(code=-2, dsc=f"The message does not fit the template with id {id_tmp}.")
            # Get fields "Long registration" and "Aircraft types".
            # if result.get("long_registration") is None and self.is_aeec_620:
            #     result |= self._get_filters()
            self._result = self._convert_filters(result)  # convert to structure's format
            record_data = self._extract_records(self.template.records, self.messages)
            result_fields = self._extract_fields(self.template.fields, record_data, self.messages)
            self._result |= result_fields
        except Exception as error:
            result_exception = self._handler_exceptions(error)
            return self._create_data(**result_exception)
        self.template = None

        if self.exceptions:
            return self._create_data(code=1, dsc="Warning parse.", data=self._result, exceptions=self._return_exceptions())

        return self._create_data(code=0, dsc="Success parse.", data=self._result)


class discriminator(YampBase, DiscriminatorHandler):
    """
    Class YAMP discriminator classifications messages by templates_downlink.
    YAMP - Yet Another Message Processor.
    """

    def __init__(self, db_directory_path: str = None):
        """
        Constructor class create object discriminator's class.
        :param db_directory_path: path to directory with database's files. Files templates_downlink is in directory 'templates_downlink/'.
        Exceptions:
        :exception NotFileException: Not found file for work.
        :exception ValidateModelToSchemaException: This model's schema validation error.
        :exception ValidateTemplateToSchemaException: This template's schema validation error.
        :exception TemplateDuplicateException:  The current template has similar identification settings (same
                                                identifier values and, if applicable, common additional identification
                                                filter criteria) to these templates_downlink.
        :exception DuplicateDefaultTemplateException: Duplicate default template.
        :exception DuplicateTemplateIdException: Duplicate templates_downlink with same ID.

        Example:
            message = '21.txt'
            1. Templates in file JSON:
                discriminator = discriminator(path_db='db')
                discriminator_result = discriminator.identify_template(message)
            2. Text message:
                message = load_file('21.txt')
                discriminator_result = discriminator.identify_template(message)
        """
        super().__init__(db_directory_path=db_directory_path)
        self._template_ids = []
        self._hash_table = {}
        self.default_template_ground = None
        self.default_template_ground_not_620 = None
        self.default_template_downlink = None
        self.default_template_uplink = None
        self._result = DescriptorResult()
        self._models = self._get_models()
        self.templates_downlink, self.templates_uplink, self.templates_ground = self._get_templates()

    def get_templates(self):
        return self.templates_downlink + self.templates_ground

    def get_default_template(self):
        if self.type_message == 0:
            return self.default_template_downlink
        if self.type_message == 2 and self.is_aeec_620:
            return self.default_template_ground
        if self.type_message == 2 and not self.is_aeec_620:
            return self.default_template_ground_not_620
        if self.type_message == 1:
            return self.default_template_uplink

    def identify_template(self, message: str, user_id: int | None = None) -> DescriptorResult:
        """
        Classification message by templates.
        :param message: text message.
        :param user_id: identifier user
        :return: DescriptorResult.
        """
        self._result.clear_data()
        self.exceptions = []
        self.messages = message
        self.is_aeec_620 = self._identify_aeec620()
        self.type_message = self._type_message(message)

        try:
            best_template = self.match_template(message, user_id)
        except Exception as error:
            result_exception = self._handler_exceptions(error)
            return self._create_data(**result_exception)

        if self.exceptions:
            return self._create_data(1, "Warning", best_template, best_template.template_id, self._return_exceptions())

        return self._create_data(0, "Success", best_template, best_template.template_id)


class modeller(ModellerHandler):
    """
    Class YAMP modeller convert parser's structure to file .txt.
    YAMP - Yet Another Message Processor.
    """

    def __init__(self, db_directory_path: str = None):
        """
        Constructor class create object modeller's class.
        :param db_directory_path: path to directory with database's files.
        Example:
            modeller = modeller(path_db='db')
        """
        self.path_db = db_directory_path
        self.path_db_settings = os.path.join(self.path_db, 'settings')
        self.files_db = [os.path.join('settings', i) for i in os.listdir(self.path_db_settings)]
        self.path_field_types = os.path.join(self.path_db, FileFieldTypesPath)
        file_name = FileDataFormatsPath
        self.data_formats = self.check_file_in_db(file_name)
        self.data_formats = {data_format.get('DataFormatId'): data_format for data_format in self.data_formats}
        file_name = FileFieldTypesPath
        self.field_types = self.check_file_in_db(file_name)
        self.field_types = {data_format.get('FieldTypeId'): data_format for data_format in self.field_types}
        file_name = FileLookupTablesPath
        self.lookup_tables = self.check_file_in_db(file_name)
        file_name = FileLookupItemsPath
        self.lookup_items = self.check_file_in_db(file_name)
        self.lookup = self._create_lookup_dict()
        file_name = FilePredefinedFieldsPath
        self.predefined_fields = self.check_file_in_db(file_name)
        file_name = FileCustomFieldsPath
        self.custom_fields = self.check_file_in_db(file_name)
        self._result = ModellerResult()
        self.templates = self._get_templates(os.path.join(self.path_db, 'templates'))

    def reformat(self, structure: dict, model: ModelInfo) -> ModellerResult:
        """
        This method convert .jinja template to file .txt.
        :param structure: JSON structure.
        :param model: model for convert.
        :return: object ModellerResult's class - which has code, dsc and reformat message.
            Exception's codes:
            -1  -  Bad template.
            -3  -  Parsing error, unknown fields;
            -4  -  bad format field;
            -7  -  Errors.
        """
        self._result.clear_data()
        template = self.templates.get(model.template_id)
        if template is None:
            return self._create_data(-1, f'Bad template. Template with id={model.template_id} not found.')
        self._result.id_template = model.template_id
        self._result.id_model = model.model_id
        structures_jinja = {"DATA": structure}
        # Worker for template jinja
        worker = WorkerModeller(template, model, self.field_types, self.data_formats,
                                self.lookup, self.predefined_fields, self.custom_fields)
        try:
            message = self._run_jinja(structures_jinja, worker, model.aeron_model_body)
            if model.force_caps:
                message = message.upper()
        except Exception as error:
            result_exception = self._handler_exceptions(error)
            return self._create_data(**result_exception)
        return self._create_data(0, 'Success', message)
