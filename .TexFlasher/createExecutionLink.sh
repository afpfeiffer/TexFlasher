#!/bin/bash
set -e

ROOT_UID="0"

#Check if run as root
if [ "$UID" != "$ROOT_UID" ] ; then
	echo "Stupid you. You must be root!"
	exit 1
fi

if [ ! -f run-TexFlasher.sh ]; then
	echo "Stupid you. I didn't find run-TexFlasher.sh in $PWD!"
	exit 1
fi

startupscript=/usr/local/bin/texflasher
echo "#!/bin/bash" > $startupscript
echo "cd $PWD " >> $startupscript
echo "bash run-TexFlasher.sh " >> $startupscript
echo "exit 0 ">> $startupscript
chmod a+x $startupscript	

echo "Link created."

exit 0