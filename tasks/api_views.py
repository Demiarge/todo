"""
REST API: List tasks, Create task.
Role-based: Owner → full access; Collaborator → update only (status).
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q
from django.utils.timesince import timesince

from .models import Task, Notification
from .serializers import TaskListSerializer, TaskCreateSerializer, TaskUpdateSerializer
from .utils import user_can_edit_task, user_can_view_task, user_can_update_status


def get_visible_tasks(user):
    """Tasks user owns or is assigned to (collaborator)."""
    return Task.objects.filter(
        Q(creator=user) | Q(assigned_users=user)
    ).distinct().order_by('-created_at')


class TaskListCreateAPI(generics.ListCreateAPIView):
    """
    GET: List tasks (owner or collaborator only).
    POST: Create task (creator = request.user).
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskListSerializer

    def get_queryset(self):
        return get_visible_tasks(self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class TaskDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve task (owner or collaborator).
    PUT/PATCH: Owner → full update; Collaborator → status only.
    DELETE: Owner only.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskListSerializer

    def get_queryset(self):
        return get_visible_tasks(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TaskUpdateSerializer
        return TaskListSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if not user_can_view_task(request.user, instance):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user_can_edit_task(request.user, instance):
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(TaskListSerializer(instance).data)
        # Collaborator: update status only
        if not user_can_update_status(request.user, instance):
            return Response({'detail': 'You can only update status for this task.'}, status=status.HTTP_403_FORBIDDEN)
        new_status = request.data.get('status')
        if new_status not in dict(Task.STATUS_CHOICES):
            return Response({'status': ['Invalid choice.']}, status=status.HTTP_400_BAD_REQUEST)
        instance.status = new_status
        instance.save()
        return Response(TaskListSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not user_can_edit_task(request.user, instance):
            return Response({'detail': 'Only the task owner can delete it.'}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_unread_count(request):
    """Get unread notification count for the current user."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'count': count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_latest(request):
    """Get latest notifications since a given notification ID."""
    since_id = request.GET.get('since', 0)
    try:
        since_id = int(since_id)
    except (ValueError, TypeError):
        since_id = 0
    
    notifications = Notification.objects.filter(
        user=request.user,
        id__gt=since_id
    ).order_by('-created_at')[:10]
    
    notification_list = []
    for n in notifications:
        notification_list.append({
            'id': n.id,
            'message': n.message,
            'time': timesince(n.created_at) + ' ago',
            'is_read': n.is_read,
            'task_id': n.task.id if n.task else None
        })
    
    return Response({'notifications': notification_list})
