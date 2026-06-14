from django.contrib import admin

from .models import AuditLog, FileTransfer


@admin.register(FileTransfer)
class FileTransferAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "sender",
        "receiver",
        "status",
        "created_at",
        "accepted_at",
        "downloaded_at",
    )
    search_fields = ("original_filename", "sender__username", "receiver__username", "file_hash")
    list_filter = ("status", "created_at", "accepted_at", "downloaded_at")
    ordering = ("-created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "ip_address", "timestamp")
    search_fields = ("user__username", "user__email", "action", "ip_address")
    list_filter = ("action", "timestamp")
    ordering = ("-timestamp",)
