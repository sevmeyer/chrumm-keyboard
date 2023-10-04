import copy
import io
import logging
import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Vector


log = logging.getLogger(__name__)


def toKiCadFootprint(planR, planL):
    """Return switch position markers in the KiCad 7 footprint format."""
    layoutR = copy.deepcopy(planR.layout)
    layoutL = copy.deepcopy(planL.layout)

    _flattenLayout(layoutR)
    _flattenLayout(layoutL)

    for key in layoutR.all() + layoutL.all():
        if abs(key.position.z) > 1e-6:
            log.warning("Could not flatten layout for KiCad footprint.")
            return ""

    with io.StringIO() as stream:
        stream.write(
            '(footprint "" (generator chrumm)\n'
            '  (attr board_only exclude_from_pos_files exclude_from_bom)\n'
            '  (fp_text reference "" (at 0 0) (layer "F.Fab") hide)\n'
            '  (fp_text value "" (at 0 0) (layer "F.Fab") hide)\n')

        _writeKeys(stream, layoutR.all("right"), "F")
        _writeKeys(stream, layoutL.all("left"), "B")

        if cfg.pcb.mount:
            _writeMounts(stream, layoutR, "F")
            _writeMounts(stream, layoutL, "B")

        stream.write(')\n')
        return stream.getvalue()


def _flattenLayout(layout):
    splitAngle = cfg.body.splitAngle
    tiltAngle = cfg.body.tiltAngle
    pinkyTentAngle = cfg.body.pinkyTentAngle
    alnumTentAngle = cfg.body.alnumTentAngle
    switchHeight = cfg.switch.innerHeight
    pcbThickness = cfg.pcb.thickness

    # Rotate layout to align the pinky with the xy plane

    pinkyAlign = Matrix()
    pinkyAlign = pinkyAlign.rotatedZ(-splitAngle)
    pinkyAlign = pinkyAlign.rotatedX(-tiltAngle)
    pinkyAlign = pinkyAlign.rotatedY(-pinkyTentAngle)

    for key in layout.all():
        key.transform(pinkyAlign)

    # Unfold alnum and align with the xy plane

    alnumAngle = alnumTentAngle - pinkyTentAngle
    maxAlnum = layout.maxAlnum().position
    minPinky = layout.minPinky().position

    midPos = (maxAlnum + minPinky)/2
    midDir = Vector(math.sin(alnumAngle/2), 0, math.cos(alnumAngle/2))
    pcbPos = minPinky - Vector(0, 0, switchHeight + pcbThickness)
    pcbDir = Vector(1, 0, 0)
    midLine = Line(midPos, midDir)
    pcbLine = Line(pcbPos, pcbDir)
    alnumPivot = pcbLine.intersect(midLine)
    alnumAlign = Matrix().rotatedY(-alnumAngle, alnumPivot)

    for key in layout.alnum():
        key.transform(alnumAlign)

    # Set origin to the first pinky key

    originDelta = -layout.pinky()[0].position

    for key in layout.all():
        key.translate(originDelta)


def _writeKeys(stream, keys, layer):
    width = cfg.switch.width
    depth = cfg.switch.depth
    for key in keys:
        _writeKiCadMarker(stream, key.matrix, width, depth, layer)


def _writeMounts(stream, layout, layer):
    diameter = cfg.pcb.mount.threadDiameter
    xDist = cfg.pcb.mount.xDistToFirstPinky
    yDist = cfg.pcb.mount.yDistToFirstPinky
    matrix = layout.pinky()[0].matrix.translated(Vector(-xDist, -yDist))
    _writeKiCadMarker(stream, matrix, diameter, diameter, layer)


def _writeKiCadMarker(stream, matrix, width, height, layer):
    def pretty(num):
        return f"{num:.3f}".rstrip("0").rstrip(".")

    marker = Edge(
        Vector(-width/2, -height/2),
        Vector(width/2, -height/2),
        Vector()).transformed(matrix)

    coords = [f'{pretty(-p.x)} {pretty(-p.y)}' for p in marker]
    angle = pretty(math.degrees((marker[1] - marker[0]).angle2D()))

    for i in range(3):
        stream.write(
            f'  (fp_line (start {coords[i-1]}) (end {coords[i]})'
            f' (layer "{layer}.Cu") (width 0.05))\n')

    if angle != "0":
        stream.write(
            f'  (fp_text user "-{angle}°" (at {coords[-1]}) (layer "{layer}.Fab")\n'
            f'    (effects (font (size 3 3) (thickness 0.3)) (justify left)))\n')
