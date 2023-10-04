import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Vector

from .arc import arc2D
from .arc import uprightHalfHole2D


class Cable:
    def __init__(self, pos, wallThickness):
        #  .-+-.
        # / pos \
        # \     / z
        #  '---'  yx

        self.triangles = []
        self.wallEdgeF = Edge()
        self.wallEdgeB = Edge()
        self.splitEdgeG = Edge()
        self.splitEdgeT = Edge()

        cableRadius = cfg.cable.diameter/2
        filletRadius = cfg.cable.wallExitFillet
        bendRadius = cfg.cable.minBendRadius
        bumpRadius = cfg.cable.wallBumpRadius
        taperAngle = cfg.cable.wallBumpTaperAngle
        bracketWidth = cfg.bracket.holeLength + cfg.bracket.counterboreLength
        bumpWidth = bracketWidth*0.6 + cableRadius*0.4

        # Hole

        filletArcXY = arc2D(filletRadius, 0, math.tau/4)
        filletArcYZ = Edge(Vector(0, p.y, p.x) for p in filletArcXY)
        filletCenter = pos + Vector(0, wallThickness - filletRadius, -cableRadius)

        holeArcXY = uprightHalfHole2D(cableRadius)
        holeArcXZ = Edge(Vector(p.y, 0, p.x) for p in holeArcXY)
        holeArcs = [holeArcXZ.translated(pos + Vector(0, 0, -cableRadius))]
        holeEdgeT = holeArcs[0][:len(holeArcs[0])//2 + 1]
        holeEdgeG = holeArcs[0][len(holeArcs[0])//2:].reversed()

        for p in filletArcYZ:
            arcScale = 1 + (filletRadius - p.z)/cableRadius
            arcCenter = filletCenter + Vector(0, p.y)
            holeArcs.append(holeArcXZ.scaled(arcScale).translated(arcCenter))

        for i in range(len(holeArcs) - 1):
            self.triangles.extend(holeArcs[i+1].meshPairwise(holeArcs[i]))

        # Bump

        # minBendRadius
        # +--..
        # |    /. bendArc
        # |---/--)--
        # |45/ .' taperArc
        # | /.'
        # |/' wallBumpTaperAngle

        tipCenterXY = Vector(1, 1).normalized() * (bendRadius - bumpRadius)
        bendArcXY = arc2D(bendRadius, math.tau/4, -math.tau/8)
        bendArcXY.add(arc2D(bumpRadius, math.tau/8, -math.tau/8, tipCenterXY)[1:])
        bendArcYZ = Edge(Vector(0, -p.x, p.y) for p in bendArcXY)
        bendArcYZ = bendArcYZ.translated(holeArcs[0][-1] - bendArcYZ[0])

        taperFactor = math.sin(taperAngle) / math.cos(taperAngle)
        taperArcXY = arc2D(bumpRadius, 0, -(math.tau/4 - taperAngle), tipCenterXY)
        taperArcXY.add(Vector(0, taperArcXY[-1].y - taperArcXY[-1].x*taperFactor))
        taperArcYZ = Edge(Vector(0, -p.x, p.y) for p in taperArcXY)

        grooveArcs = [bendArcYZ.translated(p - bendArcYZ[0]) for p in holeEdgeG]
        grooveWidth = grooveArcs[-1][-1].x - pos.x
        grooveArcs.append(grooveArcs[-1].translated(Vector(bumpWidth - grooveWidth)))

        taperEdgeL = taperArcYZ.translated(grooveArcs[0][-1] - taperArcYZ[0])
        taperEdgeR = taperEdgeL.translated(Vector(bumpWidth))
        bumpEdgeR = Edge(grooveArcs[-1], taperEdgeR)
        bendEdgeB = Edge(arc[-1] for arc in reversed(grooveArcs))

        self.triangles.extend(taperEdgeL.meshPairwise(taperEdgeR))
        self.triangles.extend(bendEdgeB.meshPairwise(taperEdgeR[:1]))
        self.triangles.extend(bumpEdgeR.meshPairwise(bumpEdgeR[:1]))

        for i in range(len(grooveArcs) - 1):
            self.triangles.extend(grooveArcs[i].meshPairwise(grooveArcs[i+1]))

        # Edges

        self.wallEdgeF = Edge(holeEdgeT, bumpEdgeR[0], bumpEdgeR[-1], taperEdgeL[-1])
        self.wallEdgeB = holeArcs[-1].reversed()
        self.splitEdgeT = Edge(arc[0] for arc in reversed(holeArcs))
        self.splitEdgeG = Edge(
            reversed(taperEdgeL),
            reversed(grooveArcs[0]),
            (arc[-1] for arc in holeArcs)).collapsed()
