from django.db import models

# Create your models here.

class Person(models.Model):
	id = models.CharField(max_length=255, primary_key = True)
	name = models.CharField(max_length=255)
	friends = models.ManyToManyField('self', through='Connection', symmetrical=False)
	last_updated = models.DateField(null=True)
	connections_ready = models.BooleanField(default=False)

	def __unicode__(self):
		return self.name


class Connection(models.Model):
	from_person = models.ForeignKey(Person, related_name='+')
	to_person = models.ForeignKey(Person, related_name='+')