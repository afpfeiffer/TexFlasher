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


global saveString 
global Settings 
global Main


import os
from difflib import get_close_matches
import itertools, collections
import ConfigParser

import subprocess
import sys
import re
import commands
import xml.dom.minidom as xml
from operator import itemgetter
from time import strftime, strptime, ctime, localtime, mktime
from datetime import datetime, timedelta
from math import *
from codecs import open
import webbrowser


from Tkinter import *
import tkMessageBox
import Image, ImageTk
import tkFileDialog
import urllib2




#locals
from tagger import *
from systemInterface import *
from tooltip import *

 


######################################################################## leitner_db management ##############################################


def load_leitner_db(leitner_dir,user):
	if not os.path.isdir(leitner_dir+"/Flashcards"):
		print "No directory named 'Flashcards' found in "+leitner_dir
		sys.exit()
	if not os.path.isdir(leitner_dir+"/Details"):
		print "No directory named 'Details' found in "+leitner_dir
		sys.exit()
	if not os.path.isdir(leitner_dir+"/Users"):
		print "No directory named 'Users' found in "+leitner_dir
		sys.exit()		
	#load old flashcards
	try:
		doc= xml.parse(leitner_dir+"/Users/"+Settings["user"]+".xml")
		old_ldb=doc.getElementsByTagName('ldb')[0]
	except:
		pass
	doc=xml.Document()
	ldb = doc.createElement('ldb')
	#create new flashcard xml
	flashcards_dir=os.listdir(leitner_dir+"/Flashcards")

	for flashcard_file in flashcards_dir:
		if flashcard_file.split(".")[-1]=="dvi":
			flashcard_name=flashcard_file.split(".")[0]
			try: 
				flashcard_element=old_ldb.getElementsByTagName(flashcard_name)[0] #raises if old_ldb does not exist or not found
				ldb.appendChild(flashcard_element)
			except:
				#create new flashcard node
				flashcard_element=doc.createElement(flashcard_name)
				ldb.appendChild(flashcard_element)
				flashcard_element.setAttribute('lastReviewed', "")
				flashcard_element.setAttribute('level',"0")
				flashcard_element.setAttribute('levelHistory',"0_("+strftime("%Y-%m-%d %H:%M:%S", localtime())+")")
				flashcard_element.setAttribute('created',strftime("%Y-%m-%d %H:%M:%S", localtime()))
	xml_file = open(leitner_dir+"/Users/"+Settings["user"]+".xml", "w","utf-8")
	ldb.writexml(xml_file)
	xml_file.close()
	return ldb

def brainPowerExponent(filepath,level):
	if( level > 2 ):
		b=bpe(filepath)
		return int(pow(int(level),b))
	elif level>=0:
		return level
	else: 
		return 200000	
	
	
	

def futureCardNumber(ldir, database, offset, offset2, maxLevel ):
	LEVELS=[]
	
	for i in range(-1,maxLevel+1):
		LEVELS.append(0)
	number=0
	seconds_in_a_day = 60 * 60 * 24
	for elem in database.childNodes:
		name=elem.tagName
		lastReviewed=elem.getAttribute('lastReviewed')
		if lastReviewed!="":
			lastReviewed_time=datetime(*(strptime(lastReviewed, "%Y-%m-%d %H:%M:%S")[0:6]))
		        level=int(elem.getAttribute('level'))

			newLevel = brainPowerExponent(ldir,level)
			dt_1 = lastReviewed_time + timedelta(days=(newLevel - (offset + offset2)))		
			dt_2 = lastReviewed_time + timedelta(days=(newLevel - offset))		
		
			if (datetime.now() + timedelta(hours=int(24 - datetime.now().hour + RESTART_TIME)) < dt_1):
				if datetime.now() + timedelta(hours=int(24 - datetime.now().hour + RESTART_TIME)) >= dt_2:
					number += 1
					LEVELS[level] +=1
		elif int(elem.getAttribute('level'))>=0:
			if offset == 0:
				number += 1	
				LEVELS[int(elem.getAttribute('level'))] += 1
	return number, list(LEVELS)



def load_agenda(ldb,dir,now=datetime.now(),PageSort=True):
	local_agenda={}
	flashcards=ldb.childNodes
	seconds_in_a_day = 60 * 60 * 24
	new_fc={}
	try:
		order = xml.parse(dir+"/Flashcards/order.xml")
		for elem in flashcards:
			name=elem.tagName
			lastReviewed=elem.getAttribute('lastReviewed')
			if lastReviewed=="":
				if not int(elem.getAttribute('level'))<0:
				  place=int(order.getElementsByTagName(elem.tagName)[0].getAttribute("position"))
				  new_fc[elem.tagName]=place
			else:
				lastReviewed_time=datetime(*(strptime(lastReviewed, "%Y-%m-%d %H:%M:%S")[0:6]))
				level=int(elem.getAttribute('level'))
					
				newLevel = brainPowerExponent(dir,level)

				if level>=0:
					dt = lastReviewed_time + timedelta(days=newLevel)		
					if now + timedelta(hours=int(24 - now.hour + RESTART_TIME))>=dt:
					    diff=now-dt
					    local_agenda[elem.tagName]=diff.days * seconds_in_a_day + diff.seconds
	except:
		pass
	if PageSort:
		for elem in local_agenda:
				place=int(order.getElementsByTagName(elem)[0].getAttribute("position"))
				local_agenda[elem]=place				

	sorted_agenda = sorted(local_agenda.iteritems(), key=itemgetter(1))
	if not PageSort:
		sorted_agenda.reverse()
	sorted_new=sorted(new_fc.iteritems(), key=itemgetter(1))
	return sorted_agenda+sorted_new,sorted_new


def update_flashcard(fc_tag,ldb,selected_dir,attr_name,attr_value,lastReviewed=strftime("%Y-%m-%d %H:%M:%S", localtime()),ask=False):
	update=True
	flashcard_element=ldb.getElementsByTagName(fc_tag)[0]
	try:
		if ask and attr_name=="Level":
			update=False
			if tkMessageBox.askyesno("Reset", "Do you really want to reset the learning progress for this flashcard?"):
				update=True				
		if update==True and attr_name=="Level":
			flashcard_element.setAttribute('lastReviewed',lastReviewed)
			flashcard_element.setAttribute('level', str(attr_value))
			flashcard_element.setAttribute('levelHistory', flashcard_element.getAttribute('levelHistory')+str(attr_value)+"_("+strftime("%Y-%m-%d %H:%M:%S", localtime())+")" )
		elif update==True:
			flashcard_element.setAttribute(attr_name, str(attr_value))
	
		if update==True:
			xml_file = open(selected_dir+"/Users/"+Settings["user"]+".xml", "w","utf-8")
			ldb.writexml(xml_file)
			xml_file.close()
	except:
		print "Error while updating "+fc_tag+" attribute "+attr_name+" to "+str(attr_value)

		
def set_fc_attribute(fc_tag,fc_dir,attr_name,attr_value,ldb=False):
  if str(attr_value)=="-1":
  	text="Do you really want to hide this flashcard?"
  else:
  	text="Do you really want to unhide this flashcard?"
  if tkMessageBox.askyesno("Hide", text):  
    if not ldb:
	ldb=load_leitner_db(fc_dir,Settings['user'])
    flashcard_element=ldb.getElementsByTagName(fc_tag)[0]
    flashcard_element.setAttribute(str(attr_name), str(attr_value))
    xml_file = open(fc_dir+"/Users/"+Settings["user"]+".xml", "w","utf-8")
    ldb.writexml(xml_file)
    xml_file.close()
    
		
		
def get_all_fcs(path=False):
	all_fcs = []
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('FlashFolder')
		for elem in config_xml:
			if path and path==os.path.dirname(elem.getAttribute('filename')):			
				dir=os.path.dirname(elem.getAttribute('filename'))
				try:
					tree = xml.parse(dir+"/Users/"+Settings["user"]+".xml")
					dir_xml = tree.getElementsByTagName('ldb')[0].childNodes
					for fc_elem in dir_xml:
						all_fcs.append({"tag":fc_elem.tagName,"dir":dir,"level":fc_elem.getAttribute('level')}) # add atributes as needed
				except:
					pass
			elif not path and not elem.getAttribute('filename')=="":
				dir=os.path.dirname(elem.getAttribute('filename'))
				try:
					tree = xml.parse(dir+"/Users/"+Settings["user"]+".xml")
					dir_xml = tree.getElementsByTagName('ldb')[0].childNodes
					for fc_elem in dir_xml:
						all_fcs.append({"tag":fc_elem.tagName,"dir":dir,"level":fc_elem.getAttribute('level')}) # add atributes as
				except:
					pass
	return all_fcs	


	
	
	

################################################ Statistics ################################################################


def statistics_nextWeek(ldir):
		#checkForUpdate(Settings["user"])
		database = load_leitner_db(ldir, Settings["user"])
		DAYS=[]
		LEVELS=[]
		DATASET=[]

		flashcards = database.childNodes
		maxLevel = -1
		cards = 0.0 
		for card in flashcards:
			maxLevel = max( maxLevel, int( card.getAttribute('level') ) )
			cards += 1.0
		
		for i in range(maxLevel+1):
			LEVELS.append(0)
		
			
		for day in range(7):
			number, listOfLevels = futureCardNumber(ldir, database, day , -1 , maxLevel)
			DAYS.append( number )
			DATASET.append( [ number, list(listOfLevels)  ] )
		
		#print DATASET
		# fix for day=0
		number1, listOfLevels1 = futureCardNumber(ldir, database, 0, -1000000, maxLevel )
		DAYS[0] = number1
		DATASET[0] = [number1, list(listOfLevels1)]
		
		# TODO look into this once more
		for card in flashcards:
			LEVELS[int( card.getAttribute('level'))] += 1.0/cards
		
		
		graph_points(database, DATASET, LEVELS, cards ,ldir)
		
		

def dayToday():
    now = datetime.now()
    
    d = now.day
    m = now.month
    y = now.year
    
    if m < 3:
        z = y-1
    else:
        z = y
    dayofweek = ( 23*m//9 + d + 4 + y + z//4 - z//100 + z//400 )
    if m >= 3:
        dayofweek -= 2
    dayofweek = dayofweek%7
    return dayofweek-1
		
#def getColor( i, maxLevel ):
	#if i > 3:
		#if( (maxLevel - 5) <= 0 ):
			#n = 1
		#else:
			#n = log(maxLevel - 5)
		#i = int(round( pow(float(i), n ) + 2, 0))
	#COLORS = "yellow", "orange red",  "darkgreen", "indian red", "light sea green", "orange", "RoyalBlue1",  "lightblue"
	#if i == 0:
		#return COLORS[0]
	#else:
		#pos = i
		#while( pos+1> len(COLORS)):
			#pos -= len(COLORS)
		#return COLORS[pos]

#def getColor( i, maxLevel ):
	#COLORS = "yellow", "orange red",  "darkgreen", "indian red", "light sea green", "orange", "RoyalBlue1",  "lightblue"
	#if i <= 3:
		#return COLORS[i]
	#elif i <= 5:
		#return COLORS[4]
	#elif i <= 9:
		#return COLORS[5]
	#else:
		#return COLORS[6]
		
def getColor( i, maxLevel ):
	delim=2
	dl =int( round( (maxLevel-delim)/3.0, 0 ) )
	COLORS = "yellow", "red", "orange red", "#00CC00","#009900", "#006600"
	if i <= delim:
		return COLORS[i], dl
	else:
		if( i-delim <= dl ):
			return COLORS[delim+1], dl
		elif( i-delim <= 2*dl):
			return COLORS[delim+2], dl
		else:
			return COLORS[delim+3], dl
		

def totalCardHistory( ldb, threshold=1 ):
	TH=[]
	TS=[]
	maxLevel=3
	for elem in ldb.childNodes:
		H=cardHistory( elem )
		time = 0
		counter = 0
		pos = 0
		cardValid=True
		while time < H[len(H)-1][0]:
			#if H[pos][1] >= threshold :
				#cardValid=True
				
			if cardValid:
				while len(TS)<=counter:
					TS.append(0)
					TH.append([time, 0])
				
				if H[pos][1] >= threshold :
					TS[counter] = TS[counter] + 1
				TH[counter][1] = TH[counter][1] + H[pos][1]
				maxLevel = max( maxLevel, H[pos][1] )
				
				
			time = time + 86400 #seconds in a day
			counter = counter+1
			if time > H[pos+1][0]:
				pos = pos + 1

		
	for i in range(len(TS)-1):
		if TS[i] > 0:
			TH[i][1] = int(float(TH[i][1])/float(TS[i]))
		else:
			TH[i][1] = 0
			
			
	TH[len(TH)-1][1]=0
	return TH, maxLevel
					
def drawTotalCardHistory( ldb, stat, fontsize ):
	HISTORY, maxLevel =totalCardHistory( ldb )
	drawHistory( HISTORY, stat, fontsize, True, True, maxLevel )					

def cardHistory( flashcard ):
	history_string=flashcard.getAttribute('levelHistory')
	#print history
	history=history_string.split(')')
	HISTORY=[]
	for elem in history:
		if( elem == '' ):
			continue
		#print elem
		part=elem.split('_')
		changeTime = datetime(*(strptime(  part[1].partition('(')[2]  , "%Y-%m-%d %H:%M:%S")[0:6]))
		totalTime = mktime(changeTime.timetuple())+1e-6*changeTime.microsecond
		HISTORY.append( [ totalTime , int(part[0]) ] )
		
	offset=HISTORY[0][0]
	for elem in HISTORY:
			elem[0] = (elem[0] - offset)

	t_end=mktime(datetime.now().timetuple())+1e-6*datetime.now().microsecond
	HISTORY.append([t_end-offset, 0])

	return HISTORY
	

def drawCardHistory( flashcard, stat ):
	HISTORY=cardHistory( flashcard )
	drawHistory( HISTORY, stat, Main.f_normal )
	
def drawHistory( HISTORY, stat, fontsize,  verbose=True, alwaysOnTop=False, maxLevel = 3 ):
	height = stat.height
	width = stat.width
	
	
	if alwaysOnTop:
		height -= 20

	maxVal=maxLevel
	for elem in HISTORY:
		maxVal = max( maxVal, elem[1] )
		#print str(elem[0])+": "+str(elem[1])
	#print t_end
	dt_border= 86400- int(fmod(HISTORY[len(HISTORY)-1][0], 86400))
	dx_offset=5
	if not alwaysOnTop:
		HISTORY[len(HISTORY)-1][0]+=dt_border
	if HISTORY[len(HISTORY)-1][0] > 1e-5:
		dt=float(width-1)/(HISTORY[len(HISTORY)-1][0])
	else:
		dt=float(width-1)/(1)
	dx=float(height-2-10-dx_offset)/maxVal
	if alwaysOnTop:
		dx=float(height-2-30-dx_offset)/maxVal
	
	# set backgrund color
	#stat.create_rectangle( 1, 1, width , height -1 )
	H=HISTORY
	
	if not alwaysOnTop:
		time=0
		while time < H[len(H)-1][0] + 86400:
			stat.create_line( 1+time*dt, 5, 1+time*dt, height, fill="grey50" )
			time = time + 86400 #seconds in a day
	
	n_value=-1
	level_n_begin=-1
	level_n_end=-1
	counter=0
	for i in range(len(H)-1):
		#print str(elem[0]*dt/width)+": "+str(elem[1])
		#print H[i][1], maxLevel
		color, foo=getColor( int(H[i][1]), maxVal+1 )
		stat.create_rectangle(2+H[i][0]*dt,height-1-H[i][1]*dx - dx_offset,1+H[i+1][0]*dt, height-1, fill=color, width=2 )
		
		text_offset = 8

		if verbose:
			if n_value<0:
				n_value = H[i][1]
				level_n_begin = H[i][0]
			
			if H[i+1][1] != n_value:
				level_n_end = H[i+1][0]
				text_height = height - 1 - 0.5*( dx_offset+ H[i][1]*dx)
				if H[i][1]*dx < 10 or alwaysOnTop:
					text_height = height - 1 - dx_offset - H[i][1]*dx - text_offset


				if (level_n_end-level_n_begin )*dt >= 10:
					stat.create_text( 1+level_n_begin*dt + 0.5*(level_n_end-level_n_begin )*dt, text_height , text=str(H[i][1]),font=("Helvectica", str(fontsize)))
				level_n_begin=H[i+1][0]
				n_value = H[i+1][1]
				
				
			if alwaysOnTop:
				if (int(fmod(i,10)) == 0) and H[i][0]*dt < width - 50:
					stat.create_line( 1 + H[i][0]*dt, height, 1+ H[i][0]*dt, height+30)
					stat.create_text( 5 + H[i][0]*dt, height + 13, text="day "+ str(i), anchor=W ,font=("Helvectica", str(fontsize )))
			
	
		
def graph_points(ldb, dataSetC, dataSetB, numCards,dir):
    clear_window()
    Main.master.title(Main._title_base+" "+Main._version+" - Statistics")
    
    fontsize=int(float(WIDTH)*0.012)
    DX=WIDTH*0.00125
    DY=HEIGHT*0.001221
    #print DY
    menubar_frame=Frame(Main)
    menubar_frame.grid(row=0,columnspan=7)
    
    menu_button=create_image_button(menubar_frame,"./.TexFlasher/pictures/menu.png",40,40)
    menu_button.configure(text="Menu",command=lambda:menu())
    menu_button.grid(row=0,column=0,sticky=N+W+S+E)

    
    #Balloon = Pmw.Balloon(top)
    #Balloon.bind(menu_button, "Return to Menu") 
    Stats=Frame(Main,border=10)
    Stats.grid(row=3,column=0)
    
    DAYS =[ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun' ]
    tday=dayToday()   
           
    #global c
    c = Canvas(Stats, width=int(float(WIDTH)*0.4999), height=int(HEIGHT*0.5))  
    c.grid(row=0 , column=0, sticky=N+W+E)
    
    ymax=1
    for i in range(len(dataSetC)):
			ymax = max(ymax, dataSetC[i][0])

    D1= 50.0*DX
    D2=(HEIGHT*0.3)
    zero= D1, float(HEIGHT)*0.4
    

    valMax=5
    stepsize = 5
    if( ymax >= 100 ):
			stepsize = 25
    elif (ymax >= 40):
			stepsize = 10
					
    if(ymax%stepsize==0):
				valMax=ymax
    else:
			for i in range(1,stepsize):
				if (ymax+i) % stepsize == 0:
					valMax = (ymax+i)
					break
			
    c.create_rectangle(zero[0], 0.25*zero[1] , int(float(WIDTH)*0.4999), zero[1],width=0,fill="grey85")
			
			
    for i in range(1, 1000):
			c.create_line(zero[0], zero[1] - float(i*stepsize*D2)/float(valMax), int(float(WIDTH)*0.4999), zero[1]-float(i*stepsize*D2)/float(valMax), fill="grey50")
			c.create_line(zero[0]-0.1*D1, zero[1] - float(i*stepsize*D2)/float(valMax), zero[0]+0.1*D1, zero[1]-float(i*stepsize*D2)/float(valMax))
			c.create_text(zero[0]-0.1*D1, zero[1] - float(i*stepsize*D2)/float(valMax), anchor=E, text=str(i*stepsize),font=("Helvectica", str(fontsize + 1)))
			if (ymax <= i*stepsize):
				break
	
    assert(valMax >= 0)

    y_stretch = (HEIGHT*0.3)/valMax
    x_stretch = float(WIDTH)*0.01
    x_width = float(WIDTH)*0.045
    n = len(dataSetC)

    for x in range(len(dataSetC)):
        x0 = x * x_stretch + x * x_width + zero[0] +x_stretch
        y0 = zero[1] - (dataSetC[x][0] * y_stretch )
        x1 = x * x_stretch + x * x_width + x_width +zero[0] +x_stretch
        y1 = zero[1]
        if y1==y0:
					y0 -= 1
					
        c.create_rectangle(x0, y0, x1, y1, fill="Red", width=2)
        lastYpos = y0
        for i in range(len(dataSetC[x][1])):
					color, foo=getColor(i, len(dataSetB))
					if( dataSetC[x][1][i] >= 1 ):					
						c.create_rectangle(x0, lastYpos +dataSetC[x][1][i]*y_stretch  , x1-1, lastYpos, fill=color, width=1, outline="black")
						small_dx=float(WIDTH)*0.015
						small_dy=float(WIDTH)*0.015
						vspace = dataSetC[x][1][i]*y_stretch
						hspace = x1 - x0
						vpos = 2
						hpos = 5
						while vpos+small_dy < vspace:
							while hpos +small_dx < hspace:
								c.create_text( x0+ hpos , lastYpos + vpos, anchor="nw", text="L"+str(i),font=("Helvectica", str(fontsize - 1)), fill=color, activefill="black" )
								hpos += small_dx
							vpos += small_dy
							hpos = 5
							
					lastYpos += dataSetC[x][1][i]*y_stretch
        c.create_rectangle(x0, y0, x1, zero[1], width=2 )
				
        if( dataSetC[x][0] > 0 ):
					if( y1-y0 > 20 ):
						c.create_text(0.5*(x0+x1), y0+2, anchor=N, text=str(dataSetC[x][0]),font=("Helvectica", str(fontsize + 1)))
					else:
						c.create_text(0.5*(x0+x1), y0-2, anchor=S, text=str(dataSetC[x][0]),font=("Helvectica", str(fontsize + 1)))
        daystring = DAYS[(tday+x)%7]
        #if x==0 :
					#daystring="today"
        c.create_text(0.5*(x0+x1), y1+20, text=daystring,font=("Helvectica", str(fontsize+1)))
        
    c.create_text(int(float(WIDTH)*0.25), 20, anchor=S, text="Workload in the next few days:",font=("Helvectica", str(fontsize+4)))
    c.create_line(0, zero[1] , int(float(WIDTH)*0.4999) , zero[1], width=2)
    c.create_line( zero[0], 35  , zero[0], zero[1]+D1 , width=2)
    c.create_line( zero, zero[0]-D1*0.9, zero[1]+D1*0.9)
    c.create_text(1, zero[1]+D1*0.2, anchor=W, text="Cards",font=("Helvectica", str(fontsize + 1)))
    c.create_text(D1*0.45, zero[1]+D1*0.8, anchor=W, text="Day",font=("Helvectica", str(fontsize + 1)))
    
    
    
    
    c1 = Canvas(Stats, width=int(float(WIDTH)*0.47), height=int(HEIGHT*0.5)) 
    c1.grid(row=0 , column=1, sticky=N)

    c1.create_text(int(float(WIDTH)*0.25), 20, anchor=S, text="Level status:",font=("Helvectica", str(fontsize+4)))
   
    WIDTHHEIGHTMIN=min(WIDTH, HEIGHT)
    coords= float(WIDTH)*0.25 - float(WIDTHHEIGHTMIN)*0.15 , float(HEIGHT)*0.25 - float(WIDTHHEIGHTMIN)*0.15 , float(WIDTH)*0.25 + float(WIDTHHEIGHTMIN)*0.15 , float(HEIGHT)*0.25 + float(WIDTHHEIGHTMIN)*0.15

    center = 0.5 *(coords[0] +coords[2]), 0.5*(coords[1]+coords[3])

    counter = 0
    initialvalue=0.0
    pie_data=[center,dir]
    sectors=[[0,0]]
    for l in range( len( dataSetB )):
			if(l>0):
				w0 = frac(dataSetB[l-1])
			else:
				w0 = initialvalue			
			w1 = frac(dataSetB[l] - 1e-10)
			initialvalue+=w0
			#print "color = "+getColor(counter)
			color, foo = getColor(counter, len(dataSetB))
			c1.create_arc( coords , fill=color, start=initialvalue, extent=w1, width=2 ,activewidth=3 )
			#c1.create_arc( coords , fill=color, start=initialvalue, extent=w1, width=2 ,activewidth=4, outline="grey50" )
			sectors.append([w1+sectors[-1][0],l])
			#if( int(round(dataSetB[l+1]*numCards,0)) > 0 ):
				#textPos = center[0] + distance*cos(winkel(initialvalue +0.5*w1)), center[1] -  distance*sin(winkel(initialvalue +0.5*w1))
				#c1.create_text( textPos , text="Level "+ str(l+1) + " (" + str(int(round(dataSetB[l+1]*100.0,0))) + "%)")
			
			counter += 1
    pie_data.append(sectors)
				

    distance = 0.6*(coords[2]-coords[0]) 
    initialvalue=0.0
    for l in range( len( dataSetB ) ):
			if(l>0):
				w0 = frac(dataSetB[l-1])
			else:
				w0 = initialvalue
			w1 = frac(dataSetB[l])
			initialvalue+=w0
			if( int(round(dataSetB[l]*numCards,0)) > 0 ):
				textPos = center[0] + distance*cos(winkel(initialvalue +0.5*w1)), center[1] -  distance*sin(winkel(initialvalue +0.5*w1))
				#if l >0 :
				color, foo = getColor(l, len(dataSetB))
				c1.create_text( textPos, text=str(l) + " (" + str(int(round(dataSetB[l]*100.0,0))) + "%)",font=("Helvectica", str(fontsize )), activefill=color )
				#c1.create_text( textPos , text=str(l) ,font=("Helvectica", "12"))
				#else:
					#c1.create_text( textPos , text="N (" + str(int(round(dataSetB[l]*100.0,0))) + "%)",font=("Helvectica", "12"))
       
    c1.bind("<Button-1>",lambda e:show_pie_level(e,pie_data,0.5*(coords[2]-coords[0])))
    #c1.create_text(center[0],470,  text="Ln: Cards on level n,  N: New Cards")
    
    
    Legende=Canvas(Stats, width=int(WIDTH*0.95))
    Legende.grid(row=3 , columnspan=5)


    color, dl = getColor(0, len(dataSetB))
    ybasis = 30*DY
    coord= float(WIDTH)*0.5 -170*DX
    Legende.create_rectangle( coord, ybasis , coord + 20*DX, ybasis +18*DY,width=0, fill=color  )
    Legende.create_text( coord+25*DX, ybasis+9*DY, anchor=W, text = "Level 0 (new)",font=("Helvectica", str(fontsize + 1) ))
    color, dl = getColor(1, len(dataSetB))
    Legende.create_rectangle( coord, ybasis+20*DY, coord + 20*DX, ybasis +38*DY,width=0, fill= color )
    Legende.create_text( coord+25*DX, ybasis+29*DY, anchor=W, text = "Level 1 (bad)" ,font=("Helvectica", str(fontsize + 1)))
    color, dl = getColor(2, len(dataSetB))
    Legende.create_rectangle( coord, ybasis+40*DY, coord + 20*DX, ybasis +58*DY,width=0, fill= color )
    Legende.create_text( coord+25*DX, ybasis+49*DY, anchor=W, text = "Level 2 (improving)",font=("Helvectica", str(fontsize + 1) ))
    #Legende.create_line( 0, ybasis+65 , WIDTH, ybasis+65 )

    if( len(dataSetB)-1 >2 ):
			color, dl = getColor(3, len(dataSetB))
			Legende.create_rectangle( coord+170*DX, ybasis, coord + 190*DX, ybasis+18*DY,width=0, fill= color )
			Legende.create_text( coord+195*DX, ybasis+9*DY, anchor=W, text = "Level 3 - "+str(2+dl)+" (good)",font=("Helvectica", str(fontsize + 1) ))

    if( len(dataSetB)-1 >2+dl ):
			color, dl = getColor(int( 0.5*(len(dataSetB)+3)), len(dataSetB)) 
			Legende.create_rectangle( coord+170*DX, ybasis+20*DY, coord + 190*DX, ybasis+38*DY,width=0, fill= color )
			Legende.create_text( coord+195*DX, ybasis+29*DY, anchor=W, text = "Level "+str(2+dl+1)+" - "+str(2+2*dl)+" (excellent)" ,font=("Helvectica", str(fontsize + 1)))

    if( len(dataSetB)-1 >2+dl*2 ):
			color, dl=getColor(len(dataSetB)-1, len(dataSetB)) 
			Legende.create_rectangle( coord+170*DX, ybasis+40*DY, coord + 190*DX, ybasis+58*DY,width=0, fill= color )
			Legende.create_text( coord+195*DX, ybasis+49*DY, anchor=W, text = "Level "+str(2+2*dl+1)+" - "+str(len(dataSetB)-1)+" (outstanding)" ,font=("Helvectica", str(fontsize + 1)))
    
    stat_height=HEIGHT*0.15
    stat_width=int(float(WIDTH)*0.95)
    stat=Canvas(Stats,width=stat_width, height=stat_height)
    stat.grid(row=2, columnspan=2)
    stat.height=stat_height
    stat.width=stat_width
    Stats.stat=stat
    Stats.stat.create_text( 1, 10*DY, text="Average learning progress:", anchor=W,font=("Helvectica", str(fontsize+4)))
    drawTotalCardHistory( ldb, Stats.stat, fontsize+1 )
    #spacer
    Label(Stats,height=1).grid(row=1,columnspan=5)	#spacer
    #Label(top,height=1).grid(row=0,columnspan=5)
    
    #Legende.create_line( 0, ybasis-25 , WIDTH, ybasis-25, width=2 )

    #mainloop()


def frac(n): return 360. * n


def winkel(w): return float(w)* pi/180.0


def show_pie_level(event,pie_data,radius):
	dir=pie_data[1]	
	center=pie_data[0]
	relX = center[0] - event.x
	relY=center[1]-event.y
	if sqrt(relX*relX+relY*relY)<=radius:
		angle_rad=atan2(relY,relX)
		degree = ((angle_rad + pi) * 180 / pi)
		degree=(degree-360)*(-1)
		for i in range(0,len(pie_data[2])-1):
			if degree<=pie_data[2][i+1][0] and degree>=pie_data[2][i][0]:
				level=pie_data[2][i+1][1]
				break
		all_fcs=get_all_fcs(dir)
		fcs=[]
		for elem in all_fcs:
			if elem['level']==str(level):
				fcs.append(elem)
		display_mult_fcs(fcs,"%s flashcard(s) at level %s in %s"%(str(len(fcs)),str(level),dir.split("/")[-1]))


#################################################################################### Get FC Info

def get_fc_info(dir,tag,ldb=None,source=None):
	if not ldb:
		ldb=load_leitner(dir,Settings["user"])
	if not source:
		source_file= xml.parse(dir+"/Details/source.xml")		
	info={}
	for elem in ldb.childNodes:
		if elem.tagName==tag:
			info["ldb"]=elem	
			break
	for elem in source_file.getElementsByTagName("fc_meta_info")[0].childNodes:
		if elem.tagName==tag:
			info["source"]=elem
			break
	return info
	
def get_fc_desc(fc_dir,tag,tex_file=False,xml_file=False):

	if not tex_file:	
		try:
			tex_file_path=get_flashfolder_path(fc_dir)
			tex_file=open(tex_file_path,"r", "utf-8")
		except:
			print "Fatal Error: Cannot open file: "+tex_file_path+"!"
			sys.exit()
	else:
		tex_file.seek(0, 0)	
	if not xml_file:
		xml_file= xml.parse(fc_dir+"/Flashcards/order.xml")

	fc_elem=xml_file.getElementsByTagName(tag)[0]
	title=fc_elem.getAttribute('name')
	theorem_name=fc_elem.getAttribute('theorem_name')
	theorem_type=fc_elem.getAttribute('theorem_type')

	content_=False
	tag_=False
	content=""	
	for l in tex_file:
		if content_ and re.compile("^\\\\end\{"+theorem_type+"\}").findall(l.lstrip()):
			content_=False
			tag_=False
			break
		if tag_ and content_:
			content+=l
		if not tag_ and re.compile("^\\\\fc\{"+tag+"\}").findall(l.lstrip()):
			tag_=True
		if tag_ and re.compile("^\\\\begin\{"+theorem_type+"\}").findall(l.lstrip()):			
			content_=True

	
	#print title,theorem_name,theorem_type,content
	return title,theorem_name,theorem_type,content
	
def get_fc_section(dir,tag,source):	
	section_string=""
	elem=source.getElementsByTagName(tag)[0]
	for attr in elem.attributes.keys():
		if re.compile('name').findall(attr) and not elem.getAttribute(attr)=="None":
			section_string+=elem.getAttribute(attr)+" "
	return section_string
	
	
############################################################### Search ###########################################
tkinter_umlauts=['odiaeresis', 'adiaeresis', 'udiaeresis', 'Odiaeresis', 'Adiaeresis', 'Udiaeresis', 'ssharp']
#http://tkinter.unpythonic.net/wiki/AutocompleteEntry

def create_hash(string):
  chars={"-":"z","0":"a","1":"b","2":"c","3":"d","4":"e","5":"f","6":"g","7":"h","8":"i","9":"j"}
  newhash=""
  for n in str(hash(string)):
    newhash+=chars[n]
  return newhash


class create_index:
	def __init__(self):  
		self.min_word_len=4
		self.front_index={}
		self.completion_list={}	
	
	def replace_uml(self,string):
		return string.replace("ö","oe").replace("ä","ae").replace("ü","ue").replace("ß","ss")
	
	def create(self):
		self.front_index={}
		current_dir=""
		#back_index={}
		all_fcs=get_all_fcs()
		for fc_elem in all_fcs:
				if not fc_elem['dir']==current_dir: #load files needed for get_... funktions to speed up search
					current_dir=fc_elem['dir']
					current_source_xml=xml.parse(fc_elem['dir']+"/Details/source.xml")
					tex_file_path=get_flashfolder_path(fc_elem['dir'])
					current_tex_file=open(tex_file_path,"r", "utf-8")
					current_order_xml=xml.parse(fc_elem['dir']+"/Flashcards/order.xml")
				try:	
				
				  fc_name=current_order_xml.getElementsByTagName(fc_elem['tag'])[0].getAttribute('name')	
				  theorem_name=current_order_xml.getElementsByTagName(fc_elem['tag'])[0].getAttribute('theorem_name')	
				  try:			
				    fc_content=open(fc_elem['dir']+"/Flashcards/"+fc_elem['tag']+".detex","r","utf-8").read()				
				  except:
				    os.system("detex "+fc_elem['dir']+"/Flashcards/"+fc_elem['tag']+".tex > "+fc_elem['dir']+"/Flashcards/"+fc_elem['tag']+".detex")	
				  fc_content=open(fc_elem['dir']+"/Flashcards/"+fc_elem['tag']+".detex","r","utf-8").read()
													
				  fc_sections=get_fc_section(fc_elem['dir'],fc_elem['tag'],current_source_xml)				
				  fc_elem['query']={"front":fc_name+" "+theorem_name+" "+fc_elem['tag']+" "+fc_sections+" "+fc_content,"content":""}
					
				  for w in re.sub("[\W\d]", " ", fc_elem['query']['front'].lower().strip()).split(" "):
						if len(w)>=self.min_word_len:
							try:
								if fc_elem['tag']+"###"+fc_elem['dir'] not in self.front_index[w]:
									self.front_index[w].append(fc_elem['tag']+"###"+fc_elem['dir'])
							except:
								self.front_index[w]=[fc_elem['tag']+"###"+fc_elem['dir']]
				except:
				    if Settings['user']=="can":
					print fc_elem['tag']
		if len(self.front_index)>0:# or len(back_index)>0:				
			  doc=xml.Document()
			  index = doc.createElement('index')
			  front=doc.createElement('front')
			  index.appendChild(front)
			
			  for w in self.front_index:
			    elem=doc.createElement(create_hash(w))
			    front.appendChild(elem)
			    elem.setAttribute("key",w)
			    fcs=""
			    for fc in self.front_index[w]:
			      fcs+=fc+"|||"
			    elem.setAttribute("fcs",fcs)			  
			  xml_file = open(".TexFlasher/search_words_detex.xml", "w","utf-8")
			  index.writexml(xml_file)
			  xml_file.close()
		self.completion_list=tuple(sorted(self.front_index.keys()))  
	      
		return self.front_index#,back_index
		
	def load(self):
		self.front_index={}
		try:
		  doc= xml.parse(".TexFlasher/search_words_detex.xml")
		  for fcs in doc.getElementsByTagName('front')[0].childNodes:
		      self.front_index[fcs.getAttribute('key')]=fcs.getAttribute('fcs').split('|||')[:-1]			
		except:
		  self.create()
		self.completion_list=tuple(sorted(self.front_index.keys()))  
		return self.front_index



class Search(Entry):
        """
        Subclass of Tkinter.Entry that features autocompletion.
        
        To enable autocompletion use set_completion_list(list) to define 
        a list of possible strings to hit.
        To cycle through hits use down and up arrow keys.
        """ 
        def clear_search(self,event):
		self._def_value.set("")
		c_height=p2c(Main.winfo_width(),Main.winfo_height(),[2,2])[0]
		self.configure(font=("Sans",int(c_height)),fg="black",textvariable=self._def_value)
        
        def __init__( self, parent, **options ):
        	Entry.__init__( self, parent, **options )
        	self._def_value=StringVar()
        	c_height=p2c(Main.winfo_width(),Main.winfo_height(),[2,2])[0]
		self.configure(highlightthickness=0,font=("Sans",Main.f_large,"bold"),textvariable=self._def_value,bd =5,bg=None,fg="gray",justify=CENTER)
		self.bind("<Button-1>", self.clear_search)
		self._def_value.set("Search ...")    
		self._hits = []
		self._hit_index = 0
		self.position = 0
		self.bind('<KeyRelease>', self.handle_keyrelease)		  	
		self._completion_list = Indexer.completion_list   
		self.thresh=0.7
		
        def autocomplete(self, delta=0):
	    """autocomplete the Entry, delta may be 0/1/-1 to cycle through possible hits"""
	    if delta: # need to delete selection otherwise we would fix the current position
                        self.delete(self.position, Tkinter.END)
	    else: # set position to end so selection starts where textentry ended
                        self.position = len(self.get())
	    if not self._hits or not self._hits[0].startswith(self.get()):
                        
                # collect hits
                _hits = []
                
                for element in self._completion_list:
                        if element.startswith(self.get().split(" ")[-1].lower()):
                                _hits.append(element)


                # if we have a new hit list, keep this in mind
                if _hits != self._hits:
                        self._hit_index =0
                        self._hits=_hits
                # only allow cycling if we are in a known hit list
                if _hits == self._hits and self._hits:
                        self._hit_index = (self._hit_index + delta) % len(self._hits)
                # now finally perform the auto completion
            
	      
            if len(self._hits)==1:
                        self.config(fg="green")            
                        self.delete( len(self.get())-len(self.get().split(" ")[-1]),END)
                        self.insert( len(self.get())-len(self.get().split(" ")[-1]),self._hits[self._hit_index])
                        self.select_range(self.position,END)
            if len(self._hits)>1:
                        self.config(fg="green")
            if len(self._hits)==0:
                        self.config(fg="black")                                    		
                        

						           
        def search_flashcard(self):
		search_query=self.get()
		self._def_value.set("searching, please wait...") 
		self.configure(fg="gray")
		
		self.update()
		# set similarity sensitivity

		current_source_xml=None
		current_tex_file=None
		current_order_xml=None
		if len(search_query)>0 and not search_query=="Search ...":
			front_all=set([])
			back_all=set([])
			results=[]
			for w in search_query.lower().replace("-"," ").strip().split():
			      front_results=set([])
			      #back_results=set([])
			      front_matches=[]

			      front_matches+=get_close_matches(w,Indexer.front_index.keys(),cutoff=self.thresh)
			      for key in front_matches:
					if len(front_results)>0:
						front_results=front_results.union(set(Indexer.front_index[key]))					
					else:
						front_results=set(Indexer.front_index[key])						
			      if len(front_all)>0:
					front_all=front_all.intersection(front_results)
			      else:
					front_all=front_results					
			search_results=list(front_all)
						
			for fc in search_results:
				results.append({"tag":fc.split("###")[0],"dir":fc.split("###")[1]})				
			## display search results
			if len(results)>0:
				display_mult_fcs(results,"Search results for \""+search_query+"\"")
			else:
				self.delete(0,END)
				self.insert(0,"Nothing found!" )
				self.bind("<Button-1>", self.clear_search)


	
        def handle_keyrelease(self, event):      	
                """event handler for the keyrelease event on this widget"""
                if event.keysym == "BackSpace":
                        self.delete(self.index(INSERT), END) 
                        self.position = self.index(END)
                
                if event.keysym == "Left":
                        if self.position < self.index(END): # delete the selection
                                self.delete(self.position, END)
                        else:
                                self.position = self.position-1 # delete one character
                                self.delete(self.position, END)
                if event.keysym == "Right":
                        self.position = self.index(END) # go to end (no selection)
                if event.keysym == "Down":
                        self.autocomplete(1) # cycle to next hit
                if event.keysym == "Up":
                        self.autocomplete(-1) # cycle to previous hit
                # perform normal autocomplete if event is a single key or an umlaut
                if len(event.keysym) == 1 or event.keysym in tkinter_umlauts:
                        self.autocomplete()
                if event.keysym == "Return":
                		self.search_flashcard()
                			 
############################################################### display flashcards ###########################################################	

class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)		
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"

# TODO Alter schwede, size=BOOL(>1) (=true) size>1 oder was?
class ImageKeeper:  
	def __init__(self):
	  self.images={}	  
	def add_image(self,path,width=None,height=None):
	  image = Image.open(path)
	  im_width,im_height=image.size

	  if width and height:
	    image = image.resize((int(width), int(height)), Image.ANTIALIAS)
	    self.images[path+"X"+str(width)+"Y"+str(height)]=ImageTk.PhotoImage(image)
	  else:
	    if width:
	    	height=int(width*1/(im_width/float(im_height)))
	    	image = image.resize((int(width), int(height)), Image.ANTIALIAS)
	    	self.images[path+"X"+str(width)+"Y"+str(height)]=ImageTk.PhotoImage(image)
	    elif height:
	    	width=int(height*1/(im_height/float(im_width)))
	    	image = image.resize((int(width), int(height)), Image.ANTIALIAS)
	    	self.images[path+"X"+str(width)+"Y"+str(height)]=ImageTk.PhotoImage(image)
	    else:	    	    	
	    	self.images[path]=ImageTk.PhotoImage(image)
	  return ImageTk.PhotoImage(image)
	    
	def get_image(self,path,width=None,height=None):
	  if width and height and self.images.get(path+"X"+str(width)+"Y"+str(height), False):
	    return self.images[path+"X"+str(width)+"Y"+str(height)]
	  elif self.images.get(path, False):
	    return self.images[path]
	  else:
	    return self.add_image(path,width,height)
	    
def create_image_button(window,path,width=None,height=None,border=None):	
	button_image = IK.get_image(path,width,height)	
	if border==None:
		button=Button(window,image=button_image,bd=BD)
	else:
		button=Button(window,image=button_image,bd=border)	  
	button.img=button_image
	button.grid()
	return button


class display_multiple:
	def __init__( self, fcs, title,folders ):
		Frame.__init__( self)
		self.fcs=fcs
		self.title=title
		self.folders=folders
		self.images_per_row=3
		self.fcs_size=Main.winfo_width()/len(self.images_per_row)-40
		self.current_row=0
		self.current_column=0
		self.diffs=[]

		Main.master.title(Main._title_base+" "+Main._version+" - "+title)
		menu_button=create_image_button(Main,".TexFlasher/pictures/menu.png",None,Main.b_normal)
		menu_button.configure(command=lambda:menu())
		menu_button.grid(row=1,columnspan=5,sticky=N+W+E+S)
		
		scrollframe=Frame(self)
		scrollframe.grid(row=3,column=0)	
		vscrollbar = AutoScrollbar(scrollframe)
		vscrollbar.grid(row=2, column=2, sticky=N+S)	
		self.search_canvas = Canvas(scrollframe,yscrollcommand=vscrollbar.set)
		self.search_canvas.grid(row=2, column=0, sticky=N+S+E+W)
		vscrollbar.config(command=self.search_canvas.yview)	
		self.Search_frame = Frame(self.search_canvas,border=10)
		self.Search_frame.columnconfigure(0, weight=1)
		self.Search_frame.grid(row=0,column=0)
		Label(self.Search_frame,width=1).grid(column=2,rowspan=100)

	def add(self,fc_tag,fc_dir):
		button=create_image_button(self.Search_frame,fc_dir+"/Flashcards/"+fc_tag+"-1.png",self.fcs_size,int(self.fcs_size*0.6))
		button.grid(row=self.current_row,column=self.current_column)
		button.bind("<Button-1>", lambda event, data=res:disp_single_fc(fc_dir+"/Flashcards/"+fc_tag+"-2.png",fc_tag,fc_tag+' in '+fc_dir.split("/")[-1]))			
		button.bind('<Button-4>', lambda event: self.search_canvas.yview_scroll(-1, UNITS))
		button.bind('<Button-5>', lambda event: self.search_canvas.yview_scroll(1, UNITS))
		button.bind('<Enter>',lambda event: show_backside(button,fc_tag,fc_dir+"/Flashcards/"+fc_tag+"-2.png",self.fcs_size,int(self.fcs_size*0.6)))
		button.bind('<Leave>',lambda event: show_backside(button,fcs_tag,fcs_dir+"/Flashcards/"+fcs_tag+"-1.png",self.fcs_size,int(self.fcs_size*0.6)))
		if os.path.isfile(fc_dir+"/Diffs/Flashcards/diff_"+fc_tag+"-1.png"):
			diff={}
			diff['tag']="diff_"+fc_tag
			diff['dir']=fc_dir+"/Diffs"
			self.diffs.append(diff)	
		Label(self.Search_frame,height=1).grid(row=self.current_row,column=self.current_column)
		setattr(self.search_canvas,fc_tag+fc_dir,button.img)
		Search_frame.update()	


	
def display_mult_fcs(fcs,title,folders=None): #Syntax: fcs=[{"tag":fc_tag,"dir":fc_dir, ...]
	clear_window()
	Main.master.title(Main._title_base+" "+Main._version+" - "+title)
	toolbar=Frame(Main)
	toolbar.grid(row=1,column=0)
	menu_button=create_image_button(toolbar,".TexFlasher/pictures/menu.png",None,Main.b_normal)
	menu_button.configure(command=lambda:menu())
	
	menu_button.grid(row=0,column=0)
	query=Search(toolbar)
	query.grid(row=0,column=1,sticky=E+W+N+S)	
	
	scrollframe=Frame(Main)
	scrollframe.grid(row=3,column=0)
	
	vscrollbar = AutoScrollbar(scrollframe,bg="red")
	vscrollbar.grid(row=2, column=2, sticky=N+S)
	
	search_canvas = Canvas(scrollframe,yscrollcommand=vscrollbar.set)
	search_canvas.grid(row=2, column=0, sticky=N+S+E+W)
	vscrollbar.config(command=search_canvas.yview)
	
	Search_frame = Frame(search_canvas,border=10)
	Search_frame.columnconfigure(0, weight=1)
	Search_frame.grid(row=0,column=0)
	Label(Search_frame,width=1).grid(column=2,rowspan=100)
	i=0 #start at row
	if not folders:
	  folders={}
	  for elem in fcs:
	    try:
	      folders[elem['dir']]['count']+=1
	      folders[elem['dir']]['fcs'].append(elem)
	    except:
	      folders[elem['dir']]={"count":1,"fcs":[elem],"dir":elem['dir']}

	buttons_frame=Frame(Main)
	buttons_frame.grid(row=0)
	Label(buttons_frame,font=("Sans",Main.f_normal,"bold"),text="Found "+str(len(fcs))+":").grid(row=0,column=0)
	diff_b=Button(buttons_frame,bd=0,font=("Sans",Main.f_normal),text="loading Diff(s)")
	diff_b.grid(row=0,column=1)	
	i=2
	for Dir in folders:
	    b=Button(buttons_frame,bd=0,font=("Sans",Main.f_normal),text=str(folders[Dir]['count'])+" in "+Dir.split("/")[-1],command=lambda data=folders[Dir]:display_mult_fcs(data["fcs"],title,folders))
	    b.grid(row=0,column=i)
	    i+=1
	iterator=fcs.__iter__()
	images_row=[1,3] # increaese number of images per row by adding [1,3,6,9, ...]
	size=Main.winfo_width()/len(images_row)-40
	search_canvas.create_window(0, 0, anchor=NW, window=Search_frame)
	Search_frame.bind('<Button-4>', lambda event: search_canvas.yview_scroll(-1, UNITS))
	Search_frame.bind('<Button-5>', lambda event: search_canvas.yview_scroll(1, UNITS)) 			
	search_canvas.bind('<Button-4>', lambda event: event.widget.yview_scroll(-1, UNITS))
	search_canvas.bind('<Button-5>', lambda event: event.widget.yview_scroll(1, UNITS)) 
	Search_frame.update()
	#local function to display backside of fc on mouseover
	def show_backside(button,tag,path,width=None,height=None):
		back=IK.get_image(path,width,height)
		button.config(image=back)
		button.img=back
	diffs=[]
	for res in iterator:
		for colu in images_row:
			if colu>images_row[0]:
				try:
					res=iterator.next()
				except:
					break
			button=create_image_button(Search_frame,res['dir']+"/Flashcards/"+res['tag']+"-1.png",size,int(size*0.6))
			button.grid(row=str(i+1),column=colu)
			button.bind("<Button-1>", lambda event, data=res:disp_single_fc(data['dir']+"/Flashcards/"+data['tag']+"-2.png",data['tag'],data['tag']+' in '+data['dir'].split("/")[-1]))			
			button.bind('<Button-4>', lambda event: search_canvas.yview_scroll(-1, UNITS))
			button.bind('<Button-5>', lambda event: search_canvas.yview_scroll(1, UNITS))
			button.bind('<Enter>',lambda event,data=res,b=button: show_backside(b,data['tag'],data['dir']+"/Flashcards/"+data['tag']+"-2.png",size,int(size*0.6)))
			button.bind('<Leave>',lambda event,data=res,b=button: show_backside(b,data['tag'],data['dir']+"/Flashcards/"+data['tag']+"-1.png",size,int(size*0.6)))
			if os.path.isfile(res['dir']+"/Diffs/Flashcards/diff_"+res['tag']+"-1.png"):
			  diff=dict(res)
			  diff['tag']="diff_"+diff['tag']
			  diff['dir']=diff['dir']+"/Diffs"
			  diffs.append(diff)
			  
			dist=Label(Search_frame,height=1).grid(row=str(i+2),column=colu)
			setattr(search_canvas,res['tag']+res['dir'],button.img)
			Search_frame.update()
		i+=3
		Search_frame.update()
		search_canvas.config(scrollregion=search_canvas.bbox("all"),width=Main.winfo_width()-40,height=Main.winfo_height()-80)

	if len(diffs)>0:
	  diff_b.config(text=str(len(diffs))+" Diff(s)",command=lambda:display_mult_fcs(diffs,"Diff(s): "+title))
	else:
	  diff_b.grid_forget()
	vscrollbar.config(bg="grey")
def  disp_single_fc(image_path,tag,title=None):
	# create child window
	win = Toplevel()
	# display message
	win.title(title)
	win.iconbitmap(iconbitmapLocation)
	win.iconmask(iconbitmapLocation)

	c=Canvas(win,width=WIDTH,height=WIDTH*0.6)
	c.grid(row=3,rowspan=5,columnspan=4)
	image = Image.open(image_path)
	image = image.resize((WIDTH, int(WIDTH*0.6)), Image.ANTIALIAS)
	flashcard = ImageTk.PhotoImage(image)
	c.create_image(int(WIDTH/2), int(WIDTH*0.3), image=flashcard)	
	c.img=flashcard
	
	if not tag.startswith("diff_"):
	  menubar=Frame(win)
	  menubar.grid(row=1,columnspan=10)
	  
	  edit_b=create_image_button(menubar,"./.TexFlasher/pictures/latex.png",None,Main.b_normal)
	  edit_b.grid(row=0,column=1,sticky=N+E+W+S)
	  edit_b.configure(state=NORMAL,command=lambda:edit_fc(c,os.path.dirname(image_path).replace("/Flashcards",""),tag))	  

	  save_b=create_image_button(menubar,".TexFlasher/pictures/upload_now.png",None,Main.b_normal)
	  save_b.config(state=DISABLED)
	  save_b.grid(row=0, column=2,sticky=W+S+E+N)	
	
	  clear_b=create_image_button(menubar,".TexFlasher/pictures/clear.png",None,Main.b_normal)
	  clear_b.configure(state=DISABLED)
	  clear_b.grid(row=0, column=3,sticky=E+S+W+N)		
	
	  back_b=create_image_button(menubar,".TexFlasher/pictures/back.png",None,Main.b_normal)
	  back_b.grid(row=0, column=0,sticky=W+N+E+S)		
	  back_b.config(command=lambda: win.destroy())
	
	  hide_b=create_image_button(menubar,".TexFlasher/pictures/remove.png",None,Main.b_normal)
	  hide_b.configure(state=DISABLED)
	  hide_b.grid(row=0, column=4,sticky=E+S+W+N)
	
	  c.save_b=save_b
	  c.clear_b=clear_b
	  c.edit_b=edit_b	
	  c.back_b=back_b
	  c.hide_b=hide_b
	  
	  create_comment_canvas(c,os.path.dirname(image_path)+"/../",tag,Settings['user'])

	  c.fc_row=3
	  c.tag_buttons=[]
	  tagbar=Frame(win)
	  tagbar.grid(row=3,column=4,rowspan=2,sticky=N+S)
	  q_b=create_image_button(tagbar,".TexFlasher/pictures/question_fix.png",None,Main.b_normal)
	  q_b.grid(row=0)
	  #q_b.grid_remove()
	  c.q_b=q_b
	  w_b=create_image_button(tagbar,".TexFlasher/pictures/watchout_fix.png",None,Main.b_normal)
	  w_b.grid(row=1)
	  #w_b.grid_remove()
	  c.w_b=w_b
	  r_b=create_image_button(tagbar,".TexFlasher/pictures/repeat_fix.png",None,Main.b_normal)

	  r_b.grid(row=2)
	  #r_b.grid_remove()
	  c.r_b=r_b
	  l_b=create_image_button(tagbar,".TexFlasher/pictures/link_fix.png",None,Main.b_normal)

	  l_b.grid(row=3)		    
	  #l_b.grid_remove()
	  c.l_b=l_b

	  wi_b=create_image_button(tagbar,".TexFlasher/pictures/wiki.png",None,Main.b_normal)	

	  wi_b.grid(row=4)		    
	  #l_b.grid_remove()
	  c.wi_b=wi_b	
	
	  c.tag_buttons=[q_b,w_b,r_b,l_b,wi_b]	
	
	  c.l_b.config(command=c.rect.link_tag)
	  c.r_b.config(command=c.rect.repeat_tag)
	  c.w_b.config(command=c.rect.watchout_tag)
	  c.q_b.config(command=c.rect.question_tag)
	  c.wi_b.config(command=c.rect.wiki_tag)
	
	  ldb=load_leitner_db(os.path.dirname(image_path)+"/../",Settings["user"])
	  fc_info=get_fc_info(os.path.dirname(image_path)+"/../",tag,ldb,None)
	  
	  if fc_info["ldb"].getAttribute("level")=="-1":
	    hide_b.config(bg="red",command=lambda:set_fc_attribute(tag,os.path.dirname(image_path)+"/../","level",0,ldb),state=NORMAL)
	  else:
	    hide_b.config(command=lambda:set_fc_attribute(tag,os.path.dirname(image_path)+"/../","level",-1,ldb),state=NORMAL)
	    
	  pagemarker=fc_info["source"].getAttribute("pagemarker")
	  Label(win,text="Page: "+pagemarker+", Created: "+fc_info["ldb"].getAttribute("created"),font=("Sans",Main.f_normal)).grid(row=c.fc_row+5,columnspan=5)
	  stat_height=Main.b_normal
	  stat_width=int(float(WIDTH)*0.95)
	  stat=Canvas(win,width=stat_width, height=stat_height)
	  stat.grid(row=2, columnspan=5)
	  stat.height=stat_height
	  stat.width=stat_width
	  c.stat=stat
	
	  drawCardHistory( ldb.getElementsByTagName(tag)[0], c.stat )



###############################################################  Edit fc ######################################################################

def edit_fc(c,dir,fc_tag):
	c_height=c.winfo_reqheight()
	c_width=c.winfo_reqwidth()

	fc_name,theorem_name,theorem_type,content=get_fc_desc(dir,fc_tag)
	c.edit_b.config(state=DISABLED)
	c.back_b.config(state=DISABLED)
	c.hide_b.config(state=DISABLED)
	try:
	  c.true_b.config(state=DISABLED)
	  c.false_b.config(state=DISABLED)
	except:
	  pass
	frame=Frame(c,height=c_height,width=c_width)	

	frame.rowconfigure( 0, weight = 1 )
	frame.columnconfigure( 0, weight = 1 )	
	frame.grid_propagate(False) 	
	frame.grid()
	
	edit_text=create_textbox(frame) 
	edit_text.config(width=c_height,height=c_width)
	edit_text.insert(INSERT,content)
	edit_text.grid(row=0,column=0)

	c.clear_b.config(state=NORMAL)
	c.save_b.config(state=NORMAL)
	c.save_b.configure(command=lambda:save_edit(c,frame,edit_text,dir,fc_tag,theorem_type))
	c.clear_b.configure(text="Cancel",command=lambda:cancel_edit(c,dir,fc_tag,frame))	
	for tag in c.tag_buttons:
		tag.grid_remove()

def cancel_edit(c,dir,fc_tag,frame):
	c.clear_b.config(state=DISABLED)
	c.save_b.config(state=DISABLED)
	c.edit_b.config(state=NORMAL)
	c.back_b.config(state=NORMAL)
	c.hide_b.config(state=NORMAL)
	
	try:
	  c.true_b.config(state=NORMAL)
	  c.false_b.config(state=NORMAL)
	except:
	  pass	
	c.edit_b.configure(state=NORMAL,command=lambda:edit_fc(c,dir,fc_tag))
	frame.grid_forget()
	for tag in c.tag_buttons:
		tag.grid()	


def change_latex(file_path,fc_tag,content,theorem_type):
	file=open(file_path,"r","utf-8")
	tag=False
	new_latex=[]

	old_fcs=[] #for checking
	new_fcs=[] # -%-

	for line in file:
	    
		if re.compile('^\\\\fc\{(.*?)\}\n').findall(line.lstrip()):
			old_fcs.append(line)
		if re.compile('^\\\\fc\{'+fc_tag+'\}\n').findall(line.lstrip()):	
			tag=True
			new_latex.append(line)
		if re.compile('^\\\\begin\{'+theorem_type+'\}').findall(line.lstrip()) and tag:
			new_latex.append(line+content)
		if re.compile('^\\\\end\{'+theorem_type+'\}').findall(line.lstrip()) and tag:
			tag=False
		if not tag:
			new_latex.append(line)
	file.close()
	for line in new_latex:
		if re.compile('^\\\\fc\{(.*?)\}\n').findall(line.lstrip()):
			new_fcs.append(line)	
	if old_fcs==new_fcs: #check if # of fcs has'nt changed
		new_file=open(file_path,"w", "utf-8")
		for line in new_latex:
			#print line
			new_file.writelines(line)
		new_file.close()
	else:
		print "Error while saving, some cards would have been deleted."	
	

	
	
def save_edit(c,frame,edit_text,dir,fc_tag,theorem_type):
	content=edit_text.get('1.0', END)
	while content[-1]=="\n":
		content=content[:-1]
	content+="\n"#last break needed!so newline at \end{..}
	if os.path.isfile("./.TexFlasher/config.xml"):
			tree = xml.parse("./.TexFlasher/config.xml")
			config_xml = tree.getElementsByTagName('config')[0]
			for elem in config_xml.childNodes:
				if os.path.dirname(elem.getAttribute('filename'))==dir:
					change_latex(elem.getAttribute('filename'),fc_tag,content,theorem_type)				
					executeCommand("bash .TexFlasher/scripts/createFlashcards.sh "+elem.getAttribute('filename'), True)
 					message,window_type=get_log_status(dir)
 					if window_type=="showerror":
						exec('tkMessageBox.'+window_type+'( "Parse LaTex Logfile","%s")'%message)
					else:
						image = Image.open(os.path.dirname(elem.getAttribute('filename'))+"/Flashcards/"+fc_tag+"-2.png")
						image = image.resize((int(c.cget("width")),int(c.cget("height"))), Image.ANTIALIAS)
						flashcard = ImageTk.PhotoImage(image)
	 					c.create_image(int(flashcard.width()/2), int(flashcard.height()/2), image=flashcard,tag="frontside")
	 					c.img=flashcard	
	 					c.tag_lower("frontside","old")
						cancel_edit(c,dir,fc_tag,frame)							
					break
	else:
		tkMessageBox.showerror("Error","Fatal error while saving new content for %s: no config found!"%fc_tag)

	

############################################################### run flasher ###########################################################


class Flasher:
	def agenda_resort(self,sort):
		
		if sort=="pagesort":		
			self.agenda,self.new_cards=load_agenda(self.ldb,self.selected_dir,self.date,True)		
			self.c.sort_b.config(image=self.pagesort_img,command=lambda:self.agenda_resort("datesort"))

		if sort=="datesort":
			self.agenda,self.new_cards=load_agenda(self.ldb,self.selected_dir,self.date,False)		  
			self.c.sort_b.config(image=self.datesort_img,command=lambda:self.agenda_resort("newsort"))	
		
		if sort=="newsort":
			self.agenda,self.new_cards=load_agenda(self.ldb,self.selected_dir,self.date-timedelta(days=1000),True)
			if len(self.agenda)==0:
			    sort="pagesort"
			self.c.sort_b.config(image=self.newsort_img,command=lambda:self.agenda_resort("pagesort"))
			
		if sort=="pagesort":		
			self.agenda,self.new_cards=load_agenda(self.ldb,self.selected_dir,self.date,True)		
			self.c.sort_b.config(image=self.pagesort_img,command=lambda:self.agenda_resort("datesort"))
			
		self.reactAndInit(True , -1)			

		
	def __init__(self,selected_dir,stuffToDo=True):
		global Main

		
		clear_window()#clear main window

		Main.master.title(Main._title_base+" "+Main._version+" - "+selected_dir)
		if( stuffToDo ):
			date = datetime.now()
		else:
			date = datetime.now()+timedelta(days=1000)
		self.date=date
		self.selected_dir=selected_dir
		Main.columnconfigure(0,weight=1)		
		Main.columnconfigure(1,weight=1)
		Main.columnconfigure(2,weight=1)
		Main.columnconfigure(3,weight=1)
		Main.columnconfigure(4,weight=1)
								
		self.ldb=load_leitner_db(self.selected_dir,Settings["user"])
						
		self.agenda,self.new_cards=load_agenda(self.ldb,self.selected_dir, self.date)
		
		
		self.c=Canvas(Main,width=Main.winfo_width(),height=Main.winfo_height()-4*Main.b_large)

		self.c.order = xml.parse(self.selected_dir+"/Flashcards/order.xml")
		self.c.source = xml.parse(self.selected_dir+"/Details/source.xml")

		#spacer
		

	
		# menubar
		self.c.menu_row=1
		menubar_frame=Frame(Main)
		menubar_frame.grid(row=self.c.menu_row,column=0,columnspan=8)
		
		
		back_b=create_image_button(menubar_frame,".TexFlasher/pictures/back.png",None,Main.b_normal)
		back_b.grid(row=0, column=0,sticky=W+E)	
		
		menu_button=create_image_button(menubar_frame,"./.TexFlasher/pictures/menu.png",None,Main.b_normal)
		menu_button.configure(text="Menu",command=lambda:menu())
		menu_button.grid(row=0,column=1,sticky=W+E)
		
		edit_b=create_image_button(menubar_frame,"./.TexFlasher/pictures/latex.png",None,Main.b_normal)
		edit_b.config(state=DISABLED)
		edit_b.grid(row=0,column=4,sticky=W+E)
	
		save_b=create_image_button(menubar_frame,".TexFlasher/pictures/upload_now.png",None,Main.b_normal)
		save_b.config(state=DISABLED)
		save_b.grid(row=0, column=5,sticky=W+E)	
	
		clear_b=create_image_button(menubar_frame,".TexFlasher/pictures/clear.png",None,Main.b_normal)
		clear_b.configure(state=DISABLED)
		clear_b.grid(row=0, column=6,sticky=W+E)	
		
		hide_b=create_image_button(menubar_frame,".TexFlasher/pictures/remove.png",None,Main.b_normal)
		hide_b.configure(state=DISABLED)
		hide_b.grid(row=0, column=7,sticky=W+E)	

		query=Search(menubar_frame)
		query.grid(row=0,column=3,sticky=E+W)
		
		img = IK.get_image(".TexFlasher/pictures/datesort.png",None,Main.b_normal)		
		self.datesort_img=img
		
		img = IK.get_image(".TexFlasher/pictures/pagesort.png",None,Main.b_normal)	
		self.pagesort_img=img

		img = IK.get_image(".TexFlasher/pictures/newsort.png",None,Main.b_normal)	
		self.newsort_img=img		
					
		self.c.sort_b=Button(menubar_frame,image=self.pagesort_img,text="Sort by Pages",bd=BD,command=lambda:self.agenda_resort("datesort"))
		self.c.sort_b.grid(row=0,column=2,sticky=W+E)
		
		
		self.c.save_b=save_b
		self.c.clear_b=clear_b
		self.c.back_b=back_b
		self.c.edit_b=edit_b
		self.c.hide_b=hide_b
		
		#flashcard details
		self.c.fc_det_row=2
		fc_det_left = StringVar()
		fc_det_right = StringVar()
		desc_frame=Frame(Main,width=int(Main.winfo_width()))
		desc_frame.grid(row=self.c.fc_det_row,columnspan=100,sticky=E+W)
		desc_frame.rowconfigure(0,weight=1)
		
		desc_frame.columnconfigure(0,weight=1)
		desc_frame.columnconfigure(1,weight=1)
		
		Label(desc_frame,anchor=W,textvariable=fc_det_left,font=("Sans",Main.f_normal)).grid(row=0,column=0,sticky=W)		
		Label(desc_frame,anchor=E,textvariable=fc_det_right,font=("Sans",Main.f_normal)).grid(row=0, column=1,sticky=E)
		self.c.fc_det_left=fc_det_left
		self.c.fc_det_right=fc_det_right
		
		#stats	
		stat_height=Main.b_normal
		stat_width=int(Main.winfo_width()*0.95)
		stat=Canvas(Main,width=stat_width, height=stat_height)
		stat.grid(row=4, columnspan=5)
		stat.height=stat_height
		stat.width=stat_width
		
		self.c.stat=stat
	
	
		#fc_content
		self.c.fc_row=5
		self.c.grid(row=self.c.fc_row,columnspan=5,sticky=N+E+W+S)
	
	
		#spacer
		#Label(Main,height=1).grid(row=6,columnspan=5)	
	
		#true false
		self.c.true_false_row=8
		
		self.c.brain_true=Label(Main,font=("Sans",Main.f_normal))
		self.c.brain_true.grid(row=self.c.true_false_row-1, column=0)

		self.c.brain_false=Label(Main,font=("Sans",Main.f_normal))
		self.c.brain_false.grid(row=self.c.true_false_row-1, column=4)		
		
		true_b=create_image_button(Main,"./.TexFlasher/pictures/Flashcard_correct.png",None,Main.b_large)
		false_b=create_image_button(Main,"./.TexFlasher/pictures/Flashcard_wrong.png",None,Main.b_large)
		true_b.grid(row=self.c.true_false_row, column=0, sticky=E+W )
		false_b.grid(row=self.c.true_false_row, column=4, sticky=W+E)
		self.c.true_b=true_b
		self.c.false_b=false_b
	
		self.c.tag_buttons=[]
		tagframe=Frame(Main)
		tagframe.grid(row=self.c.true_false_row,column=1,columnspan=3,sticky=E+W)
		tagframe.columnconfigure(0,weight=1)
		tagframe.columnconfigure(1,weight=1)
		tagframe.columnconfigure(2,weight=1)
		tagframe.columnconfigure(3,weight=1)
		tagframe.columnconfigure(4,weight=1)
		
		q_b=create_image_button(tagframe,".TexFlasher/pictures/question_fix.png",None,Main.b_normal,0)
		q_b.grid(column=0)
		q_b.grid_remove()
		self.c.q_b=q_b
		
		w_b=create_image_button(tagframe,".TexFlasher/pictures/watchout_fix.png",None,Main.b_normal,0)
		w_b.grid(column=1)
		w_b.grid_remove()
		self.c.w_b=w_b
		
		r_b=create_image_button(tagframe,".TexFlasher/pictures/repeat_fix.png",None,Main.b_normal,0)
		r_b.grid(column=2)
		r_b.grid_remove()
		self.c.r_b=r_b
		
		l_b=create_image_button(tagframe,".TexFlasher/pictures/link_fix.png",None,Main.b_normal,0)
		l_b.grid(column=3)		    
		l_b.grid_remove()
		self.c.l_b=l_b
		
		wiki_b=create_image_button(tagframe,".TexFlasher/pictures/wiki.png",None,Main.b_normal,0)
		wiki_b.grid(column=4)		    
		wiki_b.grid_remove()
		self.c.wiki_b=wiki_b
				
		

				
		self.c.tag_buttons=[q_b,w_b,r_b,l_b,wiki_b]		
		self.reactAndInit(True , -1)
			
			
	def reactAndInit(self,status, listPosition,update=True):
		#self.c.config(width=WIDTH,height=WIDTH*0.6) #check if window size changed	
		if( listPosition >=0 and update):
			flashcard_name=self.agenda[listPosition][0]
			if status:
				#print "answer correct"
				flashcard=self.ldb.getElementsByTagName(flashcard_name)[0]
				current_level=int(flashcard.getAttribute('level'))
				if current_level == 0:
					update_flashcard(flashcard_name,self.ldb,self.selected_dir,"Level",2)
				else:
					update_flashcard(flashcard_name,self.ldb,self.selected_dir,"Level",current_level+1)
			else:
				#print "answer wrong"
				update_flashcard(flashcard_name,self.ldb,self.selected_dir,"Level",1)
		
		listPosition +=1
		if ( len(self.agenda) > listPosition):
			flashcard_name=self.agenda[listPosition][0]
		else:
			#print "reached end of vector"
			statistics_nextWeek(self.selected_dir)
			#sys.exit()
		for im in self.c.find_withtag("backside"):
		    self.c.delete(im)		
	    
		self.c.stat.delete("all")
		self.c.delete("info_win")		

		image = Image.open(self.selected_dir+"/Flashcards/"+flashcard_name+"-1.png")
		image = image.resize((int(self.c.cget("width")),int(self.c.cget("height"))), Image.ANTIALIAS)
		
		flashcard_image = ImageTk.PhotoImage(image)
		
		self.c.create_image(int(float(self.c.cget("width"))/2), int(float(self.c.cget("height"))/2), image=flashcard_image,tags=("frontside",flashcard_name))
		self.c.img=flashcard_image
		self.c.bind("<Button-1>", lambda e:self.answer(flashcard_name, listPosition))
		self.c.unbind("<Motion>")
		self.c.unbind("<Enter>")
		self.c.edit_b.config(state=DISABLED)
		self.c.save_b.config(state=DISABLED)
		self.c.clear_b.config(state=DISABLED)
		self.c.back_b.config(state=DISABLED)
		self.c.back_b.config(state=DISABLED,command=lambda:self.reactAndInit( True , listPosition-1,False))
		self.c.hide_b.config(state=DISABLED)
		self.c.brain_true.config(text="")
		self.c.brain_false.config(text="")		
		
		self.c.true_b.grid_remove()
		self.c.false_b.grid_remove()

		for tag in self.c.tag_buttons:
			tag.grid_remove()

		flashcardsTodo=len(self.agenda)
		totalNumberCards=len(self.ldb.childNodes)
	
		
		level = self.ldb.getElementsByTagName(flashcard_name)[0].getAttribute('level')
		color, foo = getColor( int(level), 7)
		page=self.c.source.getElementsByTagName(flashcard_name)[0].getAttribute('page') #PAGE IN FC LIST
		pagemarker=self.c.source.getElementsByTagName(flashcard_name)[0].getAttribute('pagemarker') #PAGE IN ORIGINAL
		if pagemarker==None:
			pagemarker="unset"
		fc_pos=int(self.c.order.getElementsByTagName(flashcard_name)[0].getAttribute('position'))
	
		self.c.fc_det_left.set("Flashcards (left / total): "+str(flashcardsTodo-listPosition)+" / "+str(totalNumberCards))	
	   	self.c.fc_det_right.set("Tag: "+flashcard_name+", Nr.: "+str(fc_pos)+", Page: "+str(pagemarker))

	def hide_fc(self, fc_tag):		
		set_fc_attribute(fc_tag,self.selected_dir,"level",-1,self.ldb)	
		self.ldb=load_leitner_db(self.selected_dir,Settings["user"])					
		self.agenda,self.new_cards=load_agenda(self.ldb,self.selected_dir, self.date)		
		self.reactAndInit(True , -1)

	def answer(self,flashcard_tag, listPosition):
		image = Image.open(self.selected_dir+"/Flashcards/"+flashcard_tag+"-2.png")
		image = image.resize((int(self.c.cget("width")),int(self.c.cget("height"))), Image.ANTIALIAS)
		flashcard_image = ImageTk.PhotoImage(image)
		
		for im in self.c.find_withtag("frontside"):
		   self. c.delete(im)
		for item in self.c.find_withtag('old'):#first clear possible rects from canvas
			self.c.delete(item)
		for item in self.c.find_withtag('elem'):#first clear possible rects from canvas
			self.c.delete(item)	
		drawCardHistory( self.ldb.getElementsByTagName(flashcard_tag)[0], self.c.stat )
		
		self.c.create_image(int(flashcard_image.width()/2), int(flashcard_image.height()/2), image=flashcard_image,tags=("backside",flashcard_tag))	
		self.c.img=flashcard_image			
	
		self.c.unbind("<Button-1>")
		self.c.edit_b.configure(state=NORMAL,command=lambda:edit_fc(self.c,self.selected_dir,flashcard_tag))
		self.c.back_b.configure(state=NORMAL)
		self.c.true_b.grid()
		self.c.false_b.grid()
		self.c.true_b.configure(state=NORMAL,command=lambda:self.reactAndInit(True, listPosition))
		self.c.false_b.configure(state=NORMAL,command=lambda:self.reactAndInit(False, listPosition))

		self.c.hide_b.configure(state=NORMAL,command=lambda:self.hide_fc(flashcard_tag))
			
		create_comment_canvas(self.c,self.selected_dir,flashcard_tag,Settings['user'])	

		level=self.ldb.getElementsByTagName(flashcard_tag)[0].getAttribute('level')

		if int(level) > 0:
			self.c.brain_true.config(text="review in "+str(brainPowerExponent(self.selected_dir,int(level) + 1))+" days")
		else:
			self.c.brain_true.config(text="review in 2 days")
			
		self.c.brain_false.config(text="review tomorrow")
		
		for tag in self.c.tag_buttons:
			tag.grid()
		self.c.l_b.config(command=self.c.rect.link_tag)
		self.c.r_b.config(command=self.c.rect.repeat_tag)
		self.c.w_b.config(command=self.c.rect.watchout_tag)
		self.c.q_b.config(command=self.c.rect.question_tag)
		self.c.wiki_b.config(command=self.c.rect.wiki_tag)
	
	
		


############################################################## Menu ####################################################################

def update_all( fnames ):
	working("Updateing all Latex files ...")

	folderstring=""
	for fname in fnames:
		folderstring += str(os.path.dirname(fname)+" ")
		os.system("rm "+os.path.dirname(fname)+"/Flashcards/UPDATE 2>/dev/null")
		
	#print folderstring
	executeCommand( "bash .TexFlasher/scripts/updateFiles.sh "+str(folderstring), True )
	create_flashcards( fnames, False )
		
	for fname in fnames:
		message,window_type=get_log_status(os.path.dirname(fname))
	 	if window_type=="showerror":
			exec('tkMessageBox.'+window_type+'( "Parse LaTex Logfile","%s")'%message)	
	
	Indexer.create()	
	menu()


def update_texfile( fname, user ):
	working("Updating Latex file ...")
	executeCommand( "bash .TexFlasher/scripts/updateFiles.sh "+os.path.dirname(fname), True )
	#executeCommand( "bash .TexFlasher/scripts/updateFiles.sh "+fname+" "+os.path.dirname(fname)+"/Users", True )
	#executeCommand( "bash .TexFlasher/scripts/updateFiles.sh "+os.path.dirname(fname)+"/Users/"+user+".xml "+os.path.dirname(fname)+"/Users/"+user+"_comment.xml "+fname, True )
	os.system("rm "+os.path.dirname(fname)+"/Flashcards/UPDATE 2>/dev/null")
	create_flashcards( fname )
 	message,window_type=get_log_status(os.path.dirname(fname))
 	if window_type=="showerror":
		exec('tkMessageBox.'+window_type+'( "Parse LaTex Logfile","%s")'%message)	
	else:
		if os.path.isfile(os.path.dirname(fname)+"/Flashcards/changed.texflasher"):
			Indexer.create()	
	menu()
	

def saveFiles(master):
		working("Checking for changes ...")
		try:
		  tree = xml.parse("./.TexFlasher/config.xml")
		  try: 
			size=tree.getElementsByTagName("size")[0]
			size.setAttribute("width",str(WIDTH))
			size.setAttribute("height",str(HEIGHT))
		  except:
			parent=tree.getElementsByTagName("config")[0]
			size=tree.createElement("size")
			parent.appendChild(size)
			size.setAttribute("width",str(WIDTH))
			size.setAttribute("height",str(HEIGHT))
		  xml_file = open("./.TexFlasher/config.xml", "w","utf-8")
		  tree.writexml(xml_file)
		  xml_file.close()	  
		except:
		  pass
		if checkIfNeedToSave( saveString ):
			if tkMessageBox.askyesno("Save?", "Do you want to save your changes on the server?"):
				executeCommand( "bash .TexFlasher/scripts/save.sh "+ saveString, True )
				master.quit()
			else:
				master.quit()	
		else:
			master.quit()
			
def create_new():
	file = tkFileDialog.askopenfilename(parent=Main,title='Choose LaTeX file',initialdir='./',defaultextension=".tex",filetypes=[("all files","*.tex")])
	if file != None and file!="":
		print file
		update_config(file)
		menu()
		

def working(text):
	clear_window()
	loader=Label(Main,font=("Sans",Main.f_normal,"bold"),text=text)
	loader.grid(rowspan=20,columnspan=20)
	Main.update()
	return loader

def get_flashfolder_path(dir):
	tree = xml.parse("./.TexFlasher/config.xml")
	config_xml = tree.getElementsByTagName('config')[0]  
	for elem in config_xml.childNodes:
		if elem.getAttribute('filename').startswith(dir):
		  return elem.getAttribute('filename')
		  break
		
def hide_FlashFolder(filename):
	tree = xml.parse("./.TexFlasher/config.xml")
	config_xml = tree.getElementsByTagName('config')[0]
	for elem in config_xml.childNodes:
		if elem.getAttribute('filename')==filename:
			config_xml.removeChild(elem)
	xml_file = open("./.TexFlasher/config.xml", "w", "utf-8")
	config_xml.writexml(xml_file)
	xml_file.close()
	#menu()


def reset_flash(filename):
	if tkMessageBox.askyesno("Delete?", "Do you really want to delete %s?"% filename.split("/")[-2]):
		try:
			os.remove(os.path.dirname(filename)+"/Users/"+Settings["user"]+".xml")
			os.remove(os.path.dirname(filename)+"/Users/"+Settings["user"]+"_comment.xml")
		except:
			pass
		hide_FlashFolder(filename)
		Indexer.create()	
		menu()


def clear_window():
	for widget in Main.grid_slaves():
		widget.grid_forget()

	
def get_log_status(filedir):
	message=""
	window_type="showinfo"
	if os.path.isfile(filedir+"/texFlasher.log"):
		log_time=ctime(os.path.getmtime(filedir+"/texFlasher.log"))
		message="Log from %s\\n\\n"%log_time
		log=open(filedir+"/texFlasher.log","r")
		l_count=0
		for l in log:
			if re.compile('error').findall(l.lower()):
				window_type="showerror"
				message=l.replace("\n","\\n\\n")
				l_count=0
				break
			else:
				message+=l.replace("\n","\\n\\n")
			l_count+=1
			if l_count>10:
				break
	else:
		message="No logfile found!"	
	return message,window_type


def show_log(filedir):
	message,window_type=get_log_status(filedir)
	exec('tkMessageBox.'+window_type+'( "Parse LaTex Logfile","%s")'%message)
        return


def show_tagged(tagtype,dir,tag_path):
	all_fcs=get_all_fcs(dir)
	tagged=[]
	tree = xml.parse(tag_path)
	parent=tree.getElementsByTagName(tagtype)[0]
	for elem in all_fcs:
	  if len(parent.getElementsByTagName(elem['tag']))>0:
	     tagged.append(elem)
	display_mult_fcs(tagged,str(len(tagged))+ " tagged \""+tagtype+"\" in "+dir)

        
        

def open_tex(filepath):
	try:
		webbrowser.open(filepath)
	except:
		tkMessageBox.showerror( "LaTeX Editor missing!","Please check, if you have a LaTeX Editor installed and try again!")

def open_dvi(filepath):
	try:
		webbrowser.open(filepath)
	except:
		tkMessageBox.showerror( ".DVI Viewer missing!","Please check, if you have .DVI Viewer installed and try again!")



class MyDialog:

    def __init__(self, parent):

        top = self.Main = Toplevel(parent)

        Label(top, text="Please enter a new flashfolder name:").pack()

        self.e = Entry(top)
        self.e.pack(padx=5)
        Label(top, text="Please enter the URL of an existing svn\n repository containing flashcards (optional):").pack()
        
        self.e1 = Entry(top)
        self.e1.pack(padx=25)

        b = Button(top, text="Create", command=self.ok)
        b.pack(pady=5)
    def ok(self):

        #print "value is", self.e.get()
        if self.e.get():
        	value=self.e.get().strip(" \n\r")
        	if not re.match("^[A-Za-z0-9]+$",value):
		  tkMessageBox.showerror("Error","Flashfolder has an invalid name, please try again.")		
		else:
		  repo=self.e1.get()
        	
		  #print repo
		  os.system("bash .TexFlasher/scripts/createFolder.sh "+value+" "+repo)
		  dir=os.path.abspath("./"+value+"/")
		#print dir
		  update_config(dir+"/Vorbereitung.tex")
		  menu()
		  self.Main.destroy()
	else:
		self.Main.destroy()
	  
def create_folder():
	d = MyDialog(Main)
	Main.wait_window(d.Main)

	
	
def check_tags(xml_path,tagtype):
	if os.path.isfile(xml_path):
		try:
			return 	len(xml.parse(xml_path).getElementsByTagName(tagtype)[0].childNodes) 
		except:
			return 0
	else:
		return 0
    
def bpe(filepath,b_=False):
	tree = xml.parse("./.TexFlasher/config.xml")
	config_xml = tree.getElementsByTagName('config')[0]  
	for elem in config_xml.childNodes:
		if elem.getAttribute('filename').startswith(filepath):
		  bpe=elem.getAttribute('bpe')
		  if bpe=="":
		    bpe=Main.bpe
		    elem.setAttribute('bpe',str(bpe))	
		    xml_file = open("./.TexFlasher/config.xml", "w","utf-8")
		    tree.writexml(xml_file)
		    xml_file.close()
		  elif b_:
		    bpe=b_.get()
		    elem.setAttribute('bpe',str(bpe))	
		    xml_file = open("./.TexFlasher/config.xml", "w","utf-8")
		    tree.writexml(xml_file)
		    xml_file.close()
		  break
	return float(bpe)

def menu():
	global Main
	bordersize=2
	
			
	Main.columnconfigure(0,weight=0)
	Main.columnconfigure(1,weight=1)
	Main.columnconfigure(2,weight=0)
	Main.columnconfigure(3,weight=0)
	Main.columnconfigure(4,weight=0)	
	Main.master.title(Main._title_base+" "+Main._version+" - Menu") 


	global saveString
	
	saveString = ""
	filenames=[]
	row_start=4
	
	loader_text="Loading Flashfolders ..."
	loader=working(loader_text)
	
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('config')[0]		
		for l in config_xml.childNodes:

			Widgets={}
			if l.tagName=="FlashFolder" and l.getAttribute('filename')!="" and os.path.isfile(l.getAttribute('filename')):
				filenames.append(l.getAttribute('filename'))
				todo=0;
				length=0
				ldb= load_leitner_db(os.path.dirname(l.getAttribute('filename')),Settings["user"])
				today,new_cards=load_agenda(ldb,os.path.dirname(l.getAttribute('filename')))
				todo=len(today)
				new=len(new_cards)
				length=len(ldb.childNodes)
				start_column=0
				log,window_type=get_log_status(os.path.dirname(l.getAttribute('filename')))
				


				button_status=NORMAL
				if length==0:
					button_status=DISABLED
				new_status=NORMAL					
				#open folder

				if todo-new>0:
					open_img_path="./.TexFlasher/pictures/Flashcard_folder_red.png"	
				elif new >0:
				  
					open_img_path="./.TexFlasher/pictures/Flashcard_folder_yellow.png"
				else:
					open_img_path="./.TexFlasher/pictures/Flashcard_folder.png"
				open_b=create_image_button(Main,open_img_path,None,Main.b_large)
				open_b.configure(state=button_status,command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):Flasher(fcdir, True))									
				open_b.grid(row=row_start,sticky=N+W+S+E,column=start_column)
				#folder desc
				Desc=Frame(Main)
				Desc.grid(row=row_start, column=start_column+1,sticky=W)

				Button(Desc,bd=0,justify=LEFT,font=("Sans",Main.f_normal,"bold"),command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):display_mult_fcs(get_all_fcs(fcdir),fcdir),text=l.getAttribute('filename').split("/")[-2]+" ("+str(length)+")").grid(row=0,column=0,sticky=W)
				info_frame=Frame(Desc)
				info_frame.grid(row=1,column=0,sticky=W)
				
				Label(info_frame,justify=LEFT,font=("Sans",Main.f_normal),text='todo: '+str(todo-new)+'  new: '+str(new)).grid(row=0,column=0,sticky=W)
				
    				hide_button=Button(info_frame,justify=LEFT,bd=0,font=("Sans",Main.f_normal))
    				hide_button.grid(row=0,column=1)    
    				hidden_fcs=[]
    				
    				for elem in ldb.childNodes:
    					if elem.getAttribute('level')=="-1":
						hidden_fcs.append({"dir":os.path.dirname(l.getAttribute('filename')),"tag":elem.tagName})    		
    				if len(hidden_fcs)>0:
    					hide_button.config(state=NORMAL,command=lambda data=hidden_fcs,fcdir=os.path.dirname(l.getAttribute('filename')):display_mult_fcs(data,"%s flashcard(s) are hidden in %s"%(str(len(data)),fcdir)))
					hide_button.config(text="hidden: "+str(len(hidden_fcs)))
				else:
					hide_button.grid_forget()	
				#Label(Desc,justify=LEFT,font=("Sans",Main.f_normal),text='updated: '+l.getAttribute('lastReviewed').rpartition(':')[0].partition('-')[2].replace('-','/')).grid(row=2,column=0,sticky=W)
				#bpe
				bpe_s = Scale(Main, from_=1, to=2,length=2*Main.b_normal ,font=("Sans",Main.f_normal),sliderlength=int(0.5*Main.b_normal),orient=HORIZONTAL,resolution=0.01)
				bpe_s.config(command=lambda e,b_=bpe_s,d_=l.getAttribute('filename'): bpe(d_,b_))
				bpe_s.set(bpe(l.getAttribute('filename')))
				bpe_s.grid(row=row_start,column=start_column+2)				
								
				#tags
				tag_xml_path=os.path.dirname(l.getAttribute('filename'))+"/Users/"+Settings['user']+"_comment.xml"
				q_b=create_image_button(Main,".TexFlasher/pictures/question_fix.png",None,Main.b_normal,0)
				q_b.grid(row=row_start,column=start_column+3,sticky=N+W+E+S)
				q_length=check_tags(tag_xml_path,"question")
				if q_length==None or q_length==0:
				   q_b.config(state=DISABLED)
				Label(Main,font=("Sans",Main.f_normal),text=str(q_length)).grid(row=row_start,column=start_column+3,sticky=S)
				   
				#else:
				#   Label(Main,text=str(q_length)).grid(row=row_start,column=start_column+2,sticky=S)
				q_b.config(command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):show_tagged('question',fcdir,fcdir+"/Users/"+Settings['user']+"_comment.xml"))
				w_b=create_image_button(Main,".TexFlasher/pictures/watchout_fix.png",None,Main.b_normal,0)
				w_b.grid(row=row_start,column=start_column+4,sticky=N+S+E+W)
				w_length=check_tags(tag_xml_path,"watchout")
				if w_length==None or w_length==0:
				   w_b.config(state=DISABLED)	
				w_b.config(command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):show_tagged('watchout',fcdir,fcdir+"/Users/"+Settings['user']+"_comment.xml"))
				Label(Main,font=("Sans",Main.f_normal),text=str(w_length)).grid(row=row_start,column=start_column+4,sticky=S)
				
				r_b=create_image_button(Main,".TexFlasher/pictures/repeat_fix.png",None,Main.b_normal,0)
				r_b.grid(row=row_start,column=start_column+5,sticky=N+W+E+S)
				r_length=check_tags(tag_xml_path,"repeat")
				if r_length==None or r_length==0:
				   r_b.config(state=DISABLED)	
				r_b.config(command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):show_tagged('repeat',fcdir,fcdir+"/Users/"+Settings['user']+"_comment.xml"))
				Label(Main,font=("Sans",Main.f_normal),text=str(r_length)).grid(row=row_start,column=start_column+5,sticky=S)

				l_b=create_image_button(Main,".TexFlasher/pictures/link_fix.png",None,Main.b_normal,0)
				l_b.grid(row=row_start,column=start_column+6,sticky=N+W+E+S)
				l_length=check_tags(tag_xml_path,"link")
				if l_length==None or l_length==0:
				   l_b.config(state=DISABLED)	
				l_b.config(command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):show_tagged('link',fcdir,fcdir+"/Users/"+Settings['user']+"_comment.xml"))
				Label(Main,font=("Sans",Main.f_normal),text=str(l_length)).grid(row=row_start,column=start_column+6,sticky=S)

				wiki_b=create_image_button(Main,".TexFlasher/pictures/wiki.png",None,Main.b_normal,0)
				wiki_b.grid(row=row_start,column=start_column+7,sticky=N+W+E+S)
				wiki_length=check_tags(tag_xml_path,"wiki")
				if wiki_length==None or wiki_length==0:
				   wiki_b.config(state=DISABLED)	
				wiki_b.config(command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):show_tagged('wiki',fcdir,fcdir+"/Users/"+Settings['user']+"_comment.xml"))
				Label(Main,font=("Sans",Main.f_normal),text=str(wiki_length)).grid(row=row_start,column=start_column+7,sticky=S)

				start_column+=6
				
				#update
				if os.path.isfile(os.path.dirname(l.getAttribute('filename'))+"/Flashcards/UPDATE"):
					update_image="./.TexFlasher/pictures/update_now.png"
				else:
					update_image="./.TexFlasher/pictures/update.png"
					
				if l.getAttribute('lastReviewed')==l.getAttribute('created'):
					update=create_image_button(Main,"./.TexFlasher/pictures/update_now.png",Main.b_normal,Main.b_normal)
					update.configure(command=lambda tex=l.getAttribute('filename'):update_texfile(tex,Settings["user"]))
					new_status=DISABLED
				else:
					update=create_image_button(Main,update_image,Main.b_normal,Main.b_normal)
					update.configure(command=lambda tex=l.getAttribute('filename'):update_texfile(tex,Settings["user"]))
				update.grid(row=row_start,column=start_column+2,sticky=W+N+S+E)

				#stats	
				stat=create_image_button(Main,"./.TexFlasher/pictures/stat.png",Main.b_normal,Main.b_normal)
				stat.configure(state=button_status,command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):statistics_nextWeek(fcdir))
				stat.grid(row=row_start,column=start_column+3,sticky=N+S+W+E)
				#open tex file
				tex =create_image_button(Main,"./.TexFlasher/pictures/latex.png",Main.b_normal,Main.b_normal)
				tex.configure(command=lambda texfile=l.getAttribute('filename'):open_tex(texfile))
				tex.grid(row=row_start,column=start_column+4,sticky=W+N+S+E)
				#open dvi file
				tex =create_image_button(Main,"./.TexFlasher/pictures/dvi.png",Main.b_normal,Main.b_normal)
				tex.configure(command=lambda texfile=os.path.dirname(l.getAttribute('filename'))+"/Details/source.dvi":open_dvi(texfile))
				tex.grid(row=row_start,column=start_column+5,sticky=W+N+S+E)				
				#log
				log=create_image_button(Main,"./.TexFlasher/pictures/"+window_type+".png",Main.b_normal,Main.b_normal)
				log.configure(state=new_status,command=lambda fcdir=os.path.dirname(l.getAttribute('filename')):show_log(fcdir))
				log.grid(row=row_start,column=start_column+6,sticky=N+S+E+W)
				#reset
				res=create_image_button(Main,"./.TexFlasher/pictures/delete.png",Main.b_normal,Main.b_normal)
				res.configure(command=lambda texfile=l.getAttribute('filename'):reset_flash(texfile))
				res.grid(row=row_start,column=start_column+7,sticky=N+S+E)
				
				saveString += " "+ os.path.dirname(l.getAttribute('filename'))+"/Users/"+Settings["user"]+".xml"
				saveString += "###"+ os.path.dirname(l.getAttribute('filename'))+"/Users/"+Settings["user"]+"_comment.xml"
				saveString += "###"+ l.getAttribute('filename') 
				Label(Main,height=1).grid(row=row_start+1)
				row_start+=2	

	toolbar=Frame(Main)
	
	create=create_image_button(toolbar,"./.TexFlasher/pictures/Flashcard_folder_add.png",None,Main.b_normal)
	create.configure(command=create_new) 
	ToolTip(create,"Open flaschcards script")
	create_n=create_image_button(toolbar,"./.TexFlasher/pictures/Flashcard_folder_create.png",None,Main.b_normal)
	create_n.configure(command=create_folder)
	ToolTip(create_n,"Create new flaschards folder")
	

	if row_start > 4:
		toolbar.grid(row=2,columnspan=20)
		#toolbar.rowconfigure(0,weight=1)
		#toolbar.columnconfigure(0,weight=1)
		#toolbar.columnconfigure(1,weight=1)
		#toolbar.columnconfigure(2,weight=1)
		#search field

		save_all=create_image_button(toolbar,"./.TexFlasher/pictures/upload.png",None,Main.b_normal)
		save_all.configure(command=lambda:executeCommand( "bash .TexFlasher/scripts/save.sh "+ saveString, True )) 
	
		update_all_b=create_image_button(toolbar,"./.TexFlasher/pictures/update.png",None,Main.b_normal)
		update_all_b.configure(command=lambda:update_all(filenames)) 	
	
	
	
		create.grid(row=0,column=0,sticky=E+W+N+S)
			
		create_n.grid(row=0,column=1,sticky=E+W+N+S)		
		query=Search(toolbar)
		query.grid(row=0,column=2,sticky=E+W+N+S)
		
		update_all_b.grid(row=0,column=3,sticky=E+W+N+S)
		save_all.grid(row=0,column=4,sticky=E+W+N+S)
		Label(Main,height=1).grid(sticky=E+W,row=3,columnspan=10)
	else:
		toolbar.grid(row=2,columnspan=20)
		#toolbar.rowconfigure(0,weight=1)
		#toolbar.columnconfigure(0,weight=1)
		#toolbar.columnconfigure(1,weight=1)
		create_n.grid(row=0,column=0,sticky=E+W+N+S)			
		create.grid(row=0,column=1,sticky=E+W+N+S)
	#footer
	loader.grid_forget()

def readSettings( Settings ):
	Config = ConfigParser.ConfigParser()
	Config.read("settings")
	if not "TexFlasher" in Config.sections():
		print "Fatal Error while reading config file. Please reinstall by typing 'bash install.sh'."
		sys.exit()

	options = Config.options("TexFlasher")
	
	for thing in Settings:
		if not thing in options:
			print "Fatal Error while reading config file. Please reinstall by typing 'bash install.sh'."
			sys.exit()

		else:
			Settings[thing] =  Config.get( "TexFlasher", thing )





##################################################################### Main ###############################################################################

	
	
global Settings 
Settings = { 'user':''
						}	
readSettings( Settings )

global WIDTH, HEIGHT




# just to be on the safe side






BD=1

RESTART_TIME=7 # 2 o'clock

IK=ImageKeeper()

Indexer=create_index()
Indexer.create()	


iconbitmapLocation = "@./.TexFlasher/pictures/icon.xbm"



class TexFlasher(Frame):
	def resize(self,event):
		global WIDTH, HEIGHT
		#Main Window
		WIDTH=self.master.winfo_width()-20
		HEIGHT=self.master.winfo_height()
		
		self.configure(bd=int(p2c(WIDTH,WIDTH,[1,1])[0]),height=p2c(None,HEIGHT,[92]),width=p2c(WIDTH,None,[100]))\
				
		#Header and Footer
		logo_height=p2c(HEIGHT,HEIGHT,[7,7])[0]		
		self.Logo.configure(text="TeXFlasher based on Leitner-Method",justify=CENTER,font=("Sans",int(0.3*logo_height),"bold"))	
		footer_height=p2c(HEIGHT,HEIGHT,[1,1])[0]			
		self.copyright.configure(font=("Sans",int(0.8*footer_height)),justify=CENTER,text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer")			

		#Buttons
		self.b_tiny=int(p2c(self.winfo_width(),self.winfo_height(),[3,3])[1])
		self.b_normal=int(p2c(self.winfo_width(),self.winfo_height(),[5,5])[1])
		self.b_large=int(p2c(self.winfo_width(),self.winfo_height(),[7,7])[1])		

		#fontsizes
		self.f_tiny=int(0.17*self.b_normal)
		self.f_normal=int(0.3*self.b_normal)
		self.f_large=int(0.5*self.b_normal)

	def __init__( self ):
		Frame.__init__( self)
		global WIDTH, HEIGHT		
		self.master.bind("<Configure>", self.resize)
		self.master.tk.call('namespace', 'import', '::tk::dialog::file::')
		#self.master.tk.call('set', '::tk::dialog::file::showHiddenBtn',  '1')
		self.master.tk.call('set', '::tk::dialog::file::showHiddenVar',  '0') 

		global Main
		Main=self

		self.master.rowconfigure( 0, weight = 1 )
		self.master.columnconfigure( 0, weight = 1 )	
		self.master.rowconfigure( 2, weight = 1 )
	
		ws = self.master.winfo_screenwidth()
		hs = self.master.winfo_screenheight()
		last_size=False
		try:
		    tree = xml.parse("./.TexFlasher/config.xml")
		    last_size = tree.getElementsByTagName('size')[0]
		    WIDTH=int(last_size.getAttribute("width"))
		    HEIGHT=int(last_size.getAttribute("height"))			
		except:
		  HEIGHT=int ( min( hs, ws)*0.8 )
		  WIDTH=int(0.98*HEIGHT)
		  if(ws < WIDTH):
		    WIDTH = ws	
		  
		#Main Frame Settings
		self.configure(bd=int(p2c(WIDTH,WIDTH,[1,1])[0]),height=p2c(None,HEIGHT,[90]),width=p2c(WIDTH,None,[100]))			
		self.grid(row=1,column=0,sticky=N+E+W)
		self.grid_propagate(False) 
			
		self._title_base="TeXFlasher"
		self._version="unstable build"

		# calculate position x, y
		Wi=WIDTH+20 #width of the outer window frame
		Hi=HEIGHT
		xs = (ws/2) - (int(Wi)/2) 
		ys = (hs/2) - (Hi/2)				
		self.master.geometry(str(int(Wi))+"x"+str(Hi)+"+"+str(xs)+"+"+str(ys))
		self.master.iconbitmap(iconbitmapLocation)
		self.master.iconmask(iconbitmapLocation)	
		
		#master bindings
		self.master.protocol('WM_DELETE_WINDOW',lambda:saveFiles(self.master))
		self.master.bind("<Escape>", lambda e: self.master.quit()) # quits texflasher if esc is pressed		
		self.master.title(self._title_base+" "+self._version)

		#Button type heights
		self.b_tiny=p2c(self.winfo_width(),self.winfo_height(),[3,3])[1] #3% Height of Main
		self.b_normal=p2c(self.winfo_width(),self.winfo_height(),[5,5])[1]#5% Height of Main
		self.b_large=p2c(self.winfo_width(),self.winfo_height(),[7,7])[1]#7% Height of Main
		#fontsizes
		self.f_tiny=int(0.17*self.b_normal)
		self.f_normal=int(0.3*self.b_normal)
		self.f_large=int(0.5*self.b_normal)
		
		#Header and Footer
		logo_height=p2c(HEIGHT,HEIGHT,[7,7])[0]		
		footer_height=p2c(HEIGHT,HEIGHT,[1,1])[0]		
		Header=Frame(self.master).grid(row=0,columnspan=8,sticky=E+W+N)
		#logo=IK.get_image(".TexFlasher/pictures/logo.png",None,logo_height)
		self.Logo=Label(Header)
		self.Logo.configure(text="TeXFlasher based on Leitner-Method",justify=CENTER,font=("Sans",int(0.3*logo_height),"bold"))
		self.bpe=1.3

		#self.Logo.img=logo
		self.Logo.grid(row=0,sticky=E+W+N)		
		Footer=Frame(self.master).grid(row=2,sticky=S+E+W)
		self.copyright=Label(Footer)
		self.copyright.configure(font=("Sans",int(footer_height)),justify=CENTER,text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer")
		self.copyright.grid()
		menu()

TexFlasher().mainloop()

