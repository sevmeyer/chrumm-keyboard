import logging
import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Matrix
from chrumm.geo import Plane
from chrumm.geo import Vector

from .arc import arc2D
from .arc import uprightHole2D


log = logging.getLogger(__name__)


class Boss:

    def __init__(self, pos, printDirection, wallDirection=None, roofPlane=None):
        self.pos = pos
        self.wallEdge = Edge()
        self.headHole = Edge()
        self.threadHole = Edge()
        self.clearanceHole = Edge()
        self.headTriangles = []
        self.threadTriangles = []

        self._initWall(pos, wallDirection)
        self._initHead(pos)
        self._initThread(pos, printDirection, roofPlane)

    def _initWall(self, pos, wallDirection):
        wallThickness = cfg.body.wallThickness
        bossRadius = cfg.boss.diameter/2
        bossFillet = cfg.boss.innerWallFillet
        wallMargin = cfg.boss.outerWallMargin
        protrusion = bossRadius*2 + wallMargin - wallThickness

        if wallDirection is None or protrusion < wallThickness/10:
            return

        taperAngleR = 0
        taperAngleL = 0

        if cfg.support:
            overhangAngle = cfg.support.minOverhangAngle
            if wallDirection.x < 0:
                taperAngleR = overhangAngle - (-wallDirection).angle2D()
            else:
                taperAngleL = overhangAngle + wallDirection.angle2D()

        self.wallEdge.add(_smoothTransition(
            protrusion,
            bossRadius,
            bossFillet,
            taperAngleR))

        self.wallEdge.add(_smoothTransition(
            protrusion,
            bossRadius,
            bossFillet,
            taperAngleL).mirroredX().reversed())

        matrix = Matrix().rotatedZ(wallDirection.angle2D()).translated(pos)
        self.wallEdge = self.wallEdge.collapsed().transformed(matrix)

    def _initHead(self, pos):
        outerHeight = cfg.floor.outerHeight
        sinkRadius = cfg.boss.countersinkDiameter/2
        clearRadius = cfg.boss.clearanceHoleDiameter/2
        clearLength = cfg.boss.clearanceHoleLength

        sinkLength = min(outerHeight, clearLength + (sinkRadius - clearRadius))
        sinkRadius = min(sinkRadius, clearRadius + (outerHeight - clearLength))

        # Head profile
        #    ___0  z=0
        #   |   |
        #   |___1  -clearLength
        #  /     \
        # /_______2  -sinkLength
        # |       |
        # |_______3  -outerHeight

        arcs = []
        profile = [
            (clearRadius, 0),
            (clearRadius, -clearLength),
            (sinkRadius, -sinkLength),
            (sinkRadius, -outerHeight)]

        protoArc = arc2D(clearRadius, 0, math.tau).scaled(1 / clearRadius)

        for scale, z in profile:
            arcPos = Vector(pos.x, pos.y, z)
            arcs.append(protoArc.scaled(scale).translated(arcPos))

        for i in range(len(arcs) - 1):
            self.headTriangles.extend(arcs[i].meshPairwise(arcs[i+1], True))

        self.clearanceHole = arcs[0].reversed()
        self.headHole = arcs[-1]

    def _initThread(self, pos, printDirection, roofPlane):
        radius = cfg.boss.threadDiameter/2
        minLength = cfg.boss.minThreadLength
        maxLength = cfg.boss.maxThreadLength
        roofMargin = cfg.boss.threadRoofMargin
        chamfer = cfg.boss.threadChamfer

        # Trim parallel to roof

        if roofPlane:
            marginPlane = roofPlane.translated(roofPlane.normal * -roofMargin)
            tipZ = min(maxLength, marginPlane.projectZ(pos).z)

            if tipZ < minLength:
                raise ValueError(
                    f"A boss thread overlaps the roof margin by: {minLength - tipZ:.3f}\n"
                    "  Try to decrease boss.minThreadLength, boss.threadRoofMargin,\n"
                    "  or increase body.minRoofHeight.")

            if tipZ < maxLength:
                log.debug("Excess length of trimmed boss thread: %.3f", tipZ - minLength)

            tipPlane = Plane(Vector(pos.x, pos.y, tipZ), roofPlane.normal)
        else:
            tipPlane = Plane(Vector(pos.x, pos.y, maxLength), Vector(0, 0, 1))

        # Thread profile
        #    ___2  tip
        #   |   |
        #   |___1  chamfer
        #  /     \
        # /_______0  z=0

        arcs = []
        profile = [
            (radius + chamfer/2, 0),
            (radius, chamfer)]

        rotation = Matrix().rotatedZ(printDirection.angle2D() - math.tau/4)
        protoArc = uprightHole2D(radius).scaled(1/radius).transformed(rotation)

        for scale, z in profile:
            arcPos = Vector(pos.x, pos.y, z)
            arcs.append(protoArc.scaled(scale).translated(arcPos))

        arcs.append(Edge(tipPlane.projectZ(p) for p in arcs[-1]))
        arcs.append(Edge(tipPlane.pos))

        for i in range(len(arcs) - 1):
            self.threadTriangles.extend(arcs[i+1].meshPairwise(arcs[i], True))

        self.threadHole = arcs[0]


def _smoothTransition(protrusion, bossRadius, bossFillet, minTaperAngle):
    # <--.. \  --------protrusion--
    #      '.\              ^
    #  boss   o             |
    #          \'. fillet   |
    #           \ ''--o  --wall--
    #        tangent

    filletCenterY = bossRadius - protrusion + bossFillet
    filletCenterX = max(0, (bossRadius + bossFillet)**2 - filletCenterY**2)**0.5
    filletCenter = Vector(filletCenterX, filletCenterY)

    tangentAngle = min(max(0, minTaperAngle, filletCenter.angle2D()), math.radians(89))
    arcAngle = math.tau/4 - tangentAngle
    filletArc = arc2D(bossFillet, -math.tau/4, -arcAngle, filletCenter)
    bossArc = arc2D(bossRadius, tangentAngle, arcAngle)

    gapY = bossArc[0].y - filletArc[-1].y
    gapX = gapY / math.cos(tangentAngle) * math.sin(tangentAngle)
    offset = Vector(gapX - (filletArc[-1].x - bossArc[0].x))

    return Edge(filletArc.translated(offset), bossArc).collapsed()
