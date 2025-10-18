from django.urls import path
from .views import signup_view, index_view
from django.contrib.auth import views as auth_views
from .forms import CustomAuthenticationForm

app_name = "core"

urlpatterns = [
    path('', index_view, name='index'), 
    path('signup/', signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        form_class=CustomAuthenticationForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name="core/password_reset_form.html"), name="password_reset"),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name="core/password_reset_done.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="core/password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name="core/password_reset_complete.html"), name="password_reset_complete"),
]
