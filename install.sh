#!/bin/bash

pyinstaller wechat.spec

sudo cp -vrf ./dist/wechat /opt/
cp -v ./wechat.desktop ~/.local/share/applications/
