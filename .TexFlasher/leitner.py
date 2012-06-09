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

global comp_list
global c
global velocity,autorotate	
global xold,maximages,centerrec 

global search_canvas # scrolling wheel support needs that for some reason

global saveString 
global Menu
global Settings 

global Main

import os
import subprocess
import sys
import re
import commands
import xml.dom.minidom as xml
from operator import itemgetter
from time import strftime, strptime, ctime, localtime, mktime
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
import gtk, pygtk


#locals
from tagger import *
from systemInterface import *
from gallery import *
#import Pmw


######################################################################## leitner_db management ##############################################


def load_leitner_db(leitner_dir,user):
	if not os.path.isdir(leitner_dir+"/Flashcards"):
		print "No directory named 'Flashcards' found in "+leitner_dir
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
			#mod_sec=os.stat(leitner_dir+"/Flashcards/"+flashcard_file).st_mtime
			#mod_date=datetime(*(strptime(strftime("%Y-%m-%d %H:%M:%S",localtime(mod_sec)), "%Y-%m-%d %H:%M:%S")[0:6]))

			try: 
				flashcard_element=old_ldb.getElementsByTagName(flashcard_name)[0] #raises if old_ldb does not exist or not found
			#		lastReviewed_date=datetime(*(strptime(flashcard_element.getAttribute('lastReviewed'), "%Y-%m-%d %H:%M:%S")[0:6])) #this raises if not reviewed yet	#		if mod_date>lastReviewed_date: 
			#			changed.append(flashcard_element.tagName)
				ldb.appendChild(flashcard_element)
			except:
				#create new flashcard node
				flashcard_element=doc.createElement(flashcard_name)
				ldb.appendChild(flashcard_element)
				flashcard_element.setAttribute('lastReviewed', "")
				flashcard_element.setAttribute('level',"0")
				flashcard_element.setAttribute('levelHistory',"0_("+strftime("%Y-%m-%d %H:%M:%S", localtime())+")")
				flashcard_element.setAttribute('created',strftime("%Y-%m-%d %H:%M:%S", localtime()))
	xml_file = open(leitner_dir+"/Users/"+Settings["user"]+".xml", "w")
	ldb.writexml(xml_file)
	#pretty_xml = ldb.toprettyxml()
	#xml_file.writelines(pretty_xml)
	xml_file.close()
	return ldb


def futureCardNumber( database, offset, offset2, maxLevel ):
	LEVELS=[]
	
	for i in range(maxLevel+1):
		LEVELS.append(0)
	number=0
	seconds_in_a_day = 60 * 60 * 24
	for elem in database.childNodes:
		name=elem.tagName
		lastReviewed=elem.getAttribute('lastReviewed')
		if lastReviewed!="":
			lastReviewed_time=datetime(*(strptime(lastReviewed, "%Y-%m-%d %H:%M:%S")[0:6]))
		        level=int(elem.getAttribute('level'))
			dt_1 = lastReviewed_time + timedelta(days=(level - (offset + offset2)))		
			dt_2 = lastReviewed_time + timedelta(days=(level - offset))		
		
			if (datetime.now() + timedelta(hours=int(24 - datetime.now().hour + RESTART_TIME)) < dt_1):
				if datetime.now() + timedelta(hours=int(24 - datetime.now().hour + RESTART_TIME)) >= dt_2:
					number += 1
					LEVELS[level] +=1
		else:
			if offset == 0:
				number += 1	
				LEVELS[int(elem.getAttribute('level'))] += 1
	return number, list(LEVELS)


def load_agenda(ldb,dir,now=datetime.now()):
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
				place=int(order.getElementsByTagName(elem.tagName)[0].getAttribute("position"))
				new_fc[elem.tagName]=place
			else:
				lastReviewed_time=datetime(*(strptime(lastReviewed, "%Y-%m-%d %H:%M:%S")[0:6]))
				level=elem.getAttribute('level')
				dt = lastReviewed_time + timedelta(days=int(level))		
				if now + timedelta(hours=int(24 - now.hour + RESTART_TIME))>=dt:
					diff=now-dt
					local_agenda[elem.tagName]=diff.days * seconds_in_a_day + diff.seconds
	except:
		pass
	sorted_agenda = sorted(local_agenda.iteritems(), key=itemgetter(1))
	sorted_agenda.reverse()
	sorted_new=sorted(new_fc.iteritems(), key=itemgetter(1))	
	return sorted_agenda+sorted_new,len(sorted_new)


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
			xml_file = open(selected_dir+"/Users/"+Settings["user"]+".xml", "w")
			ldb.writexml(xml_file)
			xml_file.close()
	except:
		print "Error while updating "+fc_tag+" attribute "+attr_name+" to "+str(attr_value)

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
		checkForUpdate(Settings["user"])
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
			number, listOfLevels = futureCardNumber( database, day , -1 , maxLevel)
			DAYS.append( number )
			DATASET.append( [ number, list(listOfLevels)  ] )
		
		#print DATASET
		# fix for day=0
		number1, listOfLevels1 = futureCardNumber( database, 0, -1000000, maxLevel )
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
	drawHistory( HISTORY, stat, 9 )
	
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
    Main.master.title("Statistics")
    
    fontsize=int(float(WIDTH)*0.012)
    DX=WIDTH*0.00125
    DY=HEIGHT*0.001221
    #print DY


    menu_button=create_image_button(Main,"./.TexFlasher/pictures/menu.png",40,40)
    menu_button.configure(text="Menu",command=lambda:menu())
    menu_button.grid(row=0,columnspan=7,sticky=N+W+S+E)
    #Balloon = Pmw.Balloon(top)
    #Balloon.bind(menu_button, "Return to Menu") 
    Stats=Frame(Main,border=10)
    Stats.grid(row=3,column=0)
    
    DAYS =[ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun' ]
    tday=dayToday()   
           
    global c
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
		display_mult_fcs(fcs,"%s flashcard(s) at level %s in %s"%(str(len(fcs)),str(level),dir.split("/")[-1]),"Go Back","lambda:statistics_nextWeek('%s')"%(dir),"./.TexFlasher/pictures/stat.png")


#################################################################################### Get FC Info

def get_fc_info(dir,tag,ldb=None):
	if not ldb:
		ldb=load_leitner(dir,Settings["user"])
	for elem in ldb.childNodes:
		if elem.tagName==tag:
			return elem	
			break

def get_fc_desc(fc_dir,tag,tex_file=False,xml_file=False):

	if not tex_file:	
		try:
			tex_file_path=get_flashfolder_path(fc_dir)
			tex_file=open(tex_file_path,"r")
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
		if content_ and re.compile("\\\\end\{"+theorem_type+"\}").findall(l):
			content_=False
			tag_=False
			break
		if tag_ and content_:
			content+=l
		if not tag_ and re.compile("\\\\fc\{"+tag+"\}").findall(l):
			tag_=True
		if tag_ and re.compile("\\\\begin\{"+theorem_type+"\}").findall(l):			
			content_=True

	
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

class Search(Entry):
        """
        Subclass of Tkinter.Entry that features autocompletion.
        
        To enable autocompletion use set_completion_list(list) to define 
        a list of possible strings to hit.
        To cycle through hits use down and up arrow keys.
        """ 
        def clear_search(self,event):
		self._def_value.set("")
		self.configure(font=("Helvetica",14,'bold'),fg="black",textvariable=self._def_value)
        
        def __init__( self, parent, **options ):
        	Entry.__init__( self, parent, **options )
        	self._def_value=StringVar()
		self.configure(highlightthickness=0,font=("Helvetica",20,"bold"),textvariable=self._def_value,bd =5,bg=None,fg="gray",justify=CENTER)
		self.bind("<Button-1>", self.clear_search)
		self._def_value.set("Search ...")    
		self._hits = []
		self._hit_index = 0
		self.position = 0
		self.bind('<KeyRelease>', self.handle_keyrelease)		  	
      	
      	
        def set_completion_list(self, completion_list):             	    
                self._completion_list = completion_list                

                
                
        def add_search_query(self,se_query,results):
        	global comp_list
        	if not unicode(se_query.lower()) in list(comp_list):							        		
			comp_list+=(unicode(se_query.lower()),)

        def autocomplete(self, delta=0):
                """autocomplete the Entry, delta may be 0/1/-1 to cycle through possible hits"""
                if delta: # need to delete selection otherwise we would fix the current position
                        self.delete(self.position, Tkinter.END)
                else: # set position to end so selection starts where textentry ended
                        self.position = len(self.get())
                # collect hits
                _hits = []
                for element in self._completion_list:
                        if element.startswith(self.get().lower()):
                                _hits.append(element)
                # if we have a new hit list, keep this in mind
                if _hits != self._hits:
                        self._hit_index = 0
                        self._hits=_hits
                # only allow cycling if we are in a known hit list
                if _hits == self._hits and self._hits:
                        self._hit_index = (self._hit_index + delta) % len(self._hits)
                # now finally perform the auto completion
                if self._hits:
                        self.delete(0,END)
                        self.insert(0,self._hits[self._hit_index])
                        self.select_range(self.position,END)
                       
        def search_flashcard(self):
		search_query=self.get()
		# set similarity sensitivity
		thresh=0.7 #marker and title
		current_dir=""
		current_source_xml=None
		current_tex_file=None
		current_order_xml=None
		if len(search_query)>0 and not search_query=="Search ...":		
			match_info_name=[]
			all_fcs=get_all_fcs()
			for fc_elem in all_fcs:
				if not fc_elem['dir']==current_dir: #load files needed for get_... funktions to speed up search
					current_dir=fc_elem['dir']
					current_source_xml=xml.parse(fc_elem['dir']+"/Details/source.xml")
					tex_file_path=get_flashfolder_path(fc_elem['dir'])
					current_tex_file=open(tex_file_path,"r")
					current_order_xml=xml.parse(fc_elem['dir']+"/Flashcards/order.xml")
				fc_name,theorem_name,theorem_type,fc_content=get_fc_desc(fc_elem['dir'],fc_elem['tag'],current_tex_file,current_order_xml)
				fc_sections=get_fc_section(fc_elem['dir'],fc_elem['tag'],current_source_xml)	
				try:

					fc_elem['query']=fc_name+" "+theorem_name+" "+sanatize(fc_content)+" "+fc_elem['tag']+" "+fc_sections
					match_info_name.append(fc_elem)
				except:
					pass
					#TODO: Sometimes encoding error!
					#print "Search error with "+str(fc_elem)
			search_results=[]
			for res in match_info_name:
				if not len(search_query.split(" "))>0:
					if len(get_close_matches(search_query.lower(),res['query'].lower().split(" "),cutoff=thresh))>0:			
						search_results.append(res)
				else:
					match_count=0
					for s in search_query.lower().split(" "):
						if len(get_close_matches(s,res['query'].lower().split(" "),cutoff=thresh))>0 or len(get_close_matches(s,[res['query'].lower()],cutoff=thresh))>0 or len(get_close_matches(s,res['query'].lower().split("-"),cutoff=thresh))>0:						
							match_count+=1
					if match_count==len(search_query.split(" ")):
						search_results.append(res)												
			## display search results
			if len(search_results)>0:
				display_mult_fcs(search_results,"Found "+str(len(search_results))+" search results for \""+search_query+"\"","Menu","lambda:menu()","./.TexFlasher/pictures/menu.png")
				self.add_search_query(search_query,search_results)
			else:
				self.delete(0,END)
				self.insert(0,"Nothing found!" )

	
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
	  if width and height:
	    image = image.resize((width, height), Image.ANTIALIAS)
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
#	button_image = Image.open(path)
	if width and height:
		STRS=path.partition("-1")
		thumbname=STRS[0]+"-thumb"+str(int(width))+"x"+str(int(height))+STRS[2]
		if os.path.isfile(thumbname):
			try:
				button_image = IK.get_image(thumbname)
			except:
				button_image = IK.get_image(path,width,height)
		else:
			button_image = IK.get_image(path,width,height)	
	if border==None:
		button=Button(window,image=button_image,bd=BD)
	else:
		button=Button(window,image=button_image,bd=border)
	  
	button.img=button_image
	button.grid()
	return button




def display_mult_fcs(fcs,title,button_title,button_command,button_image): #Syntax: fcs=[{"tag":fc_tag,"dir":fc_dir,"level":fc_level}, ...]
	clear_window()
	global search_canvas # scrolling wheel support needs that for some reason
	Main.master.title("Search")
	Label(Main,text=title).grid(row=0,columnspan=5)
	exec('menu_button=create_image_button(Main,"'+button_image+'",40,40)')
	exec('menu_button.configure(text="%s",command=%s)'%(button_title,button_command))
	exec('menu_button.grid(row=1,columnspan=5,sticky=N+W+E+S)')
	vscrollbar = AutoScrollbar(Main)
	vscrollbar.grid(row=2, column=2, sticky=N+S)
	search_canvas = Canvas(Main,yscrollcommand=vscrollbar.set)
	search_canvas.grid(row=2, column=0, sticky=N+S+E+W)
	vscrollbar.config(command=search_canvas.yview)
	Search_frame = Frame(search_canvas,border=10)
	Search_frame.columnconfigure(0, weight=1)
	Search_frame.grid(row=0,column=0)
	Label(Search_frame,width=1).grid(column=2,rowspan=100)
	i=0 #start at row	
	iterator=fcs.__iter__()
	images_row=[1,3] # increaese number of images per row by adding [1,3,6,9, ...]
	size=Main.winfo_width()/len(images_row)-40
	for res in iterator:
		for colu in images_row:
			if colu>images_row[0]:
				try:
					res=iterator.next()
				except:
					break
			button=create_image_button(Search_frame,res['dir']+"/Flashcards/"+res['tag']+"-1.png",size,int(size*0.6))
			exec('button.configure(command=lambda:disp_single_fc("'+res['dir']+"/Flashcards/"+res['tag']+"-2.png"+'","'+res['tag']+'","'+res['tag']+' in '+res['dir'].split("/")[-1]+' level '+res['level']+'"))')
			button.grid(row=str(i+1),column=colu)
			exec("button.bind('<Button-4>', lambda event: search_canvas.yview_scroll(-1, UNITS))")
			exec("button.bind('<Button-5>', lambda event: search_canvas.yview_scroll(1, UNITS)) ")
			dist=Label(Search_frame,height=1).grid(row=str(i+2),column=colu)
		i+=3
	search_canvas.create_window(0, 0, anchor=NW, window=Search_frame)
	exec("Search_frame.bind('<Button-4>', lambda event: search_canvas.yview_scroll(-1, UNITS))")
	exec("Search_frame.bind('<Button-5>', lambda event: search_canvas.yview_scroll(1, UNITS)) ")			
	exec("search_canvas.bind('<Button-4>', lambda event: event.widget.yview_scroll(-1, UNITS))")
	exec("search_canvas.bind('<Button-5>', lambda event: event.widget.yview_scroll(1, UNITS)) ")
	Search_frame.update_idletasks()
	search_canvas.config(scrollregion=search_canvas.bbox("all"),width=Main.winfo_width()-40,height=Main.winfo_height()-80)


def  disp_single_fc(image_path,tag,title=None):
	# create child window
	win = Toplevel()
	# display message
	win.title(title)
	win.iconbitmap(iconbitmapLocation)
	win.iconmask(iconbitmapLocation)

	c=Canvas(win,width=WIDTH,height=WIDTH*0.6)
	c.grid(row=3,columnspan=4)
	image = Image.open(image_path)
	image = image.resize((WIDTH, int(WIDTH*0.6)), Image.ANTIALIAS)
	flashcard = ImageTk.PhotoImage(image)
	c.create_image(int(WIDTH/2), int(WIDTH*0.3), image=flashcard)	
	c.img=flashcard
	#c.bind("<Button-1>", lambda e: win.destroy())
	edit_b=create_image_button(win,"./.TexFlasher/pictures/latex.png",40,40)
#	edit_b.config(state=DISABLED)
	edit_b.grid(row=1,column=1,sticky=N+E+W+S)

	save_b=create_image_button(win,".TexFlasher/pictures/upload_now.png",40,40)
	save_b.config(state=DISABLED)
	save_b.grid(row=1, column=2,sticky=W+S+E+N)	
	
	clear_b=create_image_button(win,".TexFlasher/pictures/clear.png",40,40)
	clear_b.configure(state=DISABLED)
	clear_b.grid(row=1, column=3,sticky=E+S+W+N)		

	edit_b.configure(state=NORMAL,command=lambda:edit_fc(c,os.path.dirname(image_path).replace("/Flashcards",""),tag))
	
	back_b=create_image_button(win,".TexFlasher/pictures/back.png",40,40)
	back_b.grid(row=1, column=0,sticky=W+N+E+S)		
	back_b.config(command=lambda: win.destroy())
	
	c.save_b=save_b
	c.clear_b=clear_b
	c.edit_b=edit_b	
	c.back_b=back_b
	create_comment_canvas(c,os.path.dirname(image_path)+"/../",tag,Settings['user'])

	
	
	c.fc_row=3
	c.tag_buttons=[]

	q_b=create_image_button(win,".TexFlasher/pictures/question_fix.png",20,20)
	q_b.grid(row=c.fc_row,column=0,sticky=N+W)
	#q_b.grid_remove()
	c.q_b=q_b
	w_b=create_image_button(win,".TexFlasher/pictures/watchout_fix.png",20,20)
	w_b.grid(row=c.fc_row,column=0,sticky=S+W)
	#w_b.grid_remove()
	c.w_b=w_b
	r_b=create_image_button(win,".TexFlasher/pictures/repeat_fix.png",20,20)

	r_b.grid(row=c.fc_row,column=3,sticky=N+E)
	#r_b.grid_remove()
	c.r_b=r_b
	l_b=create_image_button(win,".TexFlasher/pictures/link_fix.png",20,20)

	l_b.grid(row=c.fc_row,column=3,sticky=S+E)		    
	#l_b.grid_remove()
	c.l_b=l_b

	c.tag_buttons=[q_b,w_b,r_b,l_b]	
	
	c.l_b.config(command=c.rect.link_tag)
	c.r_b.config(command=c.rect.repeat_tag)
	c.w_b.config(command=c.rect.watchout_tag)
	c.q_b.config(command=c.rect.question_tag)	
	ldb=load_leitner_db(os.path.dirname(image_path)+"/../",Settings["user"])
	fc_info=get_fc_info(os.path.dirname(image_path)+"/../",tag,ldb)
	
	
	stat_height=40
	stat_width=int(float(WIDTH)*0.95)
	stat=Canvas(win,width=stat_width, height=stat_height)
	stat.grid(row=2, columnspan=5)
	stat.height=stat_height
	stat.width=stat_width
	c.stat=stat	
	drawCardHistory( ldb.getElementsByTagName(tag)[0], c.stat )
	
	#Label(win,height=1).grid(row=3,column=0)
	#Label(win,text="Created: "+fc_info.getAttribute("created")+", Last Reviewed:"+fc_info.getAttribute("lastReviewed")).grid(row=0,columnspan=2)	


###############################################################  Edit fc ######################################################################

def edit_fc(c,dir,fc_tag):
	c_height=c.winfo_reqheight()
	c_width=c.winfo_reqwidth()

	fc_name,theorem_name,theorem_type,content=get_fc_desc(dir,fc_tag)
	c.edit_b.config(state=DISABLED)
	c.back_b.config(state=DISABLED)
	try:
	  c.true_b.config(state=DISABLED)
	  c.false_b.config(state=DISABLED)
	except:
	  pass
	frame=Frame(c,height=c_height,width=c_width)	
	frame.grid(sticky=E+W+N+S)
	frame.grid_propagate(False) 	
	#print c_width,c_height,WIDTH,HEIGHT,int(WIDTH*0.14256),int(WIDTH*0.043)
	edit_text=create_textbox(frame,int(WIDTH*0.043),int(WIDTH*0.14256)) #TODO fit ro canvas
	edit_text.insert(INSERT,content)
	edit_text.grid(sticky=N+W+E+S)

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
	file=open(file_path,"r")
	tag=False
	new_latex=[]

	old_fcs=[] #for checking
	new_fcs=[] # -%-

	for line in file:
		if re.compile('fc\{(\w+)\}\n').findall(line):
			old_fcs.append(line)
		if re.compile('fc\{'+fc_tag+'\}\n').findall(line):	
			tag=True
			new_latex.append(line)
		if re.compile('begin\{'+theorem_type+'\}').findall(line) and tag:
			new_latex.append(line+content)
		if re.compile('end\{'+theorem_type+'\}').findall(line) and tag:
			tag=False
		if not tag:
			new_latex.append(line)
	file.close()
	for line in new_latex:
		if re.compile('fc\{(\w+)\}\n').findall(line):
			new_fcs.append(line)	
	if old_fcs==new_fcs: #check if # of fcs has'nt changed
		new_file=open(file_path,"w")
		for line in new_latex:
			#print line
			new_file.writelines(line)
		new_file.close()
	else:
		raise	
	

	
	
def save_edit(c,frame,edit_text,dir,fc_tag,theorem_type):
	content=edit_text.get('1.0', END)
	if os.path.isfile("./.TexFlasher/config.xml"):
		#try:
			tree = xml.parse("./.TexFlasher/config.xml")
			config_xml = tree.getElementsByTagName('config')[0]
			for elem in config_xml.childNodes:
				if os.path.dirname(elem.getAttribute('filename'))==dir:
					change_latex(elem.getAttribute('filename'),fc_tag,content,theorem_type)				
					executeCommand("bash .TexFlasher/scripts/recompileFlashcards.sh "+elem.getAttribute('filename'), True)
 					message,window_type=get_log_status(dir)
 					if window_type=="showerror":
						exec('tkMessageBox.'+window_type+'( "Parse LaTex Logfile","%s")'%message)
					else:
						image = Image.open(os.path.dirname(elem.getAttribute('filename'))+"/Flashcards/"+fc_tag+"-2.png")
						image = image.resize((int(c.cget("width")),int(c.cget("height"))), Image.ANTIALIAS)
						flashcard = ImageTk.PhotoImage(image)
	 					c.create_image(int(flashcard.width()/2), int(flashcard.height()/2), image=flashcard)
	 					c.img=flashcard	
						cancel_edit(c,dir,fc_tag,frame)							
					break
		#except:
		#	tkMessageBox.showerror("Error","Fatal error with %s! This is bad, because the card may have been deleted (not from latex) and we did not detect latex errors!"%fc_tag)
	else:
		tkMessageBox.showerror("Error","Fatal error while saving new content for %s: no config found!"%fc_tag)

	

############################################################### run flasher ###########################################################


class Flasher:
	def resize(self,width,height):
		print width, height

	def __init__(self,selected_dir,stuffToDo=True):
		global Main
		Main._running_classes["Flasher"]=self
		
		clear_window()#clear main window

		Main.master.title(selected_dir)

		if( stuffToDo ):
			date = datetime.now()
		else:
			date = datetime.now()+timedelta(days=1000)
		self.selected_dir=selected_dir
		Main.columnconfigure(0,weight=1)
		Main.columnconfigure(1,weight=1)
		Main.columnconfigure(2,weight=1)
		Main.columnconfigure(3,weight=1)
		Main.columnconfigure(4,weight=1)
								
		self.ldb=load_leitner_db(self.selected_dir,Settings["user"])
				
		self.agenda,new=load_agenda(self.ldb,self.selected_dir, date)
		
		
		self.c=Canvas(Main,width=WIDTH,height=Main.winfo_height()-240)

		self.c.order = xml.parse(self.selected_dir+"/Flashcards/order.xml")
		self.c.source = xml.parse(self.selected_dir+"/Details/source.xml")

		#spacer
		#Label(parent.master,height=1).grid(row=0,columnspan=5)
		
		#flashcard details
		self.c.fc_det_row=1
		fc_det_left = StringVar()
		fc_det_right = StringVar()
		Label(Main,anchor=W,textvariable=fc_det_left).grid(row=self.c.fc_det_row,column=0, columnspan=3,sticky=W)	
		Label(Main,anchor=E,textvariable=fc_det_right).grid(row=self.c.fc_det_row, column=3,columnspan=2,sticky=E)
		self.c.fc_det_left=fc_det_left
		self.c.fc_det_right=fc_det_right
	
		# menubar
		self.c.menu_row=2
		back_b=create_image_button(Main,".TexFlasher/pictures/back.png",40,40)
		back_b.grid(row=self.c.menu_row, column=0,sticky=W+E)	
		
		menu_button=create_image_button(Main,"./.TexFlasher/pictures/menu.png",40,40)
		menu_button.configure(text="Menu",command=lambda:menu())
		menu_button.grid(row=self.c.menu_row,column=1,sticky=W+E)
		
		edit_b=create_image_button(Main,"./.TexFlasher/pictures/latex.png",40,40)
		edit_b.config(state=DISABLED)
		edit_b.grid(row=self.c.menu_row,column=2,sticky=W+E)
	
		save_b=create_image_button(Main,".TexFlasher/pictures/upload_now.png",40,40)
		save_b.config(state=DISABLED)
		save_b.grid(row=self.c.menu_row, column=3,sticky=W+E)	
	
		clear_b=create_image_button(Main,".TexFlasher/pictures/clear.png",40,40)
		clear_b.configure(state=DISABLED)
		clear_b.grid(row=self.c.menu_row, column=4,sticky=W+E)		
		self.c.save_b=save_b
		self.c.clear_b=clear_b
		self.c.back_b=back_b
		self.c.edit_b=edit_b
		
		#stats	
		stat_height=40
		stat_width=int(float(WIDTH)*0.95)
		stat=Canvas(Main,width=stat_width, height=stat_height)
		stat.grid(row=4, columnspan=5)
		stat.height=stat_height
		stat.width=stat_width
		
		self.c.stat=stat
	
	
		#fc_content
		self.c.fc_row=5
		self.c.grid(row=self.c.fc_row,columnspan=5,sticky=N+E+W+S)
	
	
		#spacer
		Label(Main,height=1).grid(row=6,columnspan=5)	
	
		#true false
		self.c.true_false_row=7
		true_b=create_image_button(Main,"./.TexFlasher/pictures/Flashcard_correct.png",80,80)
		false_b=create_image_button(Main,"./.TexFlasher/pictures/Flashcard_wrong.png",80,80)
		true_b.grid(row=self.c.true_false_row, column=0, sticky=E+W )
		false_b.grid(row=self.c.true_false_row, column=4, sticky=W+E)
		self.c.true_b=true_b
		self.c.false_b=false_b
	
		self.c.tag_buttons=[]
		
		q_b=create_image_button(Main,".TexFlasher/pictures/question_fix.png",35,35)
		q_b.grid(row=self.c.true_false_row,column=2,sticky=N+W)
		q_b.grid_remove()
		self.c.q_b=q_b
		
		w_b=create_image_button(Main,".TexFlasher/pictures/watchout_fix.png",35,35)
		w_b.grid(row=self.c.true_false_row,column=2,sticky=S+W)
		w_b.grid_remove()
		self.c.w_b=w_b
		
		r_b=create_image_button(Main,".TexFlasher/pictures/repeat_fix.png",35,35)
		r_b.grid(row=self.c.true_false_row,column=2,sticky=N+E)
		r_b.grid_remove()
		self.c.r_b=r_b
		
		l_b=create_image_button(Main,".TexFlasher/pictures/link_fix.png",35,35)
		l_b.grid(row=self.c.true_false_row,column=2,sticky=S+E)		    
		l_b.grid_remove()
		self.c.l_b=l_b
		
		self.c.tag_buttons=[q_b,w_b,r_b,l_b]	
		#gallery
	#	flow_c=Canvas(top,height=90,width=600,bd=3)
	#	flow_c.grid(row=c.true_false_row,column=1,columnspan=3)
	#	flow=Flow(disp_single_fc,flow_c,)
	#	c.flow=flow
	#	pdict={}
	#	i=0
	#	for item in c.order.getElementsByTagName('order_db')[0].childNodes:
	#	  pdict[int(item.getAttribute('position'))]={"path": selected_dir+"/Flashcards/"+item.tagName+"-1.png", "desc":"Page: 	"+c.source.getElementsByTagName(item.tagName)[0].getAttribute('page'), "tag":item.tagName}	
	#	  i+=1
	#	flow.show_gallery(flow_c,3, pdict)
	
		#footer
		#Label(Main,font=("Helvetica",8),text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer",width=int(100.0*float(WIDTH/1000.))).grid(row=8,sticky=S,columnspan=5)
	
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

		drawCardHistory( self.ldb.getElementsByTagName(flashcard_name)[0], self.c.stat )
		image = Image.open(self.selected_dir+"/Flashcards/"+flashcard_name+"-1.png")
		image = image.resize((int(self.c.cget("width")),int(self.c.cget("height"))), Image.ANTIALIAS)
		
		flashcard_image = ImageTk.PhotoImage(image)
		
		self.c.create_image(int(flashcard_image.width()/2), int(flashcard_image.height()/2), image=flashcard_image,tags=("frontside",flashcard_name))
		self.c.img=flashcard_image
		self.c.bind("<Button-1>", lambda e:self.answer(flashcard_name, listPosition))
		self.c.unbind("<Motion>")
		self.c.unbind("<Enter>")
		self.c.edit_b.config(state=DISABLED)
		self.c.save_b.config(state=DISABLED)
		self.c.clear_b.config(state=DISABLED)
		self.c.back_b.config(state=DISABLED)
		self.c.back_b.config(state=DISABLED,command=lambda:self.reactAndInit( True , listPosition-1,False))
	
		
		self.c.true_b.configure(state=DISABLED)
		self.c.false_b.configure(state=DISABLED)

		for tag in self.c.tag_buttons:
			tag.grid_remove()

		flashcardsTodo=len(self.agenda)
		totalNumberCards=len(self.ldb.childNodes)
	
		
		level = self.ldb.getElementsByTagName(flashcard_name)[0].getAttribute('level')
		color, foo = getColor( int(level), 7)
		page=self.c.source.getElementsByTagName(flashcard_name)[0].getAttribute('page')
		fc_pos=int(self.c.order.getElementsByTagName(flashcard_name)[0].getAttribute('position'))
	
		self.c.fc_det_left.set("Flashcards (left today / total number): "+str(flashcardsTodo-listPosition)+" / "+str(totalNumberCards))	
	   	self.c.fc_det_right.set("Flashcardnr.: "+str(fc_pos)+", Page: "+str(page)+", Level: "+ str(level) +"  ")


	def answer(self,flashcard_tag, listPosition):
		#self.c.config(width=WIDTH,height=WIDTH*0.6)	# check if window size changed
		image = Image.open(self.selected_dir+"/Flashcards/"+flashcard_tag+"-2.png")
		image = image.resize((int(self.c.cget("width")),int(self.c.cget("height"))), Image.ANTIALIAS)
		flashcard_image = ImageTk.PhotoImage(image)
		for im in self.c.find_withtag("frontside"):
		   self. c.delete(im)
		for item in self.c.find_withtag('old'):#first clear possible rects from canvas
			self.c.delete(item)
		for item in self.c.find_withtag('elem'):#first clear possible rects from canvas
			self.c.delete(item)	
		
		self.c.create_image(int(flashcard_image.width()/2), int(flashcard_image.height()/2), image=flashcard_image,tags=("backside",flashcard_tag))	
		self.c.img=flashcard_image			
	
		self.c.unbind("<Button-1>")
		self.c.edit_b.configure(state=NORMAL,command=lambda:edit_fc(self.c,self.selected_dir,flashcard_tag))
		self.c.back_b.configure(state=NORMAL)
		self.c.true_b.configure(state=NORMAL,command=lambda:self.reactAndInit(True, listPosition))
		self.c.false_b.configure(state=NORMAL,command=lambda:self.reactAndInit(False, listPosition))
	
		#drawCardHistory( ldb.getElementsByTagName(flashcard_tag)[0], c.stat )
		
		create_comment_canvas(self.c,self.selected_dir,flashcard_tag,Settings['user'])	
	
		for tag in self.c.tag_buttons:
			tag.grid()
		self.c.l_b.config(command=self.c.rect.link_tag)
		self.c.r_b.config(command=self.c.rect.repeat_tag)
		self.c.w_b.config(command=self.c.rect.watchout_tag)
		self.c.q_b.config(command=self.c.rect.question_tag)
	
		#fc_pos=int(c.order.getElementsByTagName(flashcard_tag)[0].getAttribute('position'))
		#c.flow.goto(fc_pos)
		
		#mainloop()
	
	
		


############################################################## Menu ####################################################################







def update_texfile( fname, user ):	
	executeCommand( "bash .TexFlasher/scripts/updateFiles.sh "+os.path.dirname(fname), True )
	#executeCommand( "bash .TexFlasher/scripts/updateFiles.sh "+fname+" "+os.path.dirname(fname)+"/Users", True )
	#executeCommand( "bash .TexFlasher/scripts/updateFiles.sh "+os.path.dirname(fname)+"/Users/"+user+".xml "+os.path.dirname(fname)+"/Users/"+user+"_comment.xml "+fname, True )
	os.system("rm "+os.path.dirname(fname)+"/Flashcards/UPDATE 2>/dev/null")
	create_flashcards( fname )
	comp_list=create_completion_list()
 	message,window_type=get_log_status(os.path.dirname(fname))
 	if window_type=="showerror":
		exec('tkMessageBox.'+window_type+'( "Parse LaTex Logfile","%s")'%message)	
	menu()
	

def saveFiles(master):
	if checkIfNeedToSave( saveString ):
		if tkMessageBox.askyesno("Quit?", "Do you want to save your changes on the server?"):
			executeCommand( "bash .TexFlasher/scripts/save.sh "+ saveString, True )
			master.quit()
		else:
			master.quit()	
	else:
		master.quit()
		
def create_new():
	file = tkFileDialog.askopenfilename(parent=Main,title='Choose a LaTeX file',initialdir='./',defaultextension=".tex",filetypes=[("all files","*.tex")])
	if file != None:
		update_config(file)
		menu()


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
	xml_file = open("./.TexFlasher/config.xml", "w")
	config_xml.writexml(xml_file)
	xml_file.close()
	menu()


def reset_flash(filename):
	if tkMessageBox.askyesno("Reset", "Do you really want to delete all learning progress for %s?"% filename.split("/")[-2]):
		try:
			os.remove(os.path.dirname(filename)+"/Users/"+Settings["user"]+".xml")
			os.remove(os.path.dirname(filename)+"/Users/"+Settings["user"]+"_comment.xml")
		except:
			pass
		hide_FlashFolder(filename)
	menu()


def clear_window():
	info=Main.grid_info()
	Main.grid_remove()
	Main.grid(row=info['row'],column=info['column'])
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
	display_mult_fcs(tagged,"Tagged in "+dir,"Menu","lambda:menu()","./.TexFlasher/pictures/menu.png")

        
        

def open_tex(filepath):
	try:
		os.system("(nohup "+Settings["editor"]+" "+filepath+" > /dev/null &) 2> /dev/null")
	except:
		tkMessageBox.showerror( "LaTeX Editor Variable","Please check, if your LaTeX Editor is set correctly in run-TexFlasher.sh")




class MyDialog:

    def __init__(self, parent):

        top = self.Main = Toplevel(parent)

        Label(top, text="Please enter a new flashfolder name:").pack()

        self.e = Entry(top)
        self.e.pack(padx=5)

        b = Button(top, text="Create", command=self.ok)
        b.pack(pady=5)

    def ok(self):

        print "value is", self.e.get()
        if self.e.get():
        	value=self.e.get().strip(" \n\r")
        	os.system("bash .TexFlasher/scripts/createFolder.sh "+value)
		dir=os.path.abspath("./"+value+"/")
		#print dir
		update_config(dir+"/Vorbereitung.tex")
		menu()
        self.top.destroy()
        
def create_folder():
	d = MyDialog(Main)
	Main.wait_window(d.Main)

	
	
def check_tags(xml_path,tagtype):
	if os.path.isfile(xml_path):
		try:
			return 	len(xml.parse(xml_path).getElementsByTagName(tagtype)[0].childNodes) 
		except:
			return None
    
	


def menu():
	global Main
	bordersize=2
	clear_window()
	Main.columnconfigure(0,weight=0)
	Main.columnconfigure(1,weight=1)
	Main.columnconfigure(2,weight=0)
	Main.columnconfigure(3,weight=0)
	Main.columnconfigure(4,weight=0)	
	Main.master.title("Menu") 

		#self.rowconfigure( 1, weight = 2 )
		#self.columnconfigure( 1, weight = 1 )	
	button_size=str(40)
	global saveString 
	saveString = ""



	row_start=3
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('config')[0]		
		for l in config_xml.childNodes:

			Widgets={}
			if l.tagName=="FlashFolder" and l.getAttribute('filename')!="" and os.path.isfile(l.getAttribute('filename')):
				todo=0;
				length=0
				#try:
				ldb= load_leitner_db(os.path.dirname(l.getAttribute('filename')),Settings["user"])
				today,new=load_agenda(ldb,os.path.dirname(l.getAttribute('filename')))
				todo=len(today)
				length=len(ldb.childNodes)
			#	except:
			#		pass
				start_column=0
				log,window_type=get_log_status(os.path.dirname(l.getAttribute('filename')))
				


				button_status="NORMAL"
				if length==0:
					button_status="DISABLED"
				new_status="NORMAL"					
				#open folder
				if todo-new>0:
					exec('button_' + str(row_start)+'_open =create_image_button(Main,"./.TexFlasher/pictures/Flashcard_folder_red.png",60,60)')
					exec('button_' + str(row_start)+'_open.configure(width=70,state='+button_status+',command=lambda:Flasher("'+os.path.dirname(l.getAttribute('filename'))+'", True))')	
				elif new >0:
					exec('button_' + str(row_start)+'_open =create_image_button(Main,"./.TexFlasher/pictures/Flashcard_folder_yellow.png",60,60)')
					exec('button_' + str(row_start)+'_open.configure(width=70,state='+button_status+',command=lambda:Flasher("'+os.path.dirname(l.getAttribute('filename'))+'", True))')
				else:
					exec('button_' + str(row_start)+'_open =create_image_button(Main,"./.TexFlasher/pictures/Flashcard_folder.png",60,60)')
					exec('button_' + str(row_start)+'_open.configure(width=70,state='+button_status+',command=lambda:Flasher("'+os.path.dirname(l.getAttribute('filename'))+'", False))')
									
				exec('button_' + str(row_start)+'_open.grid(row='+str(row_start)+',sticky=N+W+S+E,column='+str(start_column)+')')
				#folder desc
				exec('fc_folder_' + str(row_start)+'_desc=Label(Main,justify=LEFT,text="'+l.getAttribute('filename').split("/")[-2]+'\\nlength: '+str(length)+'\\ntodo: '+str(todo-new)+', new: '+str(new)+'\\nupdated: '+l.getAttribute('lastReviewed')+'").grid(row='+str(row_start)+', column='+str(start_column+1)+',sticky=W)')

				#tags
				tag_xml_path=os.path.dirname(l.getAttribute('filename'))+"/Users/"+Settings['user']+"_comment.xml"
				q_b=create_image_button(Main,".TexFlasher/pictures/question_fix.png",40,40,0)
				q_b.grid(row=row_start,column=start_column+2,sticky=N+W+E+S)
				q_length=check_tags(tag_xml_path,"question")
				if q_length==None or q_length==0:
				   q_b.config(state=DISABLED)
				#else:
				#   Label(Main,text=str(q_length)).grid(row=row_start,column=start_column+2,sticky=S)
				exec("q_b.config(command=lambda:show_tagged('question','"+os.path.dirname(l.getAttribute('filename'))+"','"+tag_xml_path+"'))")
				w_b=create_image_button(Main,".TexFlasher/pictures/watchout_fix.png",40,40,0)
				w_b.grid(row=row_start,column=start_column+3,sticky=N+S+E+W)
				w_length=check_tags(tag_xml_path,"watchout")
				if w_length==None or w_length==0:
				   w_b.config(state=DISABLED)	
				exec("w_b.config(command=lambda:show_tagged('watchout','"+os.path.dirname(l.getAttribute('filename'))+"','"+tag_xml_path+"'))")
   
				r_b=create_image_button(Main,".TexFlasher/pictures/repeat_fix.png",40,40,0)
				r_b.grid(row=row_start,column=start_column+4,sticky=N+W+E+S)
				r_length=check_tags(tag_xml_path,"repeat")
				if r_length==None or r_length==0:
				   r_b.config(state=DISABLED)	
				exec("r_b.config(command=lambda:show_tagged('repeat','"+os.path.dirname(l.getAttribute('filename'))+"','"+tag_xml_path+"'))")

				l_b=create_image_button(Main,".TexFlasher/pictures/link_fix.png",40,40,0)
				l_b.grid(row=row_start,column=start_column+5,sticky=N+W+E+S)
				l_length=check_tags(tag_xml_path,"link")
				if l_length==None or l_length==0:
				   l_b.config(state=DISABLED)	
				exec("l_b.config(command=lambda:show_tagged('link','"+os.path.dirname(l.getAttribute('filename'))+"','"+tag_xml_path+"'))")

				start_column+=6
				
				#update
				if os.path.isfile(os.path.dirname(l.getAttribute('filename'))+"/Flashcards/UPDATE"):
					update_image="./.TexFlasher/pictures/update_now.png"
				else:
					update_image="./.TexFlasher/pictures/update.png"
				if l.getAttribute('lastReviewed')==l.getAttribute('created'):
					exec('button_' + str(row_start)+'_update=create_image_button(Main,"./.TexFlasher/pictures/update_now.png",'+button_size+','+button_size+')')
					exec('button_' + str(row_start)+'_update.configure(command=lambda:update_texfile("'+l.getAttribute('filename')+'", "'+Settings["user"]+'"))')
					exec('button_' + str(row_start)+'_update.grid(row='+str(row_start)+',column='+str(start_column+2)+',sticky=W+N+S+E)')
					new_status="DISABLED"
				else:
					exec('button_' + str(row_start)+'_update=create_image_button(Main,"'+update_image+'",'+button_size+','+button_size+')')
					exec('button_' + str(row_start)+'_update.configure(command=lambda:update_texfile("'+l.getAttribute('filename')+'","'+Settings["user"]+'"))')
					exec('button_' + str(row_start)+'_update.grid(row='+str(row_start)+',column='+str(start_column+2)+',sticky=W+N+S+E)')		

				#stats	
				exec('button_' + str(row_start)+'_stat=create_image_button(Main,"./.TexFlasher/pictures/stat.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start)+'_stat.configure(state='+button_status+',command=lambda:statistics_nextWeek("'+os.path.dirname(l.getAttribute('filename'))+'"))')
				exec('button_' + str(row_start)+'_stat.grid(row='+str(row_start)+',column='+str(start_column+3)+',sticky=N+S+W+E)')
				#open tex file
				exec('button_' + str(row_start)+'_tex =create_image_button(Main,"./.TexFlasher/pictures/latex.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start)+'_tex.configure(command=lambda:open_tex("'+l.getAttribute('filename')+'"))')
				exec('button_' + str(row_start)+'_tex.grid(row='+str(row_start)+',column='+str(start_column+4)+',sticky=W+N+S+E)')
				#log
				exec('button_' + str(row_start)+'_log=create_image_button(Main,"./.TexFlasher/pictures/'+window_type+'.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start) + '_log.configure(state='+new_status+',command=lambda:show_log("'+os.path.dirname(l.getAttribute('filename'))+'"))')
				exec('button_' + str(row_start)+'_log.grid(row='+str(row_start)+',column='+str(start_column+5)+',sticky=N+S+E+W)')
				#reset
				exec('button_' + str(row_start)+'_res=create_image_button(Main,"./.TexFlasher/pictures/delete.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start)+'_res.configure(command=lambda:reset_flash("'+l.getAttribute('filename')+'"))')
				exec('button_' + str(row_start)+'_res.grid(row='+str(row_start)+',column='+str(start_column+7)+',sticky=N+S+E)')
				saveString += " "+ os.path.dirname(l.getAttribute('filename'))+"/Users/"+Settings["user"]+".xml"
				saveString += "###"+ os.path.dirname(l.getAttribute('filename'))+"/Users/"+Settings["user"]+"_comment.xml"
				#saveString += "###"+ os.path.dirname(l.getAttribute('filename'))+"/Users/questions.xml"
				saveString += "###"+ l.getAttribute('filename') 
				exec('Label(Main,height=1).grid(row='+str(row_start+1)+')')
				row_start+=2	

	#print saveString
	#create button
	create=create_image_button(Main,"./.TexFlasher/pictures/Flashcard_folder_add.png",60,60)
	create.configure(width=70,command=create_new) 
	create_n=create_image_button(Main,"./.TexFlasher/pictures/Flashcard_folder_create.png",40,40)
	create_n.configure(width=70,command=create_folder)
	if row_start > 3:
		create.grid(row=1,column=0,sticky=W)
		#search field
		query=Search(Main)
		query.set_completion_list(comp_list)
		query.grid(row=1,column=1,columnspan=5,sticky=E+W+N+S)
			
		create_n.grid(row=1,column=8,columnspan=6,sticky=N+W+S+E)		
		Label(Main,height=1).grid(sticky=E+W,row=2,columnspan=10)
	else:
		create_n.grid(row=row_start+2,columnspan=8)			
		create.grid(row=row_start+1,columnspan=8)
	#footer

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
Settings = { 'user':'',
						'editor':''
	}	
readSettings( Settings )

global WIDTH, HEIGHT


window = gtk.Window()
screen = window.get_screen()
HEIGHT=int ( min( screen.get_height(), screen.get_width())*0.9 )
WIDTH=HEIGHT

# just to be on the safe side
if(screen.get_width() < WIDTH):
	WIDTH = screen.get_width()





BD=2
RESTART_TIME=5 

IK=ImageKeeper()

comp_list=create_completion_list()

iconbitmapLocation = "@./.TexFlasher/pictures/icon2.xbm"


class TexFlasher(Frame):
	def resize(self,event):
		global WIDTH, HEIGHT
		
		WIDTH=self.master.winfo_width()-20
		HEIGHT=self.master.winfo_height()
		self.configure(bd=10,height=p2c(None,HEIGHT,[90]),width=p2c(WIDTH,None,[100]))
#		Wi=WIDTH+20 #width of the outer window frame
#		Hi=WIDTH
#		ws = self.master.winfo_screenwidth()
#		hs = self.master.winfo_screenheight()		
#		xs = (ws/2) - (int(Wi)/2) 
#		ys = (hs/2) - (Hi/2)				
#		self.master.geometry(str(int(Wi))+"x"+str(Hi)+"+"+str(xs)+"+"+str(ys))
		
		
	def __init__( self ):
		Frame.__init__( self)
		global WIDTH, HEIGHT		
		self.master.bind("<Configure>", self.resize)
		global Main
		Main=self
		self._running_classes={}
		
		self.master.rowconfigure( 0, weight = 1 )
		self.master.columnconfigure( 0, weight = 1 )	
		self.master.rowconfigure( 2, weight = 1 )
		header_height=20
		footer_height=20		



		
		self.configure(bd=10,height=HEIGHT-footer_height-header_height,width=WIDTH)			
		self.grid(row=1,column=0,sticky=N+E+W)
		self.grid_propagate(False) 	
		self._version="unstable build"

		ws = self.master.winfo_screenwidth()
		hs = self.master.winfo_screenheight()
		# calculate position x, y
		Wi=WIDTH+20 #width of the outer window frame
		Hi=HEIGHT
		xs = (ws/2) - (int(Wi)/2) 
		ys = (hs/2) - (Hi/2)				
		self.master.geometry(str(int(Wi))+"x"+str(Hi)+"+"+str(xs)+"+"+str(ys))
		self.master.iconbitmap(iconbitmapLocation)
		self.master.iconmask(iconbitmapLocation)	
			
		self.master.protocol('WM_DELETE_WINDOW',lambda:saveFiles(self.master))
		self.master.bind("<Escape>", lambda e: self.master.quit()) # quits texflasher if esc is pressed		
		self.master.title("TexFlasher - "+self._version)
				
		
		#if Settings["user"] is not  "x":
		Header=Frame(self.master,height=header_height).grid(row=0,columnspan=8,sticky=E+W+N)
		Label(self.master,height=2,text="TexFlasher based on Leitner-Method",font=("Helvetica", 16,"bold")).grid(row=0,sticky=E+W+N)		
		Footer=Frame(self.master,height=footer_height).grid(row=2,sticky=S+E+W)
		Label(Footer,height=2,font=("Helvetica",8),text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer").grid(row=3,sticky=S+E+W)
		
		menu()

TexFlasher().mainloop()

