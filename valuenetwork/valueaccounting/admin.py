from django.contrib import admin
from valuenetwork.valueaccounting.models import *
from valuenetwork.valueaccounting.actions import export_as_csv

admin.site.add_action(export_as_csv, 'export_selected objects')

admin.site.register(Unit)
admin.site.register(AgentType)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'applies_to', 'description' )

admin.site.register(Category, CategoryAdmin)


class ResourceRelationshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'inverse_name', 'direction' )

admin.site.register(ResourceRelationship, ResourceRelationshipAdmin)


class EconomicAgentAdmin(admin.ModelAdmin):
    list_display = ('nick', 'name', 'agent_type', 'url', 'address', 'email', 'created_date')
    list_filter = ['agent_type',]
    search_fields = ['name', 'address']
    
admin.site.register(EconomicAgent, EconomicAgentAdmin)


class EconomicResourceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'rate', 'materiality')
    list_filter = ['category', 'materiality',]
    search_fields = ['name',]
    list_editable = ['category',]
    
admin.site.register(EconomicResourceType, EconomicResourceTypeAdmin)


class AgentResourceTypeAdmin(admin.ModelAdmin):
    list_display = ('agent', 'resource_type', 'score','relationship')
    list_filter = ['agent', 'resource_type']
    
admin.site.register(AgentResourceType, AgentResourceTypeAdmin)


class ProcessTypeResourceTypeAdmin(admin.ModelAdmin):
    list_display = ('process_type', 'resource_type', 'relationship')
    list_filter = ['process_type', 'resource_type']
    
admin.site.register(ProcessTypeResourceType, ProcessTypeResourceTypeAdmin)


class ProcessTypeResourceTypeInline(admin.TabularInline):
    model = ProcessTypeResourceType


class ProcessTypeAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ['name',]
    inlines = [ ProcessTypeResourceTypeInline, ]

admin.site.register(ProcessType, ProcessTypeAdmin)


class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_effect', 'unit_type' )

admin.site.register(EventType, EventTypeAdmin)


class EconomicResourceAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'resource_type', 'owner', 'custodian')
    list_filter = ['owner', 'custodian']
    search_fields = ['identifier', 'resource_type__name']
    
admin.site.register(EconomicResource, EconomicResourceAdmin)


class ProcessAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'
    list_display = ('name', 'start_date', 'end_date', 'process_type', 'project', 'owner', 'managed_by')
    list_filter = ['process_type', 'owner', 'managed_by']
    search_fields = ['name', 'process_type__name', 'owner__name', 'managed_by__name']
    
admin.site.register(Process, ProcessAdmin)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ['parent',]
    search_fields = ['name',]
    
admin.site.register(Project, ProjectAdmin)


class CommitmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'due_date'
    list_display = ('event_type', 'due_date', 'from_agent', 'project', 
        'resource_type', 'quantity', 'unit_of_quantity', 'description', 'quality')
    list_filter = ['event_type', 'project', 'from_agent', ]
    search_fields = ['name', 'event_type__name', 'from_agent__name', 'to_agent__name', 'resource_type__name']
    
admin.site.register(Commitment, CommitmentAdmin)


class EconomicEventAdmin(admin.ModelAdmin):
    date_hierarchy = 'event_date'
    list_display = ('event_type', 'event_date', 'from_agent', 'project', 
        'resource_type', 'quantity', 'unit_of_quantity', 'description', 'url', 'quality')
    list_filter = ['event_type', 'project', 'resource_type', 'from_agent', ]
    search_fields = ['name', 'event_type__name', 'from_agent__name', 'to_agent__name', 'resource_type__name']
    
admin.site.register(EconomicEvent, EconomicEventAdmin)


class CompensationAdmin(admin.ModelAdmin):
    list_display = ('initiating_event', 'compensating_event', 'compensation_date', 'compensating_value')
    search_fields = ['initiating_event__from_agent__name', 'initiating_event__to_agent__name']
    
admin.site.register(Compensation, CompensationAdmin)


