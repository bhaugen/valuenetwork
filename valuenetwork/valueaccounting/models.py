import datetime
from decimal import *

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from easy_thumbnails.fields import ThumbnailerImageField

from valuenetwork.valueaccounting.utils import *

"""Models based on REA

These models are based on the Bill McCarthy's Resource-Event-Agent accounting model:
https://www.msu.edu/~mccarth4/
http://en.wikipedia.org/wiki/Resources,_events,_agents_(accounting_model)

REA is also the basis for ISO/IEC FDIS 15944-4 ACCOUNTING AND ECONOMIC ONTOLOGY
http://global.ihs.com/doc_detail.cfm?item_s_key=00495115&item_key_date=920616

"""


UNIT_TYPE_CHOICES = (
    ('length', _('length')),
    ('quantity', _('quantity')),
    ('time', _('time')),
    ('value', _('value')),
    ('volume', _('volume')),
    ('weight', _('weight')),
    ('ip', _('ip')),
)
 
class Unit(models.Model):
    unit_type = models.CharField(_('unit type'), max_length=12, choices=UNIT_TYPE_CHOICES)
    abbrev = models.CharField(_('abbreviation'), max_length=8)
    name = models.CharField(_('name'), max_length=64)
    symbol = models.CharField(_('symbol'), max_length=1, blank=True)

    class Meta:
        ordering = ('abbrev',)
     
    def __unicode__(self):
        return self.abbrev


ACTIVITY_CHOICES = (
    ('active', _('active contributor')),
    ('affiliate', _('close affiliate')),
    ('inactive', _('inactive contributor')),
    ('agent', _('active agent')),
    ('passive', _('passive agent')),
    ('external', _('external agent')),
)

SIZE_CHOICES = (
    ('individual', _('individual')),
    ('org', _('organization')),
    ('network', _('network')),
    ('team', _('project team')),
    ('community', _('community')),
)

class AgentType(models.Model):
    name = models.CharField(_('name'), max_length=128)
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='sub-agents')
    member_type = models.CharField(_('member type'), 
        max_length=12, choices=ACTIVITY_CHOICES,
        default='active')
    party_type = models.CharField(_('party type'), 
        max_length=12, choices=SIZE_CHOICES,
        default='individual')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class EconomicAgent(models.Model):
    name = models.CharField(_('name'), max_length=255)
    nick = models.CharField(_('ID'), max_length=32, unique=True)
    url = models.CharField(_('url'), max_length=255, blank=True)
    agent_type = models.ForeignKey(AgentType,
        verbose_name=_('agent type'), related_name='agents')
    description = models.TextField(_('description'), blank=True, null=True)
    address = models.CharField(_('address'), max_length=255, blank=True)
    email = models.EmailField(_('email address'), max_length=96, blank=True, null=True)
    latitude = models.FloatField(_('latitude'), default=0.0, blank=True, null=True)
    longitude = models.FloatField(_('longitude'), default=0.0, blank=True, null=True)
    reputation = models.DecimalField(_('reputation'), max_digits=8, decimal_places=2, 
        default=Decimal("0.00"))
    photo = ThumbnailerImageField(_("photo"),
        upload_to='photos', blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)
    created_date = models.DateField(_('created date'))
    
    class Meta:
        ordering = ('nick',)
    
    def __unicode__(self):
        return self.nick
    
    def save(self, *args, **kwargs):
        unique_slugify(self, self.nick)
        super(EconomicAgent, self).save(*args, **kwargs)

    def seniority(self):
        return (datetime.date.today() - self.created_date).days

    def node_id(self):
        return "-".join(["Agent", str(self.id)])

    def color(self):
        return "green"



class AssociationType(models.Model):
    name = models.CharField(_('name'), max_length=128)


class AgentAssociation(models.Model):
    from_agent = models.ForeignKey(EconomicAgent,
        verbose_name=_('from'), related_name='associations_from')
    to_agent = models.ForeignKey(EconomicAgent,
        verbose_name=_('to'), related_name='associations_to')
    association_type = models.ForeignKey(AssociationType,
        verbose_name=_('association type'), related_name='associations')
    description = models.TextField(_('description'), blank=True, null=True)


MATERIALITY_CHOICES = (
    ('material', _('material')),
    ('intellectual', _('intellectual')),
    ('time-based', _('time-based')),
)


class EconomicResourceType(models.Model):
    name = models.CharField(_('name'), max_length=128)    
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='children')
    materiality = models.CharField(_('materiality'), 
        max_length=12, choices=MATERIALITY_CHOICES,
        default='material')
    unit = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="resource_units")
    photo = ThumbnailerImageField(_("photo"),
        upload_to='photos', blank=True, null=True)
    url = models.CharField(_('url'), max_length=255, blank=True)
    description = models.TextField(_('description'), blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(EconomicResourceType, self).save(*args, **kwargs)

    def node_id(self):
        return "-".join(["ResourceType", str(self.id)])

    def color(self):
        return "red"

    def producing_process_types(self):
        pts = self.process_types.exclude(direction='consumes').exclude(direction__contains='use')
        return [pt.process_type for pt in pts]

    def producing_process_type_relationships(self):
        return self.process_types.exclude(direction='consumes').exclude(direction__contains='use')

    def consuming_process_types(self):
        pts = self.process_types.exclude(direction='produces').exclude(direction='distributes')
        return [pt.process_type for pt in pts]

    def consuming_process_type_relationships(self):
        return self.process_types.exclude(direction='produces').exclude(direction='distributes')

    def consuming_agents(self):
        arts = self.agents.exclude(direction='produces').exclude(direction='distributes')
        return [art.agent for art in arts]

    def producing_agents(self):
        arts = self.agents.exclude(direction='consumes').exclude(direction__contains='use')
        return [art.agent for art in arts]

    def producing_agent_relationships(self):
        return self.agents.exclude(direction='consumes').exclude(direction__contains='use')

    def consuming_agent_relationships(self):
        return self.agents.exclude(direction='produces').exclude(direction='distributes')

    def distributors(self):
        arts = self.agents.filter(direction='distributes')
        return [art.agent for art in arts]


class EconomicResource(models.Model):
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='resources')
    identifier = models.CharField(_('identifier'), max_length=128)
    url = models.CharField(_('url'), max_length=255, blank=True)
    owner = models.ForeignKey(EconomicAgent, related_name="owned_resources",
        verbose_name=_('owner'), blank=True, null=True)
    custodian = models.ForeignKey(EconomicAgent, related_name="custody_resources",
        verbose_name=_('custodian'), blank=True, null=True)
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2, 
        default=Decimal("1.00"))
    unit_of_quantity = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit of quantity'), related_name="resource_qty_units")
    quality = models.DecimalField(_('quality'), max_digits=3, decimal_places=0, default=Decimal("0"))
    notes = models.TextField(_('notes'), blank=True, null=True)
    created_date = models.DateField(_('created date'))

    class Meta:
        ordering = ('resource_type', 'identifier',)
    
    def __unicode__(self):
        return " ".join([
            self.resource_type.name,
            self.identifier,
        ])
    
    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(EconomicResourceType, self).save(*args, **kwargs)


DIRECTION_CHOICES = (
    ('consumes', 'consumes'),
    ('uses', 'uses'),
    ('potential user', 'potential user'),
    ('produces', 'produces'),
    ('distributes', 'distributes'),
)


class AgentResourceType(models.Model):
    agent = models.ForeignKey(EconomicAgent,
        verbose_name=_('agent'), related_name='resource_types')
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='agents')
    direction = models.CharField(_('direction'), max_length=12, choices=DIRECTION_CHOICES)
    lead_time = models.IntegerField(_('lead time'), 
        default=0, help_text=_("in days"))
    value = models.DecimalField(_('value'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))
    unit_of_value = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit of value'), related_name="agent_resource_value_units")

    def __unicode__(self):
        return ' '.join([
            self.agent.name,
            self.direction,
            self.resource_type.name,
        ])

    def timeline_title(self):
        return " ".join(["Get ", self.resource_type.name, "from ", self.agent.name])


class ProcessType(models.Model):
    name = models.CharField(_('name'), max_length=128)
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='sub_process_types')
    description = models.TextField(_('description'), blank=True, null=True)
    url = models.CharField(_('url'), max_length=255, blank=True)
    estimated_duration = models.IntegerField(_('estimated duration'), 
        default=0, help_text=_("in minutes"))
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(ProcessType, self).save(*args, **kwargs)

    def timeline_title(self):
        return " ".join([self.name, "Process to be planned"])

    def node_id(self):
        return "-".join(["ProcessType", str(self.id)])

    def color(self):
        return "blue"

    def produced_resource_types(self):
        ptrts = self.resource_types.exclude(direction='consumes').exclude(direction='uses')
        return [ptrt.resource_type for ptrt in ptrts]

    def consumed_resource_types(self):
        ptrts = self.resource_types.exclude(direction='produces').exclude(direction='distributes')
        return [ptrt.resource_type for ptrt in ptrts]

    def consumed_resource_type_relationships(self):
        return self.resource_types.exclude(direction='produces').exclude(direction='distributes')


class ProcessTypeResourceType(models.Model):
    process_type = models.ForeignKey(ProcessType,
        verbose_name=_('process type'), related_name='resource_types')
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='process_types')
    direction = models.CharField(_('direction'), max_length=12, choices=DIRECTION_CHOICES)
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2, default=Decimal('0.00'))
    unit_of_quantity = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="process_resource_qty_units")

    def __unicode__(self):
        return " ".join([self.process_type.name, self.direction, str(self.quantity), self.resource_type.name])

    def diagram_input_label(self):
        if self.direction == "uses":
            return "used by"
        if self.direction == "consumes":
            return "consumed by"        


class Project(models.Model):
    name = models.CharField(_('name'), max_length=128) 
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='sub_projects')
    project_team = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="project_team", verbose_name=_('project team'))
    importance = models.DecimalField(_('importance'), max_digits=3, decimal_places=0, default=Decimal("0"))
    slug = models.SlugField(_("Page name"), editable=False)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(Project, self).save(*args, **kwargs)

    def time_contributions(self):
        et = EventType.objects.get(name='Time Contribution')
        return sum(event.quantity for event in self.events.filter(
            event_type=et))

    def contributions(self):
        return sum(event.quantity for event in self.events.filter(
            event_type__resource_effect='-'))

    def contributions_count(self):
        return self.events.filter(event_type__resource_effect='-').count()

    def contributors(self):
        ids = self.events.filter(event_type__resource_effect='-').values_list('from_agent').order_by('from_agent').distinct()
        id_list = [id[0] for id in ids]
        return EconomicAgent.objects.filter(id__in=id_list)

    def with_all_sub_projects(self):
        return flattened_children(self, Project.objects.all(), [])


class Process(models.Model):
    name = models.CharField(_('name'), max_length=128)
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='sub_processes')
    process_type = models.ForeignKey(ProcessType,
        verbose_name=_('process type'), related_name='processes')
    project = models.ForeignKey(Project,
        blank=True, null=True,
        verbose_name=_('project'), related_name='processes')
    url = models.CharField(_('url'), max_length=255, blank=True)
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), blank=True, null=True)
    managed_by = models.ForeignKey(EconomicAgent, related_name="managed_processes",
        verbose_name=_('managed by'), blank=True, null=True)
    owner = models.ForeignKey(EconomicAgent, related_name="owned_processes",
        verbose_name=_('owner'), blank=True, null=True)
    notes = models.TextField(_('notes'), blank=True)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = "processes"

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        slug = "-".join([
            self.process_type.name,
            self.name,
            self.start_date.strftime('%Y-%m-%d'),
        ])
        unique_slugify(self, slug)
        super(Process, self).save(*args, **kwargs)

    def timeline_title(self):
        return " ".join([self.name, "Process"])

    def incoming_commitments(self):
        return self.commitments.filter(to_agent__id=self.owner.id)


RESOURCE_EFFECT_CHOICES = (
    ('+', _('increase')),
    ('-', _('decrease')),
    ('xfer', _('transfer')),
    ('none', _('no effect')),
)

class EventType(models.Model):
    name = models.CharField(_('name'), max_length=128)
    resource_effect = models.CharField(_('resource effect'), 
        max_length=12, choices=RESOURCE_EFFECT_CHOICES)
    unit_type = models.CharField(_('unit type'), max_length=12, choices=UNIT_TYPE_CHOICES)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(EventType, self).save(*args, **kwargs)


class Role(models.Model):
    name = models.CharField(_('name'), max_length=128)
    rate = models.DecimalField(_('rate'), max_digits=6, decimal_places=2, default=Decimal("0.00"))
    created_by = models.ForeignKey(User, verbose_name=_('created by'),
        related_name='roles_created', blank=True, null=True)
    changed_by = models.ForeignKey(User, verbose_name=_('changed by'),
        related_name='roles_changed', blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(Role, self).save(*args, **kwargs)


class Commitment(models.Model):
    event_type = models.ForeignKey(EventType, 
        related_name="commitments", verbose_name=_('event type'))
    commitment_date = models.DateField(_('commitment date'))
    due_date = models.DateField(_('due date'))
    from_agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="given_commitments", verbose_name=_('from'))
    from_agent_role = models.ForeignKey(Role,
        blank=True, null=True,
        verbose_name=_('role'), related_name='commitments')
    to_agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="taken_commitments", verbose_name=_('to'))
    resource_type = models.ForeignKey(EconomicResourceType, 
        blank=True, null=True,
        verbose_name=_('resource type'), related_name='commitments')
    resource = models.ForeignKey(EconomicResource, 
        blank=True, null=True,
        verbose_name=_('resource'), related_name='commitments')
    process = models.ForeignKey(Process,
        blank=True, null=True,
        verbose_name=_('process'), related_name='commitments')
    project = models.ForeignKey(Project,
        blank=True, null=True,
        verbose_name=_('project'), related_name='commitments')
    description = models.TextField(_('description'), null=True, blank=True)
    url = models.CharField(_('url'), max_length=255, blank=True)
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2)
    unit_of_quantity = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="commitment_qty_units")
    quality = models.DecimalField(_('quality'), max_digits=3, decimal_places=0, default=Decimal("0"))
    value = models.DecimalField(_('value'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))
    unit_of_value = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit of value'), related_name="commitment_value_units")
    created_by = models.ForeignKey(User, verbose_name=_('created by'),
        related_name='commitments_created', blank=True, null=True)
    changed_by = models.ForeignKey(User, verbose_name=_('changed by'),
        related_name='commitments_changed', blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('due_date',)

    def __unicode__(self):
        quantity_string = str(self.quantity)
        from_agt = 'Unassigned'
        if self.from_agent:
            from_agt = self.from_agent.name
        to_agt = 'Unassigned'
        if self.to_agent:
            to_agt = self.to_agent.name
        resource_name = ""
        if self.resource_type:
			resource_name = self.resource_type.name
        return ' '.join([
            "Commitment for",
            self.event_type.name,
            self.due_date.strftime('%Y-%m-%d'),
            'from',
            from_agt,
            'to',
            to_agt,
            quantity_string,
            resource_name,
        ])

    def save(self, *args, **kwargs):
        from_id = "Unassigned"
        if self.from_agent:
            from_id = str(self.from_agent.id)
        slug = "-".join([
            str(self.event_type.id),
            from_id,
            self.due_date.strftime('%Y-%m-%d'),
        ])
        unique_slugify(self, slug)
        super(Commitment, self).save(*args, **kwargs)

    def timeline_title(self):
        quantity_string = str(self.quantity)
        from_agt = 'Unassigned'
        if self.from_agent:
            from_agt = self.from_agent.name
        process = "Unknown"
        if self.process:
            process = self.process.name
        return ' '.join([
            self.resource_type.name,
            'from',
            from_agt,
            'to',
            process,
        ])

class Reciprocity(models.Model):
    """One Commitment reciprocating another.

    The EconomicAgents in the reciprocal commitments
    must be opposites.  
    That is, the from_agent of one commitment must be
    the to-agent of the other commitment, and vice versa.
    Reciprocal commitments have a M:M relationship:
    that is, one commitment can be reciprocated by many other commitments,
    and the other commitment can reciprocate many initiating commitments.

    """
    initiating_commitment = models.ForeignKey(Commitment, 
        related_name="initiated_commitments", verbose_name=_('initiating commitment'))
    reciprocal_commitment = models.ForeignKey(Commitment, 
        related_name="reciprocal_commitments", verbose_name=_('reciprocal commitment'))
    reciprocity_date = models.DateField(_('reciprocity date'))

    class Meta:
        ordering = ('reciprocity_date',)

    def __unicode__(self):
        return ' '.join([
            'inititating commmitment:',
            self.initiating_commmitment.__unicode__(),
            'reciprocal commmitment:',
            self.reciprocal_commitment.__unicode__(),
            self.reciprocity_date.strftime('%Y-%m-%d'),
        ])

    def clean(self):
        #import pdb; pdb.set_trace()
        if self.initiating_commitment.from_agent.id != self.reciprocal_commitment.to_agent.id:
            raise ValidationError('Initiating commitment from_agent must be the reciprocal commitment to_agent.')
        if self.initiating_commitment.to_agent.id != self.reciprocal_commitment.from_agent.id:
            raise ValidationError('Initiating commitment to_agent must be the reciprocal commitment from_agent.')


class EconomicEvent(models.Model):
    event_type = models.ForeignKey(EventType, 
        related_name="events", verbose_name=_('event type'))
    event_date = models.DateField(_('event date'))
    from_agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="given_events", verbose_name=_('from'))
    from_agent_role = models.ForeignKey(Role,
        blank=True, null=True,
        verbose_name=_('role'), related_name='events')
    to_agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="taken_events", verbose_name=_('to'))
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='events')
    resource = models.ForeignKey(EconomicResource, 
        blank=True, null=True,
        verbose_name=_('resource'), related_name='events')
    process = models.ForeignKey(Process,
        blank=True, null=True,
        verbose_name=_('process'), related_name='events')
    project = models.ForeignKey(Project,
        blank=True, null=True,
        verbose_name=_('project'), related_name='events')
    url = models.CharField(_('url'), max_length=255, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2)
    unit_of_quantity = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="event_qty_units")
    quality = models.DecimalField(_('quality'), max_digits=3, decimal_places=0, default=Decimal("0"))
    value = models.DecimalField(_('value'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))
    unit_of_value = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit of value'), related_name="event_value_units")
    commitment = models.ForeignKey(Commitment, blank=True, null=True,
        verbose_name=_('fulfills commitment'), related_name="fulfillment_events")
    created_by = models.ForeignKey(User, verbose_name=_('created by'),
        related_name='events_created', blank=True, null=True)
    changed_by = models.ForeignKey(User, verbose_name=_('changed by'),
        related_name='events_changed', blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('-event_date',)

    def __unicode__(self):
        quantity_string = str(self.quantity)
        from_agt = 'Unassigned'
        if self.from_agent:
            from_agt = self.from_agent.name
        to_agt = 'Unassigned'
        if self.to_agent:
            to_agt = self.to_agent.name
        return ' '.join([
            self.event_type.name,
            self.event_date.strftime('%Y-%m-%d'),
            'from',
            from_agt,
            'to',
            to_agt,
            quantity_string,
            self.resource_type.name,
        ])

    def save(self, *args, **kwargs):
        slug = "-".join([
            str(self.event_type.id),
            str(self.from_agent.id),
            self.event_date.strftime('%Y-%m-%d'),
        ])
        unique_slugify(self, slug)
        super(EconomicEvent, self).save(*args, **kwargs)

    def my_compensations(self):
        return self.initiated_compensations.all()

    def compensation(self):
        return sum(c.compensating_value for c in self.my_compensations())

    def value_due(self):
        return self.value - self.compensation()

    def is_compensated(self):
        if self.value_due() > 0:
            return False
        return True

    def quantity_formatted(self):
        return self.quantity.quantize(Decimal('.01'), rounding=ROUND_UP)


class Compensation(models.Model):
    """One EconomicEvent compensating another.

    The EconomicAgents in the exchanging events
    must be opposites.  
    That is, the from_agent of one event must be
    the to-agent of the other event, and vice versa.
    Both events must use the same unit of value.
    Compensation events have a M:M relationship:
    that is, one event can be compensated by many other events,
    and the other events can compensate many initiating events.

    Compensation is an REA Duality.

    """
    initiating_event = models.ForeignKey(EconomicEvent, 
        related_name="initiated_compensations", verbose_name=_('initiating event'))
    compensating_event = models.ForeignKey(EconomicEvent, 
        related_name="compensations", verbose_name=_('compensating event'))
    compensation_date = models.DateField(_('compensation date'))
    compensating_value = models.DecimalField(_('compensating value'), max_digits=8, decimal_places=2)

    class Meta:
        ordering = ('compensation_date',)

    def __unicode__(self):
        value_string = '$' + str(self.compensating_value)
        return ' '.join([
            'inititating event:',
            self.initiating_event.__unicode__(),
            'compensating event:',
            self.compensating_event.__unicode__(),
            'value:',
            value_string,
        ])

    def clean(self):
        #import pdb; pdb.set_trace()
        if self.initiating_event.from_agent.id != self.compensating_event.to_agent.id:
            raise ValidationError('Initiating event from_agent must be the compensating event to_agent.')
        if self.initiating_event.to_agent.id != self.compensating_event.from_agent.id:
            raise ValidationError('Initiating event to_agent must be the compensating event from_agent.')
        #if self.initiating_event.unit_of_value.id != self.compensating_event.unit_of_value.id:
        #    raise ValidationError('Initiating event and compensating event must have the same units of value.')



class EventSummary(object):
    def __init__(self, agent, project, role, quantity, value=Decimal('0.0')):
        self.agent = agent
        self.project = project
        self.role = role
        self.quantity = quantity
        self.value=value

    def key(self):
        return "-".join([str(self.agent.id), str(self.role.id)])

    def quantity_formatted(self):
        return self.quantity.quantize(Decimal('.01'), rounding=ROUND_UP)


class CachedEventSummary(models.Model):
    agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="cached_events", verbose_name=_('agent'))
    project = models.ForeignKey(Project,
        blank=True, null=True,
        verbose_name=_('project'), related_name='cached_events')
    role = models.ForeignKey(Role,
        blank=True, null=True,
        verbose_name=_('role'), related_name='cached_events')
    role_rate = models.DecimalField(_('role_rate'), max_digits=8, decimal_places=2, default=Decimal("1.0"))
    importance = models.DecimalField(_('importance'), max_digits=3, decimal_places=0, default=Decimal("1"))
    reputation = models.DecimalField(_('reputation'), max_digits=8, decimal_places=2, 
        default=Decimal("1.00"))
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))
    value = models.DecimalField(_('value'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))

    class Meta:
        ordering = ('agent', 'project', 'role')

    def __unicode__(self):
        return ' '.join([
            'Agent:',
            self.agent.name,
            'Project:',
            self.project.name,
            'Role:',
            self.role.name,
        ])

    @classmethod
    def summarize_events(cls, project):
        all_subs = project.with_all_sub_projects()
        event_list = EconomicEvent.objects.filter(project__in=all_subs)
        summaries = {}
        for event in event_list:
            key = "-".join([str(event.from_agent.id), str(event.project.id), str(event.from_agent_role.id)])
            if not key in summaries:
                summaries[key] = EventSummary(event.from_agent, event.project, event.from_agent_role, Decimal('0.0'))
            summaries[key].quantity += event.quantity
        summaries = summaries.values()
        for summary in summaries:
            ces = cls(
                agent=summary.agent,
                project=summary.project,
                role=summary.role,
                role_rate=summary.role.rate,
                importance=summary.project.importance,
                quantity=summary.quantity,
            )
            ces.save()
        return cls.objects.all()


    def quantity_formatted(self):
        return self.quantity.quantize(Decimal('.01'), rounding=ROUND_UP)

    def value_formatted(self):
        return self.value.quantize(Decimal('.01'), rounding=ROUND_UP)
