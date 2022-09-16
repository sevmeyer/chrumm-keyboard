import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Matrix
from chrumm.geo import Triangle
from chrumm.geo import Vector

from .arc import arc2D


class CableHole:

    def __init__(self, roofIL, roofIR):
        self.wallEdgeI = Edge()
        self.wallEdgeO = Edge()
        self.triangles = []

        radius = cfg.cable.diameter/2
        chamfer = cfg.cable.wallChamfer
        lipHeight = cfg.floor.lipHeight
        lipMargin = cfg.floor.lipMargin
        wallThickness = cfg.body.wallThickness

        # Hole

        holeF = Vector(0, 0, lipHeight + lipMargin + radius)
        holeB = Vector(0, wallThickness - chamfer, holeF.z)
        wallB = Vector(0, wallThickness, holeF.z)

        holeArc = Edge(Vector(p.x, 0, p.y) for p in arc2D(radius, 0, math.tau/8))
        holeChord = radius - holeArc[-1].z
        holeArc.add(Vector(holeArc[-1].x - holeChord, 0, radius))
        holeArc.add(holeArc.mirroredX().reversed())

        chamferScale = (radius + chamfer) / radius

        holeEdges = [
            holeArc.scaled(chamferScale).translated(wallB),
            holeArc.translated(holeB),
            holeArc.translated(holeF)]

        for edge in holeEdges:
            edge.insert(0, edge[0].xy)
            edge.add(edge[-1].xy)

        self.wallEdgeI.add(holeEdges[-1])
        self.wallEdgeO.add(holeEdges[0])

        for i in range(len(holeEdges) - 1):
            self.triangles.extend(holeEdges[i+1].meshPairwise(holeEdges[i]))

        if chamfer > 0:
            self.triangles.append(Triangle(
                holeEdges[2][0],
                holeEdges[1][0],
                holeEdges[0][0]))
            self.triangles.append(Triangle(
                holeEdges[0][-1],
                holeEdges[1][-1],
                holeEdges[2][-1]))

        # Fastening hook

        if cfg.cable.hook:
            hookRadius = cfg.cable.hook.diameter / 2
            hookLength = cfg.cable.hook.length
            hookChamfer = cfg.cable.hook.wallChamfer
            hookHead = cfg.cable.hook.headThickness

            wallF = Vector(0, 0, holeF.z + radius)
            hookB = Vector(0, -hookChamfer, wallF.z)
            headB = Vector(0, -hookLength, wallF.z)
            headF = Vector(0, -hookLength - hookHead, wallF.z)

            hookArc = Edge(Vector(p.x, 0, p.y) for p in arc2D(hookRadius, 0, math.pi))

            hookChamferScale = (hookRadius + hookChamfer) / hookRadius
            hookHeadScale = (hookRadius + hookHead) / hookRadius

            hookEdges = [
                hookArc.scaled(hookChamferScale).translated(wallF),
                hookArc.translated(hookB),
                hookArc.translated(headB),
                hookArc.scaled(hookHeadScale).translated(headB),
                hookArc.scaled(hookHeadScale).translated(headF)]

            holeMid = len(holeEdges[-1]) // 2

            grooveEdgeB = holeEdges[-1][holeMid-2:holeMid+2]
            grooveEdgeF = grooveEdgeB.translated(Vector(0, -hookLength - hookHead))
            hookExtrude = Vector(0, 0, -holeChord)

            for edge in hookEdges:
                edge.insert(0, edge[0] + hookExtrude)
                edge.append(edge[-1] + hookExtrude)

            for i in range(len(hookEdges) - 1):
                self.triangles.extend(hookEdges[i].meshPairwise(hookEdges[i+1]))

            baseEdgeOR = Edge(hookEdges[3][0], hookEdges[2][0], hookEdges[1][0])
            baseEdgeIL = Edge(hookEdges[3][-1], hookEdges[2][-1], hookEdges[1][-1])
            baseEdgeIR = Edge(hookEdges[4][0], grooveEdgeF[0], grooveEdgeB[0], hookEdges[0][0])
            baseEdgeOL = Edge(hookEdges[4][-1], grooveEdgeF[-1], grooveEdgeB[-1], hookEdges[0][-1])

            self.triangles.extend(grooveEdgeF.meshPairwise(grooveEdgeB))
            self.triangles.extend(baseEdgeIR.meshPairwise(baseEdgeOR))
            self.triangles.extend(baseEdgeIL.meshPairwise(baseEdgeOL))
            self.triangles.extend(Face(hookEdges[-1] + grooveEdgeF.reversed()).triangulate())

            self.wallEdgeI = holeEdges[-1][:holeMid-1] + hookEdges[0] + holeEdges[-1][holeMid+1:]

        # Position

        pos = (roofIL + roofIR).xy / 2
        angle = (roofIR - roofIL).angle2D()
        matrix = Matrix().rotatedZ(angle).translated(pos)

        self.wallEdgeO = self.wallEdgeO.transformed(matrix)
        self.wallEdgeI = self.wallEdgeI.transformed(matrix).reversed()
        self.triangles = [t.transformed(matrix) for t in self.triangles]
