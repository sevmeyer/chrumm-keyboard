import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Vector

from .arc import arc2D


class Bumper:

    def __init__(self, pos, isHalf=False):
        self.triangles = []
        self.floorEdge = Edge()
        self.splitEdge = Edge()

        floorHeight = cfg.floor.outerHeight
        radius = cfg.bumper.diameter/2
        height = cfg.bumper.height

        arc = arc2D(radius, -math.pi/2, math.pi).snapped() if isHalf else arc2D(radius)
        edgeG = arc.translated(pos.xy - Vector(0, 0, floorHeight))
        edgeT = arc.translated(pos.xy - Vector(0, 0, floorHeight - height))

        self.triangles.extend(edgeT[:1].meshPairwise(edgeT))
        self.triangles.extend(edgeT.meshPairwise(edgeG, not isHalf))
        self.floorEdge.add(edgeG)

        if isHalf:
            self.splitEdge.add(edgeG[-1], edgeT[-1], edgeT[0], edgeG[0])
