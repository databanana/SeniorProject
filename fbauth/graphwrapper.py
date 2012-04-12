import networkx as nx
import numpy as np
from sets import ImmutableSet
import fbauth.community as community

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

	def find_groups_slow(self, num_groups):
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

	def get_group_tree(self, n):
		#Start by mapping each node to a community
		communities = {self.G.nodes()[i]:i for i in xrange(self.numNodes)}
		tree = [communities.copy()]
		m = nx.to_numpy_matrix(self.G)

		merged = set()

		for j in xrange(1,n):
			communities = {}
			community_a = 0
			numcommunities = len(m)
			deleted_communities = set([])
			remaining_communities = set(range(numcommunities))
			while community_a < numcommunities:
				if community_a in deleted_communities:
					community_a += 1
					continue
				merge_target = None
				max_mod_change = -np.inf
				for community_b in self.find_adjacencies(m, community_a):
					if community_a==community_b or community_b in deleted_communities:
						continue
					mod_change = self.find_modularity_change(m, community_a, community_b)
					if mod_change > max_mod_change:
						merge_target = community_b
						max_mod_change = mod_change
				if merge_target != None:
					upper = max(community_a, merge_target)
					lower = min(community_a, merge_target)
					#print "Merging %s with %s" % (community_a, merge_target)
					communities[upper] = lower
					deleted_communities.add(upper)
					remaining_communities.remove(upper)
					#m = self.merge_communities(m, community_a, merge_target)
					self.merge_communities_nodel(m, upper, lower)
				#print "Increasing communit_a"
				community_a += 1
				continue
			#Reformat m all in one go
			#Sort deleted_communities
			deleted_list = sorted(deleted_communities)
			#Sort remaining_communities
			remaining_list = sorted(remaining_communities)
			change = 0
			deleted_index = 0
			remaining_index = 0
			for deleted in deleted_list:
				while remaining_index < len(remaining_list) and remaining_list[remaining_index] < deleted:
					communities[remaining_list[remaining_index]] = remaining_list[remaining_index]+change
					remaining_index += 1
				change -= 1
			#Loop over remaining_communities
			while remaining_index < len(remaining_list):
				communities[remaining_list[remaining_index]] = remaining_list[remaining_index]+change

			#Update matrix
			communities['matrix'] = m
			m = m[remaining_list,:][:,remaining_list]
			tree.append(communities.copy())

		return tree

	#each community is a single row in the matrix
	def merge_communities(self, m, group_a, group_b):
		lower = min(group_a, group_b)
		upper = max(group_a, group_b)
		m[lower, :] += m[upper, :]
		m[:, lower] += m[:, upper]
		m = np.delete(m, upper, 0)
		m = np.delete(m, upper, 1)
		return m

	def merge_communities_nodel(self, m, source, target):
		m[target,:] += m[source,:]
		m[:,target] += m[:,source]

	def find_modularity_change(self, m, group_a, group_b):
		intersection = np.sum(m[group_a])
		change = 2*(m[group_a, group_b]-np.sum(m[group_a, :])*np.sum(m[group_b, :]))
		return change

	def find_adjacencies(self, m, group_a):
		result =  np.nonzero(m[group_a])[1]
		#print result.A
		if result.shape == (1,0):
			return []
		else:
			return list(result.A[0])

	#Use p between 0 and 1
	def calculate_color(self, p):
		p = min(p, 1)
		print "Calculating color for position %s" % p
		result = [0,0,0]
		if (0 < p <= float(1)/3):
			result=[(1-p)/float(1)/3, p/float(1)/3, 0]
		elif (float(1)/3 < p <= float(2)/3):
			p = p-float(1)/3
			result=[0,(1-p)/float(1)/3, (p)/float(1)/3]
		else:
			p = p-float(2)/3
			result = [(p)/float(1)/3, 0, (1-p)/float(1)/3]
		print result
		sqsum = sum([v**2 for v in result])
		sqfactor = float(255**2)/sqsum
		print sqfactor
		factor = sqfactor**0.5
		print factor
		result = [int(factor* v) for v in result]
		print result

		return "#"+''.join([hex(x)[-2:] if len(hex(x)) >3 else "0"+hex(x)[-1] for x in result])

	def get_colorscheme(self, numgroups):
		p = 1./numgroups
		result = []
		c = 0
		for i in xrange(numgroups):
			result.append(self.calculate_color(c))
			c += p
		return result
