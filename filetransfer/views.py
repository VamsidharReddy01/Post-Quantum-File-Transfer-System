from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, ListView

from .forms import FileTransferForm
from .models import FileTransfer
from .services.transfer_service import (
    accept_transfer,
    build_download_response,
    create_transfer,
    reject_transfer,
)


class SendFileView(LoginRequiredMixin, FormView):
    form_class = FileTransferForm
    template_name = "filetransfer/send_file.html"
    success_url = reverse_lazy("filetransfer:history")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        create_transfer(
            sender=self.request.user,
            receiver=form.cleaned_data["receiver"],
            uploaded_file=form.cleaned_data["file"],
            download_limit=form.cleaned_data["download_limit"],
            expires_at=form.cleaned_data["expires_at"],
            request=self.request,
        )
        messages.success(self.request, "Encrypted transfer request created.")
        return super().form_valid(form)


class ReceivedRequestsView(LoginRequiredMixin, ListView):
    model = FileTransfer
    template_name = "filetransfer/received_requests.html"
    context_object_name = "transfers"
    paginate_by = 20

    def get_queryset(self):
        return FileTransfer.objects.select_related("sender", "receiver").filter(
            receiver=self.request.user
        )


class TransferHistoryView(LoginRequiredMixin, ListView):
    model = FileTransfer
    template_name = "filetransfer/history.html"
    context_object_name = "transfers"
    paginate_by = 20

    def get_queryset(self):
        return FileTransfer.objects.select_related("sender", "receiver").filter(
            sender=self.request.user
        )


class AcceptTransferView(LoginRequiredMixin, View):
    def post(self, request, pk):
        transfer = get_object_or_404(FileTransfer, pk=pk)
        try:
            accept_transfer(transfer, request.user, request)
            messages.success(request, "Transfer accepted and signature verified.")
        except (PermissionDenied, ValidationError) as error:
            messages.error(request, str(error))
        return redirect("filetransfer:received")


class RejectTransferView(LoginRequiredMixin, View):
    def post(self, request, pk):
        transfer = get_object_or_404(FileTransfer, pk=pk)
        try:
            reject_transfer(transfer, request.user, request)
            messages.success(request, "Transfer rejected.")
        except (PermissionDenied, ValidationError) as error:
            messages.error(request, str(error))
        return redirect("filetransfer:received")


class DownloadTransferView(LoginRequiredMixin, View):
    def post(self, request, pk):
        transfer = get_object_or_404(FileTransfer, pk=pk)
        try:
            return build_download_response(transfer, request.user, request)
        except (PermissionDenied, ValidationError) as error:
            messages.error(request, str(error))
            return redirect("filetransfer:received")
