from django import forms
from .models import BookInstance


class LoanBookForm(forms.ModelForm):
    book_title = forms.CharField(disabled=True, required=False, label="Book")

    class Meta:
        model = BookInstance
        fields = ("book_title", "borrower")
