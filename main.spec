# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
			pathex=['C:\\Code\\openvna\\PyVna'],
			binaries=None,
			datas=None,
			hiddenimports=[],
			hookspath=None,
			runtime_hooks=None,
			excludes = [
				"numpy.core._dotblas.pyd",
				"scipy.linalg._fblas.pyd",
				"scipy.linalg._flapack.pyd",
				"scipy.linalg._flinalg.pyd",
				"scipy.sparse.linalg.dsolve._superlu",
				"scipy.sparse.linalg.eigen.arpack._arpack",
				"tcl",
				"tkinter",
				"_tkinter",
				"Tkinter"
			],
			cipher=block_cipher)


excludes = [
	"tcl86t.dll",
	"tk86t.dll",
]

# I'm not using matplotlib
for entry in a.datas[:]:
	if os.path.dirname(entry[1]).startswith("C:\\Python34\\Lib\\site-packages\\matplotlib"):
		a.datas.remove(entry)

for item in a.binaries[:]:
	if item[0] in excludes:
		a.binaries.remove(item)


# Manually include the VNA dll
a.binaries.append(("vnadll.dll", "../../x64/Release/vnadll.dll", "BINARY"))
# And the icon
a.binaries.append(("Akela Logo.ico", "./Akela Logo.ico", "BINARY"))

# Throw in the runtime library kitchen sink. It can't hurt, and might help.
# Worst case, the binary is now a bit bigger.
a.binaries.append(("msvcp100d.dll", "C:/Windows/System32/msvcp100d.dll", "BINARY"))
a.binaries.append(("msvcr100d.dll", "C:/Windows/System32/msvcr100d.dll", "BINARY"))
a.binaries.append(("msvcp120d.dll", "C:/Windows/System32/msvcp120d.dll", "BINARY"))
a.binaries.append(("msvcr120d.dll", "C:/Windows/System32/msvcr120d.dll", "BINARY"))
a.binaries.append(("msvcp100.dll",  "C:/Windows/System32/msvcp100.dll", "BINARY"))
a.binaries.append(("msvcr100.dll",  "C:/Windows/System32/msvcr100.dll", "BINARY"))
a.binaries.append(("msvcp120.dll",  "C:/Windows/System32/msvcp120.dll", "BINARY"))
a.binaries.append(("msvcr120.dll",  "C:/Windows/System32/msvcr120.dll", "BINARY"))


pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(pyz,
			a.scripts,
			a.binaries,
			a.zipfiles,
			a.datas,
			# exclude_binaries=True,
			name    = 'PyOpenVNA.exe',
			debug   = False,
			strip   = None,
			upx     = False,
			console = True,
			icon    = "./Akela Logo.ico"
			)


# exe = EXE(pyz,
# 		  a.scripts,
# 		  exclude_binaries=True,
# 		  name='OpenVNA.exe',
# 		  debug=False,
# 		  strip=None,
# 		  upx=False,
# 		  console=True )

# coll = COLLECT(exe,
# 			   a.binaries,
# 			   a.zipfiles,
# 			   a.datas,
# 			   strip=None,
# 			   upx=False,
# 			   name='OpenVNA')

