"""Based loosely on admin filterspecs, these are more focused on delivering controls appropriate per field type

Different filter controls can be registered per field type. When assembling a set of filter controls, these field types will generate the appropriate set of fields. These controls will be based upon what is appropriate for that field. For instance, a datetimefield for filtering requires a start/end. A boolean field needs an "all", "true" or "false" in radio buttons.

"""
from django import forms
from django.db import models
from django.utils.translation import ugettext as _

# TODO build register and lookup functions
# TODO figure out how to manage filters and actual request params, which aren't always 1-to-1 (e.g. datetime)

class FilterControl(object):
    filter_controls=[]
    def __init__(self,field_name,label=None):
        self.field_name=field_name
        self.label=label

    def get_fields(self):
        if hasattr(self, 'choices'):
            return {self.field_name:forms.ChoiceField(label=self.label or self.field_name, 
                required=False, choices=self.choices)}
        else:
            return {self.field_name:forms.CharField(label=self.label or self.field_name,required=False)}

    # Pulled from django.contrib.admin.filterspecs
    def register(cls, test, factory, datatype):
        cls.filter_controls.append((test, factory, datatype))
    register = classmethod(register)

    def create_from_modelfield(cls, f, field_name, label=None):
        # get choices for Foreign Key plus Char and Integer fields with choices set to change to and to populate select widget
        if hasattr(f, 'get_choices'):
            try:
                cls.choices = f.get_choices()
            except(AttributeError):
                # all charfields have get_choices
                # but if no choices are set, which is normally the case
                # this error is thrown because Django assumes
                # there is a foreign key relationship to follow
                # there is not, so pass
                pass

        for test, factory, datatype in cls.filter_controls:
            if test(f):
                return factory(field_name,label)
    create_from_modelfield = classmethod(create_from_modelfield)

    def create_from_datatype(cls, datatype, field_name, label=None):
        for test, factory, dt in cls.filter_controls:
            if dt == datatype:
                return factory(field_name,label)
    create_from_datatype = classmethod(create_from_datatype)

FilterControl.register(lambda m: isinstance(m,models.CharField),FilterControl,"char")
FilterControl.register(lambda m: isinstance(m,models.IntegerField),FilterControl,"integer")

class DateTimeFilterControl(FilterControl):
    def get_fields(self):
        ln=self.label or self.field_name
        start=forms.CharField(label=_("%s From")%ln,required=False,widget=forms.DateTimeInput(attrs={'class': 'vDateField'}))
        end=forms.CharField(label=_("%s To")%ln,required=False,widget=forms.DateTimeInput(attrs={'class': 'vDateField'}))
        return {"%s__gte"%self.field_name:start,"%s__lt"%self.field_name:end}

FilterControl.register(lambda m: isinstance(m,models.DateTimeField),DateTimeFilterControl,"datetime")

class BooleanFilterControl(FilterControl):
    def get_fields(self):
        return {self.field_name:forms.CharField(label=self.label or self.field_name,
                required=False,widget=forms.Select(choices=(('','All'),('1','True'),('0','False'))),initial='A')}

FilterControl.register(lambda m: isinstance(m,models.BooleanField),BooleanFilterControl,"boolean")

class ForeignKeyFilterControl(FilterControl):
    def get_fields(self):
        return {self.field_name:forms.ChoiceField(label=self.label or self.field_name, 
                required=False, choices=self.choices)}

FilterControl.register(lambda m: isinstance(m,models.ForeignKey),ForeignKeyFilterControl,"foreignkey")

# TODO add a filter control that is not based on a field, but on a method that returns a query or data to filter by
class CustomMaskFilterControl(FilterControl):
    # this is not a filter based on a field on the model in question; however it will be related to the field for filtering but have a number of subconditions
    # Effectively a subreport used to the filter the larger report
    def __init__(self, field_name, label=None):
        self.field_name=field_name
        self.label=label
        
    def get_fields(self):
        return {"%s__custom_mask"%self.field_name:forms.BooleanField(label=self.label or self.field_name, required=False)}


# TODO How do I register this one?
class StartsWithFilterControl(FilterControl):
    def get_fields(self):
        return {"%s__startswith"%self.field_name:forms.CharField(label=_("%s Starts With")%(self.label or self.field_name),
                required=False)}
