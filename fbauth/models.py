from django.db import models

# Create your models here.

class Person(models.Model):
	id = models.CharField(max_length=255, primary_key = True)
	name = models.CharField(max_length=255)
	friends = models.ManyToManyField('self')
	last_updated = models.DateField(auto_now = True)

	def __unicode__(self):
		return self.name