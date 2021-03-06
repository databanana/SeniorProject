from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from urllib2 import urlopen
from urlparse import parse_qs
from django.core.urlresolvers import reverse
from fb import Fbuser
from django.template import RequestContext
from threading import Thread
from fbauth.models import Person
from django.conf import settings



def index(request):
	#print reverse('fbauth.views.login')
	return render_to_response('fbauth/index.html', {'app_id': settings.APP_ID, 'redirect_url': "http://"+request.get_host() + reverse('fbauth.views.login') }, context_instance=RequestContext(request))

#Facebook's API redirects to this page to transfer the auth key
def login(request):
	print "In login view"
	print request.session
	app_id = settings.APP_ID
	app_secret = settings.APP_SECRET
	redirect_url = "http://"+request.get_host() + reverse('fbauth.views.login')
	#print redirect_url
	#redirect_url = 'http://localhost:8000/fbauth/login'

	try:
		code = request.GET['code']
		requestsite = urlopen("https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s" % (app_id, redirect_url, app_secret, code))
		try:
			response = ""
			for line in requestsite:
				response = response + line
		except (IOError):
			return HttpResponse("Couldn't read URL with auth key")
		results = parse_qs(response)
		access_token = results['access_token'][0]
		#expiration = results['access_token'][1]
	except (KeyError):
		return HttpResponse("Sorry, please try logging in again.")
	else:
		request.session['access_token'] = access_token
		return HttpResponseRedirect(reverse('fbauth.views.grapher'))

#This view has all the graphing functionality.
def grapher(request):
	if ('access_token' not in request.session):
		print request.session
		return HttpResponseRedirect(reverse('fbauth.views.index'))
	if ('fbuser' not in request.session): request.session['fbuser'] = Fbuser(request.session['access_token'])

	u = request.session['fbuser']
	print "Access token: %s" % u.access_token
	#Pull the user's facebook friends if they are not recently updated
	if (not u.recently_updated()):
		print("Not recently updated")
		u.create_friends()
		me = Person.objects.get(id=u.id)
		me.connections_ready = False;
		print "connections_read = " + str(me.connections_ready)
		me.save()
		connection_processor = Thread(target=u.connect_friends)
		connection_processor.start()
	return render_to_response('fbauth/graph.html', context_instance = RequestContext(request))