from django import forms
from django.contrib.auth import password_validation
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.models import User, Group
from bhtom_custom_registration.bhtom_registration.models import LatexUser
from django.utils.translation import gettext_lazy as _


class ChangeUserPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())


class GroupForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(User.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Group
        fields = ('name', 'users')

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.user_set.set(self.cleaned_data['users'])
        instance.save()
        return instance


class CustomUserCreationForm(UserCreationForm):
    """
    Form used for creation of new users and update of existing users.
    """
    username = forms.CharField(required=True,
                               label='User name*',
                               widget=forms.TextInput(attrs={'placeholder': 'User name'}),
                               max_length=150)
    first_name = forms.CharField(required=True,
                                 label='First name*',
                                 widget=forms.TextInput(attrs={'placeholder': 'First name'}),
                                 max_length=150)
    last_name = forms.CharField(required=True,
                                label='Last name*',
                                widget=forms.TextInput(attrs={'placeholder': 'Last name'}),
                                max_length=150)

    email = forms.EmailField(required=True,
                             label='Email*',
                             widget=forms.TextInput(attrs={'placeholder': 'Email'}),
                             max_length=150)

    password1 = forms.CharField(
        required=True,
        label=_("Password*"),
        widget=forms.PasswordInput(),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
        max_length=128
    )
    password2 = forms.CharField(
        required=True,
        label=_("Password confirmation*"),
        widget=forms.PasswordInput(),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
        max_length=128
    )

    latex_name = forms.CharField(required=True, label='Latex Name*',
                                 widget=forms.TextInput(attrs={'placeholder': 'Latex Name'}),
                                 help_text="Your name as you want it to appear correctly in potential publications")
    latex_affiliation = forms.CharField(required=True, label='Affiliation*',
                                        widget=forms.TextInput(attrs={'placeholder': 'Affiliation'}),
                                        help_text="Your affiliation as you want it to appear correctly in potential publications")

    address = forms.CharField(required=False, label='Address', max_length=150)
    about_me = forms.CharField(required=True, label='About me*', max_length=150)

    orcid_id = forms.CharField(
        label=mark_safe('ORCID ID, <a href="https://orcid.org/" target="_blank">more details</a>'),
        widget=forms.TextInput(attrs={'placeholder': 'Enter your ORCID ID'}),
        required=False  # You can set this to True if the field is required
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'latex_name',
                  'latex_affiliation', 'address', 'about_me', 'orcid_id')
        field_classes = {'username': UsernameField, }

    def __init__(self, *args, **kwargs):
        try:
            data = LatexUser.objects.get(user_id=kwargs['instance'].id)
        except Exception as e:
            data = None
        super().__init__(*args, **kwargs)

        if data:
            self.initial['latex_name'] = data.latex_name
            self.initial['latex_affiliation'] = data.latex_affiliation
            self.initial['address'] = data.address
            self.initial['about_me'] = data.about_me
            self.initial['orcid_id'] = data.orcid_id

            self.fields['password1'].widget.attrs.update({"placeholder": "*****", "autocomplete": "new-password"})
            self.fields['password2'].widget.attrs.update({"placeholder": "*****", "autocomplete": "new-password"})
        else:
            self.fields['password1'].widget.attrs.update({"placeholder": "Password", "autocomplete": "new-password"})
            self.fields['password2'].widget.attrs.update(
                {"placeholder": "Password confirmation", "autocomplete": "new-password"})

    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        # Because this form is used for both create and update user, and the user can be updated without modifying the
        # password, we check if the password field has been populated in order to set a new one.

        if self.cleaned_data['password1']:
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
            dp, created = LatexUser.objects.get_or_create(user=user)
            dp.user = user
            dp.latex_name = self.cleaned_data['latex_name']
            dp.latex_affiliation = self.cleaned_data['latex_affiliation']
            dp.address = self.cleaned_data['address']
            dp.about_me = self.cleaned_data['about_me']
            dp.orcid_id = self.cleaned_data['orcid_id']
            dp.save()

        return user
