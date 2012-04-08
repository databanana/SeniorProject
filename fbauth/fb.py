from urllib2 import urlopen
from urllib import urlencode
import json
from fbauth.models import Person, Connection
from django.db import connection, transaction
import datetime
from collections import deque

class Fbuser:
	def __init__(self, access_token):
		self.access_token = access_token
		data = self.read_and_parse_json('/me')
		self.name = data['name']
		self.id = data['id']
		self.updated_friends_queue = deque()
		self.links = None

	def read_and_parse_json(self, url, argdict = {}):
		#argstr = '&'.join([x[0] + '=' + x[1] for x in argdict.items()])
		argstr = urlencode(argdict)
		if (url.lower().startswith("http://") or url.lower().startswith("https://")):
			if (url.find('?') == -1):
				requesturl = "%s?%s&access_token=%s" % (url, argstr, self.access_token)
			else:
				requesturl = "%s%s&access_token=%s" % (url, argstr, self.access_token)
		else:
			requesturl = "https://graph.facebook.com%s?%s&access_token=%s" % (url, argstr, self.access_token)
		urlfile = urlopen(requesturl)
		jsonresponse = urlfile.read()
		parsedjson = json.loads(jsonresponse)
		#If paging is used and response includes a data section, merge sections together
		return json.loads(jsonresponse)

	def concat_data_pages(self, url, argdict = {}):
		parsedjson = self.read_and_parse_json(url, argdict)
		data = []
		while ("data" in parsedjson and len(parsedjson["data"]) > 0):
			data += parsedjson["data"]
			if ("paging" not in parsedjson or "next" not in parsedjson["paging"]): break
			parsedjson = self.read_and_parse_json(parsedjson["paging"]["next"])

		return data

	def get_friends(self):
		friends = self.concat_data_pages('/me/friends')
		return friends

	def run_fql(self, query):
		return self.read_and_parse_json('/fql', {"q":query})

	def get_mutual_friends(self, limit=4500):
		#FQL line limit is undocumented but is somewhere around 5000
		#There will be some overlap at the end/beginning of each query and some duplicate results
		data = []
		startID = "0"
		i=0
		while True:
			print "Starting with uid %s" % startID
			print "Found %d connections" % len(data)
			query = "SELECT uid1, uid2 FROM friend WHERE uid1 IN (SELECT uid2 FROM friend WHERE uid1=me() AND uid2 >= %s) AND uid2 IN (SELECT uid2 FROM friend WHERE uid1=me() AND uid2 >= %s) ORDER BY uid1 LIMIT %d" % (startID, startID, limit)
			print query
			mf = self.run_fql(query)
			data.extend(mf["data"])
			if len(mf["data"]) < limit: break
			startID = mf["data"][-1]["uid1"]
		return data

	def recently_updated(self, td = datetime.timedelta(2)):
		#return False
		#Default definition of "recently" is the past 2 days
		try:
			me = Person.objects.get(id = self.id)
		except Person.DoesNotExist:
			return False
		else:
			if me.last_updated == None:
				return False
			else:
				return (datetime.date.today()-me.last_updated) < td


	def create_friends(self):
		friends = self.get_friends()
		try:
			me = Person.objects.get(id=self.id)
		except Person.DoesNotExist:
			me = Person.objects.create(id = self.id, name = self.name)
		me.last_updated = datetime.date.today()
		me.save()

		for friend in friends:
			friendlookup = Person.objects.filter(id=friend['id'])
			if len(friendlookup) == 0:
				p = Person.objects.create(name = friend['name'], id = friend['id'])
				p.save()
			else:
				p = friendlookup[0]
			if (p not in me.friends.all()):
				forwardconnection = Connection.objects.create(from_person_id=self.id, to_person_id = friend['id'])
				reverseconnection = Connection.objects.create(to_person_id=self.id, from_person_id = friend['id'])
				forwardconnection.save()
				reverseconnection.save()


	def connect_friends(self):
		print "Connecting friends"
		#Get cursor from db wrapper
		cursor = connection.cursor()
		#cursor.write("BEGIN TRANSACTION")

		#Super slow. Replace with a custom SQL insert query
		#MySQL version:
		#INSERT IGNORE INTO "fbauth_person_friends" ("from_person_id", "to_person_id") VALUES (p1, p2), (p2, p1) ...
		#values = ",".join(["("+r['uid1'] + "," + r['uid2'] + "), ("+r['uid2']+","+r['uid1']+")" for r in mf])

		#SQLite version:
		#BEGIN TRANSACTION;
		#INSERT OR IGNORE INTO "fbauth_person_friends" ("from_person_id", "to_person_id") VALUES (p1, p2)
		#...
		#COMMIT;

		#insertstr = "INSERT OR IGNORE INTO \"fbauth_person_friends\" (\"from_person_id\", \"to_person_id\") VALUES "
		#''.join([insertstr+"("+r['uid1'] + "," + r['uid2'] + ");" + insertstr + "("+r['uid2']+","+r['uid1']+");" for r in mf])

		#SQLite:
		mf = self.get_mutual_friends()
		insertstr = "INSERT OR IGNORE INTO fbauth_connection (from_person_id, to_person_id) VALUES"
		#values = ''.join([insertstr+"("+r['uid1'] + "," + r['uid2'] + ");" + insertstr + "("+r['uid2']+","+r['uid1']+");" for r in mf])

		cursor.execute("BEGIN TRANSACTION")
		for r in mf:
			cursor.execute(insertstr+" (%s,%s)", params=[str(r['uid1']), str(r['uid2'])])
			cursor.execute(insertstr+" (%s,%s)", params=[str(r['uid2']), str(r['uid1'])])
		transaction.commit_unless_managed()


		#SLOWWWW version:
		#mf = self.get_mutual_friends()
		#prevp1 = None
		#p1 = None
		#for r in mf:
		#	prevp1 = p1
		#	p1 = Person.objects.get(id=r['uid1'])
		#	p2 = Person.objects.get(id=r['uid2'])
		#	p1.friends.add(p2)
		#	if (prevp1 != None and p1 != prevp1):
		#		prevp1.save()
		#		print "Saved friends for %s" % prevp1.name
		#p1.save()
		#print "Saved friends for %s" % p1.name
		print "Finished creating models"
		me = Person.objects.get(id=self.id)
		me.connections_ready = True
		me.save()
		print "connections_ready = " + str(me.connections_ready)

	def get_friends_graph(self):
		print "Started printing friends graph"
		user = Person.objects.select_related().get(id=self.id)
		print "Got user"
		friends = user.friends.all()
		print("Got list of friends")
		result = [{
			'id': friend.id,
			'name': friend.name,
			'data': {},
			'adjacencies': [self.id],
			} for friend in friends]
		result.insert(0, {
			'id': user.id,
			'name': user.name,
			'data': {},
			'adjacencies': [],
			})
		print "Created result"
		return result

	def get_friend_ids(self):
		print "Creating list of friend IDs (all node IDs)"
		user = Person.objects.select_related().get(id=self.id)
		return [f.id for f in user.friends.all()]

	def get_friend_names(self):
		user = Person.objects.select_related().get(id=self.id)
		return {f.id:f.name for f in user.friends.all()}

	def get_friends_links(self):
		if (self.links != None):
			return self.links
		else:
			user = Person.objects.get(id=self.id)
			friends = user.friends.all()
			#Try this out
			seen = set()
			seen_link = lambda l: (tuple(l) in seen) or ((l[1], l[0]) in seen)
			set_seen = lambda l: seen.add(tuple(l))

			links = []

			friend_connections = Connection.objects.filter(from_person__in=friends, to_person__in=friends)

			for l in friend_connections:
				if not seen_link([l.from_person_id, l.to_person_id]):
					links.append([l.from_person_id, l.to_person_id])
					set_seen([l.from_person_id, l.to_person_id])
			self.links = links
			return links

