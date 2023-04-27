# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
	['COMTool/Main.py'],
	pathex=[],
	binaries=[],
	datas=[
		('COMTool', 'COMTOOL'),
		('LICENSE', '.'),
		('VERSION', '.')
	],
	hiddenimports=["babel.numbers"],
	hookspath=[],
	runtime_hooks=[],
	excludes=[],
	win_no_prefer_redirects=False,
	win_private_assemblies=False,
	cipher=block_cipher,
	noarchive=False
)

pyz = PYZ(
	a.pure,
	a.zipped_data,
	cipher=block_cipher
)

exe = EXE(
	pyz,
	a.scripts,
	a.binaries,
	a.zipfiles,
	a.datas,
	[],
	name='comtool',
	icon='COMTool/assets/logo.ico',
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	console=False
)
