import re
import datetime
from itertools import chain, imap
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

def flattened_children(node, all_nodes, to_return):
     to_return.append(node)
     for subnode in all_nodes:
         if subnode.parent and subnode.parent.id == node.id:
             flattened_children(subnode, all_nodes, to_return)
     return to_return

class Edge(object):
    def __init__(self, from_node, to_node, label):
        self.from_node = from_node
        self.to_node = to_node
        self.label = label
        self.width = 1


def explode(process_type_relationship, nodes, edges, depth, depth_limit):
    if depth > depth_limit:
        return
    nodes.append(process_type_relationship.process_type)
    edges.append(Edge(
        process_type_relationship.process_type, 
        process_type_relationship.resource_type, 
        process_type_relationship.direction
    ))
    for rtr in process_type_relationship.process_type.consumed_resource_type_relationships():
        nodes.append(rtr.resource_type)
        edges.append(Edge(rtr.resource_type, process_type_relationship.process_type, rtr.diagram_input_label()))
        for art in rtr.resource_type.producing_agent_relationships():
            nodes.append(art.agent)
            edges.append(Edge(art.agent, rtr.resource_type, art.direction))
        for pt in rtr.resource_type.producing_process_type_relationships():
            explode(pt, nodes, edges, depth+1, depth_limit)

def graphify(focus, depth_limit):
    nodes = [focus]
    edges = []
    for art in focus.consuming_agent_relationships():
        nodes.append(art.agent)
        edges.append(Edge(focus, art.agent, art.direction))
    for ptr in focus.producing_process_type_relationships():
        explode(ptr, nodes, edges, 0, depth_limit)
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

def backschedule_process_types(commitment, process_type,events):
    lead_time=1
    arts = None
    if commitment.from_agent:
        arts = commitment.from_agent.resource_types.filter(resource_type=commitment.resource_type)
    if arts:
        lead_time = arts[0].lead_time
    end_date = commitment.due_date - datetime.timedelta(days=lead_time)
    start_date = end_date - datetime.timedelta(days=(process_type.estimated_duration/1440))
    ppte = TimelineEvent(
        process_type,
        start_date,
        end_date,
        process_type.timeline_title(),
        process_type.url,
        process_type.description,
    )
    events['events'].append(ppte.dictify())
    for crt in process_type.consumed_resource_types():
        explode_events(crt, start_date, events)


def backshedule_events(process, events):
    te = TimelineEvent(
        process,
        process.start_date,
        process.end_date,
        process.timeline_title(),
        process.url,
        process.notes,
    )
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
        #for pp in ic.resource_type.producing_process_types():
        #    backschedule_process_types(ic, pp,events)

    return events

class XbillNode(object):
    def __init__(self, node, depth):
         self.node = node
         self.depth = depth


def xbill_dfs(node, all_nodes, depth):
    """
    Performs a recursive depth-first search starting at ``node``. 
    """
    to_return = [XbillNode(node,depth),]
    for subnode in all_nodes:
        parents = subnode.xbill_parents()
        if parents and node in parents:
            to_return.extend(xbill_dfs(subnode, all_nodes, depth+1))
    return to_return

def explode_xbill_children(node, nodes):
    nodes.append(node)
    for kid in node.xbill_children():
        explode_xbill_children(kid, nodes)

def generate_xbill(resource_type):
    nodes = []
    explode_xbill_children(resource_type, nodes)
    #import pdb; pdb.set_trace()
    nodes = list(set(nodes))
    to_return = []
    to_return.extend(xbill_dfs(resource_type, nodes, 0))
    return to_return


#adapted from threaded_comments.util
def annotate_tree_properties(comments):
    """
    iterate through nodes and adds some magic properties to each of them
    representing opening list of children and closing it
    """
    if not comments:
        return

    it = iter(comments)

    # get the first item, this will fail if no items !
    old = it.next()

    # first item starts a new thread
    old.open = True
    last = set()
    for c in it:
        # if this comment has a parent, store its last child for future reference
        if old.last_child_id:
            last.add(old.last_child_id)

        # this is the last child, mark it
        if c.pk in last:
            c.last = True

        # increase the depth
        if c.depth > old.depth:
            c.open = True

        else: # c.depth <= old.depth
            # close some depths
            old.close = range(old.depth - c.depth)

            # new thread
            if old.root_id != c.root_id:
                # close even the top depth
                old.close.append(len(old.close))
                # and start a new thread
                c.open = True
                # empty the last set
                last = set()
        # iterate
        yield old
        old = c

    old.close = range(old.depth)
    yield old
