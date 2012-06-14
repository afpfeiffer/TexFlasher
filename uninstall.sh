#!/bin/bash


rm $HOME/Desktop/TexFlasher.desktop 
rm $HOME/.local/share/applications/TexFlasher.desktop 
rm -r .TexFlasher
rm install.sh
rm settings
rm run-TexFlasher.sh
rm uninstall.sh
startupscript=/usr/local/bin/texflasher
if [ -f $startupscript ]; then
	echo "Need root rights to remove $startupscript"
	sudo rm $startupscript
fi
exit 0