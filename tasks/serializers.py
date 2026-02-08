from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task


class TaskListSerializer(serializers.ModelSerializer):
    """List tasks: owner or collaborator only."""
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    assigned_usernames = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'due_date', 'created_at', 'updated_at', 'completed_at',
            'creator_username', 'assigned_usernames',
        ]

    def get_assigned_usernames(self, obj):
        return list(obj.assigned_users.values_list('username', flat=True))


class TaskCreateSerializer(serializers.ModelSerializer):
    """Create task: sets creator to request.user."""
    assigned_users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 'due_date',
            'assigned_users',
        ]
        extra_kwargs = {
            'status': {'default': 'pending'},
            'priority': {'default': 'medium'},
        }

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        assigned = validated_data.pop('assigned_users', [])
        task = Task.objects.create(**validated_data)
        if assigned:
            task.assigned_users.set(assigned)
        return task


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Owner: full update. Collaborator: status only (enforced in api_views)."""
    assigned_users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'due_date', 'assigned_users']
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
            'status': {'required': False},
            'priority': {'required': False},
            'due_date': {'required': False},
        }

    def update(self, instance, validated_data):
        assigned = validated_data.pop('assigned_users', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if assigned is not None:
            instance.assigned_users.set(assigned)
        return instance
