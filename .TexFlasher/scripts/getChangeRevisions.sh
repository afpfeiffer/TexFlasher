#!/bin/bash

# assamble revisions
REVISIONS="`svn log $1 | grep ' | ' | cut -d ' ' -f1 | cut -d 'r' -f2`"
echo -n $REVISIONS

