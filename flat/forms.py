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
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }