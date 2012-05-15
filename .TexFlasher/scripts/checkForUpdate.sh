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


files=$*

for thing in $files; do
	svn info $thing > /dev/null
	HAVESVN=$?
	if [ $HAVESVN -eq 0 ]; then
# 		echo "svn available for this file"
		folder=$(dirname $thing)
		filebase=$(basename $thing)
		# get filename without extension
		purefilebase=${filebase%\.*} 
		
		if [ ! -f $folder/Flashcards/UPDATE ]; then
			if [[ ! -f $folder/Flashcards/$purefilebase.bak ]]; then
				touch $folder/Flashcards/$purefilebase.bak
				echo "" > $folder/Flashcards/UPDATE
			else
				if [[ "`diff $folder/Flashcards/$purefilebase.bak $thing`" != "" ]]; then
					echo "" > $folder/Flashcards/UPDATE
				fi
			fi
			
			ownRev="`svn info $thing | grep Revision: | cut -d " " -f 2`"
#	 		echo $ownRev
			server="`svn info $thing| grep 'URL' | cut -d " " -f 2`"
			serverRev="`svn info $server | grep Revision: | cut -d " " -f 2`"
#	 		echo $serverRev
			if [ "$serverRev" != "$ownRev" ]; then
# 				echo svn info $server | grep "Last Changed Author:" | cut -d ":" -f 2 | cut -d " " -f 2 > $folder/Flashcards/UPDATE
# 				echo "`date`: revisions differ: $serverRev, $ownRev"
				echo "" > $folder/Flashcards/UPDATE
			fi
		fi
	fi
# 	else
# 		echo "svn unavailable"
done

exit 0