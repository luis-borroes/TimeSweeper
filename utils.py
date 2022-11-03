from django.utils import timezone
from datetime import datetime
from django.contrib.auth.models import User


"""
Get user intervals from database
Sort the set of intervals by their start time
Initialize results array
Set first item of array to be the first interval in the set

For every interval higher:
    Lower interval = Last item of results array
    
    Test for the intersection of the intervals
    (We know the start of higher is bigger than the start of lower)

    If start of higher <= end of lower:

        Upper bound = Largest of the ends of higher and lower
        Replace last item in results array by the interval:
            (Start of lower, upper bound)
    
    Otherwise:
        Add higher interval to the results array
"""


def mergeIntervals(intervals):
	results = []

	if len(intervals) > 0:
		first = intervals[0]
		results.append((first['start'], first['end']))

		for higher in intervals[1:]:
			lower = results[-1]

			if higher['start'] <= lower[1]:
				upperBound = max(higher['end'], lower[1])
				results[-1] = (lower[0], upperBound)

			else:
				results.append((higher['start'], higher['end']))

	return results


def getIntervalNum(dateObj):
	weekDay = dateObj.weekday()
	hour = dateObj.hour
	minute = dateObj.minute

	num = weekDay * (24 * (60 / 5))
	num = num + hour * (60 / 5)
	num = num + minute / 5
	
	return num


def ajaxToInterval(request):
	#trim off excess
	start = " ".join(request.POST['start'].split()[0:5])
	end = " ".join(request.POST['end'].split()[0:5])

	startObj = timezone.make_aware(datetime.strptime(start, "%a %b %d %Y %H:%M:%S"))
	endObj = timezone.make_aware(datetime.strptime(end, "%a %b %d %Y %H:%M:%S"))

	startNum = getIntervalNum(startObj)
	endNum = getIntervalNum(endObj)

	oldStartNum = -1
	oldEndNum = -1

	if request.POST['oldStart'] != '-1':
		oldStart = " ".join(request.POST['oldStart'].split()[0:5])
		oldEnd = " ".join(request.POST['oldEnd'].split()[0:5])

		oldStartObj = timezone.make_aware(datetime.strptime(oldStart, "%a %b %d %Y %H:%M:%S"))
		oldEndObj = timezone.make_aware(datetime.strptime(oldEnd, "%a %b %d %Y %H:%M:%S"))

		oldStartNum = getIntervalNum(oldStartObj)
		oldEndNum = getIntervalNum(oldEndObj)


	interval = {
		'startNum': startNum,
		'endNum': endNum,
		'oldStartNum': oldStartNum,
		'oldEndNum': oldEndNum
	}

	return interval
