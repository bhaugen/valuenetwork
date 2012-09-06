import datetime
from decimal import *

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from valuenetwork.valueaccounting.utils import *


class ValueEquation(models.Model):
    base_rate = models.DecimalField(_('base rate'), max_digits=8, decimal_places=2)
    role_weight = models.DecimalField(_('role weight'), max_digits=6, decimal_places=4)
    importance_weight = models.DecimalField(_('importance weight'), max_digits=6, decimal_places=4)
    quality_weight = models.DecimalField(_('quality weight'), max_digits=6, decimal_places=4)
    accountability_weight = models.DecimalField(_('accountability weight'), max_digits=6, decimal_places=4)
    regularity_weight = models.DecimalField(_('regularity weight'), max_digits=6, decimal_places=4)
    reputation_weight = models.DecimalField(_('reputation weight'), max_digits=6, decimal_places=4)
    risk_weight = models.DecimalField(_('risk weight'), max_digits=6, decimal_places=4)
    commitment_weight = models.DecimalField(_('commitment weight'), max_digits=6, decimal_places=4)
    seniority_weight = models.DecimalField(_('seniority weight'), max_digits=6, decimal_places=4)


UNIT_TYPE_CHOICES = (
    ('quantity', _('quantity')),
    ('time', _('time')),
    ('value', _('value')),
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


SIZE_CHOICES = (
    ('individual', _('individual')),
    ('org', _('organization')),
    ('network', _('network')),
)

class AgentType(models.Model):
    name = models.CharField(_('name'), max_length=128)
    active = models.BooleanField(_('active'), default=True)
    size = models.CharField(_('size'), 
        max_length=12, choices=SIZE_CHOICES,
        default='individual')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class EconomicAgent(models.Model):
    name = models.CharField(_('name'), max_length=255)
    agent_type = models.ForeignKey(AgentType,
        verbose_name=_('agent type'), related_name='agents')
    description = models.TextField(_('description'), blank=True, null=True)
    address = models.CharField(_('address'), max_length=255, blank=True)
    latitude = models.FloatField(_('latitude'), default=0.0, blank=True, null=True)
    longitude = models.FloatField(_('longitude'), default=0.0, blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(EconomicAgent, self).save(*args, **kwargs)


class EconomicResourceType(models.Model):
    name = models.CharField(_('name'), max_length=128)    
    parent = models.ForeignKey('self', blank=True, null=True, 
        verbose_name=_('parent'), related_name='children')
    slug = models.SlugField(_("Page name"), editable=False)
    unit = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="resource_units")
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(EconomicResourceType, self).save(*args, **kwargs)


class EconomicResource(models.Model):
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='resources')
    identifier = models.CharField(_('identifier'), max_length=128)
    owner = models.ForeignKey(EconomicAgent, related_name="owned_resources",
        verbose_name=_('owner'), blank=True, null=True)
    custodian = models.ForeignKey(EconomicAgent, related_name="custody_resources",
        verbose_name=_('custodian'), blank=True, null=True)
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


class ProcessType(models.Model):
    name = models.CharField(_('name'), max_length=128)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(ProcessType, self).save(*args, **kwargs)


class Process(models.Model):
    name = models.CharField(_('name'), max_length=128)
    process_type = models.ForeignKey(ProcessType,
        verbose_name=_('process type'), related_name='processes')
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

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        slug = "-".join([
            self.process_type.name,
            self.name,
            self.event_date.strftime('%Y-%m-%d'),
        ])
        unique_slugify(self, slug)
        super(Process, self).save(*args, **kwargs)


RESOURCE_EFFECT_CHOICES = (
    ('+', _('increase')),
    ('-', _('decrease')),
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
    factor = models.DecimalField(_('factor'), max_digits=6, decimal_places=4)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(Role, self).save(*args, **kwargs)


class EconomicEvent(models.Model):
    event_type = models.ForeignKey(EventType, 
        related_name="events", verbose_name=_('event type'))
    event_date = models.DateField(_('transaction date'))
    from_agent = models.ForeignKey(EconomicAgent, 
        related_name="given_events", verbose_name=_('from'))
    from_agent_role = models.ForeignKey(Role, 
        verbose_name=_('role'), related_name='events')
    to_agent = models.ForeignKey(EconomicAgent, 
        related_name="taken_events", verbose_name=_('to'))
    resource_type = models.ForeignKey(EconomicResourceType, 
        verbose_name=_('resource type'), related_name='events')
    resource = models.ForeignKey(EconomicResource, 
        blank=True, null=True,
        verbose_name=_('resource'), related_name='events')
    process = models.ForeignKey(Process, 
        verbose_name=_('process'), related_name='events')
    amount = models.DecimalField(_('amount'), max_digits=8, decimal_places=2)
    unit = models.ForeignKey(Unit, blank=True, null=True,
        verbose_name=_('unit'), related_name="event_units")
    notes = models.TextField(_('notes'), null=True, blank=True)
    created_by = models.ForeignKey(User, verbose_name=_('created by'),
        related_name='events_created', blank=True, null=True)
    changed_by = models.ForeignKey(User, verbose_name=_('changed by'),
        related_name='events_changed', blank=True, null=True)
    slug = models.SlugField(_("Page name"), editable=False)

    class Meta:
        ordering = ('event_date',)

    def __unicode__(self):
        amount_string = '$' + str(self.amount)
        return ' '.join([
            self.event_type.name,
            self.event_date.strftime('%Y-%m-%d'),
            'from',
            self.from_agent.name,
            'to',
            self.to_agent.name,
            amount_string,
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

