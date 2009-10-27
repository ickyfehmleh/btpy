#!/usr/bin/python
#
# save a file in the user's USER_DL_DIR
# (hardlink to an expired file)
#

import os
import sys
import os.path
from common import *

def getPathWithoutRoot(path,root):
	if path == root:
		s = ''
	else:
		s = path.replace(root+'/','')
	return s

if not os.path.exists(USER_DL_DIR):
	try:
		os.mkdir( USER_DL_DIR, 0700 )
	except:
                print 'Failed to create %s!' % USER_DL_DIR
		sys.exit(2)

if len( sys.argv ) == 1:
	print '%s will save a file from being expired' % sys.argv[0]
	print
	print 'Usage: %s <file> ... <fileN>' % sys.argv[0]
	sys.exit()

for currentArg in sys.argv[1:]:
	fullPath = os.path.abspath( currentArg )
	print 'Operating on %s' % currentArg
	
	if not os.path.exists( os.path.abspath( currentArg ) ):
		print '%s does not exist!' % currentArg
	elif os.path.exists( os.path.join( USER_DL_DIR, currentArg ) ):
		print '%s already exists in your download dir!' % currentArg
	else:
		if os.path.isdir( os.path.abspath( currentArg ) ):
			parentDir = os.path.abspath( currentArg )
			#print 'parentDir: %s' % parentDir
			localOutputDir = None
			for root, dirs, files in os.walk( os.path.abspath( currentArg ) ):
				localRootDir = getPathWithoutRoot(root,parentDir)
				localOutputDir = os.path.join( USER_DL_DIR, currentArg, localRootDir )

				if not os.path.exists( localOutputDir ):
					os.mkdir( localOutputDir )
				#print 'root: %s (%s)' % (root,localRootDir)

				for dir in dirs:
					localDir = os.path.join( localRootDir, dir )
					#print 'DIR: %s' % localDir
					outputDir = os.path.join( USER_DL_DIR, currentArg, localDir )
					if not os.path.exists( outputDir ):
						os.mkdir( outputDir )

				for file in files:
					localFile = os.path.join( localRootDir, file )
					#print 'FILE: %s' % localFile
					outputFile = os.path.join( USER_DL_DIR, currentArg, localFile )
					inputFile = os.path.join( root, file )
					if not os.path.exists( outputFile ):
						#print 'os.link(%s,%s)' % (inputFile, outputFile)
						os.link( inputFile, outputFile )
			print localOutputDir
		else:
			inputFile = os.path.abspath( currentArg )
			outputLink = os.path.join( USER_DL_DIR, currentArg )
			#print '### linking %s to %s' % (inputFile, outputLink )
			try:
				os.link( inputFile, outputLink )
				print outputLink
			except:
				print 'Could not save %s' % currentArg
sys.exit()

# foreach arg
#   make sure arg exists
#   cycle through files/dirs in arg
#     if dir, mkdir
#     if file, os.link()
#   print linkname to stdout
# print reminder to delete files manually OR ELSE
