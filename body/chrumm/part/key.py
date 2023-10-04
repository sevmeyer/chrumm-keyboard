import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Matrix
from chrumm.geo import Vector


class KeyFactory:
    """Construct and cache the geometry of keys."""

    def __init__(self):
        self.boundsI = Edge()
        self.boundsO = Edge()
        self.roofHoleI = Edge()
        self.roofHoleO = Edge()
        self.triangles = []

        holeW = cfg.switch.width
        holeD = cfg.switch.depth
        holeH = cfg.body.roofThickness
        pinH = cfg.switch.pinHeight
        innerH = cfg.switch.innerHeight
        innerMargin = cfg.switch.innerMargin
        outerMargin = cfg.switch.outerMargin
        entryChamfer = cfg.switch.entryChamfer

        holeL = -holeW/2
        holeR = holeW/2
        holeF = -holeD/2
        holeB = holeD/2

        # Bounds

        self.boundsO.add(
            Vector(holeL - outerMargin, holeF - outerMargin),
            Vector(holeL - outerMargin, holeB + outerMargin),
            Vector(holeR + outerMargin, holeB + outerMargin),
            Vector(holeR + outerMargin, holeF - outerMargin))
        self.boundsI.add(
            Vector(holeL - innerMargin, holeF - innerMargin, -holeH),
            Vector(holeL - innerMargin, holeB + innerMargin, -holeH),
            Vector(holeR + innerMargin, holeB + innerMargin, -holeH),
            Vector(holeR + innerMargin, holeF - innerMargin, -holeH),
            Vector(holeL, holeF, -innerH - pinH),
            Vector(holeL, holeB, -innerH - pinH),
            Vector(holeR, holeB, -innerH - pinH),
            Vector(holeR, holeF, -innerH - pinH))

        # Left side

        entryEdge = Edge(
            Vector(holeL, holeF - entryChamfer),
            Vector(holeL - entryChamfer, holeF))
        chamferEdge = Edge(
            Vector(holeL, holeF, -entryChamfer),
            Vector(holeL, holeF, -entryChamfer))
        exitEdge = Edge(
            Vector(holeL, holeF, -holeH),
            Vector(holeL, holeF, -holeH))

        for edge in [entryEdge, chamferEdge, exitEdge]:
            edge.add(edge.mirroredY().reversed())

        self.triangles.extend(exitEdge.meshPairwise(chamferEdge))
        self.triangles.extend(chamferEdge.meshPairwise(entryEdge))

        # Back clip notch

        if cfg.switch.clipNotch and cfg.switch.clipNotch.height < holeH:
            clipW = cfg.switch.clipNotch.width
            clipD = cfg.switch.clipNotch.depth
            clipH = cfg.switch.clipNotch.height
            clipAngle = cfg.switch.clipNotch.taperAngle
            clipTaper = clipD / math.cos(clipAngle) * math.sin(clipAngle)

            clipEdgeG = Edge(
                Vector(-clipW/2, holeB, -holeH),
                Vector(-clipW/2 + clipTaper, holeB + clipD, -holeH),
                Vector(clipW/2 - clipTaper, holeB + clipD, -holeH),
                Vector(clipW/2, holeB, -holeH))
            clipEdgeT = clipEdgeG.translated(Vector(0, 0, holeH - clipH))
            clipEdgeF = Edge(clipEdgeG[0], clipEdgeT[0], clipEdgeT[-1], clipEdgeG[-1])

            entryEdgeB = Edge(entryEdge[-1], entryEdge[-1].mirroredX())
            chamferEdgeB = Edge(chamferEdge[-1], chamferEdge[-1].mirroredX())
            wallEdgeB = Edge(exitEdge[-1], chamferEdgeB, exitEdge[-1].mirroredX())

            exitEdge.add(clipEdgeG)

            self.triangles.extend(chamferEdgeB.meshPairwise(entryEdgeB))
            self.triangles.extend(clipEdgeF.meshPairwise(wallEdgeB))
            self.triangles.extend(clipEdgeG.meshPairwise(clipEdgeT))
            self.triangles.extend(clipEdgeT[:2].meshPairwise(clipEdgeT[2:].reversed()))
        else:
            wallEdgeLB = Edge(exitEdge[-1], chamferEdge[-1], entryEdge[-1])
            wallEdgeRB = wallEdgeLB.mirroredX()
            self.triangles.extend(wallEdgeRB.meshPairwise(wallEdgeLB))

        # Opposite half

        entryEdge = entryEdge.collapsed()
        entryEdge.add(entryEdge.mirroredX().mirroredY())

        exitEdge = exitEdge.collapsed().reversed()
        exitEdge.add(exitEdge.mirroredX().mirroredY())

        self.roofHoleO = entryEdge
        self.roofHoleI = exitEdge
        self.triangles.extend([t.mirroredX().mirroredY() for t in self.triangles])

    def make(self, units=1):
        return Key(self, units)


class Key:

    def __init__(self, factory, units):
        self.matrix = Matrix()

        pitchX = cfg.layout.columnPitch
        pitchY = cfg.layout.rowPitch
        marginX = pitchX - cfg.layout.capWidth
        marginY = pitchY - cfg.layout.capDepth
        capW = pitchX*units - marginX
        capD = pitchY - marginY

        self._factory = factory
        self._capPivotL = Vector(-capW/2 - marginX/2, -capD/2)
        self._capPivotR = Vector(capW/2 + marginX/2, -capD/2)
        self._capBounds = Edge(
            Vector(-capW/2 - marginX, -capD/2 - marginY),
            Vector(capW/2 + marginX, -capD/2 - marginY),
            Vector(capW/2 + marginX,  capD/2 + marginY),
            Vector(-capW/2 - marginX,  capD/2 + marginY))

    def translate(self, vector):
        self.matrix = self.matrix.translated(vector)

    def transform(self, matrix):
        self.matrix = self.matrix * matrix

    @property
    def position(self):
        return Vector().transformed(self.matrix)

    @property
    def capPivotL(self):
        return self._capPivotL.transformed(self.matrix)

    @property
    def capPivotR(self):
        return self._capPivotR.transformed(self.matrix)

    @property
    def boundsI(self):
        return self._factory.boundsI.transformed(self.matrix)

    @property
    def boundsO(self):
        return (self._factory.boundsO + self._capBounds).transformed(self.matrix)

    @property
    def bounds(self):
        return self.boundsI + self.boundsO

    @property
    def roofHoleI(self):
        return self._factory.roofHoleI.transformed(self.matrix)

    @property
    def roofHoleO(self):
        return self._factory.roofHoleO.transformed(self.matrix)

    @property
    def triangles(self):
        return [t.transformed(self.matrix) for t in self._factory.triangles]
