from django import forms
from .models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "date",
            "description",
            "category",
            "amount",
            "transaction_type",
            "payment_source",
            "paid_by",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "transaction_type": forms.Select(attrs={"class": "form-select"}),
            "payment_source": forms.Select(attrs={"class": "form-select"}),
            "paid_by": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get("transaction_type")
        payment_source = cleaned_data.get("payment_source")
        paid_by = cleaned_data.get("paid_by")

        if transaction_type == "IN" and paid_by is None:
            self.add_error("paid_by", "Please select who paid this money in.")

        if transaction_type == "OUT" and payment_source == "PERSONAL" and paid_by is None:
            self.add_error("paid_by", "Please select who paid personally for this expense.")

        return cleaned_data