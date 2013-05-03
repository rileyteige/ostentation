import twitter
import dateutil.parser
import signal

from tweet import Tweet

EXIT_COMMANDS = ('exit', 'quit', 'bye', 'goodbye', 'end', 'leave', 'kill', 'q')
KEY = 'key'
SECRET = 'secret'

consumer_file = 'consumerkeys.txt'
oauth_token_file = 'oauthconfig.txt'

consumer_key = ""
consumer_secret = ""
oauth_token = ""
oauth_secret = ""

def ctrlc_handler(signum, frame):
	print
	exit(0)

signal.signal(signal.SIGINT, ctrlc_handler)

with open(consumer_file) as f:
	lines = f.readlines()
	for l in lines:
		try:
			pair = l.split('=')
			key, value = pair[0], pair[1]
			if key == KEY:
				consumer_key = value
			elif key == SECRET:
				consumer_secret = value
			else:
				raise Exception()
		except:
			print "Bad file format in file {0}.".format(consumer_file)
			exit(1)

with open(oauth_token_file) as f:
	lines = f.readlines()
	for l in lines:
		try:
			pair = l.split('=')
			key, value = pair[0], pair[1]
			if key == KEY:
				oauth_token = value
			elif key == SECRET:
				oauth_secret = value
			else:
				raise Exception()
		except:
			print "Bad file format in file {0}.".format(oauth_token_file)
			exit(1)

if consumer_key == "" or consumer_secret == "":
	raise Exception("Missing consumer OAuth values.")

if oauth_token == "" or oauth_secret == "":
	raise Exception("Missing OAuth token values.")

api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=oauth_token, access_token_secret=oauth_secret)

username = ""

while True:

	username = raw_input('Enter a username: ')

	Tweet.reset()

	if username.lower() in EXIT_COMMANDS:
		break

	print ""

	print "Getting user info for username '{0}'...\n".format(username)

	try:
		u = api.GetUser(username)
	except:
		print "An exception occurred getting user info."
		continue

	print "Got info for username '{0}'.\n".format(username)

	name = u.GetName().encode('utf8', 'ignore')

	print "Name: {0}".format(name)
	print "Location: {0}".format(u.GetLocation().encode('utf8', 'ignore'))
	print "Description: {0}".format(u.GetDescription().encode('utf8', 'ignore'))
	print "# Followers: {0}".format(u.GetFollowersCount())
	print "URL: {0}\n".format(u.GetUrl().encode('utf8', 'ignore'))

	num_statuses_checked = 1000
	num_statuses_shown = 10

	assert(num_statuses_shown <= num_statuses_checked)

	print "{0} most retweeted of the last {1} statuses for {2}".format(num_statuses_shown, num_statuses_checked, name)

	try:
		statuses = api.GetUserTimeline(username, count=num_statuses_checked + 1)
	except:
		print "An exception occurred getting status info."
		continue

	for s in sorted([Tweet(username, name, x) for x in statuses], key=lambda s: s.retweet_count, reverse=True)[:num_statuses_shown]:
		print ""
		s.dump()
		print ""