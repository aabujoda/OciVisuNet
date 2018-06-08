#!/usr/bin/python
import subprocess
import json
import networkx as nx
import matplotlib.pyplot as plt
from copy import deepcopy
from config import compartment_id,vcn_id

def pull_data(resource, subresource, compartment_id=None, vcn_id=None):
    if vcn_id == None:
        cmmd = "oci %s %s list --compartment-id %s " % (resource, subresource, compartment_id)
    else:
        cmmd = "oci %s %s list --compartment-id %s --vcn-id %s " % (resource, subresource, compartment_id, vcn_id)
    p = subprocess.Popen(cmmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()

    return json.loads(output)


class vm_instance:
    ocid = None
    name = None
    subnet_ocid = None
    private_ip = None
    public_ip = None
    lifecycle_state = None


class subnet:
    ocid = None
    name = None
    cidr_block = None
    route_table_id = None
    route_table = None

    def connected_to_GW(self, gw_id):
        prefixes = []
        for r in self.route_table.rules:
            if r["network-entity-id"] == gw_id:
                prefixes.append(r["cidr-block"])
        if prefixes != []:
            return prefixes
        else:
            return None


class IGW:
    ocid = None
    name = None


class route_table:
    ocid = None
    name = None
    rules = None


""" configuration parameters """

############## Subnets #################
cmmd = "oci network subnet list --compartment-id %s --vcn-id %s " % (compartment_id, vcn_id)
p = subprocess.Popen(cmmd, stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
p_status = p.wait()

subnets_data = json.loads(output)
# print json.dumps(subnets_data, indent=4)
subnets = []
for i in subnets_data['data']:
    s = subnet()
    s.ocid = str(i["id"])
    s.name = str(i["display-name"])
    s.cidr_block = str(i["cidr-block"])
    s.route_table_id = str(i["route-table-id"])
    subnets.append(s)

############# Route tables #################
route_tables_data = pull_data("network", "route-table", compartment_id=compartment_id, vcn_id=vcn_id)
print json.dumps(route_tables_data, indent=4)
for i in route_tables_data['data']:
    r = route_table()
    r.ocid = str(i["id"])
    r.name = str(i["display-name"])
    r.rules = i["route-rules"]
    print r.rules

    for s in subnets:
        if s.route_table_id == r.ocid:
            print "routing table was found"
            s.route_table = r
        ########### Internet Gateway #################
cmmd = "oci network internet-gateway list --compartment-id %s --vcn-id %s " % (compartment_id, vcn_id)
p = subprocess.Popen(cmmd, stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
p_status = p.wait()

IGW_data = json.loads(output)

igw = IGW()
igw.ocid = IGW_data['data'][0]["id"]
igw.name = IGW_data['data'][0]["display-name"]

############## VM Instances #################
cmmd = "oci compute instance list --compartment-id %s " % (compartment_id)
p = subprocess.Popen(cmmd, stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
p_status = p.wait()

instances_data = json.loads(output)

instances = []
for i in instances_data['data']:
    c = vm_instance()
    c.ocid = str(i["id"])
    c.name = str(i["display-name"])
    c.lifecycle_state = str(i["lifecycle-state"])
    if str(i["lifecycle-state"]) == "TERMINATED":
        continue
    instances.append(c)

######## VNICs #########################
for i in instances:
    print "Instance", i.ocid
    cmmd = "oci compute instance list-vnics --instance-id %s " % (i.ocid)
    p = subprocess.Popen(cmmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()

    vnics = json.loads(output)
    i.subnet_ocid = str(vnics['data'][0]["subnet-id"])
    i.public_ip = str(vnics['data'][0]["public-ip"])
    i.private_ip = str(vnics['data'][0]["private-ip"])

##### process data ##############
labels = {}
edge_labels = {}
G = nx.MultiGraph()
vm_nodes = []
subnets_nodes = []

""" add gateways  """
G.add_node(igw.name)
labels[igw.name] = "Internet \n GW"

for i in instances:
    G.add_node(i.name)
    vm_nodes.append(i.name)
    labels[i.name] = i.name + "\n" + i.private_ip

for s in subnets:
    G.add_node(s.cidr_block)
    subnets_nodes.append(s.cidr_block)
    labels[s.cidr_block] = "Subnet\n" + s.cidr_block

for i in instances:
    for s in subnets:
        print s.ocid
        print "VIRTUAL MACHINE ID", i.subnet_ocid
        print "###################################"
        if s.ocid == i.subnet_ocid:
            G.add_edge(i.name, s.cidr_block, weight=20)

for s in subnets:
    ''' we need to check the routing table'''
    G.add_edge(s.cidr_block, igw.name, weight=0.5)
    route_entries = s.connected_to_GW(igw.ocid)
    if route_entries != None:
        edge_labels[(s.cidr_block, igw.name)] = ""
        for r in route_entries:
            G.add_edge(s.cidr_block, igw.name, weight=0.5, route_entry=r)
            edge_labels[(s.cidr_block, igw.name)] = edge_labels[(s.cidr_block, igw.name)] + "\n" + r

    # route_entry="10.0.0.0/24"
    # G.add_edge(s.cidr_block,igw.name, weight=0.5, route_entry=route_entry)
    # edge_labels[(s.cidr_block,igw.name)]=route_entry
    # labels[igw.name]="Internet \n GW"
tmp_list = deepcopy(subnets)

for s in subnets:
    for ss in tmp_list:
        if ss.ocid != s.ocid:
            G.add_edge(ss.cidr_block, s.cidr_block, weight=5)
    for ss in tmp_list:
        if ss.ocid == s.ocid:
            tmp_list.remove(ss)
# for node in G.nodes():
# set the node name as the key and the label as its value
#    labels[node] = node
# labels[instances[0].name]=instances[0].name+ "\n"+ instances[0].private_ip

pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos, node_size=3000, nodelist=vm_nodes, node_shape='s', node_color='aquamarine', alpha=1.0)
nx.draw_networkx_nodes(G, pos, node_size=5000, nodelist=subnets_nodes, node_shape='o', node_color="skyblue")
nx.draw_networkx_nodes(G, pos, node_size=5000, nodelist=[igw.name], node_shape='p', node_color="red")
nx.draw_networkx_edges(G, pos, edge_color='blue')
nx.draw_networkx_labels(G, pos, labels, font_size=8, font_color='k')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)


plt.show()
plt.savefig("Graph.png", format="PNG")
exit()
