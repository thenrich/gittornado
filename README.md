GitTornado
==========

GitTornado is a tornado-based implementation of the git-http-backend supporting 
chunked transfer encoding. It is designed to use little resources and as such will 
try its best to avoid reading whole files or git output into memory.

How to Install
--------------

	$ pip install gittornado
	
How to Use
----------

To best suit your needs, you should include the provided RequestHandlers into your 
tornado application. An example of such an application is given in server.py. The 
example server will also install itself as a console-script, so you can do

	$ gittornado
	
and you will have the example server running on port 8080, serving the git repositories 
in your working directory world-readable.

Example password file 

[users]
USERNAME GOES HERE: SHA1_encrypted_password 

[access]
USERNAME GOES HERE: repository_abc=r,repository_def=rw


Why not WSGI
------------

The WSGI standard doesn't offer a consistent way of working with requests that do not
offer a Content-Length header. mod_wsgi provides an option to read chunked requests into 
memory and fake the Content-Length header. This however means that if you commit a 
600 MB file into your git repository, mod_wsgi will allocate 600 MB of RAM.

Tornado offers a simple event-driven approach of handling HTTP requests, therefore it is 
a prime candidate for a pythonic implementation of git-http-backend.

If you need to combine GitTornado with a WSGI app, for example if you would like to also 
have a webinterface for your repository under the same URL, you can use tornado's WSGIContainer:

	fallbackapp = tornado.wsgi.WSGIContainer(wsgiapp)
	app = tornado.web.Application([
	   ('/.*/.*/git-.*', RPCHandler, config_dict),
	   ('/.*/.*/info/refs', InfoRefsHandler, config_dict),
	   ('/.*/.*/HEAD', FileHandler, config_dict),
	   ('/.*/.*/objects/.*', FileHandler, config_dict),
	   ('.*', tornado.web.FallbackHandler, {'fallback': fallbackapp})
	])
	
Apache
------

If you want to integrate GitTornado into an existing site, you can use mod_proxy together with 
mod_proxy_http to configure a reverse proxy:

	ProxyPass /git/ http://127.0.0.1:8080/
	ProxyPassReverse /git/ http://127.0.0.1:8080/
	
Production
----------

For productional use, you might want to put GitTornado behind a reverse proxy / load balancer, for 
example Apache or nginx and start one process for every CPU instruction queue on your machine.

License
-------

GitTornado is licensed under GPLv3.
