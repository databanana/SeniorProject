from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
import json
from collections import deque
from fbauth.models import Person
import networkx as nx
from graphwrapper import GraphWrapper
from fbauth import community
import numpy as np


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
def position_friends(request, engine, width, height, widthoffset=0, auto = False):
	print "Positioning friends"
	width = width-widthoffset
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
	G = G_wrapper.G
	print "Producing layout"
	if (engine=="sfdp"):
		layout=nx.graphviz_layout(G, prog=engine, args="-Gratio=%f -Gsize=\"%f,%f\" -GK=1.5" % (ratio, 10., ratio*10.))
	elif (engine=="twopi"):
		layout=nx.graphviz_layout(G, prog=engine, args="-Gratio=%f" % ratio)
	else:
		#Invalid layout engine?
		return dajax.json()
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
		x = int((layout[node][0] + x_shift) * x_scale)+10+widthoffset
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
def find_groups(request, n):
	dajax = Dajax()
	s = request.session
	user = s['fbuser']
	G_wrapper = GraphWrapper(user.get_friend_ids(), user.get_friends_links())
	#Why does storing this in the session not work...?
	dendogram = community.generate_dendogram(G_wrapper.G)
	level = int(n * (len(dendogram)-1))
	print "Level: %s" % level
	result =community.partition_at_level(dendogram, level)
	groupmap = {}
	for entry in result.iteritems():
		#print entry
		#print groupmap
		if entry[1] in groupmap:
			groupmap[entry[1]].append(entry[0])
		else:
			groupmap[entry[1]] = [entry[0]]
	colors = G_wrapper.get_colorscheme(len(groupmap))
	response=zip(colors, groupmap.values())
	#dajax.alert("Level: %s" % level)
	dajax.add_data(response, 'grapher.colorGroups')
	return dajax.json()

@dajaxice_register
def get_rank(request, algorithm, min_radius, max_radius):
	dajax = Dajax()
	user = request.session['fbuser']
	if 'graphwrapper' in request.session:
		G_wrapper = request.session['graphwrapper']
	else:
		G_wrapper = GraphWrapper(user.get_friend_ids(), user.get_friends_links())
		request.session['graphwrapper'] = G_wrapper
	if algorithm=='PageRank':
		#if False:
		if 'pagerank' in request.session:
			rank = request.session['pagerank']
		else:
			#rank = nx.pagerank_numpy(G_wrapper.G)
			print "Calculating pagerank"
			rank = G_wrapper.calculate_pagerank()
			request.session['pagerank'] = rank
	elif algorithm=='Betweenness':
		if 'betweenness' in request.session:
			rank = request.session['betweenness']
		else:
			rank = nx.betweenness_centrality(G_wrapper.G)
			request.session['betweenness'] = rank
	elif algorithm=='Eigenvector':
		if 'eigenvector' in request.session:
			rank = request.session['eigenvector']
		else:
			#rank = nx.eigenvector_centrality(G_wrapper.G)
			rank = G_wrapper.calculate_eigenvector_centrality()
			request.session['eigenvector'] = rank
	elif algorithm=='Degree':
		#if False:
		if 'degree' in request.session:
			rank = request.session['degree']
		else:
			rank = G_wrapper.calculate_degree_centrality()
			request.session['degree'] = rank
	else:
		return dajax.json();

	#Scale nodes' area (not radius!) between the areas of circles with min and max radius
	min_area = np.pi*min_radius**2
	max_area = np.pi*max_radius**2
	area_change = max_area-min_area
	min_rank = min(rank.values())
	max_rank = max(rank.values())
	rank_change = max_rank-min_rank
	node_radii = {}
	for node, rank in rank.iteritems():
		area = (rank-min_rank)/rank_change * area_change + min_area
		radius = (area/np.pi)**0.5
		node_radii[node] = radius
	dajax.add_data(node_radii, 'grapher.resizeNodes')
	result = dajax.json()
	return result