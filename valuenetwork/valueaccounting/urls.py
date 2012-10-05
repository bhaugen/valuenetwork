from django.conf.urls import patterns, url


urlpatterns = patterns("",
    url(r"^projects/$", 'valuenetwork.valueaccounting.views.projects', name="projects"),
    url(r"^contributions/(?P<project_id>\d+)/$", 'valuenetwork.valueaccounting.views.contributions', name="contributions"),
    url(r"^contributionhistory/(?P<agent_id>\d+)/$", 'valuenetwork.valueaccounting.views.contribution_history', name="contribution_history"),
    url(r"^logtime/$", 'valuenetwork.valueaccounting.views.log_time', name="log_time"),
    url(r"^value/(?P<project_id>\d+)/$", 'valuenetwork.valueaccounting.views.value_equation', name="value_equation"),
    url(r"^xbomfg/(?P<resource_type_id>\d+)/$", 'valuenetwork.valueaccounting.views.extended_bill', name="extended_bill"),
    url(r"^network/(?P<resource_type_id>\d+)/$", 'valuenetwork.valueaccounting.views.network', name="network"),
    url(r"^timeline/$", 'valuenetwork.valueaccounting.views.timeline', name="timeline"),
    url(r"^jsontimeline/$", 'valuenetwork.valueaccounting.views.json_timeline', name="json_timeline"),
)
