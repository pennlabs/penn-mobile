from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from wrapped.models import (
    GlobalStat,
    GlobalStatKey,
    GlobalStatPageField,
    IndividualStat,
    IndividualStatKey,
    IndividualStatPageField,
    Page,
    Semester,
)


User = get_user_model()


# Will add more failing tests


class WrappedRoutesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test", password="test")
        self.client.force_authenticate(user=self.user)

        self.semester = Semester.objects.create(semester="2025fa", current=True)

        self.ind_key = IndividualStatKey.objects.create(key="gsr_hours")
        self.glob_key = GlobalStatKey.objects.create(key="total_gsr_hours")
        self.glob_key2 = GlobalStatKey.objects.create(key="total_gym_hours")
        self.ind_key2 = IndividualStatKey.objects.create(key="gym_hours")

        self.ind_stat = IndividualStat.objects.create(
            user=self.user,
            key=self.ind_key,
            value="5",
            semester=self.semester,
        )

        self.ind_stat2 = IndividualStat.objects.create(
            user=self.user,
            key=self.ind_key2,
            value="10",
            semester=self.semester,
        )

        self.glob_stat = GlobalStat.objects.create(
            key=self.glob_key,
            value="1000",
            semester=self.semester,
        )
        self.glob_stat2 = GlobalStat.objects.create(
            key=self.glob_key2,
            value="2000",
            semester=self.semester,
        )

        self.page = Page.objects.create(
            name="GSR_Page",
            id=1,
            template_path="wrapped/gsr_page.html",
            duration=timedelta(minutes=1),
        )
        self.page2 = Page.objects.create(
            name="GSR_Page2",
            id=2,
            template_path="wrapped/gsr_page2.html",
            duration=timedelta(minutes=1),
        )
        self.semester.pages.add(self.page)
        self.semester.pages.add(self.page2)

        # Through models for page fields
        self.ind_field = IndividualStatPageField.objects.create(
            individual_stat_key=self.ind_key,
            page=self.page,
            text_field_name="top",
        )
        self.ind_field2 = IndividualStatPageField.objects.create(
            individual_stat_key=self.ind_key2,
            page=self.page,
            text_field_name="middle",
        )
        self.glob_field = GlobalStatPageField.objects.create(
            global_stat_key=self.glob_key,
            page=self.page,
            text_field_name="bottom",
        )
        self.glob_field2 = GlobalStatPageField.objects.create(
            global_stat_key=self.glob_key2,
            page=self.page,
            text_field_name="middle_left",
        )

    def test_get_current_semester(self):
        response = self.client.get("/wrapped/semester/current/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "semester": "2025fa",
                "pages": [
                    {
                        "id": 1,
                        "name": "GSR_Page",
                        "template_path": "wrapped/gsr_page.html",
                        "combined_stats": {
                            "top": "5",
                            "middle": "10",
                            "bottom": "1000",
                            "middle_left": "2000",
                        },
                        "duration": "00:01:00",
                    },
                    {
                        "id": 2,
                        "name": "GSR_Page2",
                        "template_path": "wrapped/gsr_page2.html",
                        "combined_stats": {},
                        "duration": "00:01:00",
                    },
                ],
            },
        )

    def test_get_semester(self):
        response = self.client.get("/wrapped/semester/2025fa/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "semester": "2025fa",
                "pages": [
                    {
                        "id": 1,
                        "name": "GSR_Page",
                        "template_path": "wrapped/gsr_page.html",
                        "combined_stats": {
                            "top": "5",
                            "middle": "10",
                            "bottom": "1000",
                            "middle_left": "2000",
                        },
                        "duration": "00:01:00",
                    },
                    {
                        "id": 2,
                        "name": "GSR_Page2",
                        "template_path": "wrapped/gsr_page2.html",
                        "combined_stats": {},
                        "duration": "00:01:00",
                    },
                ],
            },
        )
