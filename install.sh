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


clear

python .TexFlasher/credits.py

echo

if [ -f run-TexFlasher.sh ]; then
	rm run-TexFlasher.sh
fi
if [ -f settings ]; then
	rm settings
fi

echo "Installation ..."
echo
# check for default editor
TEXEDITOR="none"
which kile > /dev/null
if [ $? -eq 0 ]; then
	TEXEDITOR="`which kile`"
fi
echo "Default latex editor: $TEXEDITOR"
while [ 1 -eq 1 ]; do
	echo -n "Press <Return> to accept or enter name of latex editor: "
	read ANSWER
	if [ "$ANSWER" == "" ]; then
		TEXEDITOR=$TEXEDITOR
		break
	elif [ "$ANSWER" == "vi" ]; then
		echo "Warning: vi not supported."
	elif [ "$ANSWER" == "vim" ]; then
		echo "Warning: vim not supported."
	else
		TEXEDITOR=$ANSWER
		break
	fi
done

echo "Latex editor: $TEXEDITOR "

which $TEXEDITOR > /dev/null
if [ ! $? -eq 0 ]; then
	echo
	echo "#####################################################"
	echo "          warning: .tex editor was not found."
	echo "#####################################################"
fi
echo

echo "#!/bin/bash" >> run-TexFlasher.sh
echo "#This file was created automatically by the script 'install.sh'. Changes will be overwritten." >> run-TexFlasher.sh
echo >> run-TexFlasher.sh

echo "#This file is part of TexFlasher." >> run-TexFlasher.sh
echo "#" >> run-TexFlasher.sh
echo "#TexFlasher is free software: you can redistribute it and/or modify">> run-TexFlasher.sh
echo "#it under the terms of the GNU General Public License as published by">> run-TexFlasher.sh
echo "#the Free Software Foundation, either version 3 of the License, or">> run-TexFlasher.sh
echo "#(at your option) any later version.">> run-TexFlasher.sh
echo "#">> run-TexFlasher.sh
echo "#TexFlasher is distributed in the hope that it will be useful," >> run-TexFlasher.sh
echo "#but WITHOUT ANY WARRANTY; without even the implied warranty of" >> run-TexFlasher.sh
echo "#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the" >> run-TexFlasher.sh
echo "#GNU General Public License for more details." >> run-TexFlasher.sh
echo "#">> run-TexFlasher.sh
echo "#You should have received a copy of the GNU General Public License">> run-TexFlasher.sh
echo "#along with TexFlasher  If not, see <http://www.gnu.org/licenses/>.">> run-TexFlasher.sh

# echo -n "Would you like to be notified if updates are available? (Y/n): "
# read ANSWER

# echo "rm UPDATE 2> /dev/null" >> run-TexFlasher.sh

# if [ "$ANSWER" != "n" ]; then
# 	echo "You will be notified."
# 	echo "bash .TexFlasher/checkForSourceUpdate.sh &" >> run-TexFlasher.sh
# fi
USERNAME=$1

if [ "$USERNAME" == "" ]; then
	USERNAME=$USER
fi

echo "Username: $USERNAME"
echo -n "Press <Return> to accept or enter new username: "
read ANSWER


if [ "$ANSWER" != "" ]; then
	USERNAME=$ANSWER
fi
echo "Username: $USERNAME"

echo "clear" >> run-TexFlasher.sh
echo "TEXFLASHDIR=$PWD" >> run-TexFlasher.sh
echo "cd \$TEXFLASHDIR" >> run-TexFlasher.sh
echo "python .TexFlasher/credits.py" >> run-TexFlasher.sh


echo
echo "echo" >> run-TexFlasher.sh

echo "echo \"TexFlasher is free software: you can redistribute it and/or modify\"">> run-TexFlasher.sh
echo "echo \"it under the terms of the GNU General Public License as published by\"">> run-TexFlasher.sh
echo "echo \"the Free Software Foundation, either version 3 of the License, or\"">> run-TexFlasher.sh
echo "echo \"(at your option) any later version.\"">> run-TexFlasher.sh
echo "echo \"\"">> run-TexFlasher.sh
echo "echo \"TexFlasher is distributed in the hope that it will be useful,\"" >> run-TexFlasher.sh
echo "echo \"but WITHOUT ANY WARRANTY; without even the implied warranty of\"" >> run-TexFlasher.sh
echo "echo \"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\"" >> run-TexFlasher.sh
echo "echo \"GNU General Public License for more details.\"" >> run-TexFlasher.sh
echo "echo \"\"">> run-TexFlasher.sh

echo "python \$TEXFLASHDIR/.TexFlasher/leitner.py" >> run-TexFlasher.sh

chmod a+x run-TexFlasher.sh
chmod a+x .TexFlasher/leitner.py

echo -n "Would you like to create a desktop shortcut? (Y/n): "
read ANSWER
if [ "$ANSWER" != "n" ]; then
	echo "Creating link on Desktop."


	if [ -f TexFlasher.desktop ]; then
		rm TexFlasher.desktop
	fi

	echo "[Desktop Entry]" >> TexFlasher.desktop
	echo "Version=6.0" >> TexFlasher.desktop
	echo "Type=Application" >> TexFlasher.desktop
	echo "Terminal=false" >> TexFlasher.desktop
	echo "Exec=$PWD/run-TexFlasher.sh" >> TexFlasher.desktop
	echo "Name=TexFlasher" >> TexFlasher.desktop
	echo "Comment=Flashcard manager with latex support." >> TexFlasher.desktop
	echo "Icon=$PWD/.TexFlasher/pictures/icon.png" >> TexFlasher.desktop
	echo "Categories=Office;Application;" >> TexFlasher.desktop
	chmod a+x  TexFlasher.desktop
	if [ -d $HOME/.local/share/applications ]; then
	 cp TexFlasher.desktop ~/.local/share/applications
	fi

	mv TexFlasher.desktop ~/Desktop/
	
fi


echo
echo "Writing settings to HD"
echo "#This file was created automatically by 'install.sh'." >> settings
echo "[TexFlasher]" >> settings
echo "user: $USERNAME" >> settings
echo "editor: $TEXEDITOR" >> settings
echo

if [ ! -f .TexFlasher/config.xml ]; then
	echo "<config><FlashFolder created=\"2012-05-07 14:49:00\" filename=\"$PWD/Example-elDG/Vorbereitung.tex\" lastReviewed=\"2012-05-07 14:49:00\"/></config>"
	echo "<config><FlashFolder created=\"2012-05-07 14:49:00\" filename=\"$PWD/Example-elDG/Vorbereitung.tex\" lastReviewed=\"2012-05-07 14:49:00\"/></config>" >>  .TexFlasher/config.xml
fi



# echo "Please run TexFlasher by typing \"./run-TexFlasher.sh\" in your bash."
# echo
# echo "Insallation complete. Please enjoy the TexFlasher."



 
exit 0

