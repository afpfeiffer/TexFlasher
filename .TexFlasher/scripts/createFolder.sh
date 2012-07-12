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


if [ ! $1 ]; then
	echo "Error: no target dir was passed to $0."
	exit 1
fi

foldername=$1


if [ -d "$foldername" ]; then 
	echo "Error: $foldername already exists."
	exit 1
fi

ping -c 1 www.google.com>>/dev/null
if [ $? -eq  0 ]; then
	if [ $2 ]; then
		svn info $2 &> /dev/null
		VALID=$?
		if [ ! $VALID ]; then
			echo "Error: svn URL not valid!"
			exit 1
		fi
		svn co $2 $foldername
		if [ ! -d $foldername/Flashcards ]; then
			svn mkdir -vp $foldername/Flashcards
		fi
		if [ ! -d $foldername/Users ]; then
			svn mkdir -vp $foldername/Users
		fi
		if [ ! -d $foldername/Details ]; then
			svn mkdir -vp $foldername/Details
		fi
		if [ ! -f $foldername/Vorbereitung.tex ]; then
			cp .TexFlasher/Example.tex -vp $foldername/Vorbereitung.tex
		fi
		
		svn add $foldername/Vorbereitung.tex
		svn commit $foldername -m "initial commit"
	else
		mkdir -vp $foldername/Flashcards
		mkdir -vp $foldername/Users
		mkdir -vp $foldername/Details

		cp .TexFlasher/Example.tex -vp $foldername/Vorbereitung.tex
	fi
else
	echo "Error: no internet connection available!"
fi
