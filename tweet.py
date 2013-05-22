import datetime
import dateutil.parser
import itertools
import re
import simplejson as json
import time

mention_pattern = "(@\w+)"
hashtag_pattern = "(#\w+)"
url_pattern = "([0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\\\.)[-A-Za-z0-9\\\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\\\$\\\\.\\\\+\\\\!\\\\*\\\\(\\\\),;:@&=\\\\?/~\\\\#\\\\%]*[^]'\\\\.}>\\\\),\\\\\"]"

r_terms = re.compile('|'.join(itertools.chain([mention_pattern, hashtag_pattern, url_pattern])))
r_words = re.compile("(\w\w*'?\w?\w?)")

class TweetEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return int(time.mktime(obj.timetuple()))
		elif not isinstance(obj, Tweet):
			return super(TweetEncoder, self).default(obj)

		return obj.__dict__

class Tweet(object):
	def __init__(self, username, status):
		self.created_on = dateutil.parser.parse(status.GetCreatedAt())
		self.text = status.GetText().encode('latin1', 'ignore')

		self.mentions = re.findall(mention_pattern, self.text)
		self.hashtags = re.findall(hashtag_pattern, self.text)
		filtered_text = re.sub(r_terms, '', self.text)

		self.words = r_words.findall(filtered_text)
		self.retweet_count = status.GetRetweetCount()
		self.username = username

	def dump(self):
		print "\tCreated On: {0}".format(self.created_on.strftime('%m/%d/%Y'))
		print "\Username: {0} ({1})".format(self.username)
		print "\tText: {0}".format(self.text)
		print "\tWords: {0}".format(self.words)
		print "\tMentions: {0}".format(self.mentions)
		print "\tHashtags: {0}".format(self.hashtags)
		print "\tRetweet Count: {0}".format(self.retweet_count)
