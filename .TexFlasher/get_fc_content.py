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

def get_content(fcard_tex):
	try:
		source_tex=open(fcard_tex,"r")
	except:
		print "Fatal Error: Cannot open file: "+fcard_tex+"!"
		sys.exit()
	content=False
	for line in source_tex:
		if line.lstrip().startswith("%"):
		    line=source_tex.next()
		if re.compile('^\\\\begin\{flashcard\}').findall(line.lstrip()) and not content:
			content=True
		if content:
			print line
		if re.compile('^\\\\end\{flashcard\}').findall(line.lstrip()) and content:
			break	
get_content(sys.argv[1])															
