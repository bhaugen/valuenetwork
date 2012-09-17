import datetime
import time
import csv
from operator import attrgetter

from django.db.models import Q
from django.http import Http404
from django.views.generic import list_detail
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template import RequestContext
from django.http import HttpResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import simplejson
from django.forms.models import formset_factory, modelformset_factory

from valuenetwork.valueaccounting.models import *
from valuenetwork.valueaccounting.views import *
from valuenetwork.valueaccounting.forms import *
from valuenetwork.valueaccounting.utils import *

def projects(request):
    roots = Project.objects.filter(parent=None)
    
    return render_to_response("valueaccounting/projects.html", {
        "roots": roots,
    }, context_instance=RequestContext(request))

def contributions(request, project_id):
    #import pdb; pdb.set_trace()
    project = get_object_or_404(Project, pk=project_id)
    event_list = project.events.all()
    paginator = Paginator(event_list, 25)

    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        events = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        events = paginator.page(paginator.num_pages)
    
    return render_to_response("valueaccounting/project_contributions.html", {
        "project": project,
        "events": events,
    }, context_instance=RequestContext(request))

def log_time(request):
    nick = request.user.username
    if nick:
        try:
            member = EconomicAgent.objects.get(nick=nick.capitalize)
        except EconomicAgent.DoesNotExist:
            member = get_object_or_404(EconomicAgent, nick=nick)
    else:
        member = "Unregistered"
    form = TimeForm()
    roots = Project.objects.filter(parent=None)
    roles = Role.objects.all()
    return render_to_response("valueaccounting/log_time.html", {
        "member": member,
        "form": form,
        "roots": roots,
        "roles": roles,
    }, context_instance=RequestContext(request))
