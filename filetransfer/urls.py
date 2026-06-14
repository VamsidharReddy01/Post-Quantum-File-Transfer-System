from django.urls import path

from .views import (
    AcceptTransferView,
    DownloadTransferView,
    ReceivedRequestsView,
    RejectTransferView,
    SendFileView,
    TransferHistoryView,
)

app_name = "filetransfer"

urlpatterns = [
    path("send/", SendFileView.as_view(), name="send"),
    path("received/", ReceivedRequestsView.as_view(), name="received"),
    path("history/", TransferHistoryView.as_view(), name="history"),
    path("<int:pk>/accept/", AcceptTransferView.as_view(), name="accept"),
    path("<int:pk>/reject/", RejectTransferView.as_view(), name="reject"),
    path("<int:pk>/download/", DownloadTransferView.as_view(), name="download"),
]
