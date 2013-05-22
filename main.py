#!/usr/bin/env python
import twitter
import dateutil.parser
import signal

from tweet import Tweet

class FileFormatException(Exception):
	def __str__(self):
		return "Bad file format in file '{}'".format(self.message)

class UserException(Exception):
	def __str__(self):
		return "Failed to obtain user data for username: {}".format(self.message)

def ctrlc_handler(signum, frame):
	print
	exit(0)

def read_lines_from_file(filename):
	with open(filename) as f:
		return f.readlines()

def get_secrets(filename):
	KEY = 'key'
	SECRET = 'secret'

	key = None
	secret = None

	lines = read_lines_from_file(filename)
	for l in lines:
		pair = l.split('=')
		k, v = pair[0], pair[1]
		if k == KEY:
			key = v
		elif k == SECRET:
			secret = v
		else:
			raise FileFormatException(filename)

	if not (key and secret):
		raise FileFormatException(filename)

	return key, secret

def load_twitter(consumer_file, oauth_token_file):
	consumer_key, consumer_secret = get_secrets(consumer_file)
	oauth_key, oauth_secret = get_secrets(oauth_token_file)

	assert(consumer_key and consumer_secret)
	assert(oauth_key and oauth_secret)

	return twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=oauth_key, access_token_secret=oauth_secret)

def load_users(user_file, n):
	lines = []
	try:
		lines = read_lines_from_file(user_file)
	except:
		print "Could not read user data from {}".format(user_file)

	if not lines:
		return None

	return [x.rstrip() for x in lines[:n]]

def pull_top_tweets_for_user(api, username, n, top_count):
	assert(api)
	assert(username)
	assert(top_count <= n)

	try:
		u = api.GetUser(username)
	except:
		print "An exception occurred getting user info for username: {}".format(username)
		return None

	name = u.GetName().encode('utf8', 'ignore')

	try:
		statuses = api.GetUserTimeline(username, count=n+1)
	except:
		print "An exception occurred getting status info."
		return None

	tweets = None
	try:
		tweets = sorted([Tweet(username, name, x) for x in statuses], key=lambda s: s.retweet_count, reverse=True)[:top_count]
	except Exception as e:
		print str(e)
		return None

	return tweets

def main():
	signal.signal(signal.SIGINT, ctrlc_handler)

	consumer_file = 'secrets/consumerkeys.txt'
	oauth_token_file = 'secrets/oauthconfig.txt'
	user_file = 'assets/top1000.data'

	api = load_twitter(consumer_file, oauth_token_file)

	num_users = 3
	users = load_users(user_file, num_users)

	for username in users:
		num_tweets = 10
		top_count = 3
		user_tweets = pull_top_tweets_for_user(api, username, num_tweets, top_count)

		if user_tweets:
			print "Successfully obtained user data for username: {}".format(username)
		else:
			raise UserException(username)

if __name__ == "__main__":
	main()