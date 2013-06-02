import sys
import traceback

error_filename = 'errors.log'
num_exceptions = 0

def num_exceptions_encountered():
	return num_exceptions

def log_exception(e, handled=True, should_quit=False):
	global num_exceptions

	title = ("UNHANDLED " if not handled else "") + "EXCEPTION"
	sys.stderr.write('\n\n ***** {} ***** \n\n'.format(title))
	sys.stderr.write('CALL STACK:\n\n')
	if isinstance(e, TwitterException):
		for frame in traceback.format_list(e.trace):
			sys.stderr.write(frame)
	else:
		TRACE_IDX = 2
		for frame in traceback.format_tb(sys.exc_info()[TRACE_IDX]):
			sys.stderr.write(frame)

	sys.stderr.write("\nException of class {} occurred.\nMessage: {}\n"\
						.format(e.__class__.__name__, e))

	num_exceptions += 1

	if should_quit:
		print "\nA fatal error has caused the termination of execution."
		print "{} exceptions logged to {}"\
				.format(num_exceptions, error_filename)
		exit(1)

class TwitterException(Exception):
	def __init__(self, msg=''):
		last_frame = -2
		max_frames = 10
		self.trace = traceback.extract_stack()\
						[last_frame - max_frames:last_frame]
		self.message = msg

	def __str__(self):
		return str(self.build_message())

	def build_message(self):
		return self.message

	def log(self, handled=True, should_quit=False):
		log_exception(self, handled, should_quit)

class FileException(TwitterException):
	def __init__(self, filename):
		super(FileException, self).__init__(filename)
		self.filename = filename

class FileFormatException(FileException):
	def build_message(self):
		return "Bad file format in file '{}'".format(self.filename)

class FileNotFoundException(FileException):
	def build_message(self):
		return "Find not found: {}".format(self.filename)

class UserException(TwitterException):
	def __init__(self, message):
		super(UserException, self).__init__(message)

	def build_message(self):
		return "Failed to obtain user data for username: {}"\
					.format(self.message)

class ApiException(TwitterException):
	def __init__(self, message):
		super(ApiException, self).__init__(message)

	def build_message(self):
		return "Could not complete Twitter API request: {}"\
					.format(self.message)

class TextConversionException(TwitterException):
	def __init__(self, string, format):
		super(TextConversionException, self).__init__()
		self.string = string
		self.failed_format = format

	def build_message(self):
		return "Could not convert the following string to {} format:\n{}"\
				.format(self.failed_format, self.string)

class TweetException(TwitterException):
	def __init__(self, message):
		super(TweetException, self).__init__(message)

	def build_message(self):
		return "Could not build tweet: {}".format(self.message)