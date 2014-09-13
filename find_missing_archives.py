#!/usr/bin/python

from chatview import logparser
from twisted.python.filepath import FilePath
from datetime import datetime
import json
import cgi
import sys

# bip-format IRC logs
LOGS = FilePath(r"C:\Users\root\Documents\Logs\logs")

# Directory containing (directories containing) .json files downloaded from every go pack
JSON_FILES = FilePath(r"C:\Users\root\Documents\ExpClj\archivebot_json")

SKIP_JSON_FILES = set([
	 "hutchpost.org-inf-20131219-232245.json"
	,"twitter.com-shallow-20131219-233747.json"
])

JOBS_NOT_MENTIONED_IN_JSON = {
	 (u"http://electrickery.xs4all.nl/", "inf"): {}
	,(u"http://mpcdot.com/forums/", "inf"): {}
	,(u"http://prod2-csa.integra.fr/", "inf"): {}
	,(u"http://semiaccurate.com/", "inf"): {}
	,(u"http://sprg.ssl.berkeley.edu", "inf"): {}
	,(u"http://tcrf.net/", "inf"): {}
	,(u"http://www.bierdopje.com/", "inf"): {}
	,(u"http://www.neil-kb.com/", "inf"): {}
}

def yieldJsonData():
	for j in JSON_FILES.walk():
		if not (j.isfile() and j.path.endswith(".json")):
			continue
		if j.basename() in SKIP_JSON_FILES:
			continue
		try:
			data = json.loads(j.getContent())
		except ValueError:
			print j
			print repr(j.getContent())
			raise
		yield data

def getArchiveMap():
	m = JOBS_NOT_MENTIONED_IN_JSON.copy()
	for data in yieldJsonData():
		url = data["url"]
		fetch_depth = data["fetch_depth"]
		assert fetch_depth in ("inf", "shallow"), fetch_depth
		m[(url, fetch_depth)] = data
	return m

command_to_depth = {"!a": "inf", "!archive": "inf", "!ao": "shallow", "!archiveonly": "shallow"}

def isValidArchiveBotUrl(u):
	return u.startswith("http://") or u.startswith("https://")

def includeUrl(u):
	# arkiver's nonsense
	if u.startswith(u"http://bofh.nikhef.nl/events/"):
		return False
	return True

def getRequestedUrls(pipelineOnly):
	startDate = datetime(2013, 1, 1)
	for line in logparser.bipLogReader(LOGS, "efnet", "#archivebot", startDate):
		##print line.rstrip()
		data = logparser.lineToStructure(line)
		if data is None:
			continue
		nick = data.nick
		message = data.message
		timestamp = data.timestamp
		if pipelineOnly and '--pipeline' not in message:
			continue
		try:
			command, url = message.split(None, 1)
			if " " in url:
				url, _ = url.split(" ", 1)
		except ValueError:
			continue
		# We don't expect invalid URLs to result in something in the go packs
		if not (isValidArchiveBotUrl(url) and includeUrl(url)):
			continue
		depth = command_to_depth.get(command)
		if depth is None:
			# No command, skip line
			continue
		yield timestamp, nick, depth, url

def tableRow(row):
	b = []
	b.append("<tr>")
	for cell in row:
		b.append("<td>")
		# hax
		if cell.startswith("http://") or cell.startswith("https://") or cell.startswith("ftp://"):
			b.append('<a href="%s">%s</a>' % (cgi.escape(cell), cgi.escape(cell)))
		else:
			b.append(cgi.escape(cell))
		b.append("</td>")
	b.append("</tr>")
	return "".join(b)

depth_to_shortcut = {"inf": "!a", "shallow": "!ao"}

def hasPathComponent(url):
	assert url.startswith("http://") or url.startswith("https://"), url
	return url.count('/') > 2

def withPathComponent(url):
	if not hasPathComponent(url):
		return url + '/'
	return url

def reportMissing(pipelineOnly):
	archives = getArchiveMap()
	print "<!doctype html>"
	print "<head>"
	print '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
	print '<meta name="referrer" content="never">'
	print "</head>"
	print "<body>"
	print "<style>body, td { white-space: nowrap; font-size: 13px; font-family: Tahoma }</style>"
	print "<table>"
	for timestamp, nick, depth, url in getRequestedUrls(pipelineOnly):
		if not ((url, depth) in archives or (withPathComponent(url), depth) in archives):
			print tableRow((timestamp.isoformat(), "<" + nick + ">", depth_to_shortcut[depth], url.encode("utf-8")))
	print "</table>"
	print "</body>"
	print "</html>"

def main():
	pipelineOnly = '--pipeline-only' in sys.argv
	reportMissing(pipelineOnly)

if __name__ == '__main__':
	main()
