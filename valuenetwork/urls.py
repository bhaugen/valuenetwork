from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from django.contrib import databrowse
from valuenetwork.valueaccounting.models import *

databrowse.site.register(
    AgentType,
    AssociationType,
    AgentAssociation,
    Category,
    EconomicAgent, 
    EconomicResourceType,
    EconomicResource,
    AgentResourceType, 
    ProcessType, 
    ProcessTypeResourceType,
    Project,
    ResourceRelationship,
    Commitment,
    EconomicEvent,
    EventType,
    Process,
    Unit,
    CachedEventSummary,
)

urlpatterns = patterns("",
    url(r"^$", direct_to_template, {"template": "homepage.html"}, name="home"),
    url(r"^admin/", include(admin.site.urls)),

    url(r"^account/", include("account.urls")),
    url(r"^accounting/", include("valuenetwork.valueaccounting.urls")),
    (r'^databrowse/(.*)', databrowse.site.root),
    url(r'^add/(?P<model_name>\w+)/?$', 'valuenetwork.tekextensions.views.add_new_model'),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
