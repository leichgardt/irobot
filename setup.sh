#!/bin/sh
libs='python3.8 python3-pip python3.8-venv'
echo "Checking requirement libs: $libs"
for lib in $libs
do
if dpkg -s $lib >> /dev/null 2>&1
then
  echo "$lib package satisfied"
  continue
else
  echo "Error. Please, install lib $lib"
  exit
fi
done
echo "Creating virtual env"
python3.8 -m venv venv
. venv/bin/activate
pip -V
echo "Installing packages"
pip install -U pip setuptools wheel
mkdir installations
cd installations || return
git clone https://github.com/carpedm20/emoji.git
cd emoji || return
echo "Installing custom module 'emoji'"
python setup.py install
cd ../../
pip install -r requirements.txt
echo "Cleaning tmp files"
rm -rf installations
echo ""
echo "Complete"
