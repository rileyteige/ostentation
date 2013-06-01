#!/usr/bin/env python
import dateutil.parser
import exception
import json
import os
import signal
import sys
import twitter

from exception import *
from tweet import Tweet, TweetEncoder, WordMap

def ctrlc_handler(signum, frame):
	print
	print "Control-C was pressed."
	exit()

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
		k = v = None

		try:
			k, v = pair[0], pair[1]
		except IndexError:
			raise FileFormatException(filename)

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
	try:
		consumer_key, consumer_secret = get_secrets(consumer_file)
		oauth_key, oauth_secret = get_secrets(oauth_token_file)
	except FileFormatException as e:
		print "Could not load data from file {}".format(e.filename)
		e.log(should_quit=True)

	return twitter.Api(consumer_key=consumer_key,\
						consumer_secret=consumer_secret,\
						access_token_key=oauth_key,\
						access_token_secret=oauth_secret\
					)

def load_users(user_file, n, offset=0):
	lines = []
	try:
		lines = read_lines_from_file(user_file)
	except:
		print "Could not read user data from {}".format(user_file)

	if not lines:
		return None

	return [x.rstrip() for x in lines[offset:n+offset]]

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
		print "\nA Twitter exception occurred:\n{}".format(e)
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
		sys.stdout.write("Downloading twitter data " +\
							"for {} users at {} tweets/user..."\
							.format(NUM_USERS, TOP_TWEETS_PER_USER))
		users = load_users(username_file, NUM_USERS)

		for username in users:
			user_tweets = pull_top_tweets_for_user(\
							api,\
							username,\
							NUM_TWEETS_PER_USER,\
							TOP_TWEETS_PER_USER\
						)

			if user_tweets:
				sys.stdout.write('.')
				tweets.extend(user_tweets)
			else:
				print "\nFailed to obtain user data for username: {}"\
						.format(username)

		print "Saving tweet data in {}...".format(load_file)

		write_tweets(load_file, tweets)
	else:
		sys.stdout.write("Loading saved twitter data...")
		with open(load_file, 'r') as f:
			json_data = f.read()
			data = json.loads(json_data, encoding='latin1')

			i = 0
			for d in data:
				i += 1
				if i % 2000 == 0:
					sys.stdout.write('.')
					i = 0

				try:
					tweet = Tweet.from_dict(d)
					tweets.append(tweet)
				except TwitterException as e:
					e.log()

			print "\nDone.\n"

	return tweets

def load_word_map(data_file):
	if not os.path.exists(data_file):
		return None

	return WordMap.from_lines(read_lines_from_file(data_file))

def rank_users(tweets):
	if not tweets:
		return None

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

	return sorted(user_scores, key=user_scores.get, reverse=True)

def post_rankings(rankings):
	if not rankings:
		print "No rankings to post."
		return

	n = len(rankings)

	BOUNDARY_SIZE = 5
	i = 0
	if n < BOUNDARY_SIZE * 2:
		print "\nIn order from most narcissistic to least:\n"
		for name in rankings:
			i += 1
			print "{}: {}".format(i, name)
	else:
		print "{} most narcissistic users:\n".format(BOUNDARY_SIZE)
		for name in rankings[:BOUNDARY_SIZE]:
			i += 1
			print "{}: {}".format(i, name)

		print "\n{} least narcissistic users:\n".format(BOUNDARY_SIZE)
		i = 0
		for name in reversed(rankings[-BOUNDARY_SIZE:]):
			i += 1
			print "{}: {}".format(i, name)


def main():
	signal.signal(signal.SIGINT, ctrlc_handler)

	consumer_file = 'secrets/consumerkeys.txt'
	oauth_token_file = 'secrets/oauthconfig.txt'
	user_file = 'assets/top1000.data'
	tweet_save_file = 'assets/tweets.json'

	try:
		api = load_twitter(consumer_file, oauth_token_file)
		tweets = load_tweets(api, user_file, tweet_save_file)
	except TwitterException as e:
		print "Could not load tweets."
		e.log(should_quit=True)

	print "Loaded {} tweets.".format(len(tweets))
	print "Analyzing twitter data...\n"

	try:
		ranked_users = rank_users(tweets)
		post_rankings(ranked_users)
	except TwitterException as e:
		print "Could not rank users."
		e.log(should_quit=True)

if __name__ == "__main__":
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
	sys.stderr = open(exception.error_filename, 'w', 0)

	try:
		main()
	except Exception as e:
		print "An unhandled exception occured."
		log_exception(e, handled=False, should_quit=True)

	errors = num_exceptions_encountered()
	if errors > 0:
		print "\n\n\n{} exceptions were handled during execution."\
				.format(errors)
	else:
		sys.stderr.close()
		os.remove(exception.error_filename)
