from django.conf.urls.defaults import patterns, include, url
from dajaxice.core import dajaxice_autodiscover
from django.conf import settings

dajaxice_autodiscover()

urlpatterns = patterns('fbauth.views',
	url(r'^$', 'index'),
	url(r'^login$', 'login'),
	url(r'^grapher$', 'grapher'),
	)