from django.views.generic import TemplateView
from django.views.generic.edit import FormView, DeleteView
from django.views.generic.edit import UpdateView, CreateView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash
from django_comments.models import Comment
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib.auth.views import PasswordResetView
from .forms import CustomPasswordResetForm
from rest_framework.authtoken.models import Token

from bhtom_base.bhtom_common.forms import ChangeUserPasswordForm, CustomUserCreationForm, GroupForm
from bhtom_base.bhtom_common.mixins import SuperuserRequiredMixin


class GroupCreateView(SuperuserRequiredMixin, CreateView):
    """
    View that handles creation of a user ``Group``. Requires authorization.
    """
    form_class = GroupForm
    model = Group
    success_url = reverse_lazy('user-list')


class GroupDeleteView(SuperuserRequiredMixin, DeleteView):
    """
    View that handles deletion of a user ``Group``. Requires authorization.
    """
    model = Group
    success_url = reverse_lazy('user-list')


class GroupUpdateView(SuperuserRequiredMixin, UpdateView):
    """
    View that handles modification of a user ``Group``. Requires authorization.
    """
    form_class = GroupForm
    model = Group
    success_url = reverse_lazy('user-list')

    def get_initial(self, *args, **kwargs):
        """
        Adds the ``User`` objects that are associated with this ``Group`` to the initial data.

        :returns: list of users
        :rtype: QuerySet
        """
        initial = super().get_initial(*args, **kwargs)
        initial['users'] = self.get_object().user_set.all()
        return initial


class UserListView(LoginRequiredMixin, TemplateView):
    """
    View that handles display of the list of ``User`` and ``Group`` objects. Requires authentication.
    """
    template_name = 'auth/user_list.html'


class UserDeleteView(SuperuserRequiredMixin, DeleteView):
    """
    View that handles deletion of a ``User``. Requires authorization.
    """
    success_url = reverse_lazy('user-list')
    model = User


class UserPasswordChangeView(SuperuserRequiredMixin, FormView):
    """
    View that handles modification of the password for a ``User``. Requires authorization.
    """
    template_name = 'bhtom_common/change_user_password.html'
    success_url = reverse_lazy('user-list')
    form_class = ChangeUserPasswordForm

    def form_valid(self, form):
        """
        Called after form is validated. Updates the password for the current specified user.

        :param form: Password submission form
        :type form: django.forms.Form
        """
        user = User.objects.get(pk=self.kwargs['pk'])
        user.set_password(form.cleaned_data['password'])
        user.save()
        messages.success(self.request, 'Password successfully changed')
        return super().form_valid(form)


class UserCreateView(SuperuserRequiredMixin, CreateView):
    """
    View that handles ``User`` creation. Requires authorization.
    """
    template_name = 'bhtom_common/create_user.html'
    success_url = reverse_lazy('user-list')
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        """
        Called after form is validated. Creates the ``User`` and adds them to the public ``Group``.

        :param form: User creation form
        :type form: django.forms.Form
        """
        super().form_valid(form)
        group, _ = Group.objects.get_or_create(name='Public')
        group.user_set.add(self.object)
        group.save()
        return redirect(self.get_success_url())


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """
    View that handles ``User`` modification. Requires authentication to call, and authorization to update.
    """
    model = User
    template_name = 'bhtom_common/create_user.html'
    form_class = CustomUserCreationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        try:
            token = Token.objects.get(user=user) 
            context['user_token'] = token.key
        except Token.DoesNotExist:
            context['user_token'] = None
        return context
    
    def get_success_url(self):
        """
        Returns the redirect URL for a successful update. If the current user is a superuser, returns the URL for the
        user list. Otherwise, returns the URL for updating the current user.

        :returns: URL for user list or update user
        :rtype: str
        """
        if self.request.user.is_superuser:
            return reverse_lazy('user-list')
        else:
            return reverse_lazy('user-update', kwargs={'pk': self.request.user.id})

    def get_form(self, form_class=None):
        """
        Gets the user update form and removes the password requirement. Removes the groups field if the user is not a
        superuser.

        :returns: Form used by this view
        :rtype: CustomUserCreationForm
        """
        form = super().get_form()
        form.fields['password1'].required = False
        form.fields['password2'].required = False

        return form

    def dispatch(self, *args, **kwargs):
        """
        Directs the class-based view to the correct method for the HTTP request method. Ensures that non-superusers
        are not incorrectly updating the profiles of other users.
        """
        if not self.request.user.is_superuser and self.request.user.id != self.kwargs['pk']:
            return redirect('user-update', self.request.user.id)
        else:
            return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        Called after form is validated. Updates the ``User`` and the session hash to maintain login session.

        :param form: User creation form
        :type form: django.forms.Form
        """
        super().form_valid(form)
        if self.get_object() == self.request.user:
            update_session_auth_hash(self.request, self.object)
        messages.success(self.request, 'Profile updated')
        return redirect(self.get_success_url())


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """
    View that handles deletion of a ``Comment``. Requires authentication to call, and authorization to delete.
    """
    model = Comment

    def get_success_url(self):
        messages.success(self.request, 'Successfully delete')
        print(self.kwargs)
        return reverse_lazy('bhtom_targets:detail', kwargs={'pk': self.kwargs['pk_target']})

    def delete(self, request, *args, **kwargs):

        if request.user == self.get_object().user or request.user.is_superuser:
            return super().delete(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Not authorized')


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
      
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs