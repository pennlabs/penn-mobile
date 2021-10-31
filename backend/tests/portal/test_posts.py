import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Post, TargetPopulation


User = get_user_model()


class TestPosts(TestCase):
    """Tests Created/Update/Retrieve for Posts"""

    def setUp(self):
        self.target_id = TargetPopulation.objects.create(population="SEAS").id
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

        payload = {
            "source": "Test Source 1",
            "title": "Test Title 1",
            "subtitle": "Test Subtitle 1",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "comment 1",
        }
        self.client.post("/portal/posts/", payload)
        post_1 = Post.objects.all().first()
        post_1.approved = True
        post_1.save()
        self.id = post_1.id

    def test_create_post(self):
        # Creates an unapproved post
        payload = {
            "source": "Test Source 2",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "comment 2",
        }
        response = self.client.post("/portal/posts/", payload)
        res_json = json.loads(response.content)
        # asserts that post was created and that the admin comment cannot be made
        self.assertEqual(2, Post.objects.all().count())
        self.assertEqual("Test Source 2", res_json["source"])
        self.assertEqual(None, Post.objects.get(id=res_json["id"]).admin_comment)

    def test_update_post(self):
        payload = {"source": "New Test Source 3"}
        response = self.client.patch(f"/portal/posts/{self.id}/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(self.id, res_json["id"])
        self.assertEqual("New Test Source 3", Post.objects.get(id=self.id).source)

    def test_browse(self):
        payload = {
            "source": "Test Source 2",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "comment 2",
        }
        self.client.post("/portal/posts/", payload)
        response = self.client.get("/portal/posts/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        self.assertEqual(2, Post.objects.all().count())
