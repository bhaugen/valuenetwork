import re
import datetime
from django.template.defaultfilters import slugify

def split_thousands(n, sep=','):
    s = str(n)
    if len(s) <= 3: return s  
    return split_thousands(s[:-3], sep) + sep + s[-3:]

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

def dfs(node, all_nodes, depth):
    """
    Performs a recursive depth-first search starting at ``node``. 
    """
    to_return = [node,]
    for subnode in all_nodes:
        if subnode.parent and subnode.parent.id == node.id:
            to_return.extend(dfs(subnode, all_nodes, depth+1))
    return to_return


class Edge(object):
     def __init__(self, from_node, to_node):
         self.from_node = from_node
         self.to_node = to_node
         self.width = 1


def explode(process_type, to_node, nodes, edges):
    nodes.append(process_type)
    edges.append(Edge(process_type, to_node))
    for rt in process_type.consumed_resource_types():
        nodes.append(rt)
        edges.append(Edge(rt, process_type))
        for pt in rt.producing_process_types():
            explode(pt, rt, nodes, edges)

def graphify(focus):
    nodes = [focus]
    edges = []
    for agt in focus.consuming_agents():
        nodes.append(agt)
        edges.append(Edge(focus, agt))
    for pt in focus.producing_process_types():
        explode(pt, focus, nodes, edges)
    return [nodes, edges]

class TimelineEvent(object):
    def __init__(self, node, start, end, title, link, description):
         self.node = node
         self.start = start
         self.end = end
         self.title = title
         self.link = link
         self.description = description

    def dictify(self):
        d = {
            "start": self.start.strftime("%b %e %Y 00:00:00 GMT-0600"),
            "title": self.title,
            "description": self.description,
        }
        if self.end:
            d["end"] = self.end.strftime("%b %e %Y 00:00:00 GMT-0600")
            d["durationEvent"] = True
        else:
            d["durationEvent"] = False
        if self.link:
            d["link"] = self.link
        return d

def explode_events(resource_type, backsked_date, events):
    for art in resource_type.producing_agent_relationships():
        order_date = backsked_date - datetime.timedelta(days=art.lead_time)
        te = TimelineEvent(
            art,
            order_date,
            "",
            art.timeline_title(),
            resource_type.url,
            resource_type.description,
        )
        events['events'].append(te.dictify())
    for pp in resource_type.producing_process_types():
        start_date = backsked_date - datetime.timedelta(days=(pp.estimated_duration/1440))
        ppte = TimelineEvent(
            pp,
            start_date,
            backsked_date,
            pp.timeline_title(),
            pp.url,
            pp.description,
        )
        events['events'].append(ppte.dictify())
        for crt in pp.consumed_resource_types():
            explode_events(crt, start_date, events)

def backshedule_events(process):
    te = TimelineEvent(
        process,
        process.start_date,
        process.end_date,
        process.timeline_title(),
        process.url,
        process.notes,
    )
    events = {'dateTimeFormat': 'Gregorian','events':[]}
    events['events'].append(te.dictify())
    for ic in process.incoming_commitments():
        te = TimelineEvent(
            ic,
            ic.due_date,
            "",
            ic.timeline_title(),
            ic.url,
            ic.description,
        )
        events['events'].append(te.dictify())
        for pp in ic.resource_type.producing_process_types():
            lead_time=1
            if ic.from_agent:
                arts = ic.from_agent.resource_types.filter(resource_type=ic.resource_type)
            if arts:
                lead_time = arts[0].lead_time
            end_date = ic.due_date - datetime.timedelta(days=lead_time)
            start_date = end_date - datetime.timedelta(days=(pp.estimated_duration/1440))
            ppte = TimelineEvent(
                pp,
                start_date,
                end_date,
                pp.timeline_title(),
                pp.url,
                pp.description,
            )
            events['events'].append(ppte.dictify())
            for crt in pp.consumed_resource_types():
                explode_events(crt, start_date, events)

    return events
