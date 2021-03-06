import pickle
import sys
import MySQLdb as mdb
from pprint import pprint
cursor
USE_CACHE = False

SQL_GET_ALL_MOVIES = """
	SELECT id FROM movies
	WHERE year >= 2005
"""

SQL_GET_ROLES_OF_MOVIE = """
	SELECT actor_id, first_name, last_name
	FROM imdb.movies movies 
	LEFT OUTER JOIN imdb.roles roles ON movies.id = roles.movie_id 
	LEFT OUTER JOIN imdb.actors actors ON actors.id = roles.actor_id 
	WHERE actors.id IS NOT NULL AND movies.id = %d
"""

def build_graph():
	global cursor
	adj = {}
	con = mdb.connect('127.0.0.1', 'root', 'geekchamp3!', 'imdb')
	with con:
		cur = con.cursor()
		cursor = cur
		cur.execute(SQL_GET_ALL_MOVIES)
		rows = cur.fetchall()
		for row in rows:
			movie_id = long(row[0])
			cur_two = con.cursor()
			roles = SQL_GET_ROLES_OF_MOVIE % int(movie_id)
			cur_two.execute(roles)
			rows_two = cur_two.fetchall()
			for rt in rows_two:
				actor = str(long(rt[0])) + "_" + str(rt[1]) + "_" + str(rt[2])
				for rt_other in rows_two:
					actor_other = str(rt_other[0]) + "_" + str(rt_other[1]) + "_" + str(rt_other[2])
					if(actor != actor_other):
						#print "check for actor: " + actor + " against: " + actor_other + " in movie with id: " + str(movie_id)
						if(actor in adj):
							# check if other actor is already present and increment
							if(actor_other in adj[actor]):
								adj[actor][actor_other] += 1
							else:
								adj[actor][actor_other] = 1
						else:
							adj[actor] = {}
	return adj


def naive_max_edgeweighted_4clique(G):
	global cursor
	current_clique = ((),-1)
	for v, v_neighbours in G.iteritems():
		for u, u_wt in v_neighbours.iteritems():
			for w, w_wt in v_neighbours.iteritems():
				if(w in G[u]):
					for z, z_wt in v_neighbours.iteritems():
						if(z in G[w] and z in G[u] and z != w and z != u):
							if(get_clique_weight(G,v,u,w,z) > current_clique[1]):
								current_clique = ((v,u,w,z),get_clique_weight(G,v,u,w,z))
								print "Found clique: " + "v: " + v + ", u: " + u + ", w: " + w + ", z: " + z
								print "Weight of clique: " + str(get_clique_weight(G,v,u,w,z))
								args = (v.split('_')[0], u.split('_')[0], w.split('_')[0], z.split('_')[0], "@p_count")
								cursor.callproc('Check4Clique', args)
	return current_clique


def optimized_max_edgeweighted_4clique(G):
	global cursor
	current_clique = ((),-1)
	triangles = node_iterator_plus_plus(G);
	#print len(triangles)
	for v,u,w in triangles:
		v_adj,u_adj,w_adj = G[v].keys(),G[u].keys(),G[w].keys()
		#union_set = (v_adj.union(u_adj)).union(w_adj)
		union_list = intersect(intersect(v_adj,u_adj),w_adj)
		#print union_list
		if(len(union_list) > 0):
			for z in union_list:
				weight = get_clique_weight(G,v,u,w,z)
				if(weight >= current_clique[1]):
					print "Found clique: " + "v: " + v + ", u: " + u + ", w: " + w + ", z: " + z
					print "Weight of clique: " + str(weight)
					current_clique = ((v,u,w,z),weight)
					args = (v.split('_')[0], u.split('_')[0], w.split('_')[0], z.split('_')[0], "@p_count")
					cursor.callproc('Check4Clique', args)
	return current_clique



# TRIANGLE COUNTING
def node_iterator_plus_plus(G):
	global cursor
	triangles = []
	for v, v_neighbours in G.iteritems():
		for u, u_wt in v_neighbours.iteritems():
			if(len(G[u]) >= len(v_neighbours)):
				for w, w_wt in v_neighbours.iteritems():
					if(len(G[w]) >= len(G[u])):
						if(w in G[u]):
							triangles.append((v,u,w))

	return triangles

# HELPERS
def get_clique_weight(adj,v,u,w,z):
	return min(adj[v][u],adj[v][w],adj[v][z],adj[u][w],adj[u][z],adj[w][z])
	#return adj[v][u] + adj[v][w] + adj[v][z] + adj[u][w] + adj[u][z] + adj[w][z]

def intersect(a, b):
    """ return the intersection of two lists """
    return list(set(a) & set(b))



# RUN

# build graph
if not USE_CACHE:
	print "Building graph from DB..."
	graph = build_graph();
	with open('cache.pickle', 'wb') as handle:
		pickle.dump(graph, handle)
else:
	print "Building graph from cache..."
	with open('cache.pickle', 'rb') as handle:
		graph = pickle.load(handle)
print "Finished building graph"
#pprint(graph)


print "Running algorithm..."

# NAIVE
max_clique = naive_max_edgeweighted_4clique(graph)
#pprint(max_clique)

# OPTIMIZED
#optimized_max_edgeweighted_4clique(graph)








