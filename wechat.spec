# -*- mode: python -*-

block_cipher = None

a = Analysis(['./wechatlauncher.py'],
             pathex=['/home/zhaohongxing/workspace/python/webwechat','/home/zhaohongxing/workspace/python/libwechatweb'],
             binaries=[],
             datas=[
             	('./resource','resource'),
             	('./icons','icons'),
             	('./wechat.sh',''),
             	('./logo.ico','')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='wechat',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='logo.ico' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='wechat')
