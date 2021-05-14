#!/bin/sh
echo "create virtual env"
python3 -m venv venv
source venv/bin/activate
echo "installing env"
pip install -U pip setuptools
pip install -r requirements.txt
mkdir installations
cd installations
git clone https://github.com/carpedm20/emoji.git
cd emoji
echo "installing custom module 'emoji'"
python setup.py install
cd ../../
rm -rf installations
echo ""
echo "complete"
