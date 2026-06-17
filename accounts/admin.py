from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, PQCKey


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "user_id", "email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "user_id", "email", "first_name", "last_name")
    ordering = ("username",)
    readonly_fields = ("user_id",)


@admin.register(PQCKey)
class PQCKeyAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "kyber_public_preview",
        "dilithium_public_preview",
        "created_at",
    )

    readonly_fields = (
        "user",
        "created_at",
        "kyber_public_preview",
        "kyber_private_preview",
        "dilithium_public_preview",
        "dilithium_private_preview",
    )

    def kyber_public_preview(self, obj):
        return (
            obj.kyber_public_key.hex()[:100]
            if obj.kyber_public_key
            else "No Key"
        )

    kyber_public_preview.short_description = "Kyber Public Key"

    def kyber_private_preview(self, obj):
        return (
            obj.kyber_private_key.hex()[:100]
            if obj.kyber_private_key
            else "No Key"
        )

    kyber_private_preview.short_description = "Kyber Private Key"

    def dilithium_public_preview(self, obj):
        return (
            obj.dilithium_public_key.hex()[:100]
            if obj.dilithium_public_key
            else "No Key"
        )

    dilithium_public_preview.short_description = "Dilithium Public Key"

    def dilithium_private_preview(self, obj):
        return (
            obj.dilithium_private_key.hex()[:100]
            if obj.dilithium_private_key
            else "No Key"
        )

    dilithium_private_preview.short_description = "Dilithium Private Key"
