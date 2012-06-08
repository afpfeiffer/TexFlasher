#!/bin/python


import os
import subprocess
import sys

FILE=sys.argv[1]

print "Searching for accidently removed flashcards in svn history of file "+FILE+"\n"

# assamble revisions
process = subprocess.Popen(["bash", ".TexFlasher/scripts/getChangeRevisions.sh" , str(FILE) ] , stdout=subprocess.PIPE)
output  = process.stdout.read()


#print output+"\n"

output_list=output.split(' ')


#print output_list
#print

for i in range(len(output_list) -1):
	print "\033[0mcomparing revisions "+str(output_list[i+1]) +":"+ str(output_list[i])+ "... \t\t" ,
	process = subprocess.Popen(["bash", ".TexFlasher/scripts/checkForFcDelete.sh" , str(FILE), output_list[i+1] , output_list[i] ] , stdout=subprocess.PIPE)
	output  = process.stdout.read()
	if output == "":
		print "\033[92m[OK]"
	else:
		print "\033[91m[ERROR]"
		print
		print "Flashcards have been removed:"
		print output
		print
		
print "\033[0m"



# svn diff -r169:171 dg-i-goette/Vorbereitung.tex  | grep '\-\\fc{'