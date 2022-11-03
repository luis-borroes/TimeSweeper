import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Interval(models.Model):
	start = models.IntegerField(default=0)
	end = models.IntegerField(default=0)
	title = models.CharField(max_length=200, default='')

	class Meta:
		abstract = True


	def getEdge(self, ofEnd):
		if not ofEnd:
			edge = self.start

		else:
			edge = self.end

		return edge


	def getWeekDay(self, ofEnd):
		edge = self.getEdge(ofEnd)

		return edge // (24 * (60/5)) #intervals of 5 minutes


	def getTimeTuple(self, ofEnd):
		edge = self.getEdge(ofEnd)

		numOnDay = edge % (24 * (60/5))

		hours = numOnDay // 12
		minutes = (numOnDay % 12) * 5

		return (int(hours), int(minutes))


	def getDate(self, ofEnd):
		#find the difference in days between current weekday and
		#interval weekday. calculate date using that. populates calendar

		now = timezone.now()
		weekDayDiff = self.getWeekDay(ofEnd) - now.weekday()

		delta = timezone.timedelta(weekDayDiff)

		actualDate = now + delta

		return actualDate


	def getRealTime(self, ofEnd):
		date = self.getDate(ofEnd)
		timeTuple = self.getTimeTuple(ofEnd)

		date = date.replace(hour=timeTuple[0], minute=timeTuple[1])

		return date


	def getRealTimes(self):
		return (self.getRealTime(False), self.getRealTime(True))


	def getJSInterval(self):
		times = []

		for i in self.getRealTimes():
			times.append(i.strftime("%Y-%m-%dT%H:%M:00"))

		return {'start': times[0], 'end': times[1], 'title': self.title}


	def intersects(self, interval):
		return (self.start < interval.end and self.end > interval.start)





class Timetable(Interval):
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	def __str__(self):
		return str(self.user) + " " + str(self.start) + " " + str(self.end) + " " + str(self.title)



class Group(models.Model):
	name = models.CharField(max_length=200)
	founder = models.ForeignKey(User, on_delete=models.CASCADE, default=2)

	def __str__(self):
		return self.name

	def getAllIntervals(self):
		# union the set of timetable intervals for all users in this group with
		# the set of all meetings for users in this group
		timetables = Timetable.objects.filter(user__usergroup__group=self, user__usergroup__accepted=True).values('start', 'end')
		meetings = Meeting.objects.filter(usermeeting__user__usergroup__group=self, usermeeting__user__usergroup__accepted=True).values('start', 'end')
		meetings = meetings.exclude(group=self)

		intervals = timetables.union(meetings)
		intervals = intervals.order_by('start')

		return intervals



class UserGroup(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	group = models.ForeignKey(Group, on_delete=models.CASCADE)
	admin = models.BooleanField(default=False)
	accepted = models.BooleanField(default=False)

	def __str__(self):
		return str(self.user) + " " + str(self.group) + " " + str(self.admin) + " " + str(self.accepted)



class Meeting(Interval):
	group = models.ForeignKey(Group, on_delete=models.CASCADE)
	location = models.CharField(max_length=200)
	notes = models.CharField(max_length=500)
	lock = models.BooleanField(default=False)

	def goingMembers(self, user):
		gMembers = User.objects.filter(usermeeting__meeting=self).exclude(id=user.id).values('username')

		return gMembers

	def goingMembersSerialized(self, user):
		gMembers = self.goingMembers(user)

		memberString = "['"
		hasMembers = False

		for i in gMembers:
			memberString += i['username'] + "', '"
			hasMembers = True


		if hasMembers:
			memberString = memberString[:-3]

		else:
			memberString = memberString[:-1]

		memberString += "]"

		return memberString

	def __str__(self):
		return str(self.group) + " " + str(self.start) + " " + str(self.end) + " " + str(self.title)



class UserMeeting(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)

	def __str__(self):
		return str(self.user) + " " + str(self.meeting)
