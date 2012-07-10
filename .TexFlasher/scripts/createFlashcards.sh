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
rm $folder/texFlasher.log &> /dev/null

mkdir -p $folder/Diffs/Flashcards &> /dev/null
# get current versions of files 
for thing in $FILES; do
	cp $WD/.TexFlasher/tools/$thing $folder/Flashcards/
	cp $WD/.TexFlasher/tools/$thing $folder/Diffs/
done


# get latest version of file (if file is under revision control)
# if [ $HAVESVN -eq 0 ]; then
# 	svn up $file
# fi

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
	cd $folder/Details
	latex -halt-on-error $folder/Details/source.tex 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error|Missing|No pages of output.|Emergency stop.' | tee -a $folder/texFlasher.log
	Errors="`cat $folder/texFlasher.log | grep -rniE 'error|ERROR|Error|Missing|No pages of output.|Emergency stop.'`"
	if [ ! "$Errors" == ""  ]; then
		echo "Fatal latex error in source file." >> $folder/texFlasher.log
		exit 1
	fi
	python $WD/.TexFlasher/diviasm.py source.dvi > source.dump	
	cd $WD

	# create a temprorary folder for flashcards. make sure its empty
	if [ -d "$folder/Flashcards.tmp" ]; then 
		rm -rf $folder/Flashcards.tmp &> /dev/null
	fi
	mkdir $folder/Flashcards.tmp
  
  echo "parsing ..." | tee  $folder/texFlasher.log
	python "$WD/.TexFlasher/parse_tex.py" "$folder/Flashcards.tmp" "$folder/Details" | tee -a $folder/texFlasher.log
	
	Errors="`cat $folder/texFlasher.log | grep -rniE 'Fatal Error'`"
	if [ ! "$Errors" == ""  ]; then
		echo "Fatal Error while parsing source file." >> $folder/texFlasher.log
		exit 1
	fi
	
	cp $file $folder/Flashcards/$purefilebase.bak
  
  recompile="0"
	compilenumber="0"
	changedContent="0"
	newnumber="0"
  TARGETS=""
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
        rm $folder/Flashcards.tmp/$name &> /dev/null
        if [ ! -f $folder/Flashcards/$purename.dvi ]; then
					compilenumber=`echo $compilenumber + "1" | bc`
					TARGETS="$TARGETS $purename.dvi"
				fi

					
      else
				recompile=`echo $recompile + "1" | bc`
			
				python .TexFlasher/get_fc_content.py $folder/Flashcards.tmp/$name > FILEA
				python .TexFlasher/get_fc_content.py $folder/Flashcards/$name > FILEB
								
				if [[ "`diff FILEA FILEB`" != "" ]]; then
					latexdiff $folder/Flashcards/$name $folder/Flashcards.tmp/$name > $folder/Diffs/diff_$name 2> /dev/null
					echo "changed content: $purename" | tee -a $folder/texFlasher.log
					changedContent=`echo $changedContent + "1" | bc`
				fi
				
				rm FILEA FILEB &> /dev/null
      fi
    else
			rm $folder/Flashcards/$purename* 2> /dev/null
		fi
  done

  listnumber="`ls -1 $folder/Flashcards.tmp/ | wc -l`"
  compilenumber=`echo $compilenumber + $listnumber | bc`
  newnumber=`echo $compilenumber - $recompile | bc`
  changedHeader=`echo $recompile - $changedContent | bc`
  

  NEWFLASHCARDS="`ls $folder/Flashcards.tmp/*.tex`" 2>/dev/null
  for newflashcard in $NEWFLASHCARDS; do
    # get filename with extension
    name=$(basename $newflashcard)
    # get filename without extension
    purename=${name%\.*}
    TARGETS="$TARGETS $purename.dvi"
   done
  
  cp $folder/Flashcards.tmp/* $folder/Flashcards/ 2> /dev/null
  rm -r $folder/Flashcards.tmp &> /dev/null
  
  procs=1
  if [ "`uname`" == "Linux" ] ; then
    procs="`grep -c processor /proc/cpuinfo`"
  elif [ "`uname`" == "Darwin" ] ; then
    procs="`/usr/sbin/system_profiler -detailLevel full SPHardwareDataType | grep -i 'number of cores' | awk '{ print $5 }'`"
  fi
  
  
  cd $folder/Flashcards
  echo "compiling card(s):" | tee -a $folder/texFlasher.log
	echo "  -> $newnumber new card(s)" | tee -a $folder/texFlasher.log
  echo "  -> $changedContent card(s) with changed content" | tee -a $folder/texFlasher.log
	echo "  -> $changedHeader card(s) with changed header" | tee -a $folder/texFlasher.log
  echo "Starting compilation on $procs processor(s). Please wait, this can take several minutes..."
	

	buildCounter="0"
	pBase=`echo "scale=2; 100.0 / $compilenumber.0" | bc`
	echo $pBase
	for target in $TARGETS; do
# 		echo "building target $target ..."
		# get percentage
		percent=`echo "$buildCounter.0 * $pBase" | bc`
		percent=`echo "1* $percent * 1" | bc`
		ceol=`tput el`
		echo -ne "\r${ceol}$percent%"
		
		make -j$procs $target 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error|Missing|Emergency stop.' | tee -a $folder/texFlasher.log
		buildCounter=`echo $buildCounter + "1" | bc`
	done
	echo -n "100%"
	

  cd $folder/Diffs
  make -i -j$procs images 2>&1 < /dev/null &> /dev/null
  cp *.png Flashcards/
  cd $WD
    
#  cd $folder/Details
#  latex $folder/Details/source.tex
#   make -j$procs pdf 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error' | tee -a $folder/texFlasher.log    
  echo "done"


fi  

# better be save than sorry
make -j$procs images 2>&1 < /dev/null | grep -rniE 'compiled flashcard|error|ERROR|Error|Missing|Emergency stop.' | tee -a $folder/texFlasher.log

exit 0
