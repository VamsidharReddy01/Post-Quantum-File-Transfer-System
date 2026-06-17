from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from filetransfer.models import FileTransfer, TransferStatus


class LandingPageView(TemplateView):
    template_name = "dashboard/landing.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update(
            sent_count=FileTransfer.objects.filter(sender=user).count(),
            received_count=FileTransfer.objects.filter(receiver=user).count(),
            pending_count=FileTransfer.objects.filter(
                receiver=user,
                status=TransferStatus.PENDING,
            ).count(),
            downloaded_count=FileTransfer.objects.filter(
                receiver=user,
                status=TransferStatus.DOWNLOADED,
            ).count(),
            recent_transfers=FileTransfer.objects.filter(receiver=user)[:5],
        )
        return context
