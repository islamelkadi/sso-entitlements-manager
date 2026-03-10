# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/cli/sso.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('src/schemas/*.json', 'schemas'),
    ],
    hiddenimports=[
        'boto3',
        'botocore',
        'yaml',
        'jsonschema',
        'rich',
        'src.core.utils',
        'src.core.constants',
        'src.core.version',
        'src.core.access_control_file_reader',
        'src.services.aws.aws_organizations_manager',
        'src.services.aws.aws_identity_center_manager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='sso-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)