from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import PQCKey
from .pqc_service import generate_dilithium_keypair, generate_kyber_keypair


@transaction.atomic
def register_user(cleaned_data, request=None):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=cleaned_data["username"],
        email=cleaned_data["email"].lower(),
        password=cleaned_data["password1"],
        first_name=cleaned_data.get("first_name", ""),
        last_name=cleaned_data.get("last_name", ""),
    )
    kyber_public_key, kyber_private_key = generate_kyber_keypair()
    dilithium_public_key, dilithium_private_key = generate_dilithium_keypair()
    PQCKey.objects.create(
        user=user,
        kyber_public_key=kyber_public_key,
        kyber_private_key=kyber_private_key,
        dilithium_public_key=dilithium_public_key,
        dilithium_private_key=dilithium_private_key,
    )
    return user
