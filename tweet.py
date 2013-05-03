import dateutil.parser
import itertools
import re

mention_pattern = "(@\w+)"
hashtag_pattern = "(#\w+)"
url_pattern = "([0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\\\.)[-A-Za-z0-9\\\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\\\$\\\\.\\\\+\\\\!\\\\*\\\\(\\\\),;:@&=\\\\?/~\\\\#\\\\%]*[^]'\\\\.}>\\\\),\\\\\"]"
unicode_backslash_pattern = "(\\\\u[\da-fA-F]{4})"

r_terms = re.compile('|'.join(itertools.chain([mention_pattern, hashtag_pattern, url_pattern])))
r_words = re.compile("(\w\w*'?\w?\w?)")

unicode_mappings = {
	'\u263a': ':-)',
	'\u2764': '<3',
	'\u2018': '\'',
	'\u2019': '\'',
	'\u201c': '\"',
	'\u201d': '\"',
	'\u2026': '...',
	'\u2014': '--',
	'&amp;': '&'
}

def unicode_replace(str):
	if not str:
		return str

	for k in unicode_mappings.keys():
		str = str.replace(k, unicode_mappings[k])

	return str

unicode_found = False

class Tweet(object):
	def __init__(self, username, name, status):
		global unicode_found
		self.created_on = dateutil.parser.parse(status.GetCreatedAt())
		self.text = unicode_replace(status.GetText().encode('ascii', 'backslashreplace'))

		unicode_matches = re.findall(unicode_backslash_pattern, self.text)
		if unicode_matches:
			unicode_found = True
		for u in unicode_matches:
			print "Unicode character found: {0}".format(u)
		self.mentions = re.findall(mention_pattern, self.text)
		self.hashtags = re.findall(hashtag_pattern, self.text)
		filtered_text = re.sub(r_terms, '', self.text)

		self.words = r_words.findall(filtered_text)
		self.retweet_count = status.GetRetweetCount()
		self.username = username
		self.name = name

	@staticmethod
	def reset():
		global unicode_found
		unicode_found = False

	def dump(self):
		if unicode_found:
			return
		print "\tCreated On: {0}".format(self.created_on.strftime('%m/%d/%Y'))
		print "\tName: {0} ({1})".format(self.name, self.username)
		print "\tText: {0}".format(self.text)
		print "\tWords: {0}".format(self.words)
		print "\tMentions: {0}".format(self.mentions)
		print "\tHashtags: {0}".format(self.hashtags)
		print "\tRetweet Count: {0}".format(self.retweet_count)