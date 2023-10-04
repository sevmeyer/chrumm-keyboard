from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Vector

from .arc import uprightHalfHole2D


class Encoder:

    def __init__(self, roofPlaneO, roofPlaneI):
        """Place at roofPlaneO.pos and align to roofPlaneO.normal"""
        self.triangles = []
        self.roofEdgeI = Edge()
        self.roofEdgeO = Edge()
        self.splitEdgeF = Edge()
        self.splitEdgeB = Edge()

        width = cfg.encoder.width
        depth = cfg.encoder.depth
        holeRadius = cfg.encoder.holeDiameter/2
        holeHeight = cfg.encoder.holeHeight
        holeChamfer = cfg.encoder.holeChamfer
        notchDepth = cfg.encoder.pinNotchDepth

        pos = roofPlaneO.pos
        normal = roofPlaneO.normal
        align = Matrix.fromAlignment(Vector(0, 0, 1), normal).translated(pos)

        #    Hole
        #  __|  |__  z
        # |Box     | xy

        holeArc = Edge(Vector(p.y, p.x) for p in uprightHalfHole2D(holeRadius))
        holeEdgeT = holeArc.scaled(1 + holeChamfer/holeRadius).transformed(align)
        holeEdgeC = holeArc.translated(Vector(0, 0, -holeChamfer)).transformed(align)
        holeEdgeG = holeArc.translated(Vector(0, 0, -holeHeight)).transformed(align)

        #  Box
        # 0---1
        #     :\
        # y   : 2
        # zx  : | Notch

        boxEdgeT = Edge(
            Vector(0, depth/2, -holeHeight),
            Vector(width/2, depth/2, -holeHeight),
            Vector(width/2 + notchDepth, depth/2 - notchDepth, -holeHeight))
        boxEdgeT.add(boxEdgeT.mirroredY().reversed())
        boxEdgeT = boxEdgeT.transformed(align)
        boxEdgeG = Edge(roofPlaneI.intersect(Line(p, normal)) for p in boxEdgeT)

        # Chamfered notch
        boxEdgeT[2] = boxEdgeT[1]
        boxEdgeT[3] = boxEdgeT[4]

        boxFaceEdge = Edge(
            boxEdgeT[0],
            boxEdgeT[1],
            boxEdgeT[4],
            boxEdgeT[5],
            reversed(holeEdgeG))

        edges = [boxEdgeG, boxEdgeT, holeEdgeG, holeEdgeC, holeEdgeT]

        self.splitEdgeF.add(e[-1] for e in reversed(edges))
        self.splitEdgeB.add(e[0] for e in edges)
        self.roofEdgeI.add(boxEdgeG.collapsed().reversed())
        self.roofEdgeO.add(holeEdgeT)

        self.triangles.extend(holeEdgeC.meshPairwise(holeEdgeT))
        self.triangles.extend(holeEdgeG.meshPairwise(holeEdgeC))
        self.triangles.extend(boxEdgeG.meshPairwise(boxEdgeT))
        self.triangles.extend(Face(boxFaceEdge).triangulate())
