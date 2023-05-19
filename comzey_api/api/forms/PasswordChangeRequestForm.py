from django import forms

class PasswordChangeRequestForm(forms.Form):
    email_or_username = forms.CharField(label=("Email Or Username"), max_length=254)