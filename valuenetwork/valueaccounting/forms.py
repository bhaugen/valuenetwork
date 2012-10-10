import sys
from decimal import *
from django import forms
from django.utils.translation import ugettext_lazy as _

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
        hours = 1
        rate = 1
        reputation = 1
        seniority = 1
        importance = 1
        eq = equation.split(" ")
        for i, x in enumerate(eq):
            try:
                y = Decimal(x)
                eq[i] = "".join(["Decimal('", x, "')"])
            except InvalidOperation:
                continue
        s = " "
        eq = s.join(eq)

        try:
            eval(eq)
        except NameError:
            raise forms.ValidationError(sys.exc_info()[1])
        except SyntaxError:
            raise forms.ValidationError("Equation syntax error")
        except:
            raise forms.ValidationError(sys.exc_info()[0])

        return equation
