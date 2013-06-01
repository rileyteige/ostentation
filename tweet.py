import datetime
import dateutil.parser
import itertools
import re
import simplejson as json
import time

from exception import *

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

def encode(string, to, error_behavior):
	try:
		return string.encode(to, error_behavior)
	except:
		raise TextConversionException(string, to)

class StandardizingException(TwitterException): pass

def standardize(expr):
	convert_to = 'ascii'
	error_behavior = 'ignore'

	try:
		if isinstance(expr, basestring):
			return encode(expr, convert_to, error_behavior)
		elif isinstance(expr, list):
			return [encode(x, convert_to, error_behavior) for x in expr]
	except TextConversionException as e:
		e.log()
		raise StandardizingException()

def extract_words(line):
	return r_words.findall(re.sub(r_terms, '', line))

class TweetEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return int(time.mktime(obj.timetuple()))
		elif not isinstance(obj, Tweet):
			return super(TweetEncoder, self).default(obj)

		return obj.__dict__

class Tweet(object):
	def __init__(self, username=None, status=None):
		if not (username and status):
			return

		self.created_on = dateutil.parser.parse(status.GetCreatedAt())
		try:
			self.text = standardize(status.GetText())
		except StandardizingException:
			raise TweetException('Failed to standardize string format')
		self.mentions = re.findall(mention_pattern, self.text)
		self.hashtags = re.findall(hashtag_pattern, self.text)
		self.words = extract_words(self.text)
		self.retweet_count = status.GetRetweetCount()
		self.username = username

	@staticmethod
	def from_dict(d):
		if not isinstance(d, dict):
			raise TweetException('Bad dictionary')

		t = Tweet()

		try:
			t.username = standardize(d['username'])
			t.text = standardize(d['text'])
			t.hashtags = standardize(d['hashtags'])
			t.created_on = datetime.datetime.fromtimestamp(d['created_on'])
			t.words = standardize(d['words'])
			t.mentions = standardize(d['mentions'])
			t.retweet_count = d['retweet_count']
		except StandardizingException:
			raise TweetException('Failed to standardize string format')

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

	@staticmethod
	def from_lines(lines):
		wordmap = WordMap(None)

		word_lines = map(lambda x: extract_words(x), lines)
		for l in word_lines:
			wordmap.add_many_words(l)

		return wordmap

	def _build_map(self, words):
		map = {}

		if not words:
			return map

		for w in map(lambda x: x.lower(), words):
			if w not in map:
				map[w] = 1
			else:
				map[w] += 1

	def add_word(self, word, n=1):
		lword = word.lower()
		if lword not in self.map:
			self.map[lword] = n
		else:
			self.map[lword] += n

	def add_many_words(self, words):
		for word in words:
			self.add_word(word)

	def join(self, wordmap):
		for w in wordmap.map.keys():
			self.add_word(w, wordmap.map[w])

	def score(self, words):
		"""Score a list of words against the word map.
		Each word that occurs in the word map increases the score
		by the amount of times that word occurred within the word map
		itself, giving a score of similarity to the word map's
		provided data sets."""

		return sum([self.map[w.lower()] for w in words if w in self.map])

