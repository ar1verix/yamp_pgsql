# -*- coding: UTF-8 -*-
import json
from copy import deepcopy
from typing import Optional, Dict


class TemplateBase:
    def __init__(self, data: dict = None, *args, **kwargs):
        self.__data = data
        self.__kwargs = kwargs

    def __str__(self):
        return f"{self.name} - ID: {self.__id__()}"

    def __repr__(self):
        return f"<{self.name}> - object class {type(self).__name__}"

    def _data_or_kwargs(self, field: str):
        return self.__data.get(field) if self.__data is not None else self.__kwargs.get(field)

    def get(self, field):
        return self._data_or_kwargs(field)

    def to_json(self):
        dict_values = self.__dict__
        dict_values.pop('_TemplateBase__data')
        dict_values.pop('_TemplateBase__kwargs')
        return json.dumps(self,
                          default=lambda o: dict_values,
                          sort_keys=True,
                          indent=4)

    def to_dict(self):
        dict_values = self.__dict__
        if '_TemplateBase__data' in dict_values:
            dict_values.pop('_TemplateBase__data')
        if '_TemplateBase__kwargs' in dict_values:
            dict_values.pop('_TemplateBase__kwargs')
        return dict_values


class TemplateInfo(TemplateBase):
    def __init__(self, data: dict = None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.template_id = self._data_or_kwargs('TemplateId')
        self.msg_category = self._data_or_kwargs('MsgCategory')
        self.source = self._data_or_kwargs('Source')
        self.type = self._data_or_kwargs('Type')
        self.template_name = self._data_or_kwargs('TemplateName')
        self.parent = self._data_or_kwargs('Parent')
        self.active = self._data_or_kwargs('Active')
        self.specificity = self._data_or_kwargs('Specificity')
        self.owner = self._data_or_kwargs('Owner')
        self.msg_example = self._data_or_kwargs('MsgExample')
        self.is_620_format = self._data_or_kwargs('Is620Format')
        self.auto_reply_template = self._data_or_kwargs('AutoReplyTemplate')
        self.smi = self._data_or_kwargs('SMI')
        self.sub_smi_1 = self._data_or_kwargs('SubSMI1')
        self.sub_smi_2 = self._data_or_kwargs('SubSMI2')
        self.sub_smi_3 = self._data_or_kwargs('SubSMI3')
        self.priority = self._data_or_kwargs('Priority')
        self.oooi_type = self._data_or_kwargs('OOOIType')
        self.auto_ack = self._data_or_kwargs('AutoAck')
        self.wait_hold_stage_id = self._data_or_kwargs('WaitHoldStageId')
        self.wait_hold_time = self._data_or_kwargs('WaitHoldTime')
        self.validity = self._data_or_kwargs('Validity')
        self.max_wait_hold_time = self._data_or_kwargs('MaxWaitHoldTime')
        self.send_waiting_uplinks = self._data_or_kwargs('SendWaitingUplinks')
        self.trim_cr_lf = self._data_or_kwargs('TrimCrLf')
        self.xml_msg_type = self._data_or_kwargs('XMLMsgType')
        self.xml_msg_sub_type = self._data_or_kwargs('XMLMsgSubType')
        self.stop_hold_period = self._data_or_kwargs('StopHoldPeriod')
        self.start_hold_period = self._data_or_kwargs('StartHoldPeriod')
        self.hold_period = self._data_or_kwargs('HoldPeriod')
        self.allow_multi_distrib_to_same_user = self._data_or_kwargs('AllowMultiDistribToSameUser')
        self.wait_hold_type = self._data_or_kwargs('WaitHoldType')
        self.use_dsp = self._data_or_kwargs('UseDsp')
        self.message_type = self._data_or_kwargs('MessageType')
        self.template_description = self._data_or_kwargs('TemplateDescription')
        self.aircraft_types = self._data_or_kwargs('Aircraft types')
        self.long_registration = self._data_or_kwargs('Long registration')
        self.users = self._data_or_kwargs('Users') if self._data_or_kwargs('Users') is not None else []
        self.records = [TemplateRecord(i) for i in self._data_or_kwargs('Records')] if isinstance(self.get('Records'),
                                                                                                  list) else []
        self.fields = [TemplateField(i) for i in self._data_or_kwargs('Fields')] if isinstance(self.get('Fields'),
                                                                                               list) else []
        self.models = [ModelInfo(i) for i in self._data_or_kwargs('Models')] if isinstance(self.get('Models'),
                                                                                           list) else []
        self.subsmis = {
            1: self.sub_smi_1,
            2: self.sub_smi_2,
            3: self.sub_smi_3,
        }
        self.data = data

    def __id__(self) -> str:
        return str(self.template_id)

    def get_smi_values(self) -> Dict[str, Optional[str]]:
        """
        This method gets smi and all sub-smi from row table Template.
        :return: dict with all values smi
        """
        return {
            "SMI": self.smi,
            "SubSMI 1": self.sub_smi_1,
            "SubSMI 2": self.sub_smi_2,
            "SubSMI 3": self.sub_smi_3,
        }

    @property
    def name(self):
        return self.template_name

    @name.setter
    def name(self, name):
        self.template_name = name

    @name.deleter
    def name(self):
        del self.template_name

    def to_dict(self):
        return self.__dict__


class TemplateRecord(TemplateBase):
    def __init__(self, data: dict = None, *args, **kwargs):
        """
        Rec_id, TemplateId, RecName, BlockStartId, BlockEndId1, BlockEndId2,
        BlockEndId3, UntilEnd, RecStartId, Offset, Length, Delimiter, DelOccurrence,
        RecOccurrence, RecSeparator, EndOffset
        :param data:
        :param args:
        :param kwargs:
        """
        super().__init__(data, *args, **kwargs)
        self.rec_id = self._data_or_kwargs('RecId')
        self.template_id = self._data_or_kwargs('TemplateId')
        self.rec_name = self._data_or_kwargs('RecName')
        self.block_start_id = self._data_or_kwargs('BlockStartId')
        self.block_end_id_1 = self._data_or_kwargs('BlockEndId1')
        self.block_end_id_2 = self._data_or_kwargs('BlockEndId2')
        self.block_end_id_3 = self._data_or_kwargs('BlockEndId3')
        self.until_end = self._data_or_kwargs('UntilEnd')
        self.rec_start_id = self._data_or_kwargs('RecStartId')
        self.offset = self._data_or_kwargs('Offset')
        self.length = self._data_or_kwargs('Length')
        self.delimiter = self._data_or_kwargs('Delimiter')
        self.del_occurrence = self._data_or_kwargs('DelOccurrence')
        self.rec_occurrence = self._data_or_kwargs('RecOccurrence')
        self.rec_separator = self._data_or_kwargs('RecSeparator')
        self.end_offset = self._data_or_kwargs('EndOffset')

    def __id__(self) -> str:
        return str(self.rec_id)

    @property
    def name(self):
        return self.rec_name

    @name.setter
    def name(self, name):
        self.rec_name = name

    @name.deleter
    def name(self):
        del self.rec_name


class TemplateField(TemplateBase):
    def __init__(self, data: dict = None, *args, **kwargs):
        """
        TemplateFieldId, TemplateId, FieldTypeId, FieldName, PositionId, Mandatory,
        DataFormatId, Delimiter, DelOccurrence, StartId, EndId1, EndId2, EndId3, UntilEnd,
        "Offset", "Length", LookupTableId, RecId, DynRoutId, NormalValHigh, NormalValLow,
        AbnormalValHigh, AbnormalValLow, FieldOrder, UnitId, UnitMultiplier, EndOffset,
        UseLookupTableToConvertValues, UseLookupTableForDistributionCriteria
        """
        super().__init__(data, *args, **kwargs)
        self.template_field_id = self._data_or_kwargs('TemplateFieldId')
        self.template_id = self._data_or_kwargs('TemplateId')
        self.field_type_id = self._data_or_kwargs('FieldTypeId')
        self.field_name = self._data_or_kwargs('FieldName')
        self.position_id = self._data_or_kwargs('PositionId')
        self.mandatory = self._data_or_kwargs('Mandatory')
        self.data_format_id = self._data_or_kwargs('DataFormatId')
        self.delimiter = self._data_or_kwargs('Delimiter')
        self.del_occurrence = self._data_or_kwargs('DelOccurrence')
        self.start_id = self._data_or_kwargs('StartId')
        self.end_id_1 = self._data_or_kwargs('EndId1')
        self.end_id_2 = self._data_or_kwargs('EndId2')
        self.end_id_3 = self._data_or_kwargs('EndId3')
        self.until_end = self._data_or_kwargs('UntilEnd')
        self.offset = self._data_or_kwargs('Offset')
        self.length = self._data_or_kwargs('Length')
        self.lookup_table_id = self._data_or_kwargs("LookupTableId")
        self.rec_id = self._data_or_kwargs('RecId')
        self.dyn_rout_id = self._data_or_kwargs('DynRoutId')
        self.normal_val_high = self._data_or_kwargs('NormalValHigh')
        self.normal_val_low = self._data_or_kwargs('NormalValLow')
        self.abnormal_val_high = self._data_or_kwargs('AbnormalValHigh')
        self.abnormal_val_low = self._data_or_kwargs('AbnormalValLow')
        self.field_order = self._data_or_kwargs('FieldOrder')
        self.unit_id = self._data_or_kwargs('UnitId')
        self.unit_multiplier = self._data_or_kwargs('UnitMultiplier')
        self.end_offset = self._data_or_kwargs('EndOffset')
        self.use_lookup_table_to_convert_values = self._data_or_kwargs('UseLookupTableToConvertValues')
        self.use_lookup_table_for_distribution_criteria = self._data_or_kwargs('UseLookupTableForDistributionCriteria')

    def __id__(self) -> str:
        return str(self.template_field_id)

    @property
    def name(self):
        return self.field_name

    @name.setter
    def name(self, name):
        self.field_name = name

    @name.deleter
    def name(self):
        del self.field_name


class BaseResult:
    def __init__(self):
        self.code = 0
        self.dsc = ''
        self.id_template = None
        self.exceptions = []

    def clear_data(self):
        self.code = 0
        self.dsc = ''
        self.id_template = None
        self.exceptions = []

    def to_dict(self):
        return self.__dict__


class ParserResult(BaseResult):
    def __init__(self):
        super().__init__()
        self.structure = None

    def clear_data(self):
        super().clear_data()
        self.structure = None


class DescriptorResult(BaseResult):
    def __init__(self):
        super().__init__()
        self.template = None

    def clear_data(self):
        super().clear_data()
        self.template = None

    def __repr__(self):
        return f"{self.id_template} - Code: {self.code}."

    def to_dict(self):
        result = deepcopy(self.__dict__)
        if result['template'] is not None:
            result['template'] = str(result['template'])
        return result


class ModellerResult(BaseResult):
    def __init__(self):
        super().__init__()
        self.message = ''
        self.id_model = None

    def clear_data(self):
        super().clear_data()
        self.message = ''
        self.id_model = None


class ModelInfo(TemplateBase):
    def __init__(self, data: dict = None, *args, **kwargs):
        """
        ModelId, TemplateId, ModelName, ModelText, IsDefault, LineLen, QuoteLen, TotalLines, TotalLen,
        TotalExceededAction, ForceCaps, IncludeCRC, MultipartHeader, MultipartFooter, EFBConvertToXML,
        ModelDescription
        """
        super().__init__(data, *args, **kwargs)
        self.model_id = self._data_or_kwargs('ModelId')
        self.template_id = self._data_or_kwargs('TemplateId')
        self.model_name = self._data_or_kwargs('ModelName')
        self.model_text = self._data_or_kwargs('ModelText')
        self.is_default = self._data_or_kwargs('IsDefault')
        self.line_len = self._data_or_kwargs('LineLen')
        self.quote_len = self._data_or_kwargs('QuoteLen')
        self.total_lines = self._data_or_kwargs('TotalLines')
        self.total_len = self._data_or_kwargs('TotalLen')
        self.total_exceeded_action = self._data_or_kwargs('TotalExceededAction')
        self.force_caps = self._data_or_kwargs('ForceCaps')
        self.include_crc = self._data_or_kwargs('IncludeCRC')
        self.multipart_header = self._data_or_kwargs('MultipartHeader')
        self.multipart_footer = self._data_or_kwargs('MultipartFooter')
        self.efb_convert_To_xml = self._data_or_kwargs('EFBConvertToXML')
        self.model_description = self._data_or_kwargs('ModelDescription')
        self.aircom_model_body = self._data_or_kwargs('AircomModelBody')
        self.aeron_model_body = self._data_or_kwargs('AeronModelBody')
        self.fields = [ModelField(i) for i in self._data_or_kwargs('Fields')] if isinstance(self.get('Fields'),
                                                                                            list) else None

    @property
    def name(self):
        return self.model_name

    @name.setter
    def name(self, name):
        self.model_name = name

    @name.deleter
    def name(self):
        del self.model_name


class ModelField(TemplateBase):
    def __init__(self, data: dict = None, *args, **kwargs):
        """
       ModelFieldId, ModelId, TemplateFieldId, DataFormatId, Alignment, DecSeparator, NbCharBeforeSep, NbCharAfterSep,
       UseLookup, LookupTableId, InvertBit, Operand, Operator, FieldTypeId
        """
        super().__init__(data, *args, **kwargs)
        self.model_field_id = self._data_or_kwargs('ModelFieldId')
        self.model_id = self._data_or_kwargs('ModelId')
        self.template_field_id = self._data_or_kwargs('TemplateFieldId')
        self.data_format_id = self._data_or_kwargs('DataFormatId')
        self.alignment = self._data_or_kwargs('Alignment')
        self.dec_separator = self._data_or_kwargs('DecSeparator')
        self.nb_char_before_sep = self._data_or_kwargs('NbCharBeforeSep')
        self.nb_char_after_sep = self._data_or_kwargs('NbCharAfterSep')
        self.use_lookup = self._data_or_kwargs('UseLookup')
        self.lookup_table_id = self._data_or_kwargs('LookupTableId')
        self.invert_bit = self._data_or_kwargs('InvertBit')
        self.operand = self._data_or_kwargs('Operand')
        self.operator = self._data_or_kwargs('Operator')
        self.field_type_id = self._data_or_kwargs('FieldTypeId')
        self.replacement = self._data_or_kwargs('Replacement')

    @property
    def name(self):
        return self.model_field_id

    @name.setter
    def name(self, name):
        self.model_field_id = name

    @name.deleter
    def name(self):
        del self.model_field_id
