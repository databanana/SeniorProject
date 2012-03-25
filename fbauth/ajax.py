from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
import json

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
