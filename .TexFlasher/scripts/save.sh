#!/bin/bash
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
echo
echo "                    OOOOO OOOO O   O   OOOO O     OOO  OOOO O  O OOOO OOOO"
echo "                      O   O     O O    O    O    O   O O    O  O O    O  O"
echo "                      O   OOO    O     OOO  O    OOOOO OOOO OOOO OOO  OOOO"
echo "                      O   O     O O    O    O    O   O    O O  O O    O O"
echo "                      O   OOOO O   O   O    OOOO O   O OOOO O  O OOOO O  O"
echo
echo
echo "Saving files on server:"
echo "_________________________________________________________________________________________________"
echo
echo "Please note: Your learning progress and changes, that you have made to the latex source files,"
echo "             are constantly saved on your HD. This function is ONLY neccessary to upload these"
echo "             changes onto the server(s), e.g. if you share latex sources with your friends."
echo "_________________________________________________________________________________________________"
echo 
#save files on server

files=$*

txtrst=$(tput sgr0) # Text reset
txtclr=$(tput setaf 2) 
txtbgw=$(tput setb 7) #white background
txtbld=$(tput bold) #bold
texthb=$(tput dim) #half bright

# Other variables you can define as follows:
# txtgrn=$(tput setaf 2) # Green
# txtylw=$(tput setaf 3) # Yellow
# txtblu=$(tput setaf 4) # Blue
# txtpur=$(tput setaf 5) # Purple
# txtcyn=$(tput setaf 6) # Cyan
# txtwht=$(tput setaf 7) # White
# txtrst=$(tput sgr0) # Text reset
# Following are the tput details further:
# tput setab [1-7] : Set a background colour using ANSI escape
# tput setb [1-7] : Set a background colour
# tput setaf [1-7] : Set a foreground colour using ANSI escape
# tput setf [1-7] : Set a foreground colour
# 
# tput Text Mode Capabilities:
# 
# tput bold : Set bold mode
# tput dim : turn on half-bright mode
# tput smul : begin underline mode
# tput rmul : exit underline mode
# tput rev : Turn on reverse mode
# tput smso : Enter standout mode (bold on rxvt)
# tput rmso : Exit standout mode
# tput sgr0 : Turn off all attributes (doesn’t work quite as expected)
rm SAVE &> /dev/null

ping -c 1 www.google.com>>/dev/null
if [ $? -eq  0 ]; then
	for thing in $files; do
	# 	echo $thing
			seperatedFiles="`echo $thing | sed -e 's/###/ /g'`"
	# 		echo $seperatedFiles
	# 		touch $seperatedFiles
			svn add $seperatedFiles &> /dev/null  
			

			folder=""
			for files in $seperatedFiles; do
				folder=$(dirname $files)
			done

			svn info $folder &> /dev/null
			
			HAVESVN=$?
			if [ $HAVESVN -eq 0 ]; then
				echo "processing: "
				for files in $seperatedFiles; do
					fulldiff="`svn diff $files`" > /dev/null
					if [ "$fulldiff" == "" ]; then			
						echo "  -> ${texthb}$files ${txtrst}"
					else
						echo "  -> ${txtclr}${txtbld}$files ${txtrst} "
					fi
				done
				
				for files in $seperatedFiles; do
					fulldiff="`svn diff $files`" > /dev/null			
				
	#	 				echo "svn available for this file"
					if [ "$fulldiff" != "" ]; then
						echo "${texthb}`svn up $files`${txtrst}"
						echo "${txtclr}${txtbld}`svn commit $files -m 'save learning progress'`${txtrst}"
	# 				else
	# 					echo "$files unchanged"

					fi	
				done
			fi
			echo
	done
else
	echo "Error: no internet connection available!"
fi
exit 0