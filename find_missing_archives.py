from chatview import logparser
from twisted.python.filepath import FilePath
from datetime import datetime
import json

# bip-format IRC logs
LOGS = FilePath(r"C:\Users\root\Documents\Logs\logs")

# Directory containing (directories containing) .json files downloaded from every go pack
JSON_FILES = FilePath(r"C:\Users\root\Documents\ExpClj\archivebot_json")

SKIP_JSON_FILES = set([
	 "hutchpost.org-inf-20131219-232245.json"
	,"twitter.com-shallow-20131219-233747.json"
])

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
	m = {}
	for data in yieldJsonData():
		url = data["url"]
		fetch_depth = data["fetch_depth"]
		assert fetch_depth in ("inf", "shallow"), fetch_depth
		m[(url, fetch_depth)] = data
	return m

command_to_depth = {"!a": "inf", "!archive": "inf", "!ao": "shallow", "!archiveonly": "shallow"}

def main():
	startDate = datetime(2013, 1, 1)
	archives = getArchiveMap()
	for line in logparser.bipLogReader(LOGS, "efnet", "#archivebot", startDate):
		print line.rstrip()
		data = logparser.lineToStructure(line)
		if data is None:
			continue
		nick = data.nick
		message = data.message
		timestamp = data.timestamp
		try:
			command, url, _ = message.split(None, 2)
		except ValueError:
			continue
		depth = command_to_depth.get(command)
		if depth is None:
			# No command, skip line
			continue
		print timestamp, nick, depth, url

if __name__ == '__main__':
	main()
