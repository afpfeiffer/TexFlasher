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

# DEACTIVATED TODO NOTE FIXME
exit 0

FILENAME=${1%\.*}

echo "compiled flashcard $FILENAME"
convert -density 400 $FILENAME.pdf -quality 50 -crop 1910x1130+745+490 $FILENAME.jpg
convert $FILENAME-0.jpg -quality 100 -resize 360x216 $FILENAME-thumb360x216.jpg

