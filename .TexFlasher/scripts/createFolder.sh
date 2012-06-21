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

echo "IMPORTANT: The folder you are about to create will not be managed by svn."
echo "           You will not have the possibility to share this folder with   "
echo "           your friends or colleagues."
echo 

if [ -d "$foldername" ]; then 
	echo "Error: $foldername already exists."
	exit 1
fi

if [ $2 ]; then
	svn info $2 &> /dev/null
	VALID=$?
	if [ ! $VALID ]; then
		echo "Error: svn URL not valid!"
		exit 1
	fi
	svn co $2 $1
else
	mkdir -vp $foldername/Flashcards
	mkdir -vp $foldername/Users
	mkdir -vp $foldername/Details

	cp .TexFlasher/Example.tex -vp $foldername/Vorbereitung.tex
fi
