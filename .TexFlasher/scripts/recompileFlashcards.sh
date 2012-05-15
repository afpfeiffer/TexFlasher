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
echo "Recompiling flashcards."
echo

WD=$PWD

file=$1
   
folder=$(dirname $file)
filebase=$(basename $file)
# get filename without extension
purefilebase=${filebase%\.*}  

# check if svn is available in subfolder
svn info $file > /dev/null
HAVESVN=$?
 
# # check if Flashcards - folder exists, otherwise create it
# if [ ! -d "$folder/Flashcards" ]; then
#   echo "creating subfolder Flashcards"
#   svn mkdir $folder/Flashcards
#   svn propset svn:ignore -F .TexFlasher/svnignore $folder/Flashcards/
#   svn commit $folder/Flashcards -m  "new folder created"
#   if [ ! -d "$folder/Flashcards" ]; then
#     echo "error: folder could not be created"
#   fi
# fi

FILES="Makefile pdf2jpg_dummy.sh dvi2png_dummy.sh flashcards.cls"

# get current versions of files 
for thing in $FILES; do
	cp $WD/.TexFlasher/tools/$thing $folder/Flashcards/
	cp $WD/.TexFlasher/tools/$thing $folder/Details/
done

 
	# create a temprorary folder for flashcards. make sure its empty
	if [ -d "$folder/Flashcards.tmp" ]; then 
		rm -rf $folder/Flashcards.tmp
	fi

	cp $file $folder/Details/	

	mkdir $folder/Flashcards.tmp
  
  echo "parsing ..." | tee  $folder/texFlasher.log
	python "$WD/.TexFlasher/parse_tex.py" "$file"  "%###%"  "%fc=" "$folder/Flashcards.tmp"  | tee -a $folder/texFlasher.log
	cp $file $folder/Flashcards/$purefilebase.bak
  
  recompile="0"
	compilenumber="0"
	newnumber="0"
	# buffer old flash cards
	OLDFLASHCARDS="`ls $folder/Flashcards/*.tex`" 2>/dev/null
	for oldflashcard in $OLDFLASHCARDS; do
    # get filename with extension
    name=$(basename $oldflashcard)
    # get filename without extension
    purename=${name%\.*}

		
    if [ -f $folder/Flashcards.tmp/$name ]; then
      if [[ "`diff $folder/Flashcards.tmp/$name $folder/Flashcards/$name`" == "" ]]; then
        # file has not changed, we don't want it to be overwritten
        # (not even by identical file) in order to preserve the timestamp
        # which is important for the Makefile
        rm $folder/Flashcards.tmp/$name
        if [ ! -f $folder/Flashcards/$purename.dvi ]; then
					compilenumber=`echo $compilenumber + "1" | bc`
				fi

					
      else
				recompile=`echo $recompile + "1" | bc`
				
				ts="`date +%s`"
				echo "changed content: $folder/Flashcards/$purename" | tee -a $folder/texFlasher.log
      fi
    else 
      # delete files, that are no longer used!
      rm $folder/Flashcards/old_$purename*
      rm $folder/Flashcards/$purename.*
      rm $folder/Flashcards/$purename-*.png
    fi
  done

  listnumber="`ls -1 $folder/Flashcards.tmp/ | wc -l`"
  compilenumber=`echo $compilenumber + $listnumber | bc`
  newnumber=`echo $compilenumber - $recompile | bc`
  
  cp $folder/Flashcards.tmp/* $folder/Flashcards/ 2> /dev/null
  rm -r $folder/Flashcards.tmp
  
  cd $folder/Flashcards
  echo "recompiling card(s):" | tee -a $folder/texFlasher.log
	echo "  -> $recompile card(s) with changed content" | tee -a $folder/texFlasher.log
	echo "  -> $newnumber new card(s)" | tee -a $folder/texFlasher.log
  echo "please wait, this can take several minutes..."
	procs=1
    if [ "`uname`" == "Linux" ] ; then
      procs="`grep -c processor /proc/cpuinfo`"
    elif [ "`uname`" == "Darwin" ] ; then
      procs="`/usr/sbin/system_profiler -detailLevel full SPHardwareDataType | grep -i 'number of cores' | awk '{ print $5 }'`"
    fi
  make -j$procs images 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error' | tee -a $folder/texFlasher.log
  cd $WD
  
  cd $folder/Details
  make -j$procs images 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error' | tee -a $folder/texFlasher.log

    
  echo "done"


exit 0
