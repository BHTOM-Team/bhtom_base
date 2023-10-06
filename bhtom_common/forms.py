from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.models import User, Group
from bhtom_custom_registration.bhtom_registration.models import LatexUser


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
    email = forms.EmailField(required=True, label='Email*')
    groups = forms.ModelMultipleChoiceField(Group.objects.all().exclude(name='Public'),
                                            required=False, widget=forms.CheckboxSelectMultiple)

    latex_name = forms.CharField(required=True, label='Latex Name*',
                                 help_text="Your name as you want it to appear correctly in potential publications")
    latex_affiliation = forms.CharField(required=True, label='Latex Affiliation*',
                                        help_text="Your affiliation as you want it to appear correctly in potential publications")
    address = forms.CharField(label='Address')
    about_me = forms.CharField(label='About me')
    orcid_id = forms.CharField(
        label=mark_safe('ORCID ID, <a href="https://orcid.org/" target="_blank">more details</a>'),
        widget=forms.TextInput(attrs={'placeholder': 'Enter your ORCID ID'}),
        required=False  # You can set this to True if the field is required
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'groups')
        field_classes = {'username': UsernameField}
        labels = {
            'username': 'Username*',
        }
    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        # Because this form is used for both create and update user, and the user can be updated without modifying the
        # password, we check if the password field has been populated in order to set a new one.
        
        if self.cleaned_data['password1']:
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
            dp, created= LatexUser.objects.get_or_create(user=user)
            dp.user = user
            dp.latex_name = self.cleaned_data['latex_name']
            dp.latex_affiliation = self.cleaned_data['latex_affiliation']
            dp.address = self.cleaned_data['address']
            dp.about_me =self.cleaned_data['about_me']
            dp.orcid_id =self.cleaned_data['orcid_id']
            dp.save()
        
        return user
