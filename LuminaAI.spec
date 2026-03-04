# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all ultralytics submodules to ensure everything is included
hidden_imports = collect_submodules('ultralytics')
hidden_imports += ['sklearn.utils._typedefs', 'sklearn.neighbors._partition_nodes', 'scipy.special.cython_special']

# Collect data files for ultralytics (these go into _internal)
datas = collect_data_files('ultralytics')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LuminaAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    Tree('configs', prefix='configs'),
    [('yolov8n.pt', 'yolov8n.pt', 'DATA')],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LuminaAI',
)
