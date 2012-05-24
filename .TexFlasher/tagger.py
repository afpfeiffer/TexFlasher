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



########################################################## Comment on fc ##############################################################

def question_tag_command(tagtype,xml_path,tags,fc_tag,canvas,item,user):
		frame=Frame()
		tree = xml.parse(xml_path)
		content=""
		creator=""
		fg="black"
		if not fc_tag==None:
		  tag_xml = tree.getElementsByTagName(tagtype)[0]
		  for node in tag_xml.getElementsByTagName(fc_tag):
		    if node.getAttribute('created')==list(tags)[1]+" "+list(tags)[2]:
		      creator=node.getAttribute('user')
		      try:
			content=node.getAttribute('comment')
		      except:
			pass
		      break
		if fc_tag==None or creator=="":
		  creator="unsaved"
		  content="comment here ..."
		  fg="red"
		Label(frame,text="Tagtype: "+tagtype+"\n"+creator,fg=fg,bg=None).grid(row=0,column=0,columnspan=4)
		comment_field=Text(frame,width=20,height=10)
		comment_field.insert(INSERT,content)
		comment_field.grid(row=1,columnspan=4)
		#check if text exists if so insert!
		image = Image.open(".TexFlasher/pictures/clear.png")
		image = image.resize((20,20), Image.ANTIALIAS)
		image = ImageTk.PhotoImage(image)
		frame.edit_img=image		
		Button(frame,text="Delete",image=image,command=lambda:delete_c_elem_from_xml(canvas,fc_tag,tags,tagtype,item)).grid(row=2,column=3,sticky=E)

		image = Image.open(".TexFlasher/pictures/upload.png")
		image = image.resize((20,20), Image.ANTIALIAS)
		image = ImageTk.PhotoImage(image)
		frame.comment_img=image		
		Button(frame,text="Comment",image=image,command=lambda:savefile(canvas,fc_tag,user,tagtype,item,comment_field)).grid(row=2,column=0,sticky=W)		
		return frame 
		
		
class RectTracker:
  
	def __init__(self, canvas,dir,user):
		self.canvas = canvas
		self.item = None
		self.time=strftime("%Y-%m-%d %H:%M:%S", localtime())
		self.user=user
		self.canvas.tagtypes={}
		self.canvas.tagtypes["rect"]={"xml_path":dir+"/Users/"+user+"_comment.xml","new":"re","old":"ore","type":"rectangle","command":question_tag_command}
		self.canvas.tagtypes["link"]={"xml_path":dir+"/Users/links.xml","new":"li","old":"oli","type":"image","image_path":".TexFlasher/pictures/link_fix.png","command":question_tag_command}
		self.canvas.tagtypes["question"]={"xml_path":dir+"/Users/questions.xml","new":"qu","old":"oqu","type":"image","image_path":".TexFlasher/pictures/question_fix.png","image_path_other":".TexFlasher/pictures/question_other.png","command":question_tag_command}

		self.canvas.tags_imgs={}
		for tagtype in self.canvas.tagtypes:
		    try:# doesnt work for rectagle tags
		      image = Image.open(self.canvas.tagtypes[tagtype]['image_path'])		      
		      image = image.resize((40,40), Image.ANTIALIAS)
		      self.canvas.tags_imgs[tagtype]=ImageTk.PhotoImage(image)	
		      setattr(c,tagtype+"_img", self.canvas.tags_imgs[tagtype])
		    except:
			pass
		self.selected_circle=None
		self.follow_size=(20,20)
		self.fix_size=(40,40)
		self.tags_tag="tagger"
		
	def question_tag(self):
	  image = Image.open(".TexFlasher/pictures/question_follow.png")
	  image = image.resize(self.follow_size, Image.ANTIALIAS)
	  image = ImageTk.PhotoImage(image)
	  self.canvas.tag_follow_image=image	  
	  self.canvas.current_tag="question"	  
	  self.canvas.tag_fix="qu"
	  self.canvas.tag_follow=("question",self.tags_tag)
	  
	def link_tag(self):
	  image = Image.open(".TexFlasher/pictures/link_follow.png")
	  image = image.resize(self.follow_size, Image.ANTIALIAS)
	  image = ImageTk.PhotoImage(image)
	  self.canvas.tag_follow_image=image
	  self.canvas.current_tag="link"
	  self.canvas.tag_fix="li"
	  self.canvas.tag_follow=("link",self.tags_tag)
	  
	def draw(self, start, end, **opts):
		"""Draw the rectangle"""
		if sqrt((start[0]-end[0])*(start[0]-end[0])+(start[1]-end[1])*(start[1]-end[1]))<20:
		    return self.canvas.create_rectangle(*(list(start)+list(end)),dash=[4,4], tags="rect"+" "+self.time,outline="grey",**opts)		    
		else:
		    return self.canvas.create_rectangle(*(list(start)+list(end)),dash=[4,4], tags="rect"+" "+self.time+" elem",outline="red",**opts)
		
	def autodraw(self, **opts):
		"""Setup automatic drawing; supports command option"""
		self.start = None


		self.canvas.bind("<Button-1>", self.__update, '+')
		self.canvas.bind("<Double-Button-1>", self.__tag, '+')
		self.canvas.bind("<B1-Motion>", self.__update, '+')
		self.canvas.bind("<ButtonRelease-1>", self.__stop, '+')
		self._command = opts.pop('command', lambda *args: None)
		self.rectopts = opts
	def up_time(self,time):
		self.time=time
		
	def __update(self, event):
		if not self.start:
			self.start = [event.x, event.y]
			return		 
		if self.item is not None:
			self.canvas.delete(self.item)
		self.canvas.delete(self.canvas.current_tag)  
		self.item = self.draw(self.start, (event.x, event.y), **self.rectopts)
		self._command(self.start, (event.x, event.y))
		
	def __tag(self,event):
		    tags=self.canvas.tag_fix+" "+self.time+" elem"
		    self.canvas.create_image(event.x,event.y-10, image=self.canvas.tags_imgs[self.canvas.current_tag],tags=tags)

	
	    
	def __stop(self, event):

		if self.item is not None:		
			if sqrt((self.start[0]-event.x)*(self.start[0]-event.x)+(self.start[1]-event.y)*(self.start[1]-event.y))<20:
				self.canvas.delete(self.item)	
			else:
			    item_tags=list(self.canvas.gettags(self.item))
			    item_tags[0]="re"
			    self.canvas.itemconfig(self.item,tags=tuple(item_tags))
		self.start = None
		self.item = None
		
	def show_tags(self,fc_tag):
	    for tagtype in self.canvas.tagtypes:
		if os.path.isfile(self.canvas.tagtypes[tagtype]['xml_path']):
			doc= xml.parse(self.canvas.tagtypes[tagtype]['xml_path'])
		  	tags=doc.getElementsByTagName(fc_tag)
		  	for tag in tags:
				timestamp=tag.getAttribute('created')
				tags="old"+" "+timestamp+" "+self.canvas.tagtypes[tagtype]['old']+" "+fc_tag
				
				if self.canvas.tagtypes[tagtype]['type']=="rectangle":
					self.canvas.create_rectangle(int(float(tag.getAttribute("startx"))),int(float(tag.getAttribute("starty"))),int(float(tag.getAttribute("endx"))),int(float(tag.getAttribute("endy"))),dash=[4,4], tags=tags,outline="red",fill="", width=2)
				if self.canvas.tagtypes[tagtype]['type']=="image" and self.user==tag.getAttribute('user'):
					self.canvas.create_image(float(tag.getAttribute('startx')),float(tag.getAttribute('starty'))-10, image=self.canvas.tags_imgs[tagtype],tags=tags)
				elif self.canvas.tagtypes[tagtype]['type']=="image":
					other_img={}
					image = Image.open(self.canvas.tagtypes[tagtype]['image_path_other'])
					image = image.resize((40,40), Image.ANTIALIAS)
					other_img["img"]=ImageTk.PhotoImage(image)
					setattr(self.canvas,tagtype+"_"+tag.getAttribute('user'),other_img["img"])
					self.canvas.create_image(float(tag.getAttribute('startx')),float(tag.getAttribute('starty'))-10, image=other_img["img"],tags=tags.replace("old ","other "))

			

def create_comment_canvas(c,dir,fc_tag,user):
 	def onDrag(start,end):
		global x,y
	try:
		c.rect
	except:
		c.rect=False
	if not c.rect: #initialize
		rect = RectTracker(c,dir,user)
		rect.question_tag() #default start tag
		c.rect=rect
		rect.autodraw(fill="", width=2, command=onDrag)

	else:
		rect=c.rect
	x, y = None, None
	rect.show_tags(fc_tag)


		
	def cool_design(event):
		global x, y, tag_win
		
		kill_xy()
		c.cursor_image=c.create_image(event.x,event.y-10, image=c.tag_follow_image,tags=c.tag_follow)	
		rect.up_time(strftime("%Y-%m-%d %H:%M:%S", localtime()))
		for item in c.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5):
		    
		    for tagtype in c.tagtypes:
		      
		      if c.tagtypes[tagtype]['new'] in list(c.gettags(item)) or c.tagtypes[tagtype]['old'] in list(c.gettags(item)):
			try:
			  if not tag_win:

			    tag_win=c.create_window(c.coords(item)[0],c.coords(item)[1]+25,window=c.tagtypes[tagtype]['command'](tagtype,c.tagtypes[tagtype]['xml_path'],c.gettags(item),fc_tag,c,item,user),tag="info_win")
			except:
			    tag_win=c.create_window(c.coords(item)[0],c.coords(item)[1]+25,window= c.tagtypes[tagtype]['command'](tagtype,c.tagtypes[tagtype]['xml_path'],c.gettags(item),fc_tag,c,item,user),tag="info_win")	    
		try:  
		    if not tag_win in c.find_overlapping(event.x-30, event.y-30, event.x+30, event.y+30):
		      c.delete("info_win")
		      tag_win=False
		except:
		    pass
	def kill_xy(event=None):
		c.delete("tagger")
		
	c.bind('<Motion>', cool_design, '+')	
	c.bind('<Enter>',cool_design,'+')
	c.bind('<Leave>',kill_xy)

		    
					


def savefile(canvas,fc_tag,user,tagtype,item,comment_field):
	    if item in canvas.find_withtag(canvas.tagtypes[tagtype]['new']):
		tags=canvas.gettags(item)

		canvas.itemconfig(item, tags=("old"+" "+tags[1]+" "+tags[2]+" "+canvas.tagtypes[tagtype]['old']))
		try:
			doc= xml.parse(canvas.tagtypes[tagtype]['xml_path'])
			tag_xml=doc.getElementsByTagName(tagtype)[0]
		except:
		  	doc=xml.Document()
			tag_xml = doc.createElement(tagtype)
			
		flashcard_element=doc.createElement(fc_tag)
		tag_xml.appendChild(flashcard_element)
		coord_names=['startx','starty','endx','endy']
		for i in range(0,len(canvas.coords(item))):
		  flashcard_element.setAttribute(coord_names[i], str(canvas.coords(item)[i]))
		flashcard_element.setAttribute('created',tags[1]+" "+tags[2])	
		flashcard_element.setAttribute('user',user)
		
		content=comment_field.get('1.0', END)
		flashcard_element.setAttribute('comment',content)	
		
		xml_file = open(canvas.tagtypes[tagtype]['xml_path'], "w")
		tag_xml.writexml(xml_file)
		xml_file.close()

				
		
def delete_c_elem_from_xml(canvas,fc_tag,tags,tagtype,item):
	for win in canvas.find_withtag("info_win"):
	    canvas.delete(win)
	canvas.delete(item)
	 
	if os.path.isfile(canvas.tagtypes[tagtype]["xml_path"]) and canvas.tagtypes[tagtype]["old"] in list(tags):
		  doc= xml.parse(canvas.tagtypes[tagtype]["xml_path"])
		  items_xml=doc.getElementsByTagName(fc_tag)
		  for item in items_xml:
		  	  if item.getAttribute('created')==list(tags)[1]+" "+list(tags)[2]:
		        	item.parentNode.removeChild(item)
		        	break
	  	  xml_file = open(canvas.tagtypes[tagtype]["xml_path"], "w")
	  	  doc.writexml(xml_file)
	  	  xml_file.close()
	  	  
