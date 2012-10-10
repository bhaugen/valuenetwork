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
from django.utils import simplejson

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

def contribution_history(request, agent_id):
    #import pdb; pdb.set_trace()
    agent = get_object_or_404(EconomicAgent, pk=agent_id)
    event_list = agent.given_events.all()
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
    
    return render_to_response("valueaccounting/agent_contributions.html", {
        "agent": agent,
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


class EventSummary(object):
    def __init__(self, agent, role, quantity, value=Decimal('0.0')):
        self.agent = agent
        self.role = role
        self.quantity = quantity
        self.value=value

    def key(self):
        return "-".join([str(self.agent.id), str(self.role.id)])

    def quantity_formatted(self):
        return self.quantity.quantize(Decimal('.01'), rounding=ROUND_UP)


class AgentSummary(object):
    def __init__(self, 
        agent, 
        value=Decimal('0.0'), 
        percentage=Decimal('0.0'),
        amount=Decimal('0.0'),
    ):
        self.agent = agent
        self.value=value
        self.percentage=percentage
        self.amount=amount


def value_equation(request, project_id):
    project = get_object_or_404(Project, pk=project_id)    
    if not CachedEventSummary.objects.all().exists():
        summaries = CachedEventSummary.summarize_events(project)
    all_subs = project.with_all_sub_projects()
    summaries = CachedEventSummary.objects.select_related(
        'agent', 'project', 'role').filter(project__in=all_subs).order_by(
        'agent__name', 'project__name', 'role__name')
    total = 0
    agent_totals = []
    init = {"equation": "( hours * ( rate + importance + reputation ) ) + seniority"}
    form = EquationForm(data=request.POST or None,
        initial=init)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if form.is_valid():
            data = form.cleaned_data
            equation = data["equation"]
            amount = data["amount"]
            if amount:
                amount = Decimal(amount)
            eq = equation.split(" ")
            for i, x in enumerate(eq):
                try:
                    y = Decimal(x)
                    eq[i] = "".join(["Decimal('", x, "')"])
                except InvalidOperation:
                    continue
            s = " "
            equation = s.join(eq)
            agent_sums = {}
            total = Decimal("0.00")
            for summary in summaries:
                hours = summary.quantity
                rate = summary.role_rate
                importance = summary.importance
                reputation = summary.reputation
                seniority = summary.agent.seniority()
                summary.value = eval(equation)
                agent = summary.agent
                if not agent.id in agent_sums:
                    agent_sums[agent.id] = AgentSummary(agent)
                agent_sums[agent.id].value += summary.value
                total += summary.value
            agent_totals = agent_sums.values()
            #import pdb; pdb.set_trace()
            for at in agent_totals:
               pct = at.value / total
               at.value = at.value.quantize(Decimal('.01'), rounding=ROUND_UP)
               at.percentage = ( pct * 100).quantize(Decimal('.01'), rounding=ROUND_UP)
               if amount:
                   at.amount = (amount * pct).quantize(Decimal('.01'), rounding=ROUND_UP)

    paginator = Paginator(summaries, 50)
    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        events = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        events = paginator.page(paginator.num_pages)
    
    return render_to_response("valueaccounting/value_equation.html", {
        "project": project,
        "events": events,
        "form": form,
        "agent_totals": agent_totals,
        "total": total,
    }, context_instance=RequestContext(request))

def extended_bill(request, resource_type_id):
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    return render_to_response("valueaccounting/extended_bill.html", {
        "resource_type": rt,
        "photo_size": (128, 128),
    }, context_instance=RequestContext(request))

def network(request, resource_type_id):
    #import pdb; pdb.set_trace()
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    nodes, edges = graphify(rt)
    return render_to_response("valueaccounting/network.html", {
        "resource_type": rt,
        "photo_size": (128, 128),
        "nodes": nodes,
        "edges": edges,
    }, context_instance=RequestContext(request))

def timeline(request):
    process = Process.objects.get(pk=1)
    timeline_date = datetime.date.today().strftime("%b %e %Y 00:00:00 GMT-0600")
    return render_to_response("valueaccounting/timeline.html", {
        "process": process,
        "timeline_date": timeline_date,
    }, context_instance=RequestContext(request))

def json_timeline(request):
    #data = "{ 'wiki-url':'http://simile.mit.edu/shelf/', 'wiki-section':'Simile JFK Timeline', 'dateTimeFormat': 'Gregorian','events': [{'start':'May 28 2006 09:00:00 GMT-0600','title': 'Writing Timeline documentation','link':'http://google.com','description':'Write some doc already','durationEvent':false }, {'start': 'Jun 16 2006 00:00:00 GMT-0600' ,'end':  'Jun 26 2006 00:00:00 GMT-0600' ,'durationEvent':true,'title':'Friends wedding'}]}"
    #import pdb; pdb.set_trace()
    process = Process.objects.get(pk=1)
    events = backshedule_events(process)
    data = simplejson.dumps(events, ensure_ascii=False)
    return HttpResponse(data, mimetype="text/json-comment-filtered")
