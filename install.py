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


import sys
import os
import subprocess

def main(argv=None):
	
	# initialize copyright
	COPYRIGHT=[]
	with open( '.TexFlasher/copyright.txt', 'r' ) as f:
		COPYRIGHT=f.readlines()
  

  # print copyright
	for line in COPYRIGHT:
		print line,
  


  
if __name__ == "__main__":
	main()