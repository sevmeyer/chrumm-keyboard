import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Vector

from .arc import arc2D
from .arc import cornerArc2D


class BossFactory:
    """Construct and cache the geometry of screw bosses."""

    def __init__(self):
        self._initScrew()
        self._initBoss()

    def _initScrew(self):
        self.threadHole = Edge()
        self.threadTriangles = []
        self.clearanceHole = Edge()
        self.headHole = Edge()
        self.headTriangles = []

        outerHeight = cfg.floor.outerHeight
        sinkRadius = cfg.boss.countersinkDiameter/2
        clearRadius = cfg.boss.clearanceHoleDiameter/2
        clearLength = cfg.boss.clearanceHoleLength
        threadChamfer = cfg.boss.threadChamfer
        threadRadius = cfg.boss.threadDiameter/2
        threadLength = cfg.boss.threadLength
        threadTip = cfg.boss.threadTipLength

        # Thread profile
        #     0
        #    / \
        #   /_1_\  threadLength
        #   |   |
        #   |_2_|  threadChamfer
        #  /     \
        # /___3___\  z=0

        threadProfile = [
            (0, threadLength + threadTip),
            (threadRadius, threadLength),
            (threadRadius, threadChamfer),
            (threadRadius + threadChamfer/2, 0)]

        # Head profile
        #    _0_   z=0
        #   |   |
        #   |_1_|  -clearLength
        #  /     \
        # /___2___\  -sinkLength
        # |       |
        # |___3___|  -outerHeight

        sinkLength = min(outerHeight, clearLength + (sinkRadius - clearRadius))
        sinkRadius = min(sinkRadius, clearRadius + (outerHeight - clearLength))
        headProfile = [
            (clearRadius, 0),
            (clearRadius, -clearLength),
            (sinkRadius, -sinkLength),
            (sinkRadius, -outerHeight)]

        unitArc = arc2D(threadRadius, 0, math.tau).scaled(1 / threadRadius)
        headArcs = []
        threadArcs = []

        for scale, z in headProfile:
            headArcs.append(unitArc.scaled(scale).translated(Vector(0, 0, z)))

        for scale, z in threadProfile:
            threadArcs.append(unitArc.scaled(scale).translated(Vector(0, 0, z)))

        self.threadHole.add(threadArcs[-1])
        self.clearanceHole.add(headArcs[0].reversed())
        self.headHole = headArcs[-1]

        for i in range(len(threadArcs) - 1):
            self.threadTriangles.extend(threadArcs[i].meshPairwise(threadArcs[i+1], True))

        for i in range(len(headArcs) - 1):
            self.headTriangles.extend(headArcs[i].meshPairwise(headArcs[i+1], True))

    def _initBoss(self):
        self.wallEdge = Edge()

        wallThickness = cfg.body.wallThickness
        wallMargin = cfg.boss.outerWallMargin
        radius = cfg.boss.diameter/2
        cornerRadius = cfg.boss.cornerRadius

        #      \
        # o-----o----- apex
        #  '''.. \
        #  boss '.\
        #          o
        #           \'. corner
        #            \ ''...
        # wall -------o-----o--
        #       tangent\

        apex = Line(Vector(0, radius), Vector(1, 0))
        wall = Line(Vector(0, wallThickness - radius - wallMargin), Vector(1, 0))

        if radius > wallThickness/2:
            cornerY = wall.pos.y + cornerRadius
            cornerX = ((radius + cornerRadius)**2 - cornerY**2)**0.5
            cornerDir = Vector(cornerX, cornerY).normalized()
            tangent = Line(cornerDir*radius, cornerDir.ortho2D())

            if tangent.dir.x > 0:
                # Avoid an hourglass boss shape
                cornerX = radius + cornerRadius
                tangent = Line(Vector(radius, 0), Vector(0, 1))

            if cornerRadius > 0:
                cornerStart = Vector(cornerX, wall.pos.y)
                self.wallEdge.add(cornerArc2D(
                    cornerRadius,
                    cornerStart,
                    tangent.intersect(wall),
                    tangent.pos))
            else:
                self.wallEdge.add(Vector(radius, wall.pos.y))

            self.wallEdge.add(cornerArc2D(
                radius,
                tangent.pos,
                tangent.intersect(apex),
                apex.pos))

        self.wallEdge.add(self.wallEdge.mirroredX().reversed())
        self.wallEdge = self.wallEdge.collapsed()

    def make(self, pos, direction=None):
        return Boss(self, pos, direction)


class Boss:

    def __init__(self, factory, pos, direction=None):
        self.pos = pos
        self.wallEdge = Edge()
        self._factory = factory

        if direction is not None:
            matrix = Matrix().rotatedZ(direction.angle2D()).translated(pos)
            self.wallEdge = self._factory.wallEdge.transformed(matrix)

    @property
    def threadHole(self):
        return self._factory.threadHole.translated(self.pos)

    @property
    def threadTriangles(self):
        return [t.translated(self.pos) for t in self._factory.threadTriangles]

    @property
    def clearanceHole(self):
        return self._factory.clearanceHole.translated(self.pos)

    @property
    def headHole(self):
        return self._factory.headHole.translated(self.pos)

    @property
    def headTriangles(self):
        return [t.translated(self.pos) for t in self._factory.headTriangles]
