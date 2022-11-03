function getCookie(name) {
	var cookieValue = null;

	if (document.cookie && document.cookie !== '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = cookies[i].trim();
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

var csrftoken = getCookie('csrftoken');


function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}


$.ajaxSetup({
	beforeSend: function(xhr, settings) {
		if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
			xhr.setRequestHeader("X-CSRFToken", csrftoken);
		}
	}
});


function sendAjax(url, data) {
	$.ajax({
		url: url,
		type: "POST",
		data: data,
		success: function(response) {
			if (response.reload === 'true') {
				location.reload();
			}

			if (response.redirect !== undefined) {
				location.href = response.redirect;
			}
		},
		complete: function() {},
		error: function (data) {
			if (data.responseJSON.error === 'badMeeting') {
				alert(data.responseJSON.msg);

				var g = $('#going');
				var ng = $('#notGoing');

				g.attr('checked', false);
				g.parent().removeClass('active');
				ng.attr('checked', true);
				ng.parent().addClass('active');
				
				gEventArg.setExtendedProp('going', 'false');
				gEventArg.setProp('color', 'orange');
			}
		}
	});
}


function postEvt(url, start, end, title = '', oldStart = -1, oldEnd = -1, evLocation = '', notes = '', lock = '') {
	data = {
		start: start,
		end: end,
		title: title,
		oldStart: oldStart,
		oldEnd: oldEnd,
		location: evLocation,
		notes: notes,
		lock: lock
	};

	sendAjax(url, data);
}


function postAtMeeting(url, start, end, isJoin) {
	data = {
		start: start,
		end: end,
		join: isJoin,
		oldStart: -1,
		oldEnd: -1
	};

	sendAjax(url, data);
}


function postCreateGroup(url, groupName) {
	data = {
		groupName: groupName
	};

	sendAjax(url, data)
}


function postGroupLeave(url) {
	data = {
		leave: 'true'
	};

	sendAjax(url, data);
}


function postUserAdmin(url, action, userID, username = '') {
	data = {
		action: action,
		userID: userID,
		username: username
	};

	sendAjax(url, data)
}


function postInvite(url, action, groupID) {
	data = {
		action: action,
		groupID: groupID
	};

	sendAjax(url, data)
}



var USER_TABLE = 0;
var GROUP_TABLE = 1;

var gCalendar;
var gEventArg;
var gEventCreated;
var gAddUrl = "";
var gRemUrl = "";
var gAtMeetingUrl = "";
var gMembershipUrl = "";
var gGroupCreateUrl = "";

var gMember = 0;
var gUserAdminUrl = "";
var gInvitationUrl = "";

var gIsAdmin = "False";


function buildCalender(tableType, date, evts) {
	document.addEventListener('DOMContentLoaded', function() {
		var calendarEl = document.getElementById('calendar');


		switch (tableType) {
			case USER_TABLE:
				evtCol = null;
				break;

			case GROUP_TABLE:
				evtCol = 'orange';
				break;

			default:
				evtCol = null;
				break;
		}


		var calendar = new FullCalendar.Calendar(calendarEl, {
			plugins: [ 'interaction', 'timeGrid', 'list' ],
			header: {
				left: 'title',
				center: '',
				right: 'timeGridWeek,timeGridDay,listMonth'
			},
			defaultDate: date,
			defaultView: 'timeGridWeek',
			firstDay: 1,
			navLinks: false, // can click day/week names to navigate views
			businessHours: true, // display business hours
			editable: true,
			selectable: true,
			selectMirror: true,
			selectOverlap: false,
			eventOverlap: false,
			eventColor: evtCol,
			snapDuration: '00:05',

			select: function(arg) {
				openModal(arg, true, false);
			},

			eventClick: function(arg) {
				if (arg.event.extendedProps.evType === 'redirect') {
					location.href = arg.event.extendedProps.redirect;

				} else if (arg.event.extendedProps.evType !== 'static') {
					openModal(arg.event, false);
				}
			},

			eventDrop: function(arg) {
				postEvt(gAddUrl, arg.event.start, arg.event.end, arg.event.title, arg.oldEvent.start, arg.oldEvent.end);
			},

			eventResize: function(arg) {
				postEvt(gAddUrl, arg.event.start, arg.event.end, arg.event.title, arg.prevEvent.start, arg.prevEvent.end);
			},

			events: evts
		});

		calendar.render();

		gCalendar = calendar;
	});
}


function radioOn(elem) {
	elem.attr('checked', true);
	elem.parent().addClass('active');
}

function radioOff(elem) {
	elem.attr('checked', false);
	elem.parent().removeClass('active');
}


function openModal(arg, created, canDelete = true) {
	gEventArg = arg;
	gEventCreated = created;

	if (canDelete) {
		$('#evtDelete').attr('disabled', false);

	} else {
		$('#evtDelete').attr('disabled', true);
	}

	var g = $('#going');
	var ng = $('#notGoing');
	var l = $('#locked');
	var nl = $('#unlocked');

	if (!created) {

		if (arg.extendedProps.going === 'true') {
			radioOn(g);
			radioOff(ng);

		} else {
			radioOn(ng);
			radioOff(g);

		}

		if (arg.extendedProps.lock === 'True') {
			radioOn(l);
			radioOff(nl);

			if (gIsAdmin === 'False') {
				$('#evtTitle').attr('disabled', true);
				$('#evtLocation').attr('disabled', true);
				$('#evtNotes').attr('disabled', true);
				$('#evtDelete').addClass('d-none');

				$('#modalTitle').text("Edit meeting (locked)");
				$('#modalSave').addClass('d-none');
			}


		} else {
			radioOn(nl);
			radioOff(l);

			$('#evtTitle').attr('disabled', false);
			$('#evtLocation').attr('disabled', false);
			$('#evtNotes').attr('disabled', false);
			$('#evtDelete').removeClass('d-none');

			$('#modalTitle').text("Edit meeting");
			$('#modalSave').removeClass('d-none');
		}


		g.attr('disabled', false);
		ng.attr('disabled', false);


		$('#goingRow').empty()

		if (arg.extendedProps.goingMembers != undefined) {
			for (var i = 0; i < arg.extendedProps.goingMembers.length; i++) {	
				$('#goingRow').append('<div class="col-sm-4 my-auto"><h5>' + arg.extendedProps.goingMembers[i] + '</h5></div>')
			}
		}


		$('#evtLocation').val(arg.extendedProps.location);
		$('#evtNotes').val(arg.extendedProps.notes);
		$('#hiddenModal').removeClass('d-none');

	} else {
		radioOff(g);
		radioOff(ng);
		g.attr('disabled', true);
		ng.attr('disabled', true);

		radioOn(nl);
		radioOff(l);

		$('#evtTitle').attr('disabled', false);
		$('#evtLocation').attr('disabled', false);
		$('#evtNotes').attr('disabled', false);
		$('#evtDelete').removeClass('d-none');

		$('#modalTitle').text("Edit meeting");
		$('#modalSave').removeClass('d-none');

		$('#evtLocation').val('');
		$('#evtNotes').val('');
		$('#hiddenModal').addClass('d-none');
	}

	$('#evtTitle').val(arg.title);
	$('#modal').modal();
}


function editActivity() {
	var title = $('#evtTitle').val();

	if (gEventCreated) {
		gCalendar.addEvent({
			start: gEventArg.start,
			end: gEventArg.end,
			title: title
		});

	} else {
		gEventArg.setProp('title', title);
	}

	postEvt(gAddUrl, gEventArg.start, gEventArg.end, title);

	gCalendar.unselect()
}


function editMeeting() {
	var title = $('#evtTitle').val();

	var evLocation = $('#evtLocation').val();
	var notes = $('#evtNotes').val();
	var lock = $('input[name=lockRadio]:checked').val();
	
	if (lock) {
		var fixLock = lock[0].toUpperCase() + lock.slice(1);
	} else {
		var fixLock = '';
	}


	if (gEventCreated) {
		gCalendar.addEvent({
			start: gEventArg.start,
			end: gEventArg.end,
			title: title,
			going: 'false',
			location: evLocation,
			notes: notes,
			lock: fixLock,
			goingMembers: []
		});

	} else {
		gEventArg.setProp('title', title);
		gEventArg.setExtendedProp('location', evLocation);
		gEventArg.setExtendedProp('notes', notes);
		gEventArg.setExtendedProp('lock', fixLock);
	}

	postEvt(gAddUrl, gEventArg.start, gEventArg.end, title, -1, -1, evLocation, notes, lock);

	gCalendar.unselect()
}


function evtGoing() {
	postAtMeeting(gAtMeetingUrl, gEventArg.start, gEventArg.end, true);
	gEventArg.setExtendedProp('going', 'true');
	gEventArg.setProp('color', 'lightgreen');
}


function evtNotGoing() {
	postAtMeeting(gAtMeetingUrl, gEventArg.start, gEventArg.end, false);
	gEventArg.setExtendedProp('going', 'false');
	gEventArg.setProp('color', 'orange');
}


function deleteEvt() {
	postEvt(gRemUrl, gEventArg.start, gEventArg.end);

	gEventArg.remove();
}



function openLeaveModal() {
	$('#modalLeave').modal();
}


function createGroup() {
	postCreateGroup(gGroupCreateUrl, $('#createGroupName').val());
}


function leaveGroup() {
	postGroupLeave(gMembershipUrl);
}


function openAdminUserModal(user, founder, member, memberIsAdmin, memberHasAccepted) {
	gMember = member;

	var g = $('#giveAdmin');
	var ng = $('#removeAdmin');

	if (member != founder) {
		$('#kick').attr('disabled', false);

	} else {
		$('#kick').attr('disabled', true);
	}

	if (user == founder && memberHasAccepted === 'True') {
		if (memberIsAdmin === 'True') {
			radioOn(g);
			radioOff(ng);

		} else {
			radioOn(ng);
			radioOff(g);
		}

		g.attr('disabled', false);
		ng.attr('disabled', false);
		$('#hiddenAdminModal').removeClass('d-none');
	
	} else {
		radioOff(g);
		radioOff(ng);
		g.attr('disabled', true);
		ng.attr('disabled', true);
		$('#hiddenAdminModal').addClass('d-none');
	}

	$('#userAdminModal').modal();
}


function kick() {
	postUserAdmin(gUserAdminUrl, 'kick', gMember);
}


function giveAdmin() {
	postUserAdmin(gUserAdminUrl, 'giveAdmin', gMember);
}


function removeAdmin() {
	postUserAdmin(gUserAdminUrl, 'removeAdmin', gMember);
}


function addUsername() {
	postUserAdmin(gUserAdminUrl, 'invite', -1, $('#addUsername').val())
}


function acceptGroup(groupID) {
	postInvite(gInvitationUrl, 'accept', groupID)
}


function denyGroup(groupID) {
	postInvite(gInvitationUrl, 'deny', groupID)
}
