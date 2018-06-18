#!/bin/bash

pyinstaller wechat.spec

sudo cp -vrf ./dist/wechat /opt/
sudo ln -sf /opt/wechat/resource/icons/ /opt/wechat/icons
cp -v ./wechat.desktop ~/.local/share/applications/
