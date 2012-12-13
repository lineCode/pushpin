# Copyright (C) 2012 Fan Out Networks, Inc.
#
# This file is part of Pushpin.
#
# Pushpin is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Pushpin is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
# more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import json
import BaseHTTPServer

g_server = None

def get_channel(path):
	if path[-1] == "/":
		path = path[:-1]
	parts = path[1:].split("/")
	if len(parts) == 2 and parts[0] == "publish":
		return parts[1]
	elif len(parts) == 4 and parts[0] == "realm" and parts[2] == "publish":
		return parts[3]
	else:
		return None

class Server(BaseHTTPServer.HTTPServer):
	handler_func = None
	context = None

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def send_reply(self, code, status, body):
		self.send_response(code, status)
		self.send_header("Content-Type", "text/plain")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def do_POST(self):
		try:
			content_length = int(self.headers.getheader("content-length"))
		except:
			self.send_reply(411, "Length Required", "Missing or invalid Content-Length header.\n")
			return

		channel = get_channel(self.path)
		if not channel:
			self.send_reply(404, "Not Found", "Not Found\n")
			return

		body = self.rfile.read(content_length)

		try:
			m = json.loads(body)
		except:
			self.send_reply(400, "Bad Request", "Body is not valid JSON.\n");
			return

		ret = self.server.handler_func(self.server.context, channel, m)

		if ret is None:
			self.send_reply(200, "OK", "Published\n")
		else:
			self.send_reply(400, "Bad Request", "Bad Request: %s\n" % ret)

def run(port, handler_func, context):
	global g_server
	g_server = Server(("", port), RequestHandler)
	g_server.handler_func = handler_func
	g_server.context = context
	g_server.serve_forever()

def stop():
	g_server.shutdown()