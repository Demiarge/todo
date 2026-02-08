"""
Helper for permissions and notifications.
Role-based access for shared tasks:
  Owner (creator) → full access: edit, delete, assign.
  Collaborator (assigned user) → update only: view, update status, add comments.
"""
from .models import Task, Notification


def user_can_edit_task(user, task):
    """Owner only: edit/delete/assign."""
    return task.creator_id == user.id


def user_can_update_status(user, task):
    """Owner or collaborator: update status."""
    if task.creator_id == user.id:
        return True
    return task.assigned_users.filter(pk=user.pk).exists()


def user_can_view_task(user, task):
    """Creator or assigned user can view."""
    if task.creator_id == user.id:
        return True
    return task.assigned_users.filter(pk=user.pk).exists()


def notify_assigned(task, assigned_user, message=None):
    if message is None:
        message = f'You were assigned to task: {task.title}'
    Notification.objects.create(user=assigned_user, message=message, task=task)


def notify_status_update(task, message):
    """Notify creator and assigned users about status change."""
    users = [task.creator]
    for u in task.assigned_users.all():
        if u != task.creator:
            users.append(u)
    for user in users:
        Notification.objects.create(user=user, message=message, task=task)
