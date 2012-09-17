from django.conf.urls import patterns, url


urlpatterns = patterns("",
    url(r"^projects/$", 'valuenetwork.valueaccounting.views.projects', name="projects"),
    url(r"^contributions/(?P<project_id>\d+)/$", 'valuenetwork.valueaccounting.views.contributions', name="contributions"),
    url(r"^logtime/$", 'valuenetwork.valueaccounting.views.log_time', name="log_time"),
)
