from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import LoginForm, RegisterForm
from .services.audit_service import log_action
from .services.registration_service import register_user


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = register_user(form.cleaned_data, self.request)
        log_action(user, "Registration", self.request)
        messages.success(self.request, "Registration successful. You can now log in.")
        self.object = user
        return redirect(self.get_success_url())


class UserLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    pass
