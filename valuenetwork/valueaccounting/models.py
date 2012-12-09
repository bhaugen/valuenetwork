import datetime
import re
from decimal import *

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.template.defaultfilters import slugify

from easy_thumbnails.fields import ThumbnailerImageField


"""Models based on REA

These models are based on the Bill McCarthy's Resource-Event-Agent accounting model:
https://www.msu.edu/~mccarth4/
http://en.wikipedia.org/wiki/Resources,_events,_agents_(accounting_model)

REA is also the basis for ISO/IEC FDIS 15944-4 ACCOUNTING AND ECONOMIC ONTOLOGY
http://global.ihs.com/doc_detail.cfm?item_s_key=00495115&item_key_date=920616

"""

def unique_slugify(instance, value, slug_field_name='slug', queryset=None,
                   slug_separator='-'):
    """
    Calculates a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug. Chop its length down if we need to.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create a queryset, excluding the current instance.
    if not queryset:
        queryset = instance.__class__._default_manager.all()
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = '-%s' % next
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len-len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = '%s%s' % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator=None):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
        value = re.sub('%s+' % re_sep, separator, value)
    return re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)

CATEGORIZATION_CHOICES = (
    ('Anything', _('Anything')),
    ('EconomicResourceType', _('EconomicResourceType')),
)


class Category(models.Model):
    name = models.CharField(_('name'), max_length=128)
    applies_to = models.CharField(_('applies to'), max_length=128, 
        choices=CATEGORIZATION_CHOICES)
    description = models.TextField(_('description'), blank=True, null=True)
    orderable = models.BooleanField(_('orderable'), default=False,
        help_text=_('Should appear in Order form?'))

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ('name',)
     
    def __unicode__(self):
        return self.name


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
        ordering = ('name',)
     
    def __unicode__(self):
        return self.name

    @classmethod
    def add_new_form(cls):
        return None


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
        verbose_name=_('parent'), related_name='sub-agents', editable=False)
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

    def produced_resource_type_relationships(self):
        return self.resource_types.filter(relationship__direction='out')

    def produced_resource_types(self):
        return [ptrt.resource_type for ptrt in self.produced_resource_type_relationships()]

    def consumed_resource_type_relationships(self):
        return self.resource_types.filter(relationship__direction='in')

    def consumed_resource_types(self):
        return [ptrt.resource_type for ptrt in self.consumed_resource_type_relationships()]

    def xbill_parents(self):
        return self.produced_resource_type_relationships()

    def xbill_children(self):
        return []

    def xbill_class(self):
        return "economic-agent"  


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


RESOURCE_EFFECT_CHOICES = (
    ('+', _('increase')),
    ('-', _('decrease')),
    ('x', _('transfer')), #means - for from_agent, + for to_agent
    ('=', _('no effect')),
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


""" design_issue:
    Materiality is probably part of a Category model.

"""

MATERIALITY_CHOICES = (
    ('material', _('material')),
    ('intellectual', _('intellectual')),
    ('work', _('work')),
    ('tool', _('tool')),
)

class EconomicResourceTypeManager(models.Manager):

    def types_of_work(self):
        return EconomicResourceType.objects.filter(materiality="work")



class EconomicResourceType(models.Model):
    name = models.CharField(_('name'), max_length=128)    
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='children', editable=False)
    category = models.ForeignKey(Category, blank=True, null=True, 
        verbose_name=_('category'), related_name='resource_types',
        limit_choices_to=Q(applies_to='Anything') | Q(applies_to='EconomicResourceType'))
    materiality = models.CharField(_('materiality'), 
        max_length=12, choices=MATERIALITY_CHOICES,
        default='material')
    unit = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="resource_units")
    photo = ThumbnailerImageField(_("photo"),
        upload_to='photos', blank=True, null=True)
    url = models.CharField(_('url'), max_length=255, blank=True)
    description = models.TextField(_('description'), blank=True, null=True)
    rate = models.DecimalField(_('rate'), max_digits=6, decimal_places=2, default=Decimal("0.00"))
    created_by = models.ForeignKey(User, verbose_name=_('created by'),
        related_name='resource_types_created', blank=True, null=True)
    changed_by = models.ForeignKey(User, verbose_name=_('changed by'),
        related_name='resource_types_changed', blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)
    
    objects = EconomicResourceTypeManager()

    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name
    
    @classmethod
    def add_new_form(cls):
        from valuenetwork.valueaccounting.forms import EconomicResourceTypeWithPopupForm
        return EconomicResourceTypeWithPopupForm

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(EconomicResourceType, self).save(*args, **kwargs)

    def children(self):
        return self.children.all()

    def node_id(self):
        return "-".join(["ResourceType", str(self.id)])

    def color(self):
        return "red"

    def producing_process_type_relationships(self):
        return self.process_types.filter(relationship__direction='out')

    def main_producing_process_type_relationship(self):
        ptrts = self.producing_process_type_relationships()
        if ptrts:
            return ptrts[0]
        else:
            return None

    def producing_process_types(self):
        return [pt.process_type for pt in self.producing_process_type_relationships()]

    def main_producing_process_type(self):
        pts = self.producing_process_types()
        if pts:
            return pts[0]
        else:
            return None

    def consuming_process_type_relationships(self):
        return self.process_types.filter(relationship__direction='in')

    def consuming_process_types(self):
        return [pt.process_type for pt in self.consuming_process_type_relationships()]

    def producing_agent_relationships(self):
        return self.agents.filter(relationship__direction='out')

    def consuming_agent_relationships(self):
        return self.agents.filter(relationship__direction='in')

    def consuming_agents(self):
        return [art.agent for art in self.consuming_agent_relationships()]

    def producing_agents(self):
        return [art.agent for art in self.producing_agent_relationships()]

    #todo: hacks based on name 'distributes' which is user-changeable
    def distributor_relationships(self):
        return self.agents.filter(relationship__name='distributes')

    def distributors(self):
        return [art.agent for art in self.distributor_relationships()]

    def producer_relationships(self):
        return self.agents.filter(relationship__direction='out').exclude(relationship__name='distributes')

    def producers(self):
        arts = self.producer_relationships()
        return [art.agent for art in arts]

    def producing_commitments(self):
        return self.commitments.filter(relationship__event_type__resource_effect='+')

    def consuming_commitments(self):
        return self.commitments.filter(relationship__event_type__resource_effect='-')

    def xbill_parents(self):
        answer = list(self.consuming_process_type_relationships())
        answer.extend(list(self.options.all()))
        #answer.append(self)
        return answer

    def xbill_children(self):
        answer = []
        answer.extend(self.producing_process_type_relationships())
        answer.extend(self.producer_relationships())
        answer.extend(self.distributor_relationships())
        return answer

    def xbill_child_object(self):
        return self

    def xbill_class(self):
        return "economic-resource-type"

    def xbill_parent_object(self):
        return self

    def xbill_explanation(self):
        return "Resource Type"

    def xbill_label(self):
        return ""

    def xbill_category(self):
        return self.category

    def change_form(self):
        from valuenetwork.valueaccounting.forms import EconomicResourceTypeForm
        return EconomicResourceTypeForm(instance=self)


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
    ('in', _('input')),
    ('out', _('output')),
)

class ResourceRelationship(models.Model):
    name = models.CharField(_('name'), max_length=32)
    inverse_name = models.CharField(_('inverse name'), max_length=40, blank=True)
    direction = models.CharField(_('direction'), 
        max_length=12, choices=DIRECTION_CHOICES, default='in')
    event_type = models.ForeignKey(EventType,
        blank=True, null=True,
        verbose_name=_('event type'), related_name='resource_relationships')

    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return self.name

    @classmethod
    def add_new_form(cls):
        return None

    def inverse_label(self):
        if self.inverse_name:
            return self.inverse_name
        else:
            return self.name

    def infer_label(self):
        if self.direction == "out":
            return self.inverse_name
        else:
            return self.name



class AgentResourceType(models.Model):
    agent = models.ForeignKey(EconomicAgent,
        verbose_name=_('agent'), related_name='resource_types')
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='agents')
    score = models.DecimalField(_('score'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"),
        help_text=_("the quantity of contributions of this resource type from this agent"))
    relationship = models.ForeignKey(ResourceRelationship,
        blank=True, null=True,
        verbose_name=_('relationship'), related_name='agent_resource_types')
    lead_time = models.IntegerField(_('lead time'), 
        default=0, help_text=_("in days"))
    value = models.DecimalField(_('value'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))
    unit_of_value = models.ForeignKey(Unit, blank=True, null=True,
        limit_choices_to={'unit_type': 'value'},
        verbose_name=_('unit of value'), related_name="agent_resource_value_units")

    def __unicode__(self):
        return ' '.join([
            self.agent.name,
            self.relationship.name,
            self.resource_type.name,
        ])

    def label(self):
        return "source"

    def timeline_title(self):
        return " ".join(["Get ", self.resource_type.name, "from ", self.agent.name])

    def inverse_label(self):
        return self.relationship.inverse_label()

    def xbill_label(self):
        return self.relationship.infer_label()

    def xbill_explanation(self):
        return "Source"

    def xbill_child_object(self):
        if self.relationship.direction == 'out':
            return self.agent
        else:
            return self.resource_type

    def xbill_class(self):
        return self.xbill_child_object().xbill_class()

    def xbill_category(self):
        return Category(name="sources")

    def xbill_parent_object(self):
        if self.relationship.direction == 'out':
            return self.resource_type
        else:
            return self.agent

    def node_id(self):
        return "-".join(["AgentResource", str(self.id)])

    def xbill_change_prefix(self):
        return "".join(["AR", str(self.id)])

    def xbill_change_form(self):
        from valuenetwork.valueaccounting.forms import AgentResourceTypeForm
        return AgentResourceTypeForm(instance=self, prefix=self.xbill_change_prefix())


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
        #todo: hack
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


class ProcessType(models.Model):
    name = models.CharField(_('name'), max_length=128)
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='sub_process_types', editable=False)
    project = models.ForeignKey(Project,
        blank=True, null=True,
        verbose_name=_('project'), related_name='process_types')
    description = models.TextField(_('description'), blank=True, null=True)
    url = models.CharField(_('url'), max_length=255, blank=True)
    estimated_duration = models.IntegerField(_('estimated duration'), 
        default=0, 
        help_text=_("in minutes, e.g. 3 hours = 180"))
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

    def produced_resource_type_relationships(self):
        return self.resource_types.filter(relationship__direction='out')

    def produced_resource_types(self):
        return [ptrt.resource_type for ptrt in self.produced_resource_type_relationships()]


    def consumed_resource_type_relationships(self):
        return self.resource_types.filter(relationship__direction='in')

    def consumed_resource_types(self):
        return [ptrt.resource_type for ptrt in self.consumed_resource_type_relationships()]

    def xbill_parents(self):
        return self.produced_resource_type_relationships()

    def xbill_children(self):
        kids = list(self.consumed_resource_type_relationships())
        kids.extend(self.features.all())
        return kids

    def xbill_explanation(self):
        return "Process Type"

    def xbill_change_prefix(self):
        return "".join(["PT", str(self.id)])

    def xbill_change_form(self):
        from valuenetwork.valueaccounting.forms import ChangeProcessTypeForm
        return ChangeProcessTypeForm(instance=self, prefix=self.xbill_change_prefix())

    def xbill_input_prefix(self):
        return "".join(["PTINPUT", str(self.id)])

    def xbill_input_form(self):
        from valuenetwork.valueaccounting.forms import ProcessTypeResourceTypeForm
        return ProcessTypeResourceTypeForm(prefix=self.xbill_input_prefix())

    def xbill_class(self):
        return "process-type"


class ProcessTypeResourceType(models.Model):
    process_type = models.ForeignKey(ProcessType,
        verbose_name=_('process type'), related_name='resource_types')
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='process_types')
    relationship = models.ForeignKey(ResourceRelationship,
        blank=True, null=True,
        verbose_name=_('relationship'), related_name='process_resource_types')
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2, default=Decimal('0.00'))
    unit_of_quantity = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="process_resource_qty_units")

    class Meta:
        ordering = ('resource_type',)

    def __unicode__(self):
        return " ".join([self.process_type.name, self.relationship.name, str(self.quantity), self.resource_type.name])        

    def inverse_label(self):
        return self.relationship.inverse_label()

    def xbill_label(self):
        if self.relationship.direction == 'out':
            return self.inverse_label()
        else:
           abbrev = ""
           if self.unit_of_quantity:
               abbrev = self.unit_of_quantity.abbrev
           return " ".join([self.relationship.name, str(self.quantity), abbrev])

    def xbill_explanation(self):
        if self.relationship.direction == 'out':
            return "Process Type"
        else:
            return "Input"

    def xbill_child_object(self):
        if self.relationship.direction == 'out':
            return self.process_type
        else:
            return self.resource_type

    def xbill_class(self):
        return self.xbill_child_object().xbill_class()

    def xbill_parent_object(self):
        if self.relationship.direction == 'out':
            return self.resource_type
            #if self.resource_type.category.name == 'option':
            #    return self
            #else:
            #    return self.resource_type
        else:
            return self.process_type

    def xbill_parents(self):
        return [self.resource_type, self]

    def xbill_category(self):
        if self.relationship.direction == 'out':
            return Category(name="processes")
        else:
            return self.resource_type.category

    def node_id(self):
        return "-".join(["ProcessResource", str(self.id)])

    def xbill_change_prefix(self):
        return "".join(["PTRT", str(self.id)])

    def xbill_change_form(self):
        from valuenetwork.valueaccounting.forms import ProcessTypeResourceTypeForm, LaborInputForm
        #todo: hack based on user-changeable string
        if self.resource_type.materiality == "work":
            return LaborInputForm(instance=self, prefix=self.xbill_change_prefix())
        else:
            return ProcessTypeResourceTypeForm(instance=self, prefix=self.xbill_change_prefix())


class Process(models.Model):
    name = models.CharField(_('name'), max_length=128)
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='sub_processes', editable=False)
    process_type = models.ForeignKey(ProcessType,
        blank=True, null=True,
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
        return " ".join([
            self.name,
            "ending",
            self.end_date.strftime('%Y-%m-%d'),
            "starting",
            self.start_date.strftime('%Y-%m-%d'),
            ])

    def save(self, *args, **kwargs):
        slug = "-".join([
            self.process_type.name,
            self.name,
            self.start_date.strftime('%Y-%m-%d'),
        ])
        unique_slugify(self, slug)
        super(Process, self).save(*args, **kwargs)

    def label(self):
        return "process"

    def timeline_title(self):
        #return " ".join([self.name, "Process"])
        return self.name

    def incoming_commitments(self):
        return self.commitments.filter(relationship__direction='in')

    def outgoing_commitments(self):
        return self.commitments.filter(relationship__direction='out')

    def main_outgoing_commitment(self):
        cts = self.outgoing_commitments()
        if cts:
            return cts[0]
        else:
            return None


class Feature(models.Model):
    name = models.CharField(_('name'), max_length=128)
    option_category = models.ForeignKey(Category,
        verbose_name=_('option category'), related_name='features',
        blank=True, null=True,
        help_text=_("option selections will be limited to this category"),
        limit_choices_to=Q(applies_to='Anything') | Q(applies_to='EconomicResourceType'))
    product = models.ForeignKey(EconomicResourceType, 
        related_name="features", verbose_name=_('product'))
    process_type = models.ForeignKey(ProcessType,
        blank=True, null=True,
        verbose_name=_('process type'), related_name='features')
    relationship = models.ForeignKey(ResourceRelationship,
        blank=True, null=True,
        verbose_name=_('relationship'), related_name='features')
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2, default=Decimal('0.00'))
    unit_of_quantity = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="feature_units")

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return " ".join([self.name, "Feature for", self.product.name])

    def xbill_child_object(self):
        return self

    def xbill_class(self):
        return "feature"

    def xbill_parent_object(self):
        return self.process_type

    def xbill_children(self):
        return self.options.all()

    def xbill_explanation(self):
        return "Feature"

    def xbill_label(self):
        abbrev = ""
        if self.unit_of_quantity:
           abbrev = self.unit_of_quantity.abbrev
        return " ".join([str(self.quantity), abbrev])

    def xbill_category(self):
        return Category(name="features")

    def node_id(self):
        return "-".join(["Feature", str(self.id)])

    def xbill_parents(self):
        return [self.process_type, self]

    def options_form(self):
        from valuenetwork.valueaccounting.forms import OptionsForm
        return OptionsForm(feature=self)

    def options_change_form(self):
        from valuenetwork.valueaccounting.forms import OptionsForm
        option_ids = self.options.values_list('component__id', flat=True)
        init = {'options': option_ids,}
        return OptionsForm(feature=self, initial=init)

    def xbill_change_prefix(self):
        return "".join(["FTR", str(self.id)])

    def xbill_change_form(self):
        from valuenetwork.valueaccounting.forms import FeatureForm
        return FeatureForm(instance=self, prefix=self.xbill_change_prefix())


class Option(models.Model):
    feature = models.ForeignKey(Feature, 
        related_name="options", verbose_name=_('feature'))
    component = models.ForeignKey(EconomicResourceType, 
        related_name="options", verbose_name=_('component'))

    class Meta:
        ordering = ('component',)

    def __unicode__(self):
        return " ".join([self.component.name, "option for", self.feature.name])

    def xbill_child_object(self):
        return self.component

    def xbill_class(self):
        return "option"

    def xbill_parent_object(self):
        return self.feature

    def xbill_children(self):
        return self.component.xbill_children()

    def xbill_explanation(self):
        return "Option"

    def xbill_label(self):
        return ""

    def xbill_category(self):
        return Category(name="features")

    def node_id(self):
        return "-".join(["Option", str(self.id)])

    def xbill_parents(self):
        return [self.feature, self]


class Order(models.Model):
    receiver = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="purchase_orders", verbose_name=_('receiver'))
    provider = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="sales_orders", verbose_name=_('provider'))
    order_date = models.DateField(_('order date'), default=datetime.date.today)
    due_date = models.DateField(_('due date'))
    description = models.TextField(_('description'), null=True, blank=True)

    class Meta:
        ordering = ('due_date',)

    def __unicode__(self):
        return " ".join(
            ["Order", 
            str(self.id), 
            ", provider:", 
            self.provider.name, 
            "receiver:", 
            self.receiver.name, 
            "due:",
            self.due_date.strftime('%Y-%m-%d'),
            ])

    def producing_commitments(self):
        return self.commitments.all()

class Commitment(models.Model):
    order = models.ForeignKey(Order,
        blank=True, null=True,
        related_name="commitments", verbose_name=_('order'))
    independent_demand = models.ForeignKey(Order,
        blank=True, null=True,
        related_name="dependent_commitments", verbose_name=_('independent_demand'))
    event_type = models.ForeignKey(EventType, 
        related_name="commitments", verbose_name=_('event type'))
    relationship = models.ForeignKey(ResourceRelationship,
        blank=True, null=True,
        verbose_name=_('relationship'), related_name='commitments')
    commitment_date = models.DateField(_('commitment date'), default=datetime.date.today)
    due_date = models.DateField(_('due date'))
    from_agent_type = models.ForeignKey(AgentType,
        blank=True, null=True,
        related_name="given_commitments", verbose_name=_('from agent type'))
    from_agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="given_commitments", verbose_name=_('from'))
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
        resource_name = ""
        if self.resource_type:
            resource_name = self.resource_type.name
        if self.order:
            from_agt = 'Unassigned'
            if self.from_agent:
                from_agt = self.from_agent.name
            to_agt = 'Unassigned'
            if self.to_agent:
                to_agt = self.to_agent.name
            if self.relationship.direction == "out":
                name1 = from_agt
                name2 = to_agt
                prep = "for"
            else:
                name2 = from_agt
                name1 = to_agt
                prep = "from"
            return ' '.join([
                name1,
                self.relationship.name,
                quantity_string,
                resource_name,
                self.due_date.strftime('%Y-%m-%d'),          
                prep,
                name2,
            ])
        else:
            return ' '.join([
                self.process.name,
                self.relationship.name,
                quantity_string,
                resource_name,
                self.due_date.strftime('%Y-%m-%d'),          
        ])

    def label(self):
        return self.relationship.get_direction_display()

    def feature_label(self):
        if not self.order:
            return ""
        features = self.resource_type.features.all()
        if not features:
            return ""
        inputs = [ct.resource_type for ct in self.process.incoming_commitments()]
        selected_options = []
        for feature in features:
            options = feature.options.all()
            for option in options:
                if option.component in inputs:
                    selected_options.append(option.component)
        names = ', '.join([so.name for so in selected_options])
        prefix = "with option"
        if len(selected_options) > 1:
              prefix = "with options"
        return " ".join([prefix, names])    

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


class SelectedOption(models.Model):
    commitment = models.ForeignKey(Commitment, 
        related_name="options", verbose_name=_('commitment'))
    option = models.ForeignKey(Option, 
        related_name="commitments", verbose_name=_('option'))

    class Meta:
        ordering = ('commitment', 'option')

    def __unicode__(self):
        return " ".join([self.option.name, "option for", self.commitment.resource_type.name])


class EconomicEvent(models.Model):
    event_type = models.ForeignKey(EventType, 
        related_name="events", verbose_name=_('event type'))
    event_date = models.DateField(_('event date'))
    from_agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="given_events", verbose_name=_('from'))
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
    def __init__(self, agent, project, resource_type, quantity, value=Decimal('0.0')):
        self.agent = agent
        self.project = project
        self.resource_type = resource_type
        self.quantity = quantity
        self.value=value

    def key(self):
        return "-".join([str(self.agent.id), str(self.resource_type.id)])

    def quantity_formatted(self):
        return self.quantity.quantize(Decimal('.01'), rounding=ROUND_UP)



class CachedEventSummary(models.Model):
    agent = models.ForeignKey(EconomicAgent,
        blank=True, null=True,
        related_name="cached_events", verbose_name=_('agent'))
    project = models.ForeignKey(Project,
        blank=True, null=True,
        verbose_name=_('project'), related_name='cached_events')
    resource_type = models.ForeignKey(EconomicResourceType,
        blank=True, null=True,
        verbose_name=_('resource type'), related_name='cached_events')
    resource_type_rate = models.DecimalField(_('resource type rate'), max_digits=8, decimal_places=2, default=Decimal("1.0"))
    importance = models.DecimalField(_('importance'), max_digits=3, decimal_places=0, default=Decimal("1"))
    reputation = models.DecimalField(_('reputation'), max_digits=8, decimal_places=2, 
        default=Decimal("1.00"))
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))
    value = models.DecimalField(_('value'), max_digits=8, decimal_places=2, 
        default=Decimal("0.0"))

    class Meta:
        ordering = ('agent', 'project', 'resource_type')

    def __unicode__(self):
        return ' '.join([
            'Agent:',
            self.agent.name,
            'Project:',
            self.project.name,
            'Resource Type:',
            self.resource_type.name,
        ])

    @classmethod
    def summarize_events(cls, project):
        all_subs = project.with_all_sub_projects()
        event_list = EconomicEvent.objects.filter(project__in=all_subs)
        summaries = {}
        for event in event_list:
            key = "-".join([str(event.from_agent.id), str(event.project.id), str(event.resource_type.id)])
            if not key in summaries:
                summaries[key] = EventSummary(event.from_agent, event.project, event.resource_type, Decimal('0.0'))
            summaries[key].quantity += event.quantity
        summaries = summaries.values()
        for summary in summaries:
            ces = cls(
                agent=summary.agent,
                project=summary.project,
                resource_type=summary.resource_type,
                resource_type_rate=summary.resource_type.rate,
                importance=summary.project.importance,
                quantity=summary.quantity,
            )
            ces.save()
        return cls.objects.all()


    def quantity_formatted(self):
        return self.quantity.quantize(Decimal('.01'), rounding=ROUND_UP)

    def value_formatted(self):
        return self.value.quantize(Decimal('.01'), rounding=ROUND_UP)
