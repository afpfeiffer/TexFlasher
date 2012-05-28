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

def open_xml_file(file_path):
	try:
		return xml.parse(file_path)		  
	except:
		return False
########################################################## Comment on fc ##############################################################

def tag_command(tagtype,xml_path,tags,fc_tag,canvas,item,user,color,position):
		frame=Frame(canvas,bd=5,bg=color)
		content=""
		creator=""
		fg="black"
		if not fc_tag==None:
		  try:
		    tree = xml.parse(xml_path)		  
		    tag_xml = tree.getElementsByTagName(tagtype)[0]
		    for node in tag_xml.getElementsByTagName(fc_tag):
		      if node.getAttribute('created')==list(tags)[1]+" "+list(tags)[2]:
			creator=node.getAttribute('user')
			try:
			  content=node.getAttribute('comment')
			except:
			  pass
			break
		  except:
		    pass
		Label(frame,text=tagtype.upper()+"\n"+creator,fg=fg,bg=color).grid(row=0,column=0,columnspan=4)
		comment_field=Text(frame,width=20,height=10,bd=0)
		if not content=="":
			comment_field.insert(INSERT,content)
		comment_field.grid(row=2,columnspan=4)
		#check if text exists if so insert!
		image = Image.open(".TexFlasher/pictures/clear.png")
		image = image.resize((20,20), Image.ANTIALIAS)
		image = ImageTk.PhotoImage(image)
		frame.edit_img=image	
		del_row=3
		if position=="upper":
		  del_row=1
		if position=="lower":
		  del_row=3
		Button(frame,text="Delete",image=image,command=lambda:delete_c_elem_from_xml(canvas,fc_tag,tags,tagtype,item)).grid(row=del_row,columnspan=4,sticky=N+W+S+E)		
		return frame,comment_field 
		
		
class RectTracker:

	def question_tag(self):
	  image = Image.open(".TexFlasher/pictures/question_fix.png")
	  image = image.resize(self.follow_size, Image.ANTIALIAS)
	  image = ImageTk.PhotoImage(image)
	  self.canvas.tag_follow_image=image	  
	  self.canvas.current_tag="question"	  
	  self.canvas.tag_fix="qu"
	  self.canvas.tag_follow=("question",self.tags_tag)
	  
	def link_tag(self):
	  image = Image.open(".TexFlasher/pictures/link_fix.png")
	  image = image.resize(self.follow_size, Image.ANTIALIAS)
	  image = ImageTk.PhotoImage(image)
	  self.canvas.tag_follow_image=image
	  self.canvas.current_tag="link"
	  self.canvas.tag_fix="li"
	  self.canvas.tag_follow=("link",self.tags_tag)

	def repeat_tag(self):
	  image = Image.open(".TexFlasher/pictures/repeat_fix.png")
	  image = image.resize(self.follow_size, Image.ANTIALIAS)
	  image = ImageTk.PhotoImage(image)
	  self.canvas.tag_follow_image=image
	  self.canvas.current_tag="repeat"
	  self.canvas.tag_fix="rep"
	  self.canvas.tag_follow=("repeat",self.tags_tag)

	def watchout_tag(self):
	  image = Image.open(".TexFlasher/pictures/watchout_fix.png")
	  image = image.resize(self.follow_size, Image.ANTIALIAS)
	  image = ImageTk.PhotoImage(image)
	  self.canvas.tag_follow_image=image
	  self.canvas.current_tag="watchout"
	  self.canvas.tag_fix="wa"
	  self.canvas.tag_follow=("watchout",self.tags_tag)
  
	def __init__(self, canvas,dir,user):
		self.canvas = canvas
		self.item = None
		self.time=strftime("%Y-%m-%d %H:%M:%S", localtime())
		self.user=user
		self.canvas.tagtypes={}
		self.canvas.tagtypes["rect"]={"xml_path":dir+"/Users/"+user+"_comment.xml","new":"re","old":"ore","type":"rectangle","command":tag_command}
		self.canvas.tagtypes["link"]={"init":self.link_tag,"xml_path":dir+"/Users/links.xml","new":"li","old":"oli","type":"image","image_path":".TexFlasher/pictures/link_fix.png","command":tag_command}
		self.canvas.tagtypes["question"]={"init":self.question_tag,"xml_path":dir+"/Users/questions.xml","new":"qu","old":"oqu","type":"image","image_path":".TexFlasher/pictures/question_fix.png","image_path_other":".TexFlasher/pictures/question_other.png","command":tag_command}
		self.canvas.tagtypes["repeat"]={"init":self.repeat_tag,"xml_path":dir+"/Users/repeat.xml","new":"rep","old":"orep","type":"image","image_path":".TexFlasher/pictures/repeat_fix.png","command":tag_command}		
		self.canvas.tagtypes["watchout"]={"init":self.watchout_tag,"xml_path":dir+"/Users/watchout.xml","new":"wa","old":"owa","type":"image","image_path":".TexFlasher/pictures/watchout_fix.png","command":tag_command}
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
			try:
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
			except:
				pass

				
def rounded_rect(centerX,centerY,width,height,rad,color,canvas,tags):
  x0=centerX-width/2.
  y0=centerY-height/2.
  x1=centerX+width/2.
  y1=centerY+height/2.
  centers=[[x0,y0,x0+rad,y0+rad],[x0,y1-rad,x0+rad,y1],[x1-rad,y1-rad,x1,y1],[x1-rad,y0,x1,y0+rad]]
  ang=0
  items={}
  for center in centers:
    items[ang]=canvas.create_arc(center[0],center[1],center[2],center[3],start=ang,extent=270,width=0,fill=color,outline="",tags=tags)
    ang+=90
  items["in1"]=canvas.create_rectangle(x0+rad/2.,y0,x1-rad/2.,y1,width=0,fill=color,tags=tags)
  items["in2"]=canvas.create_rectangle(x0,y0+rad/2.,x1,y1-rad/2.,width=0,fill=color,tags=tags)					
  return items
				
class tag_tracker:
	def __init__(self, canvas,user,fc_tag):
		self.fc_tag=fc_tag	
		self.user=user
		self.canvas=canvas
		self.tag_win=False
		self.comment_field=False
		self.current_item=False
		self.current_tagtype=False
	def check_for_tag(self, event):
		if not self.tag_win:
			for item in self.canvas.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5):		    
				for tagtype in self.canvas.tagtypes:		      
				      if self.canvas.tagtypes[tagtype]['new'] in list(self.canvas.gettags(item)) or self.canvas.tagtypes[tagtype]['old'] in list(self.canvas.gettags(item)):
						coords=self.canvas.coords(item)
						#rounded_rect(coords[0],coords[1]+25,170,230,30,"lightgray",self.canvas,"info_win")
						if coords[1]>float(self.canvas.cget("height"))/2.:
						   position="upper"
						else:
						   position="lower"
						frame,self.comment_field=self.canvas.tagtypes[tagtype]['command'](tagtype,self.canvas.tagtypes[tagtype]['xml_path'],self.canvas.gettags(item),self.fc_tag,self.canvas,item,self.user,"lightgray",position)
						self.current_tagtype=tagtype
						self.current_item=item
						self.tag_win=self.canvas.create_window(coords[0],coords[1]+25,window=frame,tag="info_win")	    

						self.comment_field.focus_set()				

		else: 
		    if not self.tag_win in self.canvas.find_overlapping(event.x-30, event.y-30, event.x+30, event.y+30) and not self.current_item in  self.canvas.find_overlapping(event.x-30, event.y-30, event.x+30, event.y+30):
			savefile(self.canvas,self.fc_tag,self.user,self.current_tagtype,self.current_item,self.comment_field.get('1.0', END))		    
			self.canvas.delete("info_win")

			self.tag_win=False

	def reset(self):
		self.tag_win=False
		self.comment_field=False
		self.current_item=False
		self.current_tagtype=False		


	
		
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

	c.tag_tracker=tag_tracker(c,user,fc_tag)
		
	def cool_design(event):
		global x, y
		kill_xy()
		c.cursor_image=c.create_image(event.x,event.y-10, image=c.tag_follow_image,tags=c.tag_follow)	
		rect.up_time(strftime("%Y-%m-%d %H:%M:%S", localtime()))
		c.tag_tracker.check_for_tag(event)
		    
	def kill_xy(event=None):
		c.delete("tagger")
		
	def switch_tag(direction):
		rect.watchout_tag()
		
	c.bind('<4>', lambda event : switch_tag("next"))
	c.bind('<5>', lambda event : switch_tag("back"))        
	c.bind('<Motion>', cool_design, '+')	
	c.bind('<Enter>',cool_design,'+')
	c.bind('<Leave>',kill_xy)

		    
					


def savefile(canvas,fc_tag,user,tagtype,item,content):
	 #   if item in canvas.find_withtag(canvas.tagtypes[tagtype]['new']) or item in :
		tags=canvas.gettags(item)
		flashcard_element=None
		
		canvas.itemconfig(item, tags=("old"+" "+tags[1]+" "+tags[2]+" "+canvas.tagtypes[tagtype]['old']))
		try:
			doc= xml.parse(canvas.tagtypes[tagtype]['xml_path'])
			tag_xml=doc.getElementsByTagName(tagtype)[0]
		except:
		  	doc=xml.Document()
			tag_xml = doc.createElement(tagtype)
		try:
			elements=doc.getElementsByTagName(fc_tag)
			for element in elements:
			    if element.getAttribute('created')==tags[1]+" "+tags[2]:
			      flashcard_element=element
			      break
			if flashcard_element==None:
			  raise
		except:	      
			flashcard_element=doc.createElement(fc_tag)
			
		tag_xml.appendChild(flashcard_element)
		coord_names=['startx','starty','endx','endy']
		for i in range(0,len(canvas.coords(item))):
		  flashcard_element.setAttribute(coord_names[i], str(canvas.coords(item)[i]))
		flashcard_element.setAttribute('created',tags[1]+" "+tags[2])	
		flashcard_element.setAttribute('user',user)

		if content=="\n":
			content=""
		try:
			if content[-1]=="\n":
				content=content[:-1]
			if content[-1]==" ":
				content=content[:-1]			
		except:
			pass
		flashcard_element.setAttribute('comment',content)	
		xml_file = open(canvas.tagtypes[tagtype]['xml_path'], "w")
		tag_xml.writexml(xml_file)
		xml_file.close()

				
		
def delete_c_elem_from_xml(canvas,fc_tag,tags,tagtype,item):

	for win in canvas.find_withtag("info_win"):
	    canvas.delete(win)
	canvas.delete(item)
	canvas.tag_tracker.reset()
	
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
	  	  
