#!/usr/bin/env python
import dateutil.parser
import json
import os
import signal
import twitter

from tweet import Tweet, TweetEncoder, WordMap

class FileFormatException(Exception):
	def __str__(self):
		return "Bad file format in file '{}'".format(self.message)

class UserException(Exception):
	def __str__(self):
		return "Failed to obtain user data for username: {}"\
					.format(self.message)

def ctrlc_handler(signum, frame):
	print
	print "Control-C was pressed."
	exit()
	for username in users:
		user_tweets = pull_top_tweets_for_user(\
						api,\
						username,\
						NUM_TWEETS_PER_USER,\
						TOP_TWEETS_PER_USER\
					)

		if user_tweets:
			print "Successfully obtained user data for username: {}"\
					.format(username)
			tweets.extend(user_tweets)
		else:
			print "Failed to obtain user data for username: {}"\
					.format(username)

	print "Writing tweet data to {}...".format(output_file)

	write_tweets(output_file, tweets)
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

	return twitter.Api(consumer_key=consumer_key,\
						consumer_secret=consumer_secret,\
						access_token_key=oauth_key,\
						access_token_secret=oauth_secret\
					)

def load_users(user_file, n):
	lines = []
	try:
		lines = read_lines_from_file(user_file)
	except:
		print "Could not read user data from {}".format(user_file)

	if not lines:
		return None

	return [x.rstrip() for x in lines[:n]]

def write_tweets(output_file, tweets):
	data = json.dumps(tweets, cls=TweetEncoder)
	with open(output_file, 'w') as f:
		f.write(data)

def pull_top_tweets_for_user(api, username, n, top_count):
	assert(api)
	assert(username)
	assert(top_count <= n)

	try:
		statuses = api.GetUserTimeline(username, count=n+1)
	except twitter.TwitterError as e:
		print "Twitter exception occurred: {}".format(e)
		exit(1)
	except:
		print "An exception occurred getting status info."
		return None

	if not statuses:
		return None

	tweets = sorted([Tweet(username, x) for x in statuses],\
					key=lambda s: s.retweet_count,\
					reverse=True)[:top_count]

	return tweets

def load_tweets(api, username_file, load_file):
	NUM_USERS = 150
	NUM_TWEETS_PER_USER = 1000
	TOP_TWEETS_PER_USER = 250

	tweets = []

	if not os.path.exists(load_file):
		print "No tweet cache found. Downloading twitter data."
		users = load_users(username_file, NUM_USERS)

		for username in users:
			user_tweets = pull_top_tweets_for_user(\
							api,\
							username,\
							NUM_TWEETS_PER_USER,\
							TOP_TWEETS_PER_USER\
						)

			if user_tweets:
				print "Successfully obtained user data for username: {}"\
						.format(username)
				tweets.extend(user_tweets)
			else:
				print "Failed to obtain user data for username: {}"\
						.format(username)

		print "Writing tweet data to {}...".format(load_file)

		write_tweets(load_file, tweets)
	else:
		print "Loading cached twitter data."
		with open(load_file, 'r') as f:
			json_data = f.read()
			data = json.loads(json_data, encoding='latin1')
			for d in data:
				tweet = Tweet.from_dict(d)
				tweets.append(tweet)

	return tweets

def load_word_map(data_file):
	if not os.path.exists(data_file):
		return None

	return WordMap.from_lines(read_lines_from_file(data_file))

def score_tweets(tweets):
	narcisistic_file = 'assets/narcissistic.txt'
	selfless_file = 'assets/selfless.txt'

	narcisistic = load_word_map(narcisistic_file)
	selfless = load_word_map(selfless_file)

	user_scores = {}

	for t in tweets:
		name = t.username
		if name not in user_scores:
			user_scores[name] = 0

		words = t.words
		user_scores[name] += narcisistic.score(words) - selfless.score(words)

	return user_scores

def main():

	signal.signal(signal.SIGINT, ctrlc_handler)

	consumer_file = 'secrets/consumerkeys.txt'
	oauth_token_file = 'secrets/oauthconfig.txt'
	user_file = 'assets/top1000.data'
	output_file = 'assets/tweets.json'

	api = load_twitter(consumer_file, oauth_token_file)
	tweets = load_tweets(api, user_file, output_file)

	if tweets:
		scores = score_tweets(tweets)
		ranked_users = sorted(scores, key=scores.get, reverse=True)
		n = len(ranked_users)
		BOUNDARY_SIZE = 10
		i = 0
		if n < BOUNDARY_SIZE * 2:
			print "\nIn order from most narcissistic to least:\n"
			for name in ranked_users:
				i += 1
				print "{}: {}".format(i, name)
		else:
			print "{} most narcissistic users:\n".format(BOUNDARY_SIZE)
			for name in ranked_users[:BOUNDARY_SIZE]:
				i += 1
				print "{}: {}".format(i, name)

			print "\n{} least narcissistic users:\n".format(BOUNDARY_SIZE)
			i = 0
			for name in reversed(ranked_users[-BOUNDARY_SIZE:]):
				i += 1
				print "{}: {}".format(i, name)


	else:
		print "An error occurred loading the tweets."

if __name__ == "__main__":
	main()