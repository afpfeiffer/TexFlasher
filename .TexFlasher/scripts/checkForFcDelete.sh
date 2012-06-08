#!/bin/bash

# svn diff -r$2:$3 $1  | grep '\-\\fc{'

DIFF="`svn diff -r$2:$3 $1  | grep '\\-\\\\fc{'`"

for thing in $DIFF; do
	echo -n "-> "
	echo $thing | cut -d '-' -f 2
done

if [ "$DIFF" != "" ]; then
	echo
	echo -n "User to blame:"
	svn log $1 | grep $3 | cut -d '|' -f2
fi
