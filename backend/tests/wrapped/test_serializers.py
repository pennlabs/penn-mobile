from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from wrapped.serializers import PageSerializer, SemesterSerializer

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


class WrappedSerializersTestCase(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username="test", password="test")
        self.semester = Semester.objects.create(semester="2025fa")

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


    def test_page_serializer(self):
        serializer = PageSerializer(self.page, context={"semester": self.semester, "user": self.user})
        data = serializer.data
        self.assertEqual(data["name"], "GSR_Page")
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["template_path"], "wrapped/gsr_page.html")
        self.assertEqual(data["duration"], "00:01:00")
        self.assertEqual(data["combined_stats"], {"top": "5", "bottom": "1000", "middle": "10", "middle_left": "2000"})


    def test_semester_serializer(self):
        serializer = SemesterSerializer(self.semester, context={"user": self.user})
        data = serializer.data
        self.assertEqual(data["semester"], "2025fa")
        self.assertEqual(data["pages"], [PageSerializer(self.page, context={"semester": self.semester, "user": self.user}).data, PageSerializer(self.page2, context={"semester": self.semester, "user": self.user}).data])
