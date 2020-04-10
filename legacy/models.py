# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and
#   * delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Account(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    first = models.TextField(blank=True, null=True)
    last = models.TextField(blank=True, null=True)
    pennkey = models.CharField(unique=True, max_length=255)
    pennid = models.IntegerField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    affiliation = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "account"


class AnalyticsEvent(models.Model):
    user = models.ForeignKey("User", models.DO_NOTHING, db_column="user", blank=True, null=True)
    account = models.ForeignKey(Account, models.DO_NOTHING, blank=True, null=True)
    timestamp = models.DateTimeField()
    type = models.CharField(max_length=50)
    index = models.IntegerField()
    post_id = models.CharField(max_length=255, blank=True, null=True)
    is_interaction = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "analytics_event"


class AnonymousId(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    type = models.CharField(max_length=255, blank=True, null=True)
    device_key = models.CharField(max_length=255, blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "anonymous_id"


class ArInternalMetadata(models.Model):
    key = models.CharField(primary_key=True, max_length=255)
    value = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "ar_internal_metadata"


class Course(models.Model):
    name = models.TextField()
    dept = models.TextField()
    code = models.TextField()
    section = models.TextField()
    term = models.TextField()
    weekdays = models.TextField()
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    start_time = models.TextField()
    end_time = models.TextField()
    building = models.TextField(blank=True, null=True)
    room = models.TextField(blank=True, null=True)
    extra_meetings_flag = models.IntegerField()

    class Meta:
        managed = False
        db_table = "course"


class CourseAccount(models.Model):
    account = models.OneToOneField(Account, models.DO_NOTHING, primary_key=True)
    course = models.ForeignKey(Course, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "course_account"
        unique_together = (("account", "course"),)


class CourseAnonymousId(models.Model):
    anonymous = models.OneToOneField(AnonymousId, models.DO_NOTHING, primary_key=True)
    course = models.ForeignKey(Course, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "course_anonymous_id"
        unique_together = (("anonymous", "course"),)


class CourseInstructor(models.Model):
    course = models.OneToOneField(Course, models.DO_NOTHING, primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "course_instructor"
        unique_together = (("course", "name"),)


class CourseMeetingTime(models.Model):
    course = models.OneToOneField(Course, models.DO_NOTHING, primary_key=True)
    weekday = models.CharField(max_length=3)
    start_time = models.CharField(max_length=10)
    end_time = models.TextField()
    building = models.TextField(blank=True, null=True)
    room = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "course_meeting_time"
        unique_together = (("course", "weekday", "start_time"),)


class Degree(models.Model):
    code = models.CharField(primary_key=True, max_length=255)
    name = models.TextField()
    school = models.ForeignKey("School", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "degree"


class DiningBalance(models.Model):
    account = models.ForeignKey(Account, models.DO_NOTHING, blank=True, null=True)
    dining_dollars = models.FloatField()
    swipes = models.IntegerField()
    guest_swipes = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "dining_balance"


class DiningPreference(models.Model):
    created_at = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey("User", models.DO_NOTHING)
    account = models.ForeignKey(
        Account, models.DO_NOTHING, db_column="account", blank=True, null=True
    )
    venue_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "dining_preference"


class DiningTransaction(models.Model):
    account = models.ForeignKey(Account, models.DO_NOTHING, blank=True, null=True)
    date = models.DateTimeField()
    description = models.TextField()
    amount = models.FloatField()
    balance = models.FloatField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "dining_transaction"


class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.TextField()
    name = models.TextField()
    description = models.TextField()
    image_url = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    image_file_name = models.CharField(max_length=255, blank=True, null=True)
    image_content_type = models.CharField(max_length=255, blank=True, null=True)
    image_file_size = models.IntegerField(blank=True, null=True)
    image_updated_at = models.DateTimeField(blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "event"


class EventUsers(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(unique=True, max_length=255)
    encrypted_password = models.CharField(max_length=255)
    reset_password_token = models.CharField(unique=True, max_length=255, blank=True, null=True)
    reset_password_sent_at = models.DateTimeField(blank=True, null=True)
    remember_created_at = models.DateTimeField(blank=True, null=True)
    sign_in_count = models.IntegerField()
    current_sign_in_at = models.DateTimeField(blank=True, null=True)
    last_sign_in_at = models.DateTimeField(blank=True, null=True)
    current_sign_in_ip = models.CharField(max_length=255, blank=True, null=True)
    last_sign_in_ip = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "event_users"


class GsrRoomName(models.Model):
    lid = models.IntegerField(primary_key=True)
    gid = models.IntegerField()
    rid = models.IntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "gsr_room_name"
        unique_together = (("lid", "gid", "rid"),)


class HomeCellOrder(models.Model):
    cell_type = models.TextField()

    class Meta:
        managed = False
        db_table = "home_cell_order"


class Housing(models.Model):
    account = models.OneToOneField(
        Account, models.DO_NOTHING, db_column="account", primary_key=True
    )
    house = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    off_campus = models.IntegerField(blank=True, null=True)
    start = models.IntegerField()
    end = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "housing"
        unique_together = (("account", "start"),)


class LaundryPreference(models.Model):
    created_at = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey("User", models.DO_NOTHING)
    account = models.ForeignKey(
        Account, models.DO_NOTHING, db_column="account", blank=True, null=True
    )
    room_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "laundry_preference"


class LaundrySnapshot(models.Model):
    date = models.DateField()
    time = models.IntegerField()
    room = models.IntegerField()
    washers = models.IntegerField()
    dryers = models.IntegerField()
    total_washers = models.IntegerField()
    total_dryers = models.IntegerField()

    class Meta:
        managed = False
        db_table = "laundry_snapshot"


class Major(models.Model):
    code = models.CharField(primary_key=True, max_length=255)
    name = models.TextField()
    degree_code = models.ForeignKey(Degree, models.DO_NOTHING, db_column="degree_code")

    class Meta:
        managed = False
        db_table = "major"


class NotificationSetting(models.Model):
    account = models.OneToOneField(
        Account, models.DO_NOTHING, db_column="account", primary_key=True
    )
    setting = models.CharField(max_length=255)
    enabled = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "notification_setting"
        unique_together = (("account", "setting"),)


class NotificationToken(models.Model):
    account = models.OneToOneField(
        Account, models.DO_NOTHING, db_column="account", primary_key=True
    )
    ios_token = models.CharField(max_length=255, blank=True, null=True)
    android_token = models.CharField(max_length=255, blank=True, null=True)
    dev = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "notification_token"


class Post(models.Model):
    account = models.ForeignKey("PostAccount", models.DO_NOTHING, db_column="account")
    source = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)
    time_label = models.TextField(blank=True, null=True)
    post_url = models.TextField(blank=True, null=True)
    image_url = models.TextField()
    filters = models.IntegerField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    approved = models.IntegerField(blank=True, null=True)
    offline = models.IntegerField()
    testers = models.IntegerField()
    emails = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    image_url_cropped = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "post"


class PostAccount(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    name = models.TextField()
    email = models.CharField(unique=True, max_length=255)
    encrypted_password = models.CharField(max_length=255)
    reset_password_token = models.CharField(unique=True, max_length=255, blank=True, null=True)
    reset_password_token_sent_at = models.DateTimeField(blank=True, null=True)
    sign_in_count = models.IntegerField()
    last_sign_in_at = models.DateTimeField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "post_account"


class PostAccountEmail(models.Model):
    account = models.OneToOneField(
        PostAccount, models.DO_NOTHING, db_column="account", primary_key=True
    )
    email = models.CharField(max_length=255)
    verified = models.IntegerField(blank=True, null=True)
    auth_token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "post_account_email"
        unique_together = (("account", "email"),)


class PostFilter(models.Model):
    post = models.OneToOneField(Post, models.DO_NOTHING, db_column="post", primary_key=True)
    type = models.CharField(max_length=255)
    filter = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "post_filter"
        unique_together = (("post", "type", "filter"),)


class PostStatus(models.Model):
    post = models.OneToOneField(Post, models.DO_NOTHING, db_column="post", primary_key=True)
    status = models.CharField(max_length=255)
    msg = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "post_status"
        unique_together = (("post", "status", "created_at"),)


class PostTargetEmail(models.Model):
    post = models.OneToOneField(Post, models.DO_NOTHING, db_column="post", primary_key=True)
    email = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "post_target_email"
        unique_together = (("post", "email"),)


class PostTester(models.Model):
    post = models.OneToOneField(Post, models.DO_NOTHING, db_column="post", primary_key=True)
    email = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "post_tester"
        unique_together = (("post", "email"),)


class PrivacySetting(models.Model):
    account = models.OneToOneField(
        Account, models.DO_NOTHING, db_column="account", primary_key=True
    )
    setting = models.CharField(max_length=255)
    enabled = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "privacy_setting"
        unique_together = (("account", "setting"),)


class SchemaMigrations(models.Model):
    version = models.CharField(primary_key=True, max_length=255)

    class Meta:
        managed = False
        db_table = "schema_migrations"


class School(models.Model):
    name = models.TextField()
    code = models.TextField()

    class Meta:
        managed = False
        db_table = "school"


class SchoolMajorAccount(models.Model):
    account = models.OneToOneField(Account, models.DO_NOTHING, primary_key=True)
    school = models.ForeignKey(School, models.DO_NOTHING)
    major = models.ForeignKey(Major, models.DO_NOTHING, db_column="major")
    expected_grad = models.TextField()

    class Meta:
        managed = False
        db_table = "school_major_account"
        unique_together = (("account", "school", "major"),)


class StudySpacesBooking(models.Model):
    date = models.DateTimeField(blank=True, null=True)
    lid = models.IntegerField(blank=True, null=True)
    rid = models.IntegerField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    booking_id = models.TextField(blank=True, null=True)
    is_cancelled = models.IntegerField()
    reminder_sent = models.IntegerField()
    account = models.ForeignKey(
        Account, models.DO_NOTHING, db_column="account", blank=True, null=True
    )
    user = models.ForeignKey("User", models.DO_NOTHING, db_column="user", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "study_spaces_booking"


class UniversityEvent(models.Model):
    type = models.TextField()
    name = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "university_event"


class User(models.Model):
    created_at = models.DateTimeField(blank=True, null=True)
    platform = models.TextField()
    device_id = models.TextField()
    email = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "user"
