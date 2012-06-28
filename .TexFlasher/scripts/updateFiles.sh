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
echo "Updating files."
echo


folder=$1

echo "processing: $folder"

echo

ping -c 1 www.google.com>>/dev/null
if [ $? -eq  0 ]; then
	svn info $folder &> /dev/null

	HAVESVN=$?
	if [ $HAVESVN -eq 0 ]; then
		svn up $folder
		echo
	else
		echo "Folder not under svn control."
		echo
	fi
else
	echo "Error: no internet connection available!"
	echo
fi
exit 0


# files=$*
# 
# echo "processing: "
# for thing in $files; do
# 	echo "  -> $thing"
# done
# echo
# 	
# folder=""
# for thing in $files; do
# 	folder=$(dirname $thing)
# done
# 
# svn info $folder &> /dev/null
# 
# HAVESVN=$?
# if [ $HAVESVN -eq 0 ]; then
# 	svn up $files
# 	echo
# else
# 	echo "svn unavailable"
# 	echo
# fi
# 
# exit 0


