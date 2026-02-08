from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, Http404

from .models import Task, Notification, Profile, TaskComment
from .forms import UserRegistrationForm, TaskForm, TaskStatusForm, ProfileForm, CommentForm, UserUpdateForm
from .utils import (
    user_can_edit_task,
    user_can_update_status,
    user_can_view_task,
    notify_assigned,
    notify_status_update,
)


def home(request):
    """Landing page."""
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    return render(request, 'tasks/home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('tasks:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'tasks/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}.')
            next_url = request.GET.get('next') or 'tasks:dashboard'
            return redirect(next_url)
        messages.error(request, 'Invalid username or password.')
    return render(request, 'tasks/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('tasks:home')


@login_required
def dashboard(request):
    """Personalized dashboard: created, assigned, completed, overdue."""
    user = request.user
    today = timezone.now().date()

    created = Task.objects.filter(creator=user)
    assigned = Task.objects.filter(assigned_users=user).exclude(creator=user)
    my_tasks = (created | assigned).distinct()

    completed = my_tasks.filter(status='completed')
    overdue = my_tasks.filter(due_date__lt=today).exclude(status='completed')

    # Quick stats for the overview cards
    total = my_tasks.count()
    completed_count = completed.count()
    
    # Exclude overdue tasks from Pending/In Progress counts.
    # A task is overdue if its due_date < today AND it's not completed.
    
    pending_count = my_tasks.filter(
        Q(status='pending') & (Q(due_date__gte=today) | Q(due_date__isnull=True))
    ).count()
    
    in_progress_count = my_tasks.filter(
        Q(status='in_progress') & (Q(due_date__gte=today) | Q(due_date__isnull=True))
    ).count()

    # Weekly analytics
    week_start = today - timezone.timedelta(days=today.weekday())
    completed_this_week = my_tasks.filter(
        status='completed',
        completed_at__date__gte=week_start
    ).count()
    completion_percentage = round((completed_count / total * 100) if total else 0, 1)

    # Handle search & filter from the query params
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search = request.GET.get('q', '').strip()

    created_qs = created
    assigned_qs = assigned

    if status_filter:
        created_qs = created_qs.filter(status=status_filter)
        assigned_qs = assigned_qs.filter(status=status_filter)
    if priority_filter:
        created_qs = created_qs.filter(priority=priority_filter)
        assigned_qs = assigned_qs.filter(priority=priority_filter)
    if search:
        created_qs = created_qs.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
        assigned_qs = assigned_qs.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    context = {
        'created_tasks': created_qs,
        'assigned_tasks': assigned_qs,
        'completed_tasks': completed[:10],
        'overdue_tasks': overdue[:10],
        'total_tasks': total,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_this_week': completed_this_week,
        'completion_percentage': completion_percentage,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search': search,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, creator=request.user)
        if form.is_valid():
            task = form.save()
            # Let 'em know they've been assigned!
            for u in task.assigned_users.all():
                notify_assigned(task, u)
            return redirect('tasks:task_detail', slug=task.slug)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm(creator=request.user)
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create Task'})


@login_required
def task_detail(request, slug):
    try:
        task = get_object_or_404(Task, slug=slug)
    except Http404:
        return render(request, '404.html', status=404)
    if not user_can_view_task(request.user, task):
        return render(request, 'tasks/access_denied.html', status=403)
    can_edit = user_can_edit_task(request.user, task)
    can_update_status = user_can_update_status(request.user, task)
    status_form = TaskStatusForm(instance=task) if can_update_status else None
    comments = task.comments.select_related('user').all()
    comment_form = CommentForm()
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'can_edit': can_edit,
        'can_update_status': can_update_status,
        'status_form': status_form,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
def task_add_comment(request, slug):
    try:
        task = get_object_or_404(Task, slug=slug)
    except Http404:
        return render(request, '404.html', status=404)
    if not user_can_view_task(request.user, task):
        return render(request, 'tasks/access_denied.html', status=403)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added.')
            return redirect('tasks:task_detail', slug=task.slug)
    return redirect('tasks:task_detail', slug=task.slug)


@login_required
def task_edit(request, slug):
    try:
        task = get_object_or_404(Task, slug=slug)
    except Http404:
        return render(request, '404.html', status=404)
    if not user_can_edit_task(request.user, task):
        return render(request, 'tasks/access_denied.html', status=403)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, creator=request.user)
        if form.is_valid():
            old_assigned = set(task.assigned_users.values_list('pk', flat=True))
            task = form.save()
            new_assigned = set(task.assigned_users.values_list('pk', flat=True))
            for uid in new_assigned - old_assigned:
                u = task.assigned_users.get(pk=uid)
                notify_assigned(task, u)
            messages.success(request, f'Task "{task.title}" updated.')
            return redirect('tasks:task_detail', slug=task.slug)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm(instance=task, creator=request.user)
    return render(request, 'tasks/task_form.html', {'form': form, 'task': task, 'title': 'Edit Task'})


@login_required
def task_delete(request, slug):
    try:
        task = get_object_or_404(Task, slug=slug)
    except Http404:
        return render(request, '404.html', status=404)
    if not user_can_edit_task(request.user, task):
        return render(request, 'tasks/access_denied.html', status=403)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('tasks:dashboard')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_update_status(request, slug):
    try:
        task = get_object_or_404(Task, slug=slug)
    except Http404:
        return render(request, '404.html', status=404)
    if not user_can_update_status(request.user, task):
        return render(request, 'tasks/access_denied.html', status=403)
    if request.method == 'POST':
        form = TaskStatusForm(request.POST, instance=task)
        if form.is_valid():
            old_status = task.status
            form.save()
            if task.status != old_status:
                notify_status_update(
                    task,
                    f'Task "{task.title}" status changed to {task.get_status_display()}.'
                )
            messages.success(request, 'Status updated.')
            return redirect('tasks:task_detail', slug=task.slug)
    return redirect('tasks:task_detail', slug=task.slug)


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)[:50]
    # Mark all unread notifications as read on page load
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'tasks/notifications.html', {'notifications': notifications})


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    if request.GET.get('next'):
        return redirect(request.GET.get('next'))
    return redirect('tasks:notifications')


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('tasks:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile
    }
    return render(request, 'tasks/profile.html', context)


@login_required
def user_search_api(request):
    """Return usernames matching query (for assignee autocomplete)."""
    q = (request.GET.get('q') or '').strip()
    if len(q) < 1:
        return JsonResponse({'users': []})
    users = list(
        User.objects.filter(username__istartswith=q)
        .exclude(pk=request.user.pk)
        .values_list('username', flat=True)[:10]
    )
    return JsonResponse({'users': users})


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)
