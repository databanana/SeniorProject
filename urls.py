from django.conf.urls.defaults import patterns, include, url
import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^polls/', include('polls.urls')),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^fbauth/', include('fbauth.urls')),
	url(r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
	)

if settings.DEBUG:
	from django.views.static import serve
	_media_url = settings.MEDIA_URL
	if _media_url.startswith('/'):
		_media_url = _media_url[1:]
		urlpatterns += patterns('',
			(r'^%s(?P<path>.*)$' % _media_url,
			serve,
			{'document_root': settings.MEDIA_ROOT}))
	del(_media_url, serve)