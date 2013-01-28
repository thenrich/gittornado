# -*- coding: utf-8 -*-
#
# Copyright 2011 Manuel Stocker <mensi@mensi.ch>
#
# This file is part of GitTornado.
#
# GitTornado is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GitTornado is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GitTornado.  If not, see http://www.gnu.org/licenses

import os.path
import logging
import ConfigParser
import hashlib

import tornado.ioloop, tornado.httpserver
from tornado.options import define, options, parse_command_line
from gittornado import RPCHandler, InfoRefsHandler, FileHandler

accessfile = ConfigParser.ConfigParser()

def permsToDict(str):
    perms_dict = {}
    perms = str.split(',')
    for p in perms:
        ps = p.split('=')
        perms_dict[ps[0]] = ps[1]

    return perms_dict

def auth(request):
    pathlets = request.path.strip('/').split('/')
    author = request.headers.get('Authorization', None)
    if author is None:
        return False, False

    if author.strip().lower()[:5] != 'basic':
        return False, False

    userpw_base64 = author.strip()[5:].strip()
    user, pw = userpw_base64.decode('base64').split(':', 1)
    if accessfile.has_option('users', user):
        if accessfile.get('users', user) == hashlib.new('SHA1', pw).hexdigest():
            if accessfile.has_option('access', user):
		perms = permsToDict(accessfile.get('access', user))
		return pathlets[0] in perms and 'r' in perms[pathlets[0]], pathlets[0] in perms and 'w' in perms[pathlets[0]]

    return False, False

def gitlookup(request):
    pathlets = request.path.strip('/').split('/')

    path = os.path.abspath(os.path.join(options.gitbase, pathlets[0]))
    if not path.startswith(os.path.abspath(options.gitbase)):
        return None

    if os.path.exists(path):
        return path

def auth_failed(request):
    msg = 'Authorization needed to access this repository'
    request.write('HTTP/1.1 401 Unauthorized\r\nContent-Type: text/plain\r\nContent-Length: %d\r\nWWW-Authenticate: Basic realm="%s"\r\n\r\n%s' % (
                    len(msg), options.realm.encode('utf-8'), msg))

def main():
    define('port', default=8080, type=int, help="Port to listen on")
    define('gitbase', default='.', type=str, help="Base directory where bare git directories are stored")
    define('accessfile', type=str, help="File with access permissions")
    define('realm', default='my git repos', type=str, help="Basic auth realm")
    define('certfile', default='', type=str, help="Location of SSL cert")
    define('keyfile', default='', type=str, help="Location of SSL key")

    parse_command_line()

    if options.accessfile:
        accessfile.read(options.accessfile)

    conf = {'auth': auth,
            'gitlookup': gitlookup,
            'auth_failed': auth_failed
            }

    app = tornado.web.Application([
                           ('/.*/git-.*', RPCHandler, conf),
                           ('/.*/info/refs', InfoRefsHandler, conf),
                           ('/.*/HEAD', FileHandler, conf),
                           ('/.*/objects/.*', FileHandler, conf),
                           ])

    server = tornado.httpserver.HTTPServer(app, ssl_options={
	    "certfile":options.certfile,
	    "keyfile":options.keyfile
        }
    )
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

