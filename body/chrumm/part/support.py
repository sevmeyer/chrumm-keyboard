import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Vector

from .arc import arc2D


class SupportFactory:
    """Construct and cache the geometry of key hole supports."""

    def __init__(self):
        self.triangles = []

        holeW = cfg.switch.width
        holeD = cfg.switch.depth
        holeH = cfg.body.roofThickness

        # Support names use print orientation

        baseW = cfg.support.baseWidth
        baseD = cfg.support.baseDepth
        topD = cfg.support.topDepth
        sideGap = cfg.support.sideGap
        baseGap = cfg.support.baseGap
        topGap = cfg.support.topGap

        # Construct in standard orientation

        boundL = -holeW/2 + baseGap
        boundR = holeW/2 - topGap
        boundB = holeD/2 - sideGap
        boundG = -holeH + sideGap

        centerL = Vector(boundL, boundB - baseD/2, boundG + baseD/2)
        centerR = Vector(boundR, boundB - topD/2, boundG + topD/2)
        insetL = Vector(0, 2*boundB - baseW, 0)

        arc = Edge(Vector(0, p.y, -p.x) for p in arc2D(topD/2, 0, math.pi))
        edgeL = arc.scaled(baseD/topD).translated(centerL)
        edgeR = arc.translated(centerR)

        edgeL.add(edgeL.mirroredY().reversed().translated(insetL))
        edgeR.add(edgeR.mirroredY().reversed())

        self.triangles.extend(edgeL.meshPairwise(edgeR, True))
        self.triangles.extend(Face(edgeL.reversed()).triangulate())
        self.triangles.extend(Face(edgeR).triangulate())

    def make(self, key):
        angle = abs(Vector(1, 0).transformedNormal(key.matrix).angle2D())

        if angle <= cfg.support.minOverhangAngle:
            return [t.transformed(key.matrix) for t in self.triangles]

        return []


class Support:

    def __init__(self, plan):
        self.faces = []
        self.triangles = []

        supportFactory = SupportFactory()

        for key in plan.layout.all(plan.side):
            self.triangles.extend(supportFactory.make(key))
