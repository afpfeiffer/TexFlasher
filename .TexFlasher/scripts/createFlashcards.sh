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
echo "(Re-)Compiling flashcards."
echo

WD=$PWD

file=$1
user=$2
   
folder=$(dirname $file)
filebase=$(basename $file)
# get filename without extension
purefilebase=${filebase%\.*}  
lastFolder="`python .TexFlasher/scripts/repoName.py $file`"

## Update Cards
ToBeUpdated="$filebase Users/$user.xml Users/${user}_comment.xml Users/questions.xml"
for element in $ToBeUpdated; do
	echo "looking at $element"
	path1="$WD/$lastFolder/$element"
	path2="$WD/.$lastFolder/$element"
	svndiff1="`svn diff $path1`" > /dev/null
	# check if we modified the file
	if [ "$svndiff1" == "" ]; then
		echo "you did not modify $element"
		# if we did not modify the file, we only need to check, if a new revision is online.
		# if that is 
		localdiff1="`diff $path1 $path2`"
		if [ "$localdiff1" != "" ]; then
			echo "a newer version of $element is available"
			# a new version is out there. We assuem that path2 holds a reasonably new version (less than 10 min)
			cp $path2 $path1
			rev2="`svn info $path2 | grep Revision | cut -d ' ' -f 2`"
			svn up -r$rev2 $path1 & #don't wait for me to finish, this is just to make sure the revisions are up to date...
		fi
	else
		rev1="`svn info $path1 | grep Revision | cut -d ' ' -f 2`"
		rev2="`svn info $path2 | grep Revision | cut -d ' ' -f 2`"
		if [ "$rev1" != "$rev2"  ]; then
			#this means merging work is to be done. we don't bypass svn here.
			echo "you have modified $element, as has someone else => svn merge"
			svn up $path1
		fi
	fi	
done


sleep 20
# some files in tools folder
FILES="Makefile pdf2jpg_dummy.sh dvi2png_dummy.sh flashcards.cls"

# get current versions of files 
for thing in $FILES; do
	cp $WD/.TexFlasher/tools/$thing $folder/Flashcards/
done


if [[ ! -f $folder/Flashcards/$purefilebase.bak ]]; then
   touch $folder/Flashcards/$purefilebase.bak
fi
# create all new flashcards in temporary folder
# echo "$folder/Flashcards/$purefilebase.bak $file"
if [[ "`diff $folder/Flashcards/$purefilebase.bak $file`" == "" ]]; then
  echo "flashcards up to date" 
  echo "done"
else 
	cp $file $folder/Details/source.tex
	rm $folder/texFlasher.log
	cd $folder/Details
	latex $folder/Details/source.tex 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error' | tee -a $folder/texFlasher.log
	
	Errors="`cat $folder/texFlasher.log | grep -rniE 'error|ERROR|Error'`"
	if [ ! "$Errors" == ""  ]; then
		echo "Fatal latex error in source file." >> $folder/texFlasher.log
		exit 1
	fi
	python $WD/.TexFlasher/diviasm.py source.dvi > source.dump	
	cd $WD
	# create a temprorary folder for flashcards. make sure its empty
	if [ -d "$folder/Flashcards.tmp" ]; then 
		rm -rf $folder/Flashcards.tmp
	fi
  
	mkdir $folder/Flashcards.tmp
  
  echo "parsing ..." | tee  $folder/texFlasher.log
	python "$WD/.TexFlasher/parse_tex.py" "$folder/Flashcards.tmp" "$folder/Details" | tee -a $folder/texFlasher.log
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
  echo "compiling card(s):" | tee -a $folder/texFlasher.log
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
    
#  cd $folder/Details
#  latex $folder/Details/source.tex
#   make -j$procs pdf 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error' | tee -a $folder/texFlasher.log    
  echo "done"


fi  

# update shaddow folder in background
svn up ".$lastFolder" &

exit 0
