from django import forms
from django.contrib.auth.models import User
from .models import Task, Profile, TaskComment


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Password')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm password')

    class Meta:
        model = User
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        data = super().clean()
        if data.get('password') != data.get('password_confirm'):
            raise forms.ValidationError({'password_confirm': 'Passwords do not match.'})
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class TaskForm(forms.ModelForm):
    assigned_usernames = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter usernames separated by commas'}),
        label='Assign to users',
        help_text='Type usernames separated by commas (e.g. alice, bob)'
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'status', 'priority', 'due_date')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.creator = kwargs.pop('creator', None)
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        if instance and instance.pk:
            usernames = list(instance.assigned_users.values_list('username', flat=True))
            initial['assigned_usernames'] = ', '.join(usernames)
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_assigned_usernames(self):
        raw = self.cleaned_data.get('assigned_usernames', '')
        if isinstance(raw, list):
            usernames = [str(u).strip() for u in raw if u]
        else:
            raw = (raw or '').strip()
            usernames = [u.strip() for u in raw.split(',') if u.strip()]
        if not usernames:
            return []
        found = set(User.objects.filter(username__in=usernames).values_list('username', flat=True))
        missing = set(usernames) - found
        if missing:
            raise forms.ValidationError(f'User(s) not found: {", ".join(missing)}')
        return list(found)

    def save(self, commit=True):
        task = super().save(commit=False)
        if self.creator:
            task.creator = self.creator
        if commit:
            task.save()
            usernames = self.cleaned_data.get('assigned_usernames', [])
            if usernames:
                users = User.objects.filter(username__in=usernames)
                task.assigned_users.set(users)
            else:
                task.assigned_users.clear()
        return task


class TaskStatusForm(forms.ModelForm):
    """Minimal form for assigned users to update status only."""

    class Meta:
        model = Task
        fields = ('status',)


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar',)
        widgets = {
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment…'}),
        }
