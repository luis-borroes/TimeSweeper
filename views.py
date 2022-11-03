from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from sweeper.utils import mergeIntervals, getIntervalNum, ajaxToInterval

from .models import *


@login_required
def index(request):
	user = request.user

	groups = Group.objects.filter(usergroup__user=user, usergroup__accepted=True)
	invites = Group.objects.filter(usergroup__user=user, usergroup__accepted=False)


	userMeetings = Meeting.objects.filter(usermeeting__user=user)
	meetings = []

	for i in userMeetings:
		jsInterval = i.getJSInterval()

		dateA, timeA = jsInterval['start'].split('T')
		dateB, timeB = jsInterval['end'].split('T')

		timeA = timeA[0:5]
		timeB = timeB[0:5]

		timeFormat = {
			'dateA': dateA,
			'dateB': dateB,
			'timeA': timeA,
			'timeB': timeB
		}


		meeting = {
			'obj': i,
			'timeFormat': timeFormat,
			'interval': jsInterval,
			'group': i.group,
			'goingMembers': i.goingMembers(user)
		}
		
		meetings.append(meeting)


	context = {
		'groups': groups,
		'invites': invites,
		'meetings': meetings
	}

	return render(request, 'sweeper/index.html', context)


def about(request):
	user = request.user

	return render(request, 'sweeper/about.html')


@login_required
@ensure_csrf_cookie
def timetable(request):
	user = request.user

	now = timezone.now()
	date = now.strftime("%Y-%m-%d")

	intervals = Timetable.objects.filter(user=user)
	activityDates = [i.getJSInterval() for i in intervals]


	userMeetings = Meeting.objects.filter(usermeeting__user=user)
	meetingDates = []

	for i in userMeetings:
		jsInterval = i.getJSInterval()
		jsInterval['group'] = i.group.name
		jsInterval['redirect'] = reverse('sweeper:group', args=[i.group.id])
		meetingDates.append(jsInterval)


	context = {
		'username': user.username,
		'date': date,
		'activityDates': activityDates,
		'meetingDates': meetingDates
	}

	return render(request, 'sweeper/timetable.html', context)


@login_required
@ensure_csrf_cookie
def add(request):
	user = request.user

	interval = ajaxToInterval(request)
	startNum = interval['startNum']
	endNum = interval['endNum']
	oldStartNum = interval['oldStartNum']
	oldEndNum = interval['oldEndNum']

	title = request.POST['title']


	if oldStartNum == -1:
		newInterval, isCreated = user.timetable_set.get_or_create(start=startNum, end=endNum)
		newInterval.title = title
		newInterval.save()

	else:
		newInterval = user.timetable_set.get(start=oldStartNum, end=oldEndNum)
		newInterval.start = startNum
		newInterval.end = endNum
		newInterval.title = title
		newInterval.save()


	return HttpResponseRedirect(reverse('sweeper:timetable'))


@login_required
@ensure_csrf_cookie
def remove(request):
	user = request.user

	interval = ajaxToInterval(request)
	startNum = interval['startNum']
	endNum = interval['endNum']


	try:
		userIntervals = user.timetable_set.filter(start=startNum, end=endNum)

	except (KeyError, Timetable.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:timetable'))

	else:
		for userInterval in userIntervals:
			userInterval.delete()

	return HttpResponseRedirect(reverse('sweeper:timetable'))



@login_required
@ensure_csrf_cookie
def group(request, groupID):
	user = request.user

	try:
		group = Group.objects.get(id=groupID)
		usergroup = UserGroup.objects.get(user=user, group=group, accepted=True)

	except (KeyError, UserGroup.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))

	except (KeyError, Group.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))


	now = timezone.now()
	date = now.strftime("%Y-%m-%d")

	intervals = group.getAllIntervals()
	merged = mergeIntervals(intervals)
	timetableObjs = [Timetable(start=i[0], end=i[1], user=user) for i in merged]
	blockedDates = [i.getJSInterval() for i in timetableObjs]

	
	userGoing = Meeting.objects.filter(group=groupID, usermeeting__user=user)
	userNotGoing = Meeting.objects.filter(group=groupID).exclude(usermeeting__user=user)

	meetingDates = []

	for i in userGoing:
		jsInterval = i.getJSInterval()
		jsInterval['going'] = 'true'
		jsInterval['color'] = 'lightgreen'
		jsInterval['location'] = i.location
		jsInterval['notes'] = i.notes
		jsInterval['lock'] = i.lock
		jsInterval['goingMembers'] = i.goingMembersSerialized(user)
		meetingDates.append(jsInterval)

	for i in userNotGoing:
		jsInterval = i.getJSInterval()
		jsInterval['going'] = 'false'
		jsInterval['color'] = 'orange'
		jsInterval['location'] = i.location
		jsInterval['notes'] = i.notes
		jsInterval['lock'] = i.lock
		jsInterval['goingMembers'] = i.goingMembersSerialized(user)
		meetingDates.append(jsInterval)


	members = UserGroup.objects.filter(group=group).select_related('user')


	context = {
		'username': user.username,
		'group': group,
		'date': date,
		'blockedDates': blockedDates,
		'meetingDates': meetingDates,
		'groupID': groupID,
		'members': members,
		'usergroup': usergroup
	}

	return render(request, 'sweeper/group.html', context)


@login_required
@ensure_csrf_cookie
def groupAdd(request, groupID):
	user = request.user

	try:
		group = Group.objects.get(id=groupID)
		member = UserGroup.objects.get(user=user, group=group, accepted=True)

	except (KeyError, UserGroup.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))

	except (KeyError, Group.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))


	interval = ajaxToInterval(request)
	startNum = interval['startNum']
	endNum = interval['endNum']
	oldStartNum = interval['oldStartNum']
	oldEndNum = interval['oldEndNum']

	title = request.POST['title']
	location = request.POST['location']
	notes = request.POST['notes']


	if oldStartNum == -1:
		meeting, isCreated = Meeting.objects.get_or_create(group=group, start=startNum, end=endNum)
		
	else:
		meeting = Meeting.objects.get(group=group, start=oldStartNum, end=oldEndNum)
		meeting.start = startNum
		meeting.end = endNum


	if not meeting.lock or member.admin:
		meeting.title = title
		meeting.location = location
		meeting.notes = notes

		if member.admin:
			if request.POST['lock'] == 'true':
				meeting.lock = True

			elif request.POST['lock'] == 'false':
				meeting.lock = False

		else:
			meeting.lock = False

		meeting.save()


	return HttpResponseRedirect(reverse('sweeper:group', args=[groupID]))


@login_required
@ensure_csrf_cookie
def groupRemove(request, groupID):
	user = request.user

	try:
		member = UserGroup.objects.get(user=user, group=groupID, admin=True, accepted=True)
		interval = ajaxToInterval(request)
		startNum = interval['startNum']
		endNum = interval['endNum']

		meetings = Meeting.objects.filter(group=groupID, start=startNum, end=endNum)

	except (KeyError, UserGroup.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))
	
	except (KeyError, Meeting.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:group', args=[groupID]))

	else:
		for meeting in meetings:
			meeting.delete()


	return HttpResponseRedirect(reverse('sweeper:group', args=[groupID]))


@login_required
@ensure_csrf_cookie
def atMeeting(request, groupID):
	user = request.user

	try:
		group = Group.objects.get(id=groupID)
		member = UserGroup.objects.get(user=user, group=group, accepted=True)
		interval = ajaxToInterval(request)
		startNum = interval['startNum']
		endNum = interval['endNum']

		meeting = Meeting.objects.get(group=group, start=startNum, end=endNum)


	except (KeyError, UserGroup.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))

	except (KeyError, Group.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))
	
	except (KeyError, Meeting.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:group', args=[groupID]))


	if request.POST['join'] == 'true':
		intervals = group.getAllIntervals()
		merged = mergeIntervals(intervals)
		timetableObjs = [Timetable(start=i[0], end=i[1], user=user) for i in merged]

		for i in timetableObjs:
			if meeting.intersects(i):
				response = JsonResponse({"error": "badMeeting", "msg": "Meeting is invalid: overlaps a blocked date"})
				response.status_code = 403
				return response

		userMeeting = UserMeeting.objects.get_or_create(user=user, meeting=meeting)

	elif request.POST['join'] == 'false':
		try:
			userMeetings = UserMeeting.objects.filter(user=user, meeting=meeting)
	
		except (KeyError, UserMeeting.DoesNotExist):
			return HttpResponseRedirect(reverse('sweeper:group', args=[groupID]))

		else:
			for userMeeting in userMeetings:
				userMeeting.delete()



	return HttpResponseRedirect(reverse('sweeper:group', args=[groupID]))


@login_required
@ensure_csrf_cookie
def groupMembership(request, groupID):
	user = request.user

	try:
		member = UserGroup.objects.get(user=user, group=groupID)

	except (KeyError, UserGroup.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))


	if request.POST['leave'] == 'true':
		UserMeeting.objects.filter(user=user, meeting__group__id=groupID).delete()
		member.delete()
		return JsonResponse({'reload': 'true'})


@login_required
@ensure_csrf_cookie
def createGroup(request):
	user = request.user

	if request.POST['groupName'] == '':
			return JsonResponse({'redirect': reverse('sweeper:index')})

	newGroup = Group.objects.create(name=request.POST['groupName'], founder=user)
	userGroup = UserGroup.objects.create(user=user, group=newGroup, admin=True, accepted=True)

	return JsonResponse({'redirect': reverse('sweeper:group', args=[newGroup.id])})


@login_required
@ensure_csrf_cookie
def invitation(request):
	user = request.user

	try:	
		group = Group.objects.get(id=request.POST['groupID'])
		userGroup = UserGroup.objects.get(user=user, group=group)

	except (KeyError, Group.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))

	except (KeyError, UserGroup.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))


	if request.POST['action'] == 'accept':
		userGroup.accepted = True
		userGroup.save()

	elif request.POST['action'] == 'deny':
		userGroup.delete()


	return JsonResponse({'reload': 'true'})


@login_required
@ensure_csrf_cookie
def adminUser(request, groupID):
	user = request.user

	try:
		usergroup = UserGroup.objects.get(user=user, group=groupID, admin=True, accepted=True)
		group = Group.objects.get(id=groupID)

		if request.POST['userID'] != '-1':
			member = User.objects.get(id=request.POST['userID'])

		else:
			member = User.objects.get(username__iexact=request.POST['username'])


	except (KeyError, User.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))

	except (KeyError, Group.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))

	except (KeyError, UserGroup.DoesNotExist):
		return HttpResponseRedirect(reverse('sweeper:index'))


	if request.POST['action'] == 'kick':
		if (group.founder != member):
			kickGroup = UserGroup.objects.get(user=member, group=group)
			UserMeeting.objects.filter(user=member, meeting__group=group).delete()
			kickGroup.delete()


	elif request.POST['action'] == 'invite':

		newMember, isCreated = UserGroup.objects.get_or_create(user=member, group=group, admin=False, accepted=False)


	elif request.POST['action'] == 'giveAdmin':
		if (group.founder == user):
			adminGroup = UserGroup.objects.get(user=member, group=group, accepted=True)
			adminGroup.admin = True
			adminGroup.save()


	elif request.POST['action'] == 'removeAdmin':
		if (group.founder == user):
			adminGroup = UserGroup.objects.get(user=member, group=group, accepted=True)
			adminGroup.delete()
			adminGroup.admin = False
			adminGroup.save()


	return JsonResponse({'reload': 'true'})
