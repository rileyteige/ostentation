import datetime
import dateutil.parser
import itertools
import re
import simplejson as json
import time

mention_pattern = r'(@\w+)'
hashtag_pattern = r'(#\w+)'
word_pattern = r'(\w\w*\'?\w?\w?)'
url_pattern = r'([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]\'\\.}>\\),\\"]'

def rgx(expr):
	if isinstance(expr, basestring):
		return re.compile(expr)
	elif isinstance(expr, list):
		return re.compile('|'.join(itertools.chain(expr)))

r_terms = rgx([mention_pattern, hashtag_pattern, url_pattern])
r_words = rgx(word_pattern)

def latin(expr):
	if isinstance(expr, basestring):
		return expr.encode('latin1', 'ignore')
	elif isinstance(expr, list):
		return [x.encode('latin1', 'ignore') for x in expr]

class TweetEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return int(time.mktime(obj.timetuple()))
		elif not isinstance(obj, Tweet):
			return super(TweetEncoder, self).default(obj)

		return obj.__dict__

class Tweet(object):
	def __init__(self, username, status):
		if not (username and status):
			return

		self.created_on = dateutil.parser.parse(status.GetCreatedAt())
		self.text = status.GetText().encode('latin1', 'ignore')

		self.mentions = re.findall(mention_pattern, self.text)
		self.hashtags = re.findall(hashtag_pattern, self.text)
		filtered_text = re.sub(r_terms, '', self.text)

		self.words = r_words.findall(filtered_text)
		self.retweet_count = status.GetRetweetCount()
		self.username = username

	@staticmethod
	def from_dict(d):
		username = latin(d['username'])
		text = latin(d['text'])
		hashtags = latin(d['hashtags'])
		created_on = datetime.datetime.fromtimestamp(d['created_on'])
		words = latin(d['words'])
		mentions = latin(d['mentions'])
		retweet_count = d['retweet_count']

		t = Tweet(None, None)
		t.username = username
		t.text = text
		t.hashtags = hashtags
		t.created_on = created_on
		t.words = words
		t.mentions = mentions
		t.retweet_count = retweet_count

		return t

	def dump(self):
		print "\tCreated On: {0}".format(self.created_on.strftime('%m/%d/%Y'))
		print "\tUsername: {0}".format(self.username)
		print "\tText: {0}".format(self.text)
		print "\tWords: {0}".format(self.words)
		print "\tMentions: {0}".format(self.mentions)
		print "\tHashtags: {0}".format(self.hashtags)
		print "\tRetweet Count: {0}".format(self.retweet_count)

class WordMap(object):
	# Keeps a count of words in a given word list.

	def __init__(self, words):
		self.map = self._build_map(words)

	def _build_map(self, words):
		map = {}

		if not words:
			return map

		for w in words:
			if w not in map:
				map[w] = 1
			else:
				map[w] += 1

	def add_word(self, word, n=1):
		if word not in self.map:
			self.map[word] = n
		else:
			self.map[word] += n

	def join(self, wordmap):
		for w in wordmap.map.keys():
			self.add_word(w, wordmap.map[w])

	def score(self, words):
		"""Score a list of words against the word map.
		Each word that occurs in the word map increases the score
		by the amount of times that word occurred within the word map
		itself, giving a score of similarity to the word map's
		provided data sets."""

		return sum([self.map[w] for w in words if w in self.map])

