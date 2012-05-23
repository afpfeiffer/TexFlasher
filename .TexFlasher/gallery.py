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
	
class Flow:
	def __init__(self, clickfunc, canvas):
	         self.cfunc = clickfunc
		 self.canvas = canvas

	def goto(self, nr):
		global velocity,autorotate	
		clickeditem = self.canvas.find_withtag("pic_" + str(nr))
		tagsofitem= self.canvas.gettags(clickeditem)

		oldcenteritem= self.canvas.find_withtag('center')
		if clickeditem:
			if oldcenteritem: 
				itemtags= self.canvas.gettags(oldcenteritem) 
				self.canvas.itemconfig(oldcenteritem, tags=(itemtags[0], itemtags[1],  itemtags[2], 'pic', 'nocenter' ) )
			itemtags= self.canvas.gettags(clickeditem) 
			self.canvas.itemconfig(clickeditem, tags=(itemtags[0], itemtags[1],  itemtags[2], 'pic', 'center' ) )
			autorotate=True
		
			self.canvas.update_idletasks()
			self.canvas.after(0)
	 	

	def show_gallery(self,canvas, maxdispimages, pathdict):
	 global velocity,xold,maximages,autorotate,centerrec 
	 distance= 10
	 velocity= 0
	 xold=0
	 autorotate=False
	 mydict={}
	 infodict={}
	 CWIDTH = canvas.winfo_reqwidth()
	 CHEIGHT = canvas.winfo_reqheight()
	 PICWIDTH= (CWIDTH-distance)/(maxdispimages) - distance
	 
	 maximages= len(pathdict)
	 
	 
	 CWIDTH=(PICWIDTH+distance)*maxdispimages + distance
	 
	 def forward():
		print "lol"         
	
  	 #TODO
  	 #forward_button=Button(top,width=4,height=2)
	 #forward_button.configure(command=forward)
	 #forward_button.grid(row=0,column=1,sticky=S,columnspan=1)	


	 #set background image
	 #bgim = Image.open("bg.jpg") 
	 #bglineim= Image.open("bgline.jpg") 
	 #bgim = bgim.resize((CWIDTH,CHEIGHT), Image.ANTIALIAS)
	 #bglineim= bglineim.resize((CWIDTH,distance/2), Image.ANTIALIAS)
	 #bgimage = ImageTk.PhotoImage(bgim)
	 #bglineimage= ImageTk.PhotoImage(bglineim)
	 #canvas.create_image(CWIDTH/2,CHEIGHT/2 , image=bgimage)
	 #canvas.create_image(CWIDTH/2, CHEIGHT/2 - PICHEIGHT/2 - distance  , image=bglineimage)
	 #canvas.background=bgimage
	 #canvas.backgroundline=bglineimage
	 #canvas.create_image(CWIDTH/2, CHEIGHT/2 + PICHEIGHT/2 + distance  , image=bglineimage)
	 #canvas.backgroundline2=bglineimage
	 
	 #clipim = Image.open("clip.png") 
	 #clipim = clipim.resize(PICWIDTH,PICHEIGHT)
	 #clipimage = ImageTk.PhotoImage(clipim)
         #clipitem = canvas.create_image(CWIDTH/2,CHEIGHT/2 , image=clipimage)


	 #create label for infos
	
	 #coolline =  canvas.create_line(0,CHEIGHT/2+PICHEIGHT/2, CWIDTH,CHEIGHT/2+PICHEIGHT/2, fill="white", width=2) 


	 for i in range(0,maximages):
	      	im = Image.open(pathdict[i]['path']) 
		imh = float(im.size[1])
		imw= float(im.size[0])
		factor= imh/imw
		PICHEIGHT= int(PICWIDTH*factor)
	      	im = im.resize((PICWIDTH,PICHEIGHT), Image.ANTIALIAS)
	      	mydict[i]= ImageTk.PhotoImage(im)
		infodict[str(i)]= "Text_" + str(i)
	      	mydict["pic_"+ str(i)]=canvas.create_image(distance + PICWIDTH/2 +i*(distance + PICWIDTH), CHEIGHT/2 , image=mydict[i])
	      	setattr(canvas, "pic_"+ str(i), mydict[i]) 
	      	if i < maxdispimages:
			canvas.itemconfig(mydict["pic_"+ str(i)], tags=('visible','pic_' + str(i),str(distance + PICWIDTH/2 +i*(distance + PICWIDTH)), 'pic', 'nocenter') )
	      	else: 
			canvas.itemconfig(mydict["pic_"+ str(i)], tags=('invisible','pic_' + str(i),str(distance + PICWIDTH/2 +i*(distance + PICWIDTH)), 'pic', 'nocenter') )
	 
	 #canvas.create_rectangle(distance, distance, CWIDTH-distance, CHEIGHT-distance, outline="black", width=20, outlinestipple="gray50")		
 	 infolabel = canvas.create_text(CWIDTH/2,CHEIGHT/2 + PICHEIGHT/2 + 3*distance, text="INFO", fill= "white")
	 def doubleclick(event):
		global velocity,autorotate	
		#clickeditem= canvas.find_withtag(CURRENT) TODO: why doesnt that work correctly?
		clickeditem= canvas.find_closest(event.x,event.y)	
		tagsofitem= canvas.gettags(clickeditem)
		oldcenteritem= canvas.find_withtag('center')
		if clickeditem:
			if oldcenteritem: 
				itemtags= canvas.gettags(oldcenteritem) 
				canvas.itemconfig(oldcenteritem, tags=(itemtags[0], itemtags[1],  itemtags[2], 'pic', 'nocenter' ) )
			itemtags= canvas.gettags(clickeditem) 
			if itemtags[3]:
				canvas.itemconfig(clickeditem, tags=(itemtags[0], itemtags[1],  itemtags[2], 'pic', 'center' ) )
				autorotate=True
		
			canvas.update_idletasks()
			canvas.after(0)

	 def movemouse(event):
		global velocity,autorotate
		if not autorotate and event.y < (CHEIGHT/2 + PICWIDTH/2 + distance) : velocity= int(1.1*(event.x-CWIDTH/2)/10)
		elif not autorotate : velocity = 0

	 def rollWheel(event):
		global velocity
		if event.num == 4:
			velocity-=10
		
		elif event.num == 5:
			velocity+=10

	 def stopvel(event):
		global velocity
		if not autorotate: velocity=0 


	 def update_canvas():
		global velocity,maximages,autorotate, centerrec
	 	centeritem = canvas.find_withtag("center")
		visibleitems = canvas.find_withtag("visible")
		invisibleitems = canvas.find_withtag("invisible")
		picitems=canvas.find_withtag("pic")
	
		leftitem=canvas.find_withtag("pic_0")
		rightitem=canvas.find_withtag("pic_" + str(maximages-1))
		leftitemtags=canvas.gettags(leftitem)
		rightitemtags=canvas.gettags(rightitem)

		#canvas.itemconfig(coolline, width=abs(velocity/4))
		if centeritem and autorotate:
			itemtags= canvas.gettags(centeritem) 
			centerrec = canvas.find_withtag("centerrec")
			xpos=  int(itemtags[2])
			velocity= int(1.1*(xpos- CWIDTH/2)/5)
			if velocity == 0 or abs(xpos-CWIDTH/2) < 2 : 
				canvas.itemconfig(centeritem, tags=('visible',itemtags[1],  itemtags[2], 'pic', 'nocenter' ) )	
				canvas.itemconfig(infolabel, text= infodict[ itemtags[1][4:]])
				autorotate=False
				canvas.delete(centerrec)
				#canvas.delete(clipitem)
				#print "stop"
		
			if not centerrec: 
				#canvas.create_image(CWIDTH/2,CHEIGHT/2 , image=clipimage)
	 			#canvas.clipitem=clipimage	
				canvas.create_rectangle(xpos-PICWIDTH/2, CHEIGHT/2-PICHEIGHT/2, xpos+PICWIDTH/2, CHEIGHT/2+PICHEIGHT/2, outline="black", width=2 ,tags=('centerrec') )
			else: canvas.coords(centerrec,xpos-PICWIDTH/2, CHEIGHT/2-PICHEIGHT/2, xpos+PICWIDTH/2, CHEIGHT/2+PICHEIGHT/2)	


		for item in picitems:
		        itemtags= canvas.gettags(item) 
			if (velocity < 0 and int(leftitemtags[2]) < CWIDTH/2) or (velocity > 0 and int(rightitemtags[2]) > CWIDTH/2):
				xnew=int(itemtags[2])-velocity
				canvas.coords(item, xnew, CHEIGHT/2 )	
		     		centertag= "nocenter"
				if itemtags[4] == 'center':  
					centertag= "center"
				if xnew >= CWIDTH-distance or xnew <= distance :
					canvas.itemconfig(item, tags=('invisible',itemtags[1],  str(xnew) ,'pic', centertag) )
	 			else: 
					#if itemtags[0] is "invisible":
					#	curr_index = int(itemtags[1][4:])
					#	newitem=canvas.create_image(xnew, CHEIGHT/2 , image=mydict[ str( contents[curr_index] ) ] )
					canvas.itemconfig(item, tags=('visible',itemtags[1],  str(xnew) , 'pic', centertag) )
				#if (xnew>CWIDTH/2-PICWIDTH) and (xnew<CWIDTH/2+PICWIDTH): canvas.itemconfig(item, tags=(itemtags[0], itemtags[1],  itemtags[2], 'pic', 'center' ) )
	   	canvas.update()
		canvas.after(1,update_canvas)

	 def clickB1(event):
		curritem= canvas.find_closest(event.x,event.y)
		clickedtags=canvas.gettags(curritem)
		if clickedtags[1]: self.cfunc(pathdict[int(clickedtags[1][4:])]['path'].replace("-1.png","-2.png"),pathdict[int(clickedtags[1][4:])]['tag'])
		doubleclick(event)
	 
	 def key(event):
		print "taste"
	 
	 #canvas.bind("<Double-Button-1>", doubleclick)
	 canvas.bind("<B1-Motion>", movemouse )
	 canvas.bind("<ButtonRelease>", stopvel)
	 canvas.bind('<Button-4>', rollWheel)
	 canvas.bind('<Button-5>', rollWheel)
	 canvas.bind('<Double-Button-1>', clickB1)
	 canvas.bind('<Key>', key)


	 canvas.after_idle(update_canvas) 
