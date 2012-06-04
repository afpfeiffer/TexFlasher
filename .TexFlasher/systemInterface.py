#!/usr/bin/python
# encoding: utf-8
#     This file is part of TexFlasher.
#     Copyright (c) 2012:
#          Can Oezmen
#          Axel Pfeiffer
#
#     TexFlasher is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     TexFlasher is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with TexFlasher  If not, see <http://www.gnu.org/licenses/>.


import os
import subprocess
import sys
import re
import commands
import xml.dom.minidom as xml
from operator import itemgetter
from time import strftime, strptime, ctime, localtime
from datetime import datetime, timedelta
from Tkinter import *
from math import *
import tkFont
import tkMessageBox
import Image, ImageTk
import tkFileDialog
from difflib import get_close_matches
import itertools, collections
import ConfigParser


def checkForUpdate(user):
	files=""
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('config')[0]
		for elem in config_xml.childNodes:
			if elem.tagName=="FlashFolder" and not elem.getAttribute('filename')=="":
				files += str(elem.getAttribute('filename')) + " "
				#files += str(os.path.dirname(elem.getAttribute('filename'))+"/Users/"+user+".xml ")
				#files += str(os.path.dirname(elem.getAttribute('filename'))+"/Users/"+user+"_comment.xml ")
				#files += str(os.path.dirname(elem.getAttribute('filename'))+"/Users/questions.xml ")
	os.system( "bash .TexFlasher/scripts/checkForUpdate.sh "+ files + "&")
	

def checkIfNeedToSave( files ):
	process = subprocess.Popen(['bash', '.TexFlasher/scripts/checkIfNeedToSave.sh', files], stdout=subprocess.PIPE)
	output  = process.stdout.read()
	
	if str(output) == "":
		return False
	else:
		return True
		
def executeCommand( command ,wait=True):
	win = Toplevel()
	cmd="\""+str(command)+"; exit; sh\""
	if not wait:
		os.system('xterm -geometry 110x42 -sb -e '+ cmd +' &' )
	else:
		os.system('xterm -geometry 110x42 -sb -e '+ cmd )		
	win.destroy()

	
def sanatize(string):
	out=""
	for s in string.split("\n"):
		s=s.replace(",","").replace("}","").replace("]","").replace("."," ")#.split(":")[0].split("\[")[0].split("$")[0]
		out+=s+" "
	return out	
	
def create_completion_list():
	results=[]
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('config')[0]
		max=1
		for elem in config_xml.childNodes:
			dir=elem.getAttribute('filename')
			if len(dir)>0 and os.path.isfile(dir):
				tex=open(dir,"r")
				for line in tex:
					#words={}
					for word in line.split(" "):
						try:
							word=unicode(sanatize(word).replace("\n","").lower())
							#for w in words:
							#	words[w]+=word+" "
							#	results.append(words[w])
							#words[word]=word+" "
							results.append(word)

						except:
							pass

					#print words	
	return tuple(results)
	
	



def create_flashcards( filename ):
	update_config(filename)
	#os.system("bash .TexFlasher/scripts/createFlashcards.sh "+ filename)
	executeCommand("bash .TexFlasher/scripts/createFlashcards.sh "+ filename, True)


def update_config(filename):
	dir_name=os.path.dirname(filename)
	doc=xml.Document()
	config_xml = doc.createElement('config')
	doc.appendChild(config_xml)
	if os.path.isfile("./.TexFlasher/config.xml"):
		try:
			tree = xml.parse("./.TexFlasher/config.xml")
			config_xml = tree.getElementsByTagName('config')[0]
		except:
			pass
	if not os.path.exists(filename):
		print "filename does not exist."
		return
		#menu()
	dirFound=False
	for elem in config_xml.childNodes:
		if elem.tagName=="FlashFolder" and elem.getAttribute('filename')==filename:
			elem.setAttribute('lastReviewed', strftime("%Y-%m-%d %H:%M:%S", localtime()))
			dirFound=True
	if not dirFound:
		elem=doc.createElement("FlashFolder")
		config_xml.appendChild(elem)
		now=strftime("%Y-%m-%d %H:%M:%S", localtime())
		elem.setAttribute('filename',filename)
		elem.setAttribute('lastReviewed', now)
		elem.setAttribute('created',now)	
	xml_file = open("./.TexFlasher/config.xml", "w")
	config_xml.writexml(xml_file)
	xml_file.close()
	

	