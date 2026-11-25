from django import forms


class ComplaintForm(forms.Form):
    complain = forms.CharField(
        strip=False,
        error_messages={"required": "Please enter a complaint before submitting."},
    )

    def clean_complain(self):
        text = self.cleaned_data["complain"]
        if not text.strip():
            raise forms.ValidationError(
                self.fields["complain"].error_messages["required"],
                code="required",
            )
        return text
