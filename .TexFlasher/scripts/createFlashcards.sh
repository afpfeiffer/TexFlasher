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
   
folder=$(dirname $file)
filebase=$(basename $file)
# get filename without extension
purefilebase=${filebase%\.*}  

# check if svn is available in subfolder
# svn info $file > /dev/null
# HAVESVN=$?
 
# # check if Karteikarten - folder exists, otherwise create it
# if [ ! -d "$folder/Karteikarten" ]; then
#   echo "creating subfolder Karteikarten"
#   svn mkdir $folder/Karteikarten
#   svn propset svn:ignore -F .TexFlasher/svnignore $folder/Karteikarten/
#   svn commit $folder/Karteikarten -m  "new folder created"
#   if [ ! -d "$folder/Karteikarten" ]; then
#     echo "error: folder could not be created"
#   fi
# fi

FILES="Makefile pdf2jpg_dummy.sh dvi2png_dummy.sh flashcards.cls diviasm.py"

# get current versions of files 
for thing in $FILES; do
	cp $WD/.TexFlasher/tools/$thing $folder/Karteikarten/
<<<<<<< HEAD
	#cp $WD/.TexFlasher/tools/$thing $folder/Details/
=======
	cp $WD/.TexFlasher/tools/$thing $folder/Details/
>>>>>>> 3ebd262984735db66fb778d5a45666b1f1e6c78a
done


# get latest version of file (if file is under revision control)
# if [ $HAVESVN -eq 0 ]; then
# 	svn up $file
# fi

if [[ ! -f $folder/Karteikarten/$purefilebase.bak ]]; then
   touch $folder/Karteikarten/$purefilebase.bak
fi
# create all new flashcards in temporary folder
# echo "$folder/Karteikarten/$purefilebase.bak $file"
if [[ "`diff $folder/Karteikarten/$purefilebase.bak $file`" == "" ]]; then
  echo "flashcards up to date" 
  echo "done"
else 
<<<<<<< HEAD
	#cp $file $folder/Details/
=======
	cp $file $folder/Details/
>>>>>>> 3ebd262984735db66fb778d5a45666b1f1e6c78a
	# create a temprorary folder for flashcards. make sure its empty
	if [ -d "$folder/Karteikarten.tmp" ]; then 
		rm -rf $folder/Karteikarten.tmp
	fi
  
	mkdir $folder/Karteikarten.tmp
  
  echo "parsing ..." | tee  $folder/texFlasher.log
	python "$WD/.TexFlasher/parse_tex.py" "$file" "%###%" "$folder/Karteikarten.tmp"  | tee -a $folder/texFlasher.log
	cp $file $folder/Karteikarten/$purefilebase.bak
  
  recompile="0"
	compilenumber="0"
	newnumber="0"
	# buffer old flash cards
	OLDFLASHCARDS="`ls $folder/Karteikarten/*.tex`" 2>/dev/null
	for oldflashcard in $OLDFLASHCARDS; do
    # get filename with extension
    name=$(basename $oldflashcard)
    # get filename without extension
    purename=${name%\.*}

		
    if [ -f $folder/Karteikarten.tmp/$name ]; then
      if [[ "`diff $folder/Karteikarten.tmp/$name $folder/Karteikarten/$name`" == "" ]]; then
        # file has not changed, we don't want it to be overwritten
        # (not even by identical file) in order to preserve the timestamp
        # which is important for the Makefile
        rm $folder/Karteikarten.tmp/$name
        if [ ! -f $folder/Karteikarten/$purename.dvi ]; then
					compilenumber=`echo $compilenumber + "1" | bc`
				fi

					
      else
				recompile=`echo $recompile + "1" | bc`
				
				ts="`date +%s`"
				echo "changed content: $folder/Karteikarten/$purename" | tee -a $folder/texFlasher.log
      fi
    else 
      # delete files, that are no longer used!
      rm $folder/Karteikarten/old_$purename*
      rm $folder/Karteikarten/$purename.*
      rm $folder/Karteikarten/$purename-*.png
    fi
  done

  listnumber="`ls -1 $folder/Karteikarten.tmp/ | wc -l`"
  compilenumber=`echo $compilenumber + $listnumber | bc`
  newnumber=`echo $compilenumber - $recompile | bc`
  
  cp $folder/Karteikarten.tmp/* $folder/Karteikarten/ 2> /dev/null
  rm -r $folder/Karteikarten.tmp
  
  cd $folder/Karteikarten
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
    
<<<<<<< HEAD
  #cd $folder/Details
  #make -j$procs images 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error' | tee -a $folder/texFlasher.log
=======
  cd $folder/Details
  make -j$procs images 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error' | tee -a $folder/texFlasher.log
>>>>>>> 3ebd262984735db66fb778d5a45666b1f1e6c78a
    
  echo "done"


fi  

exit 0
