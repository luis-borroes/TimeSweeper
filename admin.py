from django.contrib import admin

from .models import Timetable, Group, UserGroup, Meeting, UserMeeting

admin.site.register(Timetable)
admin.site.register(Group)
admin.site.register(UserGroup)
admin.site.register(Meeting)
admin.site.register(UserMeeting)