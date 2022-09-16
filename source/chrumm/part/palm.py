import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Plane
from chrumm.geo import Vector

from .arc import arc2D
from .arc import cornerArc2D


class Palm:

    def __init__(self, plan, side):
        self.faces = []
        self.triangles = []

        floorHeight = cfg.floor.outerHeight
        tentAngle = cfg.palm.tentAngle
        taperAngle = cfg.palm.taperAngle
        bodyMargin = cfg.palm.bodyMargin
        palmHeight = cfg.palm.height
        floorEndRadius = cfg.palm.floorEndRadius

        thumbLF = plan.points.thumbOLF.xy
        pinkyRF = plan.points.pinkyORF.xy
        extraRF = plan.points.extraORF.xy if side == "right" else pinkyRF

        bossL = plan.bosses.hitchL
        bossR = plan.bosses.hitchR

        # Roof edges

        tentMatrix = Matrix().rotatedY(tentAngle, Vector(0, 0, palmHeight))
        roofSketch = Edge(Vector(0, p.x - bodyMargin, p.y) for p in Palm._roofSketch2D())
        roofLines = [Line(p, Vector(1)).transformed(tentMatrix) for p in roofSketch]

        planeNormal = Vector(math.cos(taperAngle), -math.sin(taperAngle))
        planeOutset = (pinkyRF - thumbLF).magnitude() / 2
        extraOutset = (extraRF - pinkyRF).magnitude()

        planeL = Plane(Vector(-planeOutset), planeNormal.mirroredX())
        planeR = Plane(Vector(planeOutset + extraOutset), planeNormal)

        roofEdgeL = Edge(planeL.intersect(r) for r in roofLines)
        roofEdgeR = Edge(planeR.intersect(r) for r in roofLines)

        # Check height

        filletCenterZ = floorEndRadius - floorHeight
        minRoofZ = min(p.z for p in roofEdgeL + roofEdgeR)
        minPalmHeight = palmHeight + filletCenterZ - minRoofZ

        if palmHeight <= minPalmHeight:
            raise ValueError(f"palm.height must be greater than: {minPalmHeight:.3f}")

        # Front ground fillet

        filletCenterF = Vector(0, roofSketch[-1].y + floorEndRadius, filletCenterZ)
        filletSketchF = arc2D(floorEndRadius, math.tau/2, math.tau/4)
        filletSketchF = Edge(Vector(0, p.x, p.y) + filletCenterF for p in filletSketchF)

        filletLinesF = [Line(p, Vector(1)) for p in filletSketchF]
        roofEdgeL.add(planeL.intersect(f) for f in filletLinesF)
        roofEdgeR.add(planeR.intersect(f) for f in filletLinesF)

        # Back ground fillet

        filletCenterB = Vector(0, roofSketch[0].y - floorEndRadius, filletCenterZ)
        filletSketchB = arc2D(floorEndRadius, math.tau*0.75, math.tau/4)
        filletSketchB = Edge(Vector(0, p.x, p.y) + filletCenterB for p in filletSketchB)

        filletLinesB = [Line(p, Vector(1)) for p in filletSketchB]
        filletLB = Edge(planeL.intersect(f) for f in filletLinesB)
        filletRB = Edge(planeR.intersect(f) for f in filletLinesB)

        # Hitch notch

        hitchTaperAngle = cfg.palm.hitch.taperAngle
        hitchWidth = cfg.palm.hitch.width
        hitchDepth = cfg.palm.hitch.depth
        hitchRadius = cfg.palm.hitch.cornerRadius
        relNotchDepth = cfg.palm.hitch.relNotchDepth

        notchOutset = max(hitchRadius, bodyMargin)
        notchRadius = hitchRadius + notchOutset
        notchDeltaG = Vector(0, 0, -floorHeight)

        notchMinY = -bodyMargin - hitchDepth - notchOutset
        notchMaxY = roofSketch[-1].y + floorHeight
        notchY = notchMinY + (notchMaxY - notchMinY)*relNotchDepth

        notchBT = Line(Vector(0, -bodyMargin, 0), Vector(1))
        notchBG = Line(Vector(0, -bodyMargin, -floorHeight), Vector(1))
        notchFT = Line(Vector(0, notchY, 0), Vector(1))
        notchFG = Line(Vector(0, notchY - floorHeight, -floorHeight), Vector(1))

        hitchDir = Vector(-math.sin(hitchTaperAngle), -math.cos(hitchTaperAngle))
        hitchOrtho = hitchDir.ortho2D()
        hitchRT = Line(Vector(hitchWidth/2, -bodyMargin - hitchDepth), hitchDir)
        notchRT = hitchRT.translated(hitchOrtho*notchOutset)
        notchRG = notchRT.translated(hitchOrtho*floorHeight + notchDeltaG)

        notchRFT = notchFT.intersect(notchRT)
        notchRFG = notchFG.intersect(notchRG)
        notchRBT = notchBT.intersect(notchRT)
        notchRBG = notchBG.intersect(notchRG)

        notchNormal = (-hitchOrtho*floorHeight - notchDeltaG).normalized()
        notchPlaneR = Plane(notchRBG, notchNormal - hitchOrtho)

        notchFilletRG = Edge(notchPlaneR.intersect(f) for f in filletLinesB)
        notchFilletRT = notchFilletRG.translated(notchRBT - notchRBG)
        notchFilletLT = notchFilletRT.mirroredX()
        notchFilletLG = notchFilletRG.mirroredX()

        notchCornerRT = cornerArc2D(notchRadius, notchRBT, notchRFT, notchRFT.yz)
        notchCornerRG = (
            notchCornerRT
            .translated(-notchRFT)
            .scaled(1 + floorHeight/notchRadius)
            .translated(notchRFG))

        notchEdgeT = Edge(notchFilletRT[0], notchCornerRT)
        notchEdgeG = Edge(notchFilletRG[0], notchCornerRG)
        notchEdgeT.add(notchEdgeT.mirroredX().reversed())
        notchEdgeG.add(notchEdgeG.mirroredX().reversed())

        self.triangles.extend(notchEdgeG.meshPairwise(notchEdgeT))
        self.triangles.extend(filletLB.meshPairwise(notchFilletLG))
        self.triangles.extend(notchFilletLG.meshPairwise(notchFilletLT))
        self.triangles.extend(notchFilletLT.meshPairwise(notchFilletRT))
        self.triangles.extend(notchFilletRT.meshPairwise(notchFilletRG))
        self.triangles.extend(notchFilletRG.meshPairwise(filletRB))

        # Faces

        floorEdge = Edge(
            notchEdgeG.reversed(),
            filletRB[0],
            roofEdgeR[-1],
            roofEdgeL[-1],
            filletLB[0])

        self.faces.append(Face(floorEdge))
        self.faces.append(Face(Edge(filletRB, roofEdgeR).collapsed()))
        self.faces.append(Face(Edge(filletLB, roofEdgeL).collapsed().reversed()))
        self.faces.append(Face(notchEdgeT, [bossL.threadHole, bossR.threadHole]))

        backEdgeT = Edge(filletLB[-1], roofEdgeL[0], roofEdgeR[0], filletRB[-1])
        backEdgeG = Edge(
            notchFilletLG[-1],
            notchFilletLT[-1],
            notchFilletRT[-1],
            notchFilletRG[-1])

        self.triangles.extend(roofEdgeL.meshPairwise(roofEdgeR))
        self.triangles.extend(backEdgeT.meshPairwise(backEdgeG))

        # Final rotation and position

        finalDelta = (thumbLF + pinkyRF)/2
        finalAngle = (pinkyRF - thumbLF).angle2D()
        finalMatrix = Matrix().rotatedZ(finalAngle).translated(finalDelta)

        self.triangles = [t.transformed(finalMatrix) for t in self.triangles]
        self.triangles.extend(bossL.threadTriangles)
        self.triangles.extend(bossR.threadTriangles)

        for face in self.faces:
            face.edge = face.edge.transformed(finalMatrix)

    @staticmethod
    def _roofSketch2D():
        """Return roof profile from back (y=0) to front (y=-palmDepth)."""
        tiltAngle = cfg.palm.tiltAngle
        palmDepth = cfg.palm.depth
        palmHeight = cfg.palm.height
        roundness = cfg.palm.relRoofRoundness
        endRadius = cfg.palm.roofEndRadius

        # Construct arcs separately

        roofAngle = math.tau/4 * max(0, min(roundness, 1))
        endAngleB = math.tau/4 - roofAngle/2 + tiltAngle
        endAngleF = math.tau/4 - roofAngle/2 - tiltAngle

        endB = arc2D(endRadius, 0, endAngleB)
        endF = arc2D(endRadius, math.pi - endAngleF, endAngleF)

        endWidthB = endB[0].x - endB[-1].x
        endWidthF = endF[0].x - endF[-1].x
        roofWidth = palmDepth - endWidthB - endWidthF
        chordLength = roofWidth / math.cos(tiltAngle)

        if roofAngle > 0:
            # https://en.wikipedia.org/wiki/Circular_segment
            roofRadius = chordLength / (2 * math.sin(roofAngle/2))
            roof = arc2D(roofRadius, endAngleB, roofAngle)
        else:
            roofHeight = chordLength * math.sin(tiltAngle)
            roof = Edge(Vector(), Vector(-roofWidth, -roofHeight))

        # Join arcs

        sketch = endB.translated(Vector(-endRadius, palmHeight - endRadius))
        sketch.add(roof[1:].translated(sketch[-1] - roof[0]))
        sketch.add(endF[1:].translated(sketch[-1] - endF[0]))

        return sketch
