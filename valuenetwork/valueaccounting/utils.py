import datetime
from itertools import chain, imap
from django.contrib.contenttypes.models import ContentType

from valuenetwork.valueaccounting.models import Commitment, Process

def split_thousands(n, sep=','):
    s = str(n)
    if len(s) <= 3: return s  
    return split_thousands(s[:-3], sep) + sep + s[-3:]

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
        process_type_relationship.relationship.name
    ))
    for rtr in process_type_relationship.process_type.consumed_resource_type_relationships():
        nodes.append(rtr.resource_type)
        edges.append(Edge(rtr.resource_type, process_type_relationship.process_type, rtr.inverse_label()))
        for art in rtr.resource_type.producing_agent_relationships():
            nodes.append(art.agent)
            edges.append(Edge(art.agent, rtr.resource_type, art.relationship.name))
        for pt in rtr.resource_type.producing_process_type_relationships():
            explode(pt, nodes, edges, depth+1, depth_limit)

def graphify(focus, depth_limit):
    nodes = [focus]
    edges = []
    for art in focus.consuming_agent_relationships():
        nodes.append(art.agent)
        edges.append(Edge(focus, art.agent, art.relationship.name))
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
        for pp in ic.resource_type.producing_process_types():
            backschedule_process_types(ic, pp,events)

    return events

def generate_schedule(process, order, user):
    pt = process.process_type
    output = process.main_outgoing_commitment()
    for ptrt in pt.consumed_resource_type_relationships():
        commitment = Commitment(
            independent_demand=order,
            event_type=ptrt.relationship.event_type,
            relationship=ptrt.relationship,
            due_date=process.start_date,
            resource_type=ptrt.resource_type,
            process=process,
            project=pt.project,
            quantity=output.quantity * ptrt.quantity,
            unit_of_quantity=ptrt.resource_type.unit,
            created_by=user,
        )
        commitment.save()
        pptr = ptrt.resource_type.main_producing_process_type_relationship()
        if pptr:
            next_pt = pptr.process_type
            start_date = process.start_date - datetime.timedelta(minutes=next_pt.estimated_duration)
            next_process = Process(          
                name=next_pt.name,
                process_type=next_pt,
                project=next_pt.project,
                url=next_pt.url,
                end_date=process.start_date,
                start_date=start_date,
            )
            next_process.save()
            next_commitment = Commitment(
                independent_demand=order,
                event_type=pptr.relationship.event_type,
                relationship=pptr.relationship,
                due_date=process.start_date,
                resource_type=pptr.resource_type,
                process=next_process,
                project=next_pt.project,
                quantity=output.quantity * pptr.quantity,
                unit_of_quantity=pptr.resource_type.unit,
                created_by=user,
            )
            next_commitment.save()
            generate_schedule(next_process, order, user)

class XbillNode(object):
    def __init__(self, node, depth):
         self.node = node
         self.depth = depth
         self.open = False
         self.close = []
         self.xbill_class = self.node.xbill_class()

    def xbill_object(self):
        return self.node.xbill_child_object()

    def xbill_label(self):
        return self.node.xbill_label()

    def xbill_explanation(self):
        return self.node.xbill_explanation()

    #def xbill_class(self):
    #    ct = ContentType.objects.get_for_model(self.xbill_object().__class__)
    #    return "-".join(ct.name.split())

    def category(self):
        return self.node.xbill_category()


def xbill_dfs(node, all_nodes, depth):
    """
    Performs a recursive depth-first search starting at ``node``. 
    """
    to_return = [XbillNode(node,depth),]
    #print "+created node:+", node, depth
    #import pdb; pdb.set_trace()
    for subnode in all_nodes:
        parents = subnode.xbill_parent_object().xbill_parents()
        if not subnode is node:
            if parents and node in parents:
                #print "*active node:*", node, "*depth:*", depth, "*subnode:*", subnode, "*parent_object:*", subnode.xbill_parent_object(), "*parents:*", parents
                #import pdb; pdb.set_trace()
                to_return.extend(xbill_dfs(subnode, all_nodes, depth+1))
    return to_return

def explode_xbill_children(node, nodes):
    nodes.append(node)
    #import pdb; pdb.set_trace()
    for kid in node.xbill_child_object().xbill_children():
        explode_xbill_children(kid, nodes)

def generate_xbill(resource_type):
    nodes = []
    for kid in resource_type.xbill_children():
        explode_xbill_children(kid, nodes)
    nodes = list(set(nodes))
    #import pdb; pdb.set_trace()
    to_return = []
    for kid in resource_type.xbill_children():
        to_return.extend(xbill_dfs(kid, nodes, 0))
    annotate_tree_properties(to_return)
    #to_return.sort(lambda x, y: cmp(x.xbill_object().name,
    #                                y.xbill_object().name))
    return to_return


#adapted from threaded_comments.util
def annotate_tree_properties(nodes):
    """
    iterate through nodes and adds some magic properties to each of them
    representing opening list of children and closing it
    """
    if not nodes:
        return

    it = iter(nodes)

    # get the first item, this will fail if no items !
    old = it.next()

    # first item starts a new thread
    old.open = True
    for c in it:

        # increase the depth
        if c.depth > old.depth:
            c.open = True

        else: # c.depth <= old.depth
            # close some depths
            old.close = range(old.depth - c.depth)

        # iterate
        old = c

    old.close = range(old.depth)

