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
        # since the user is not an admin, approved should be set to false after update
        self.assertFalse(res_json["approved"])

    def test_update_post_admin(self):
        admin = User.objects.create_superuser("admin@upenn.edu", "admin", "admin")
        self.client.force_authenticate(user=admin)
        payload = {"source": "New Test Source 3"}
        response = self.client.patch(f"/portal/posts/{self.id}/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(self.id, res_json["id"])
        self.assertTrue(res_json["approved"])
        self.assertFalse("admin_comment" in res_json)

    def test_browse(self):
        payload = {
            "source": "Test Source 2",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "not approved",
        }
        self.client.post("/portal/posts/", payload)
        response = self.client.get("/portal/posts/browse/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual(2, Post.objects.all().count())

    def test_review_post_no_admin_comment(self):
        # No admin comment
        Post.objects.create(
            user=self.test_user,
            source="Test source 2",
            title="Test title 2",
            subtitle="Test subtitle 2",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
            created_at=timezone.localtime(),
        )
        admin = User.objects.create_superuser("admin@upenn.edu", "admin", "admin")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/portal/posts/review/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("Test source 2", res_json[0]["source"])
        self.assertEqual(2, Post.objects.all().count())

    def test_review_post_admin_comment_empty(self):
        # Admin comment is empty and approved is False
        Post.objects.create(
            user=self.test_user,
            source="Test source 2",
            title="Test title 2",
            subtitle="Test subtitle 2",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
            created_at=timezone.localtime(),
            approved=False,
            admin_comment="",
        )
        admin = User.objects.create_superuser("admin@upenn.edu", "admin", "admin")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/portal/posts/review/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("Test source 2", res_json[0]["source"])
        self.assertEqual(2, Post.objects.all().count())

    def test_posts_status(self):
        Post.objects.create(
            user=self.test_user,
            source="Test Source 2",
            title="Test Title 2",
            subtitle="Test Subtitle 2",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
            created_at=timezone.localtime(),
            approved=False,
        )

        Post.objects.create(
            user=self.test_user,
            source="Test Source 3",
            title="Test Title 3",
            subtitle="Test Subtitle 3",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
            created_at=timezone.localtime(),
            approved=False,
            admin_comment="Need Revision!",
        )
        response = self.client.get("/portal/posts/status/")
        res_json = json.loads(response.content)
        self.assertEqual(3, len(res_json))

        approved = res_json["approved"]
        self.assertEqual(1, len(approved))
        self.assertEqual("Test Source 1", approved[0]["source"])

        awaiting = res_json["awaiting_approval"]
        self.assertEqual(1, len(awaiting))
        self.assertEqual("Test Source 2", awaiting[0]["source"])

        revision = res_json["revision"]
        self.assertEqual(1, len(revision))
        self.assertEqual("Test Source 3", revision[0]["source"])
