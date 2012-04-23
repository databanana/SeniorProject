import networkx as nx
import numpy as np
from sets import ImmutableSet
import fbauth.community as community
import random

#This class wraps a NetworkX graph object. It contains some custom implementations
#of already-existing NetworkX functionality for academic reasons
class GraphWrapper:
	def __init__(self, nodes, edges):
		self.G = nx.Graph()
		self.G.add_nodes_from(nodes)
		self.G.add_edges_from(edges)
		self.m = nx.to_numpy_matrix(self.G)
		self.groupCache = {}
		self.groupCache2 = {}
		self.groupCache3 = {}
		self.edgeFractionCache = {}
		self.numEdges = len(edges)
		self.numNodes = len(nodes)
		self.dendogram = None

	#The Grivan-Newman algorithm for finding communities
	#Very slow on large graphs
	def find_groups_girvan_newman(self, num_groups):
		if (num_groups==1):
			return set([self.G])
		elif (num_groups in self.groupCache):
			#return a copy of the stored set
			return self.groupCache[num_groups].copy()
		elif (num_groups > len(self.G.nodes())):
			return self.find_groups(len(self.G.nodes))
		#returns set of subgraphs
		previous_partition = self.find_groups(num_groups-1)

		#map subgraph to betweenness dict (a dict mapping edges to betweenness)
		betweenness_map = {subgraph:nx.edge_betweenness_centrality(subgraph) for subgraph in previous_partition}
		#Map subgraph to the (edge, betweenness) pair of the max betweenness in that subgraph
		betweenness_max_map = {e[0]:max(e[1].items(), key=lambda(x):x[1]) for e in betweenness_map.items() if len(e[0].nodes()) > 1}

		#Track removed edges to add them again at end of algorithm
		removed_edges = []

		#Loop until a subgraph is split
		while True:
			print "Removing edge"
			#Identify the subgraph and edge with max betweenness
			target_subgraph_edge=max(betweenness_max_map.items(), key=lambda(x):x[1][1])
			target_subgraph = target_subgraph_edge[0]
			target_edge= target_subgraph_edge[1][0]
			max_betweenness = -1
			#Remove the edge (temporarily)
			target_subgraph.remove_edge(target_edge[0], target_edge[1])
			removed_edges.append(target_edge)
			connected_components = nx.connected_components(target_subgraph)
			if len(connected_components) > 1:
				#Removing one edge from a connected component will result in max 2 connected components
				new_subgraph_1 = target_subgraph.subgraph(connected_components[0])
				new_subgraph_2 = target_subgraph.subgraph(connected_components[1])
				#Repair removed edges in target_subgraph
				target_subgraph.add_edges_from(removed_edges)
				#Remove target subgraph
				previous_partition.discard(target_subgraph)
				#Add new subgraphs
				previous_partition.add(new_subgraph_1)
				previous_partition.add(new_subgraph_2)
				#Store result
				self.groupCache[num_groups] = previous_partition
				return previous_partition.copy()
			else:
				#Recalculate betweenness, max betweenness for target subgraph
				target_betweenness = nx.edge_betweenness_centrality(target_subgraph)
				betweenness_map[target_subgraph] = target_betweenness
				betweenness_max_map[target_subgraph] = max(target_betweenness.items(), key=lambda(x):x[1])
			#Repeat loop
			continue

	def find_groups_external(self, n):
		self.dendogram = community.generate_dendogram(self.G)
		level = int(n * (len(self.dendogram)-1))
		result =community.partition_at_level(self.dendogram, level)
		groupmap = {}
		for entry in result.iteritems():
			#print entry
			#print groupmap
			if entry[1] in groupmap:
				groupmap[entry[1]].append(entry[0])
			else:
				groupmap[entry[1]] = [entry[0]]
		colors = self.get_colorscheme(len(groupmap))
		return zip(colors, groupmap.values())
		#Create list of groups

	#Returns a random RGB color
	def calculate_color(self, p):
		result = [random.randint(0,255) for x in xrange(3)]
		return "#"+''.join([hex(x)[-2:] if len(hex(x)) >3 else "0"+hex(x)[-1] for x in result])

	def get_colorscheme(self, numgroups):
		p = 1./numgroups
		result = []
		c = 0
		for i in xrange(numgroups):
			result.append(self.calculate_color(c))
			c += p
		return result

	#Calculates PageRank using interative matrix multiplication until 
	#convergence is reached
	def calculate_pagerank(self, damping=0.85):
		#A random crawler will travel upon every outgoing edge with equal probability
		#The crawler will jump to another node with P=1-damping
		m = np.array(nx.to_numpy_matrix(self.G))
		#pr_transition = nx.to_numpy_matrix(self.G)
		pr_transition = (m / np.sum(m,1))*damping + (1-damping)/self.numNodes
		pr_transition[np.isnan(pr_transition)] = 0
		#Initial probability is equal across nodes
		pr_initial = np.ones([1, self.numNodes]) * 1/self.numNodes
		#Multiply continuously and check for convergence
		eps = .00001
		max_pow = 400

		pr_prev = pr_transition
		pr_curr = np.dot(pr_prev, pr_prev)
		current_pow = 2
		print "Starting pagerank loop"
		while (np.any(np.abs(pr_prev-pr_curr) > eps) and current_pow < max_pow):
			pr_prev = pr_curr
			pr_curr = np.dot(pr_prev, pr_prev)
			current_pow = current_pow*2

		#Return results
		#pr = pr_initial * pr_curr
		pr = np.dot(pr_curr, pr_initial.T)
		pr = [rank for row in pr.tolist() for rank in row]
		return {x[0]:x[1] for x in zip(self.G.nodes(), pr)}

	#Eigenvector centrality is the eigenvector corresponding to the largest
	#eigenvalue of the adjacency matrix
	def calculate_eigenvector_centrality(self):
		m = nx.to_numpy_matrix(self.G)
		D,V = np.linalg.eig(m)
		max_index = D.argmax()
		max_eigenvector = V[:,max_index]
		ranks = [rank[0] for rank in np.real(max_eigenvector).tolist()]
		return {x[0]:x[1] for x in zip(self.G.nodes(), ranks)}

	def calculate_degree_centrality(self):
		return {node:float(len(self.G.neighbors(node))) for node in self.G.nodes()}

