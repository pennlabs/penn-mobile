from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

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


class WrappedModelsTestCase(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username="test", password="test")
        self.semester = Semester.objects.create(semester="2025fa")
        self.semester2 = Semester.objects.create(semester="2025sp")

        self.ind_key = IndividualStatKey.objects.create(key="gsr_hours")
        self.glob_key = GlobalStatKey.objects.create(key="total_gsr_hours")


        self.ind_stat = IndividualStat.objects.create(
            user=self.user,
            key=self.ind_key,
            value="5",
            semester=self.semester,
        )
        self.glob_stat = GlobalStat.objects.create(
            key=self.glob_key,
            value="1000",
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
        self.glob_field = GlobalStatPageField.objects.create(
            global_stat_key=self.glob_key,
            page=self.page,
            text_field_name="bottom",
        )

    def test_semester_current(self):
        self.semester.set_current()
        self.assertTrue(self.semester.current)
        self.assertFalse(self.semester2.current)
        self.assertEqual(Semester.objects.get(current=True), self.semester)
        self.semester2.set_current()
        self.semester.refresh_from_db()
        self.semester2.refresh_from_db()
        self.assertFalse(self.semester.current)
        self.assertTrue(self.semester2.current)
    
    def test_semester_current_unique(self):
        self.semester.set_current()
        with self.assertRaises(IntegrityError):
            self.semester2.current = True
            self.semester2.save()




    def test_str_methods(self):
        self.assertEqual("GSR_Page", str(self.page))
        self.assertEqual("User: test -- gsr_hours-2025fa : 5", str(self.ind_stat))
        self.assertEqual("Global -- total_gsr_hours-2025fa : 1000", str(self.glob_stat))
        self.assertEqual("2025fa", str(self.semester))
        self.assertEqual("GSR_Page -> top : gsr_hours", str(self.ind_field))
        self.assertEqual("GSR_Page -> bottom : total_gsr_hours", str(self.glob_field))
        
    def test_semester_pages(self):
        self.assertEqual([self.page, self.page2], list(self.semester.pages.all()))


    def test_unique_together_individualstat(self):
        with self.assertRaises(IntegrityError):
            IndividualStat.objects.create(
                user=self.user,
                key=self.ind_key,
                value="6",
                semester=self.semester,
            )
    def test_unique_together_globalstat(self):
        with self.assertRaises(IntegrityError):
            GlobalStat.objects.create(
                key=self.glob_key,
                value="200",
                semester=self.semester,
            )

    def test_page_fields(self):
        self.assertEqual([self.ind_key], list(self.page.individual_stats.all()))
        self.assertEqual([self.glob_key], list(self.page.global_stats.all()))


    def test_stat_page_fields(self):
        self.assertEqual(self.ind_key, self.ind_field.individual_stat_key)
        self.assertEqual(self.glob_key, self.glob_field.global_stat_key)
        self.assertEqual(self.page, self.ind_field.page)
        self.assertEqual(self.page, self.glob_field.page)
        self.assertEqual("top", self.ind_field.text_field_name)
        self.assertEqual("bottom", self.glob_field.text_field_name)
        
    
    def test_stat_page_get_value(self):
        self.assertEqual("5", self.ind_field.get_value(self.user, self.semester))
        self.assertEqual("1000", self.glob_field.get_value(self.user, self.semester))