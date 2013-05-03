from bs4 import BeautifulSoup
import httplib
import re

def write_list_to_file(filename, l):
	if not l:
		print "Asked to write empty list to '{0}'... returning.".format(filename)
		return

	with open(filename, 'w') as f:
		for entry in l:
			f.write(str(entry) + '\n')

def extract_usernames(html):
	user_pattern = "(\(\w+\))"
	username_td_class = "statcol_name"

	usernames = []
	soup = BeautifulSoup(html)

	for td in soup.find_all("td"):
		if td['class'] and td['class'][0] == username_td_class:
			try:
				user_text = re.findall(user_pattern, td.a.get_text().encode('utf8', 'strict'))[0]
				username = user_text.replace('(', '').replace(')', '')
				usernames.append(username)
			except Exception as e:
				print "An exception occurred: {0}".format(e)
				pass

	return usernames

def get_html(domain, method):
	conn = httplib.HTTPConnection(domain, timeout=10)
	conn.request("GET", method)

	try:
		r = conn.getresponse()
	except Exception as e:
		raise Exception("Could not receive data from {0}: {1}".format(domain + method, e))

	if r.status != 200:
		print "Failed to get data: HTTP Output = {0} {1}".format(r.status, r.reason)
		exit(1)

	return r.read()

def main():
	users = []

	domain = 'twitaholic.com'
	method_template = '/top{0}00/followers'
	for i in range(1, 11):
		method = method_template.format(i)

		print "Scraping usernames from {0}...".format(domain + method)
		users.extend(extract_usernames(get_html(domain, method)))

	filename = 'top1000'

	print "Exporting usernames to {0}...".format(filename)
	write_list_to_file(filename, users)

if __name__ == "__main__":
	main()