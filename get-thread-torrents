#!/usr/bin/python
#
#
#
from BeautifulSoup import BeautifulSoup
import urlparse
import sys
import cookielib
import urllib2
import os.path
import os
from common import *

def grabURLsFromSite(fc,url):
	parser = BeautifulSoup( fc )
	hrefs = []
	for href in parser.fetch('a'):
		if len(href.parent.attrs) > 0:
			if href.parent.attrs[0][1] == 'ih':
					for attrib in href.attrs:
						if attrib[0] == 'href':
							hrefs.append( urlparse.urljoin(url,attrib[1]) )
	return hrefs	

def fixURL(url):
	su = urlparse.urlparse(url)
	if su[2] == '/f.php':
		arg = '/tt.php?%s' % su[4]
		url = urlparse.urljoin( url, arg )
	return url

#############################################################################

## setup http
cookieFile = os.path.join(os.environ["HOME"], ".btrss", "cookies.txt" )
cj = cookielib.MozillaCookieJar()
if os.path.exists( cookieFile ):
        cj.load( cookieFile )
opener = urllib2.build_opener( urllib2.HTTPCookieProcessor( cj ) )
urllib2.install_opener( opener )
headers = {'User-Agent' : 'Mozilla/4.0 (compatible; python-based client; talk to liekomglol@gmail.com if this is problematic)'}
## end http stuffs

# fetch each file
for urlArg in sys.argv[1:]:
	try:
		url = fixURL(urlArg)
		#print 'fetch %s' % url
		req = urllib2.Request(url, None, headers)
		f = urllib2.urlopen(req)

		hrefs = grabURLsFromSite( f.read(), url )
		for href in hrefs:
			cmd = '%s/bin/start "%s"' % (COMPLETED_TORRENT_DIR,href)
			#print cmd
			os.system( cmd )
	except:
		pass
sys.exit(0)
