from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'sweeper'

urlpatterns = [
	path('', views.index, name='index'),
	path('about/', views.about, name='about'),
	path('timetable/', views.timetable, name='timetable'),
	path('timetable/add/', views.add, name='add'),
	path('timetable/remove/', views.remove, name='remove'),
	path('group/<int:groupID>/', views.group, name='group'),
	path('group/<int:groupID>/add/', views.groupAdd, name='groupAdd'),
	path('group/<int:groupID>/remove/', views.groupRemove, name='groupRemove'),
	path('group/<int:groupID>/meeting/at/', views.atMeeting, name='atMeeting'),
	path('group/<int:groupID>/membership/', views.groupMembership, name='groupMembership'),
	path('group/<int:groupID>/admin/user/', views.adminUser, name='adminUser'),
	path('group/create/', views.createGroup, name='createGroup'),
	path('group/invitation/', views.invitation, name='invitation'),
]