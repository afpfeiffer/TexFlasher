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
txtred=$(tput setaf 1) # Red

for thing in $files; do
# 	echo $thing
		seperatedFiles="`echo $thing | sed -e 's/###/ /g'`"
# 	echo $seperatedFiles
		touch $seperatedFiles
		svn add $seperatedFiles 2> /dev/null  
		svn info $seperatedFiles > /dev/null
		HAVESVN=$?
		
		echo "processing: "
		for files in $seperatedFiles; do
			fulldiff="`svn diff $files`" > /dev/null
			if [ "$fulldiff" == "" ]; then			
				echo "  -> $files"
			else
				echo "  -> ${txtred}$files ${txtrst} "
			fi
		done
		echo
		for files in $seperatedFiles; do
			fulldiff="`svn diff $files`" > /dev/null			
			if [ $HAVESVN -eq 0 ]; then
#	 				echo "svn available for this file"
				if [ "$fulldiff" != "" ]; then
					svn up $files
					svn commit $files -m "save learning progress"
# 				else
# 					echo "$files unchanged"

				fi	
			else
				echo "Warning: svn unavailable for this folder. Files are always saved on HD."
			fi
		done
		echo
done
exit 0