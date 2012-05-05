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

file=$1
foldername=$(dirname $file)



if [ ! -d "$foldername/Karteikarten" ]; then 
	echo "Error: $foldername/Karteikarten does not exist."
	exit 1
fi

texfiles=`ls -1 $foldername/*.tex | wc -l`

if [ ! $texfiles -eq 1 ]; then
  echo "Error: No or more than one .tex files found."
  exit 1
fi

bash ./.TexFlasher/createFlashcards.sh $file

