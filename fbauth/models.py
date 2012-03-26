from django.db import models

# Create your models here.

class Person(models.Model):
	id = models.CharField(max_length=255, primary_key = True)
	name = models.CharField(max_length=255)
	friends = models.ManyToManyField('self')
	last_updated = models.DateField(auto_now = True)
	refreshed_from = models.CharField(max_length=255)
	refreshed_to = models.CharField(max_length=255)

	def __unicode__(self):
		return self.name