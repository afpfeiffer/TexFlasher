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
import sys
import re
import xml.dom.minidom as xml

def parse_dvi_dump(source_path):
  	doc=xml.Document()
	fc_meta = doc.createElement('fc_meta_info')
	try:
		source_dump=open(source_path+"/source.dump","r")
		source_aux=open(source_path+"/source.aux","r")
	except:
		print "Fatal Error: Cannot open file: "+source_path+"/source.aux or source.dump!"
		sys.exit()
		
	sections={}
	for line in source_aux:
		if re.compile("writefile\{toc\}\{\\\contentsline \{(.*?)\}\{\\\\numberline \{(.*?)\}(.*?)\}\{(.*?)\}\{(.*?)\}\}").findall(line):
		  
		  matches=re.compile("writefile\{toc\}\{\\\contentsline \{(.*?)\}\{\\\\numberline \{(.*?)\}(.*?)\}\{(.*?)\}\{(.*?)\}\}").findall(line)
		  section_type,section_num,section_name,section_page,section=matches[0]
		  sections[section]={"type":section_type,"number":section_num,"name":section_name}
	source_aux.close()
	theorems={}
	doc_start=False
	page=[]
	number=""
	fc_tag=None
	current_section={"section":None,"subsection":None,"subsubsection":None}
	for l in source_dump:
		l=l.strip(' \t\n\r')
	  
		#if not doc_start and re.compile("xxx: 'ps:SDict begin \[/Count -(\d+)/Dest \((.*?)\) cvn/Title \((.*?)\) /OUT pdfmark end'").findall(l):
		#  matches=re.compile("xxx: 'ps:SDict begin \[/Count -(\d+)/Dest \((.*?)\) cvn/Title \((.*?)\) /OUT pdfmark end'").findall(l)
		#  sec_name=matches[0][2]
		#  sections[matches[0][1]]=sec_name
		#check for page start  
		
		if re.compile("xxx: 'ps:SDict begin \[/View \[/XYZ H.V\]/Dest \((.*?)\) cvn /DEST pdfmark end'").findall(l):#we got section or something like that
		  matches=re.compile("xxx: 'ps:SDict begin \[/View \[/XYZ H.V\]/Dest \((.*?)\) cvn /DEST pdfmark end'").findall(l)
		  if 'Doc-Start'==matches[0]:
			doc_start=True
		  elif re.compile('page.(\d+)').findall(matches[0]):
			page=re.compile('page.(\d+)').findall(matches[0])
		  elif doc_start and fc_tag and matches[0].startswith("sat."):
			number=matches[0].replace("sat.","")
			theorems[fc_tag]["number"]=number
	          elif doc_start and sections.get(matches[0], False):			
			section_type=sections[matches[0]]['type']
			current_section[section_type]=sections[matches[0]]
		if doc_start and re.compile("xxx: 'fc=(.*?)'").findall(l):#we got fc_tag
		  matches=re.compile("xxx: 'fc=(.*?)'").findall(l)
		  fc_tag=matches[0]
		  theorems[fc_tag]={"page":None,"number":None,"section_name":None,"section_number":None,"subsection_name":None,"subsection_number":None,"subsubsection_name":None,"subsubsection_number":None}
		  for meta in current_section:
			if not current_section[meta]==None:
			  theorems[fc_tag][meta+"_name"]=current_section[meta]['name']
			  theorems[fc_tag][meta+"_number"]=current_section[meta]['number']
			
		  theorems[fc_tag]['page']=page[0]
		  
	for fc_tag in theorems:
		element=doc.createElement(fc_tag)
		fc_meta.appendChild(element)
		for entry in theorems[fc_tag]:
		  element.setAttribute(entry,str(theorems[fc_tag][entry]))

	xml_file = open(source_path+"/source.xml", "w")
	fc_meta.writexml(xml_file)	    
	xml_file.close()
	return fc_meta



def parse_tex(fcard_dir,source_path):
	meta=parse_dvi_dump(source_path)
	try:
		source_tex=open(source_path+"/source.tex","r")
	except:
		print "Fatal Error: Cannot open file: "+source_path+"/source.tex!"
		sys.exit()
		
		
		
	theorems={}
	tex_header=""
	end_header_marker="\\begin{document}\n"
	tex_end="\end{document}\n"
	notice="%NOTICE: This file is generated automatically changes will be overwritten and wont have any effect unless you compile it yourself!\n"
	
  	doc=xml.Document()
	order_db = doc.createElement('order_db')
	counter=0
	# get tex header
	end_header_marker_status=""
	for line in source_tex:
		if re.compile('documentclass\[').findall(line):
			tex_header+=" \documentclass[avery5388,frame]{flashcards}\n"
		elif re.compile('newtheorem.*?\{(.*?)\}.*?\{(.*?)\}.*?').findall(line):
			matches=re.compile('newtheorem.*?\{(.*?)\}.*?\{(.*?)\}.*?').findall(line)		
			theorems[matches[0][0]]=matches[0][1]
			tex_header+="\\newtheorem{"+matches[0][0]+"}{"+matches[0][1]+"}[section]"

		elif line==end_header_marker:
			tex_header+=line
		  
			end_header_marker_status="found"
			break
		elif not line=="\n" or len(line)==0: #only appen if line not emty!
			tex_header+=line
	
	if not end_header_marker_status=="found":
		print "Fatal Error: No end_tex_header_marker "+end_header_marker+" found!" 
		sys.exit()
	#search for card marker
	fcards={}
	fcards_header={}
	fcard_title=""
	fcard_desc=""
	for line in source_tex:
		matches=re.compile('fc\{(\w+)\}\n').findall(line)
		try:#fails if no fc_marker in line!
			fcard_title=matches[0]
			element=doc.createElement(fcard_title)
			order_db.appendChild(element)
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
						fc_meta=meta.getElementsByTagName(fcard_title)[0]
						fc_page=fc_meta.getAttribute('page')
						fc_header=""
						fc_chapter=""
						fc_section=""
						fc_subsection=""
						fc_subsubsection=""
						
						try:
						  fc_number=fc_meta.getAttribute('number')
						  fc_header+="\\renewcommand{\\the"+matches[0][0]+"}{"+fc_number+"}"
						except:
						  pass					
						try:
						  fc_sec_name=fc_meta.getAttribute('section_name')
						  fc_sec=fc_meta.getAttribute('section_number')
						  if not fc_sec=="None":
						    fc_header+="\\renewcommand{\\thesection}{"+fc_sec+"}"
						    fc_section="\\section{"+fc_sec_name+"}"
						except:
						  pass						
						try:
						  fc_subsec_name=fc_meta.getAttribute('subsection_name')
						  fc_subsec=fc_meta.getAttribute('subsection_number')
						  if not fc_subsec=="None":
						    fc_header+="\\renewcommand{\\thesubsection}{"+fc_subsec+"}"
						    fc_subsection="\\subsection{"+fc_subsec_name+"}"
						except:
						  pass						
						try:
						  fc_subsubsec_name=fc_meta.getAttribute('subsubsection_name')
						  fc_subsubsec=fc_meta.getAttribute('subsubsection_number')
						  if not fc_subsubsec=="None":
						    fc_header+="\\renewcommand{\\thesubsubsection}{"+fc_subsubsec+"}"
						    fc_subsubsection="\\subsubsection{"+fc_subsubsec_name+"}"
						except:
						  pass
						  
						try:
							fcards[fcard_title]="\\begin{flashcard}{"+fc_chapter+"\n"+fc_section+"\n"+fc_subsection+"\n"+fc_subsubsection+"\\begin{"+matches[0][0]+"}["+matches[0][1]+"]\\end{"+matches[0][0]+"}}\n\\flushleft\n\\footnotesize\n%#begin_content#%\n"
							fcards_header[fcard_title]=fc_header
							element.setAttribute('name',matches[0][1])
							element.setAttribute('theorem_type',matches[0][0])							
							element.setAttribute('theorem_name',theorems[matches[0][0]])							
						except:
							print "Note: No theorem type found for flashcard_marker "+fcard_title
							fcards[fcard_title]="\\begin{flashcard}{"+matches[0][1]+"}\n\\flushleft\n\\footnotesize\n%#begin_content#%\n"					
					
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
			fcards[fcard_title]+="%#end_content#%\n\end{flashcard}\n"
			#check if flashcard is ok
			if re.compile('begin{flashcard}').findall(fcards[fcard_title]) and re.compile('end{flashcard}').findall(fcards[fcard_title]):
				element.setAttribute('position',str(counter))
				counter+=1
				fcard_title=""
				fcard_desc=""

			else:
				# delete malicious fcard
				fcards.pop(fcard_title)
				print "Error: flashcard_marker "+fcard_title+" had no valid syntax and could not be created!"
				fcard_title=""
				fcard_desc=""
	source_tex.close()

	
	#
	
	
	
	#create flashcard tex files
	if len(fcards)>0:		
		for fcard in fcards:
			fcard_file=open(fcard_dir+"/"+fcard+".tex","w")
			fcard_file.writelines(notice)
			fcard_file.writelines(tex_header)
			fcard_file.writelines(fcards_header[fcard])

			#bugfix because latex flashcard environment does not fully support align! 
			fcard_file.writelines(fcards[fcard].replace("\\begin{align*}","\\begin{equation*}\\begin{aligned}").replace("\\end{align*}","\\end{aligned}\\end{equation*}").replace("\\begin{align}","\\begin{equation}\\begin{aligned}").replace("\\end{align}","\\end{aligned}\\end{equation}"))

			fcard_file.writelines(tex_end)
			fcard_file.close()
		#success
		xml_file = open(source_path+"/../Flashcards/order.xml", 'w')
		order_db.writexml(xml_file)	    
		xml_file.close()		
		print "Created "+str(len(fcards))+" flashcard LaTex file(s)"
	else:
		print "Fatal Error: No flashcard_markers  found!"
		sys.exit()
try:		
	parse_tex(sys.argv[1],sys.argv[2])
except SystemExit:
	print "SystemExit"
except:
	print "Syntax:\n  flashcard_directory\n source_directory \n (jeweils ohne / am ende!)\n"
