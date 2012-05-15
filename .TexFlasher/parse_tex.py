#!/usr/bin/python
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
import sys
import re
import xml.etree.ElementTree as xml
from xml.etree.ElementTree import dump


def parse_tex(tex_file_path, end_header_marker, fcard_dir):
	try:
		tex_file=open(tex_file_path,"r")
	except:
		print "Fatal Error: Cannot open file: "+tex_file_path+"!"
		sys.exit()
	theorems={}
	tex_header=""
	tex_end="\end{document}\n"
	notice="%NOTICE: This file is generated automatically changes will be overwritten and wont have any effect unless you compile it yourself!\n"
	
	order_db = xml.Element('order_db')
	counter=0
	# get tex header
	end_header_marker_status=""
	for line in tex_file:
		if re.compile('documentclass\[').findall(line):
			line=" \documentclass[avery5388,frame]{flashcards}\n"
		if re.compile('newtheorem.*?\{(.*?)\}.*?\{(.*?)\}.*?').findall(line):
			matches=re.compile('newtheorem.*?\{(.*?)\}.*?\{(.*?)\}.*?').findall(line)		
			theorems[matches[0][0]]=matches[0][1]

		if re.compile(end_header_marker).findall(line):
			end_header_marker_status="found"
			break
		if not line=="\n" or len(line)==0: #only appen if line not emty!
			tex_header+=line
	
	if not end_header_marker_status=="found":
		print "Fatal Error: No end_tex_header_marker "+end_header_marker+" found!" 
		sys.exit()
	#search for card marker
	fcards={}
	fcard_title=""
	fcard_desc=""
	for line in tex_file:
		matches=re.compile('fc\{(\w+)\}\n').findall(line)
		try:#fails if no fc_marker in line!
			fcard_title=matches[0]
			#check for doubles
			if fcard_title in fcards:
				print "Fatal Error: flashcard_marker "+fcard_title+" used multiple times!"
		except:
			pass
		#check if we are in flashcard and not at the end
		if ((fcard_title!="") and (not re.compile('end{'+fcard_desc+'}').findall(line))):
			if fcard_title not in fcards:		
				matches=re.compile('begin\{(\w+)\}\[(.*?)\]').findall(line)
				try:
					if len(matches[0][1])>0:
						try:
							fcards[fcard_title]="\\begin{flashcard}{"+theorems[matches[0][0]]+": "+matches[0][1]+"}\n\\flushleft\n\\footnotesize\n"
						
						except:
							print "Note: No theorem type found for flashcard_marker "+fcard_title
							fcards[fcard_title]="\\begin{flashcard}{"+matches[0][1]+"}\n\\flushleft\n\\footnotesize\n"					
					
						fcard_desc=matches[0][0]
					else:
						print "Warning: flashcard_marker "+fcard_title+" has no valid title!"
				except:
					pass
			else:
				#if re.compile('ref\{(\w+)\}').findall(line):	
				#	matches=re.compile('ref\{(\w+)\}').findall(line)
				#	fcards[fcard_title]+=line.replace("\\ref{"+matches[0]+"}","\\link{"+matches[0]+"}")	
				#else:			
				fcards[fcard_title]+=line				
		#check if we are at the end of a flashcard!
		elif fcard_title!="" and re.compile('end{'+fcard_desc+'}').findall(line):
			fcards[fcard_title]+="\end{flashcard}\n"
			#check if flashcard is ok
			if re.compile('begin{flashcard}').findall(fcards[fcard_title]) and re.compile('end{flashcard}').findall(fcards[fcard_title]):
				flashcard_el=xml.Element(fcard_title)
				order_db.append(flashcard_el)
				flashcard_el.attrib['position'] = str(counter)
				counter+=1
				fcard_title=""
				fcard_desc=""

			else:
				# delete malicious fcard
				fcards.pop(fcard_title)
				print "Error: flashcard_marker "+fcard_title+" had no valid syntax and could not be created!"
				fcard_title=""
				fcard_desc=""
	tex_file.close()

	#create flashcard tex files
	if len(fcards)>0:		
		for fcard in fcards:
			fcard_file=open(fcard_dir+"/"+fcard+".tex","w")
			fcard_file.writelines(notice)
			fcard_file.writelines(tex_header)

			#bugfix because latex flashcard environment does not fully support align! 
			fcard_file.writelines(fcards[fcard].replace("\\begin{align*}","\\begin{equation*}\\begin{aligned}").replace("\\end{align*}","\\end{aligned}\\end{equation*}").replace("\\begin{align}","\\begin{equation}\\begin{aligned}").replace("\\end{align}","\\end{aligned}\\end{equation}"))

			fcard_file.writelines(tex_end)
			fcard_file.close()
		#success
		xml_file = open(os.path.dirname(tex_file_path)+"/Karteikarten/order.xml", 'w')
		xml.ElementTree(order_db).write(xml_file)
		xml_file.close()
		print "Created "+str(len(fcards))+" flashcard LaTex file(s)"
	else:
		print "Fatal Error: No flashcard_markers  found!"
		sys.exit()
try:		
	parse_tex(sys.argv[1],sys.argv[2],sys.argv[3])
except SystemExit:
	print "SystemExit"
except:
	print "Syntax:\n tex_file \n end_tex_header_marker\n flashcard_directory (ohne / am ende!)"
