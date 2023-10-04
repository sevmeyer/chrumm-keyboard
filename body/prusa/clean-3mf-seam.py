# Clean up PrusaSlicer 2.6 seam paintings, by flood-filling
# partially painted triangles. 3MF files are edited in-place,
# backups are the responsibility of the user. Format reference:
# https://github.com/prusa3d/PrusaSlicer/issues/5294
#
# Usage: python3 clean-3mf-seam.py 3MF COMMAND
#
# COMMANDs:
# e = Fill as enforcer (blue)
# b = Fill as blocker (red)
# c = Clear

import re
import sys
import zipfile


def readZip(path):
    with zipfile.ZipFile(path, "r") as z:
        return {name:z.read(name) for name in z.namelist()}


def writeZip(path, fileDict):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in fileDict.items():
            z.writestr(name, data)


MODEL = "3D/3dmodel.model"
SEARCH = b' slic3rpe:custom_seam="[0-9A-F]{2,}"'
REPLACE = {
    "e": b' slic3rpe:custom_seam="4"',
    "b": b' slic3rpe:custom_seam="8"',
    "c": b''}

zipPath = sys.argv[1]
command = sys.argv[2]

files = readZip(zipPath)
files[MODEL] = re.sub(SEARCH, REPLACE[command], files[MODEL])
writeZip(zipPath, files)
