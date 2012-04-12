from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
import json
from collections import deque
from fbauth.models import Person
import networkx as nx
from graphwrapper import GraphWrapper


@dajaxice_register
def get_friend_ids(request, auto = False):
	dajax = Dajax()
	s = request.session
	user = s['fbuser']
	print "Got fbuser object"
	names = user.get_friend_names()
	#print json.dumps(graph[0:50])
	print("Got result")
	#dajax.alert("hello world")
	if (auto):
		dajax.add_data(names, 'grapher.auto_add_nodes')
	else:
		dajax.add_data(names, 'grapher.add_nodes')
	return dajax.json()

@dajaxice_register
def position_friends(request, engine, width, height, auto = False):
	print "Positioning friends"
	ratio = float(width)/float(height)
	dajax = Dajax()
	s = request.session
	user = s['fbuser']
	print "Got fbuser object"
	p = Person.objects.get(id = user.id)
	print "AJAX checking if connections_ready = " +str(p.connections_ready)
	#Check if the connections are ready to be returned; if not tell client to wait 5s
	if (not p.connections_ready):
		print "Connections not ready"
		dajax.add_data({'time':3000, 'auto':auto}, 'grapher.waitToPosition')
		return dajax.json()
	nodes = user.get_friend_ids()
	print "Got nodes"
	links = user.get_friends_links()
	print "Got links"
	#print links
	G_wrapper = GraphWrapper(nodes, links)
	#This doesn't work--something to do with pickling files?
	#request.session['graphwrapper'] = G_wrapper
	#request.session['nxgraph'] = G_wrapper.G
	G = G_wrapper.G
	print "Producing layout"
	layout=nx.graphviz_layout(G, prog=engine, args="-Gratio=%f" % ratio)
	x_coords = [p[0] for p in layout.values()]
	y_coords = [p[1] for p in layout.values()]
	min_x = min(x_coords)
	max_x = max(x_coords)
	min_y = min(y_coords)
	max_y = max(y_coords)
	x_shift = -1 * min_x
	y_shift = -1*min_y
	x_scale = float(width-20)/float(max_x-min_x)
	y_scale = float(height-20)/float(max_y-min_y)
	scaled_layout = {}
	for node in layout:
		x = int((layout[node][0] + x_shift) * x_scale)+10
		y = int((layout[node][1] + y_shift) * y_scale)+10
		scaled_layout[node] = (x,y)
	#print scaled_layout
	if auto:
		dajax.add_data(scaled_layout, 'grapher.auto_set_positions')
	else:
		dajax.add_data(scaled_layout, 'grapher.set_positions')
	return dajax.json()

@dajaxice_register
def connect_friends(request):
	print "Connecting friends"
	dajax = Dajax()
	s = request.session
	user = s['fbuser']
	edges = user.get_friends_links()
	dajax.add_data(edges, 'grapher.add_edges')
	return dajax.json()

@dajaxice_register
def find_groups(request, numgroups):
	dajax = Dajax()
	s = request.session
	user = s['fbuser']
	G_wrapper = GraphWrapper(user.get_friend_ids(), user.get_friends_links())
	response = []
	response = G_wrapper.find_groups_external(1)
	dajax.add_data(response, 'grapher.colorGroups')
	return dajax.json()
