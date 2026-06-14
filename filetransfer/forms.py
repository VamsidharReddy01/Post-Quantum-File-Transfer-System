from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import FileTransfer

MAX_UPLOAD_SIZE = 25 * 1024 * 1024


class FileTransferForm(forms.ModelForm):
    file = forms.FileField()

    class Meta:
        model = FileTransfer
        fields = ("receiver", "file", "download_limit", "expires_at")
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "download_limit": forms.NumberInput(attrs={"min": 1, "max": 10}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["receiver"].queryset = get_user_model().objects.exclude(id=user.id)
        self.fields["receiver"].empty_label = "Select receiver"
        self.fields["expires_at"].initial = timezone.now() + timezone.timedelta(days=7)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["receiver"].widget.attrs["class"] = "form-select"

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if uploaded_file.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError("File size must be 25 MB or smaller.")
        return uploaded_file

    def clean_download_limit(self):
        limit = self.cleaned_data["download_limit"]
        if limit < 1 or limit > 10:
            raise forms.ValidationError("Download limit must be between 1 and 10.")
        return limit

    def clean_expires_at(self):
        expires_at = self.cleaned_data["expires_at"]
        if expires_at <= timezone.now():
            raise forms.ValidationError("Expiry must be in the future.")
        return expires_at


class TransferDecisionForm(forms.Form):
    transfer_id = forms.IntegerField(widget=forms.HiddenInput)
