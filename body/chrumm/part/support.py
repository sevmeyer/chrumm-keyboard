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

        # Support parameters in print orientation

        baseW = cfg.support.baseWidth
        baseD = cfg.support.baseDepth
        sideGap = cfg.support.sideGap
        baseGap = cfg.support.baseGap
        topGap = cfg.support.topGap
        topD = cfg.support.topDepth
        topW = holeD - 2*sideGap

        legacyBaseInset = 1 - sideGap/(holeH - baseD)
        legacyTopInset = 1 - sideGap/(holeH - topD)

        relBasePos = getattr(cfg.support, "relBasePosition", 0)
        relBaseInset = getattr(cfg.support, "relBaseInset", legacyBaseInset)
        relTopInset = getattr(cfg.support, "relTopInset", legacyTopInset)

        # Construction in standard orientation
        #
        #     holeW
        # .-----------.
        # | .-------. |
        # | |support| | holeD
        # |  '..    | |
        # |     ''..| | y
        # | base  top | zx

        baseInset = baseD/2 + (holeH - baseD)*relBaseInset
        topInset = topD/2 + (holeH - topD)*relTopInset

        centerL = Vector(-holeW/2 + baseGap, baseW/2 - baseD/2, -baseInset)
        centerR = Vector(holeW/2 - topGap, topW/2 - topD/2, -topInset)

        arc = Edge(Vector(0, p.y, -p.x) for p in arc2D(topD/2, 0, math.pi))
        edgeL = arc.scaled(baseD/topD).translated(centerL)
        edgeR = arc.translated(centerR)

        edgeL.add(edgeL.mirroredY().reversed())
        edgeR.add(edgeR.mirroredY().reversed())

        baseMove = Vector(0, (topW - baseW)/2 - (topW - baseW)*relBasePos)
        edgeL = edgeL.translated(baseMove)

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
