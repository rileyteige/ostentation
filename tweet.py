import dateutil.parser
import itertools
import re

mention_pattern = "(@\w+)"
hashtag_pattern = "(#\w+)"
url_pattern = "([0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\\\.)[-A-Za-z0-9\\\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\\\$\\\\.\\\\+\\\\!\\\\*\\\\(\\\\),;:@&=\\\\?/~\\\\#\\\\%]*[^]'\\\\.}>\\\\),\\\\\"]"
unicode_backslash_pattern = "(\\\\u[\da-fA-F]{4})"

r_terms = re.compile('|'.join(itertools.chain([mention_pattern, hashtag_pattern, url_pattern])))
r_words = re.compile("(\w\w*'?\w?\w?)")

class UnicodeException(Exception):
	def __init__(self, uchars):
		super(UnicodeException, self).__init__()
		self.uchars = uchars

	def __str__(self):
		return "Unicode characters found: {}".format(self.uchars)

unicode_mappings = {
	'\u2014': '--',
	'\u2018': '\'',
	'\u2019': '\'',
	'\u201c': '\"',
	'\u201d': '\"',
	'\u2026': '...',
	'\u261d': '^^^',
	'\u263a': ':-)',
	'\u2764': '<3',
	'&amp;': '&'
}

def unicode_replace(str):
	if not str:
		return str

	for k in unicode_mappings.keys():
		str = str.replace(k, unicode_mappings[k])

	return str

class Tweet(object):
	def __init__(self, username, name, status):
		self.created_on = dateutil.parser.parse(status.GetCreatedAt())
		self.text = unicode_replace(status.GetText().encode('ascii', 'backslashreplace'))

		unicode_matches = re.findall(unicode_backslash_pattern, self.text)
		if unicode_matches:
			raise UnicodeException(unicode_matches)

		self.mentions = re.findall(mention_pattern, self.text)
		self.hashtags = re.findall(hashtag_pattern, self.text)
		filtered_text = re.sub(r_terms, '', self.text)

		self.words = r_words.findall(filtered_text)
		self.retweet_count = status.GetRetweetCount()
		self.username = username
		self.name = name

	def dump(self):
		print "\tCreated On: {0}".format(self.created_on.strftime('%m/%d/%Y'))
		print "\tName: {0} ({1})".format(self.name, self.username)
		print "\tText: {0}".format(self.text)
		print "\tWords: {0}".format(self.words)
		print "\tMentions: {0}".format(self.mentions)
		print "\tHashtags: {0}".format(self.hashtags)
		print "\tRetweet Count: {0}".format(self.retweet_count)