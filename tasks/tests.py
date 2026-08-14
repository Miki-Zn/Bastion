from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Task


class TaskAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')  # nosec B106 - test fixture, not a real credential
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')  # nosec B106 - test fixture, not a real credential
        self.task = Task.objects.create(title='My task', owner=self.user)
        self.other_task = Task.objects.create(title='Not my task', owner=self.other_user)

    def test_unauthenticated_request_rejected(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_only_sees_own_tasks(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [task['title'] for task in response.data]
        self.assertIn('My task', titles)
        self.assertNotIn('Not my task', titles)

    def test_blank_title_rejected(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/tasks/', {'title': '   ', 'status': 'todo'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)