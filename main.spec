# -*- mode: python -*-
import sys
sys.setrecursionlimit(99000)

from PyInstaller.utils.hooks import is_module_satisfies
import PyInstaller.compat
PyInstaller.compat.is_module_satisfies = is_module_satisfies

block_cipher = None

a = Analysis(['main.py'],
             pathex=['C:\\Users\\kdwm66\\Downloads\\WinPython-32bit-3.5.3.1Qt5\\python-3.5.3\\LinearSwelling',
			'C:\\Users\\kdwm66\\Downloads\\WinPython-32bit-3.5.3.1Qt5\\python-3.5.3\\Lib\\site-packages\\PyQt5\\Qt\\bin'],
             binaries=[],
             datas=[],
             hiddenimports=["PyDAQmx", "xlwt"],
             hookspath=[],
             runtime_hooks=[],
             excludes=["alabaster", "boto3", "botocore", "babel", "certifi", "IPython", "jsonschema", "pytz", "qt5_plugins", "requests", "sphinx", "zmq"],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Swellometer',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Swellometer')
