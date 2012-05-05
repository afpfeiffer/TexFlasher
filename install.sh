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

echo "Begin installation."
echo -n "Please enter the .tex editor of your choice: "
read TEXEDITOR

echo -n "selected editor: "
which $TEXEDITOR 

if [ ! $? -eq 0 ]; then
	echo
	echo "#####################################################"
	echo "          warning: .tex editor was not found."
	echo "#####################################################"
fi
echo

echo "#!/bin/bash" >> run-TexFlasher.sh

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

echo "python \$TEXFLASHDIR/.TexFlasher/leitner.py $TEXEDITOR \$1" >> run-TexFlasher.sh

chmod a+x run-TexFlasher.sh
chmod a+x .TexFlasher/leitner.py

echo "creating link on Desktop"


if [ -f TexFlasher.desktop ]; then
	rm TexFlasher.desktop
fi

echo "[Desktop Entry]" >> TexFlasher.desktop
echo "Version=6.0" >> TexFlasher.desktop
echo "Type=Application" >> TexFlasher.desktop
echo "Terminal=false" >> TexFlasher.desktop
echo "Exec=$PWD/run-TexFlasher.sh" >> TexFlasher.desktop
echo "Name=TexFlasher" >> TexFlasher.desktop
echo "Icon=$PWD/.TexFlasher/icon.png" >> TexFlasher.desktop
chmod a+x  TexFlasher.desktop

mv TexFlasher.desktop ~/Desktop/

echo "done."
echo 


echo -n "Would you like to start TexFlasher now? (Y/n): "
read ANSWER

if [ "$ANSWER" != "n" ]; then
	bash run-TexFlasher.sh
else
  echo "please run TexFlasher by typing \"./run-TexFlasher.sh\" in your bash."
fi
 
exit 0

