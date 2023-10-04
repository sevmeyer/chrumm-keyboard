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
from .bumper import Bumper


class Palm:

    def __init__(self, plan):
        self.faces = []
        self.triangles = []

        floorHeight = cfg.floor.outerHeight
        taperAngle = cfg.palm.taperAngle
        bodyMargin = cfg.palm.bodyMargin
        palmHeight = cfg.palm.height
        floorFillet = cfg.palm.floorFillet
        floorContact = cfg.palm.floorContactWidth
        hitchDepth = cfg.palm.hitchDepth
        hitchRadius = cfg.palm.hitchCornerRadius

        thumbLF = plan.points.thumbOLF.xy
        pinkyRF = plan.points.pinkyORF.xy
        hitchLB = plan.points.hitchOLB
        hitchRB = plan.points.hitchORB

        bossL = plan.bosses.hitchL
        bossR = plan.bosses.hitchR

        # Roof edges

        planeNormal = Vector(math.cos(taperAngle), -math.sin(taperAngle))
        planeOutset = (pinkyRF - thumbLF).magnitude() / 2

        planeL = Plane(Vector(-planeOutset), planeNormal.mirroredX())
        planeR = Plane(Vector(planeOutset), planeNormal)

        roofSpine = Palm._roofSpine()
        roofL = Edge(planeL.intersect(r) for r in roofSpine)
        roofR = Edge(planeR.intersect(r) for r in roofSpine)

        palmBG = Vector(0, roofL[0].y, -floorHeight)
        palmFG = Vector(0, roofL[-1].y, -floorHeight)

        # Final height

        roofRaise = Vector(0, 0, palmHeight - floorHeight - max(p.z for p in roofL))
        roofL = roofL.translated(roofRaise)
        roofR = roofR.translated(roofRaise)

        minRoofZ = min(p.z for p in roofL + roofR)
        minPalmHeight = palmHeight - minRoofZ - floorHeight + floorFillet

        if palmHeight <= minPalmHeight:
            raise ValueError(f"palm.height must be greater than: {minPalmHeight:.3f}")

        # Front ground fillet

        filletCenterF = Vector(0, palmFG.y + floorFillet, -floorHeight + floorFillet)
        filletSketchF = arc2D(floorFillet, math.tau/2, math.tau/4)
        filletSketchF = Edge(Vector(0, p.x, p.y) + filletCenterF for p in filletSketchF)

        filletLinesF = [Line(p, Vector(1)) for p in filletSketchF]
        roofL.add(planeL.intersect(f) for f in filletLinesF)
        roofR.add(planeR.intersect(f) for f in filletLinesF)

        # Back ground fillet

        filletCenterB = Vector(0, palmBG.y - floorFillet, filletCenterF.z)
        filletSketchB = arc2D(floorFillet, math.tau*0.75, math.tau/4)
        filletSketchB = Edge(Vector(0, p.x, p.y) + filletCenterB for p in filletSketchB)

        filletLinesB = [Line(p, Vector(1)) for p in filletSketchB]
        filletLB = Edge(planeL.intersect(f) for f in filletLinesB)
        filletRB = Edge(planeR.intersect(f) for f in filletLinesB)

        # Hitch notch

        notchY = palmFG.y + floorContact
        notchBT = Line(Vector(0, -bodyMargin, 0), Vector(1))
        notchBG = Line(Vector(0, -bodyMargin, -floorHeight), Vector(1))
        notchFT = Line(Vector(0, notchY + floorHeight, 0), Vector(1))
        notchFG = Line(Vector(0, notchY, -floorHeight), Vector(1))

        floorOffset = Vector(0, 0, floorHeight)
        notchTaperOffset = floorOffset - planeR.normal*floorHeight
        notchFloorOffset = floorOffset + planeR.normal*floorContact

        notchRG = Line(planeR.pos - notchFloorOffset, planeR.normal.ortho2D())
        notchRT = notchRG.translated(notchTaperOffset)

        notchRFT = notchFT.intersect(notchRT)
        notchRFG = notchFG.intersect(notchRG)
        notchRBT = notchBT.intersect(notchRT)
        notchRBG = notchBG.intersect(notchRG)

        notchTaperNormal = notchTaperOffset.normalized()
        notchTaperPlaneR = Plane(notchRBG, notchTaperNormal - planeR.normal)

        notchFilletRG = Edge(notchTaperPlaneR.intersect(f) for f in filletLinesB)
        notchFilletRT = notchFilletRG.translated(notchRBT - notchRBG)
        notchFilletLT = notchFilletRT.mirroredX()
        notchFilletLG = notchFilletRG.mirroredX()
        notchCornerRT = cornerArc2D(hitchRadius, notchRBT, notchRFT, notchRFT.yz)
        notchCornerRG = (
            notchCornerRT
            .translated(-notchRFT)
            .scaled(1 + floorHeight/hitchRadius)
            .translated(notchRFG))

        notchEdgeT = Edge(notchFilletRT[0], notchCornerRT)
        notchEdgeG = Edge(notchFilletRG[0], notchCornerRG)
        notchEdgeT.add(notchEdgeT.mirroredX().reversed())
        notchEdgeG.add(notchEdgeG.mirroredX().reversed())

        backEdgeT = Edge(filletLB[-1], roofL[0], roofR[0], filletRB[-1])
        backEdgeG = Edge(
            notchFilletLG[-1],
            notchFilletLT[-1],
            notchFilletRT[-1],
            notchFilletRG[-1])

        maxNotchW = notchRBT.x * 2
        maxHitchW = (hitchLB - hitchRB).magnitude() + hitchRadius
        maxNotchY = notchRFT.y
        minHitchY = -(hitchDepth + bodyMargin)

        if maxNotchW <= maxHitchW or maxNotchY >= minHitchY:
            raise ValueError("The palm hitch overlaps the palm notch.")

        self.triangles.extend(roofL.meshPairwise(roofR))
        self.triangles.extend(backEdgeT.meshPairwise(backEdgeG))
        self.triangles.extend(notchEdgeG.meshPairwise(notchEdgeT))
        self.triangles.extend(filletLB.meshPairwise(notchFilletLG))
        self.triangles.extend(notchFilletLG.meshPairwise(notchFilletLT))
        self.triangles.extend(notchFilletLT.meshPairwise(notchFilletRT))
        self.triangles.extend(notchFilletRT.meshPairwise(notchFilletRG))
        self.triangles.extend(notchFilletRG.meshPairwise(filletRB))

        # Groove

        grooveLT = Edge()
        grooveLG = Edge()
        grooveRT = Edge()
        grooveRG = Edge()

        if cfg.palm.groove:
            grooveWidth = cfg.palm.groove.width
            grooveHeight = cfg.palm.groove.height
            grooveMargin = cfg.palm.groove.roofMargin
            relClampSize = cfg.palm.groove.relClampSize

            if grooveHeight <= floorFillet:
                raise ValueError("palm.floorFillet must be less than palm.groove.height.")

            grooveSpineT = Palm._roofSpine(grooveMargin)
            grooveSpineG = Palm._roofSpine(grooveMargin + grooveHeight)

            grooveSpineT = [g.translated(roofRaise) for g in grooveSpineT]
            grooveSpineG = [g.translated(roofRaise) for g in grooveSpineG]

            grooveLTO = Edge(planeL.intersect(g) for g in grooveSpineT)
            grooveLGO = Edge(planeL.intersect(g) for g in grooveSpineG)
            grooveRTO = Edge(planeR.intersect(g) for g in grooveSpineT)
            grooveRGO = Edge(planeR.intersect(g) for g in grooveSpineG)

            planeLI = Plane(planeL.pos - planeL.normal*grooveWidth, planeL.normal)
            planeRI = Plane(planeR.pos - planeR.normal*grooveWidth, planeR.normal)

            grooveLTI = Edge(planeLI.intersect(g) for g in grooveSpineT)
            grooveLGI = Edge(planeLI.intersect(g) for g in grooveSpineG)
            grooveRTI = Edge(planeRI.intersect(g) for g in grooveSpineT)
            grooveRGI = Edge(planeRI.intersect(g) for g in grooveSpineG)

            for edge in (
                    grooveLTO, grooveLGO, grooveRTO, grooveRGO,
                    grooveLTI, grooveLGI, grooveRTI, grooveRGI):
                edge.insert(0, edge[0].xy - floorOffset)
                edge.append(edge[-1].xy - floorOffset)

            def addClamp(a, b, c, d):
                clampSize = grooveHeight * relClampSize
                clampOut = (d - a).ortho2D().normalized() * clampSize
                clampUp = Vector(0, 0, clampSize)
                clampA = a*0.8 + d*0.2 + clampOut + clampUp
                clampD = a*0.2 + d*0.8 + clampOut + clampUp
                self.triangles.extend(Edge(a, b, c, d).meshPairwise(
                    Edge(clampA, clampA, clampD, clampD), True))

            if relClampSize > 0:
                addClamp(grooveLGO[0], grooveLGO[1], grooveLGI[1], grooveLGI[0])
                addClamp(grooveRGI[0], grooveRGI[1], grooveRGO[1], grooveRGO[0])
                addClamp(grooveLGI[-1], grooveLGI[-2], grooveLGO[-2], grooveLGO[-1])
                addClamp(grooveRGO[-1], grooveRGO[-2], grooveRGI[-2], grooveRGI[-1])
                self.triangles.extend(grooveLGO[1:-1].meshPairwise(grooveLGI[1:-1]))
                self.triangles.extend(grooveRGI[1:-1].meshPairwise(grooveRGO[1:-1]))
            else:
                self.triangles.extend(grooveLGO.meshPairwise(grooveLGI))
                self.triangles.extend(grooveRGI.meshPairwise(grooveRGO))

            self.triangles.extend(grooveLTI.meshPairwise(grooveLTO))
            self.triangles.extend(grooveRTO.meshPairwise(grooveRTI))
            self.faces.append(Face(grooveLGI + grooveLTI.reversed()))
            self.faces.append(Face(grooveRTI + grooveRGI.reversed()))
            self.faces.append(Face(grooveLGO.reversed()))
            self.faces.append(Face(grooveRGO))

            grooveLT = grooveLTO.reversed()
            grooveRT = grooveRTO.reversed()
            grooveLG = Edge(
                grooveLTO[-1], grooveLTI[-1],
                grooveLGI[-1], grooveLGO[-1],
                grooveLGO[0], grooveLGI[0],
                grooveLTI[0], grooveLTO[0])
            grooveRG = Edge(
                grooveRTO[0], grooveRTI[0],
                grooveRGI[0], grooveRGO[0],
                grooveRGO[-1], grooveRGI[-1],
                grooveRTI[-1], grooveRTO[-1])

        # Bumpers

        floorHoles = []

        if cfg.bumper:
            bumperInset = cfg.bumper.margin + cfg.bumper.diameter/2

            if cfg.palm.groove:
                bumperInset += grooveMargin + grooveHeight

            bumperInset = max(bumperInset, floorContact/2)
            bumperLineF = Line(Vector(0, palmFG.y + bumperInset), Vector(1))
            bumperLineB = Line(Vector(0, palmBG.y - bumperInset), Vector(1))

            bumperLinePos = planeL.pos - planeL.normal*(floorContact/2)
            bumperLineDir = planeL.normal.ortho2D()
            bumperLineL = Line(bumperLinePos, bumperLineDir)

            bumperLF = bumperLineL.intersect(bumperLineF)
            bumperLB = bumperLineL.intersect(bumperLineB)
            bumperRF = bumperLF.mirroredX()
            bumperRB = bumperLB.mirroredX()

            for bumperCenter in bumperLF, bumperLB, bumperRF, bumperRB:
                bumper = Bumper(bumperCenter)
                self.triangles.extend(bumper.triangles)
                floorHoles.append(bumper.floorEdge)

        # Final placement

        placeDelta = (thumbLF + pinkyRF)/2
        placeAngle = (pinkyRF - thumbLF).angle2D()
        placeMatrix = Matrix().rotatedZ(placeAngle).translated(placeDelta)

        self.triangles = [t.transformed(placeMatrix) for t in self.triangles]
        self.triangles.extend(bossL.threadTriangles)
        self.triangles.extend(bossR.threadTriangles)

        # Faces

        floorHoles = [h.transformed(placeMatrix) for h in floorHoles]
        floorEdge = Edge(
            notchEdgeG.reversed(),
            filletRB[0],
            grooveRG,
            roofR[-1],
            roofL[-1],
            grooveLG,
            filletLB[0])

        self.faces.append(Face(floorEdge, floorHoles))
        self.faces.append(Face(Edge(filletRB, roofR, grooveRT).collapsed()))
        self.faces.append(Face(Edge(filletLB, roofL, grooveLT).collapsed().reversed()))
        self.faces.append(Face(notchEdgeT, [bossL.threadHole, bossR.threadHole]))

        for face in self.faces:
            face.edge = face.edge.transformed(placeMatrix)

    @staticmethod
    def _roofSpine(inset=0):
        """Return list of lines that describe the roof profile."""
        bodyMargin = cfg.palm.bodyMargin
        tentAngle = cfg.palm.tentAngle
        tiltAngle = cfg.palm.tiltAngle
        palmDepth = cfg.palm.depth - 2*inset
        roundness = cfg.palm.relRoofRoundness
        roofFillet = max(0, cfg.palm.roofFillet - inset)

        # Construct separate 2D arcs

        roofAngle = math.tau/4 * max(0, min(roundness, 1))
        endAngleB = math.tau/4 - roofAngle/2 + tiltAngle
        endAngleF = math.tau/4 - roofAngle/2 - tiltAngle

        endArcB = arc2D(roofFillet, 0, endAngleB)
        endArcF = arc2D(roofFillet, math.pi - endAngleF, endAngleF)

        endWidthB = endArcB[0].x - endArcB[-1].x
        endWidthF = endArcF[0].x - endArcF[-1].x
        roofWidth = palmDepth - endWidthB - endWidthF
        chordLength = roofWidth / math.cos(tiltAngle)

        if roofAngle > 0:
            # https://en.wikipedia.org/wiki/Circular_segment
            roofRadius = chordLength / (2 * math.sin(roofAngle/2))
            # Scale the radius for a smoother segmentation
            roofArc = arc2D(roofRadius*2, endAngleB, roofAngle).scaled(0.5)
        else:
            roofHeight = chordLength * math.sin(tiltAngle)
            roofArc = Edge(Vector(), Vector(-roofWidth, -roofHeight))

        # Join arcs

        sketchOffset = Vector(bodyMargin + roofFillet + inset, roofFillet + inset)
        sketch = endArcB.translated(-sketchOffset)
        sketch.add(roofArc[1:].translated(sketch[-1] - roofArc[0]))
        sketch.add(endArcF[1:].translated(sketch[-1] - endArcF[0]))

        # Use sketch to position 3D lines

        tentMatrix = Matrix().rotatedY(tentAngle)
        spine = Edge(Vector(0, p.x, p.y) for p in sketch)

        return [Line(p, Vector(1)).transformed(tentMatrix) for p in spine]
