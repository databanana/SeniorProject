from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
import json
from collections import deque
from fbauth.models import Person

@dajaxice_register
def multiply(request):
	dajax = Dajax()
	dajax.alert("server says hi from ajax.py!")
	return dajax.json()

@dajaxice_register
def graph_friends(request):
	dajax = Dajax()
	s = request.session
	user = s['fbuser']
	print "got this far"
	graph = user.get_friends_graph()
	#print json.dumps(graph[0:50])
	print("Got result")
	#dajax.alert("hello world")
	dajax.add_data(graph[0:250], 'plot_friends')
	return dajax.json()

@dajaxice_register
def update_connections(request):
	dajax = Dajax()
	s = request.session
	user = s['fbuser']
	me = Person.objects.get(id=user.id)
	print"Retrieving users between %s and %s" %(me.refreshed_from, me.refreshed_to)
	lower_limit = me.refreshed_from
	upper_limit = me.refreshed_to
	new_connections = []
	query = me.friends.filter(id__lte = upper_limit).filter(id__gt = lower_limit)
	new_connections = [[friend1.id, friend2.id] for friend1 in query for friend2 in friend1.friends.all()]
	dajax.add_data(new_connections, 'add_connections')

	return dajax.json()