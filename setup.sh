#!/bin/sh
echo "create virtual env"
python3.8 -m venv venv
. venv/bin/activate
pip -V
echo "installing env"
pip install -U pip setuptools
mkdir installations
cd installations
git clone https://github.com/carpedm20/emoji.git
cd emoji
echo "installing custom module 'emoji'"
python setup.py install
cd ../../
pip install -r requirements.txt
echo "cleaning tmp files"
rm -rf installations
echo ""
echo "complete"
