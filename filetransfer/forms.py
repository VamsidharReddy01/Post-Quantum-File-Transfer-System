from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import FileTransfer

MAX_UPLOAD_SIZE = 25 * 1024 * 1024


class FileTransferForm(forms.ModelForm):
    receiver_user_id = forms.CharField(
        label="Receiver User ID",
        max_length=5,
        help_text="Enter the receiver's 5-digit user ID.",
    )
    file = forms.FileField()

    class Meta:
        model = FileTransfer
        fields = ("file", "download_limit", "expires_at")
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "download_limit": forms.NumberInput(attrs={"min": 1, "max": 10}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.receiver = None
        self.fields["expires_at"].initial = timezone.now() + timezone.timedelta(days=7)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["receiver_user_id"].widget.attrs.update(
            {
                "inputmode": "numeric",
                "pattern": "[0-9]{5}",
                "placeholder": "Example: 48291",
                "autocomplete": "off",
            }
        )

    def clean_receiver_user_id(self):
        receiver_user_id = self.cleaned_data["receiver_user_id"].strip()
        if not receiver_user_id.isdigit() or len(receiver_user_id) != 5:
            raise forms.ValidationError("Enter a valid 5-digit receiver user ID.")
        try:
            receiver = get_user_model().objects.get(user_id=receiver_user_id)
        except get_user_model().DoesNotExist as error:
            raise forms.ValidationError("User not found.") from error
        if receiver == self.user:
            raise forms.ValidationError("You cannot send a file to yourself.")
        self.receiver = receiver
        self.cleaned_data["receiver"] = receiver
        return receiver_user_id

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
