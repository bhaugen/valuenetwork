import sys
from decimal import *
from django import forms
from django.utils.translation import ugettext_lazy as _

from valuenetwork.tekextensions.widgets import SelectWithPopUp

from valuenetwork.valueaccounting.models import *


class EconomicResourceTypeForm(forms.ModelForm):
    
    class Meta:
        model = EconomicResourceType
        exclude = ('parent',)


class EconomicResourceTypeWithPopupForm(forms.ModelForm):
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all(),  
        widget=SelectWithPopUp(model=Unit))

    class Meta:
        model = EconomicResourceType
        exclude = ('parent',)

    @classmethod
    def is_multipart(cls):
        return True


class AgentResourceTypeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AgentResourceTypeForm, self).__init__(*args, **kwargs)
        self.fields["agent"].choices = [
            (agt.id, agt.name) for agt in EconomicAgent.objects.all()
        ]
        self.fields["relationship"].choices = [
            (rel.id, rel.name) for rel in ResourceRelationship.objects.filter(resource_effect="+")
        ]

    class Meta:
        model = AgentResourceType
        exclude = ('resource_type',)


class XbillProcessTypeForm(forms.ModelForm):
    quantity = forms.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = ProcessType
        exclude = ('parent',)


class ChangeProcessTypeForm(forms.ModelForm):

    class Meta:
        model = ProcessType
        exclude = ('parent',)


class ProcessTypeResourceTypeForm(forms.ModelForm):
    resource_type = forms.ModelChoiceField(
        queryset=EconomicResourceType.objects.all(), 
        empty_label=None, 
        widget=SelectWithPopUp(model=EconomicResourceType))
    relationship = forms.ModelChoiceField(
        queryset=ResourceRelationship.objects.exclude(resource_effect="+"), 
        empty_label=None, 
        widget=SelectWithPopUp(model=ResourceRelationship))
    unit_of_quantity = forms.ModelChoiceField(
        queryset=Unit.objects.all(),  
        widget=SelectWithPopUp(model=Unit))

    #def __init__(self, *args, **kwargs):
    #    super(ProcessTypeResourceTypeForm, self).__init__(*args, **kwargs)
        #self.fields["resource_type"].choices = [
        #    (res.id, res.name) for res in EconomicResourceType.objects.all()
        #]
        #self.fields["relationship"].choices = [
        #    (rel.id, rel.name) for rel in ResourceRelationship.objects.exclude(resource_effect="+")
        #]

    class Meta:
        model = ProcessTypeResourceType
        exclude = ('process_type',)


class LaborInputForm(forms.ModelForm):
    resource_type = forms.ModelChoiceField(
        queryset=EconomicResourceType.objects.types_of_work(), 
        empty_label=None, 
        widget=SelectWithPopUp(model=EconomicResourceType))
    relationship = forms.ModelChoiceField(
        queryset=ResourceRelationship.objects.exclude(resource_effect="+"), 
        empty_label=None, 
        widget=SelectWithPopUp(model=ResourceRelationship))
    unit_of_quantity = forms.ModelChoiceField(
        queryset=Unit.objects.filter(unit_type='time'),  
        widget=SelectWithPopUp(model=Unit))

    class Meta:
        model = ProcessTypeResourceType
        exclude = ('process_type',)


class TimeForm(forms.Form):

    description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(attrs={"cols": "80"}),
    )
    url = forms.CharField(
        label=_("URL"),
        max_length=96,
        required=False,
        widget=forms.TextInput(attrs={"size": "80"}),
    )

class EquationForm(forms.Form):

    equation = forms.CharField(
        label=_("Equation"),
        required=True,
        widget=forms.Textarea(attrs={"rows": "4", "cols": "60"}),
    )

    amount = forms.CharField(
        label=_("Amount to distribute"),
        required=False,
        widget=forms.TextInput(),
    )


    def clean_equation(self):
        equation = self.cleaned_data["equation"]
        safe_dict = {}
        safe_dict['hours'] = 1
        safe_dict['rate'] = 1
        safe_dict['importance'] = 1
        safe_dict['reputation'] = 1
        safe_dict['seniority'] = 1

        try:
            eval(equation, {"__builtins__":None}, safe_dict)
        except NameError:
            raise forms.ValidationError(sys.exc_info()[1])
        except SyntaxError:
            raise forms.ValidationError("Equation syntax error")
        except:
            raise forms.ValidationError(sys.exc_info()[0])

        return equation
