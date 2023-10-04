import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Vector

from .arc import arc2D
from .arc import cornerArc2D
from .arc import uprightHole2D


class CornerBracket:
    """Bracket between wall and roof, snapped to the yz plane."""

    def __init__(self, a, b, c, side):
        # b<---------a
        #    \  \  ( ) c
        #     \ (\_____|  z
        #      \___/   |  xy

        a = a.yz
        b = b.yz
        c = c.yz

        self.wallEdge = Edge()
        self.roofEdge = Edge()
        self.splitEdge = Edge()
        self.splitHoles = []
        self.triangles = []

        nutAcross = cfg.bracket.nutAcrossFlats
        nutRadius = nutAcross / 3**0.5
        boreRadius = cfg.bracket.counterboreDiameter/2
        boreLength = cfg.bracket.counterboreLength
        holeLength = cfg.bracket.holeLength
        taperAngle = cfg.bracket.taperAngle
        taperMargin = cfg.bracket.taperMargin
        wallMargin = cfg.bracket.wallMargin
        baseMargin = cfg.bracket.baseMargin
        apexMargin = cfg.bracket.apexMargin
        extraMargin = cfg.bracket.backCornerExtraMargin
        cornerRadius = cfg.bracket.cornerRadius
        cableInset = cfg.cable.bracketInset if cfg.cable else 0

        # Always construct from back to front

        isBackward = a.y < b.y

        if isBackward:
            a = a.mirroredY()
            b = b.mirroredY()
            c = c.mirroredY()
            extraMargin = 0
            cableInset = 0

        # Sketch on yz plane

        wallDir = Vector(0, 0, 1)
        wallOrtho = Vector(0, 1, 0)
        roofDir = (b - a).normalized()
        roofOrtho = Vector(0, roofDir.z, -roofDir.y)
        roofAngle = Vector(-roofDir.y, -roofDir.z).angle2D()
        taperDir = Vector(0, -math.sin(taperAngle), math.cos(taperAngle))
        taperOrtho = Vector(0, -taperDir.z, taperDir.y)

        nutRoofDist = _hexTangentDist(nutRadius, roofAngle)
        nutTaperDist = _hexTangentDist(nutRadius, taperAngle - math.pi/2)
        roofOffset = max(boreRadius, nutRoofDist) + baseMargin + extraMargin
        wallOffset = max(boreRadius, nutRadius) + wallMargin + extraMargin
        apexOffset = max(boreRadius, nutAcross/2) + apexMargin
        taperOffset = max(boreRadius, nutTaperDist) + taperMargin + cableInset

        wallOffsetLine = Line(c - wallOrtho*wallOffset, wallDir)
        roofOffsetLine = Line(a - roofOrtho*roofOffset, roofDir)
        screwCenter = roofOffsetLine.intersect(wallOffsetLine)

        wallLine = Line(c, wallDir)
        roofLine = Line(a, roofDir)
        apexLine = Line(screwCenter - Vector(0, 0, apexOffset), Vector(0, 1))
        taperLine = Line(screwCenter + taperOrtho*taperOffset, taperDir)

        # Edges and triangles

        archLBG = wallLine.intersect(apexLine)
        archLFG = taperLine.intersect(apexLine)
        archLFT = taperLine.intersect(roofLine)

        arcL = _archCorner(cornerRadius, archLBG, archLFG, archLFT)
        archL = Edge(archLBG, arcL, archLFT)
        moveR = Vector(holeLength + boreLength)
        archR = archL.translated(moveR)

        self.wallEdge = Edge(archL[0], archR[0], c + moveR)
        self.roofEdge = Edge(a + moveR, archR[-1], archL[-1])
        self.splitEdge = archL

        holeTriangles, holeL, holeR = _screwHole(screwCenter, side, False)
        edgeR = Edge(archR, self.roofEdge[0], self.wallEdge[-1])
        faceR = Face(edgeR.collapsed().reversed(), [holeR])

        self.triangles.extend(holeTriangles)
        self.triangles.extend(faceR.triangulate())
        self.splitHoles.append(holeL.reversed())

        # Ziptie

        if cfg.cable and not isBackward:
            cableDiameter = cfg.cable.diameter
            zipWidth = cfg.cable.ziptieWidth
            zipHeight = cfg.cable.ziptieHeight
            humpWidth = cfg.cable.gripHumpWidth
            humpHeight = cfg.cable.gripHumpHeight
            humpRadius = cfg.cable.minBendRadius
            humpInset = humpRadius - humpHeight

            # Ziptie hump

            humpCenterF = taperLine.translated(taperOrtho*(zipHeight + taperMargin - humpRadius))
            humpCenterT = apexLine.translated(Vector(0, 0, humpInset))
            humpCenter = humpCenterF.intersect(humpCenterT)
            bumpCenter = archLBG - Vector(0, 0, cableDiameter + humpRadius)
            maxCableDiameter = (humpCenter - bumpCenter).magnitude() - 2*humpRadius

            if cableDiameter > maxCableDiameter:
                raise ValueError(
                    "The cable does not fit between the wall bump and grip hump.\n"
                    "  Try to decrease cable.minBendRadius, cable.gripHumpHeight,\n"
                    "  or increase cable.bracketInset.")

            minHumpTaper = math.asin(humpInset / humpRadius)
            humpSpan = math.pi - taperAngle - max(minHumpTaper, taperAngle)
            humpArcXY = arc2D(humpRadius, taperAngle, humpSpan)
            humpArc = Edge(Vector(0, -p.x, -p.y) + humpCenter for p in humpArcXY)

            humpLineF = Line(humpArc[0], taperLine.dir)
            humpLineB = Line(humpArc[-1], taperLine.dir.mirroredY())
            humpLineG = Line(apexLine.pos - Vector(0, 0, humpHeight), Vector(0, 1))

            humpLFT = humpLineF.intersect(roofLine)
            humpLBT = humpLineB.intersect(apexLine)
            humpLFG = humpLineG.intersect(humpLineF)
            humpRBT = archLFT + Vector(humpWidth/2)

            humpArchL = Edge(humpLFT, humpArc, humpLBT).collapsed()
            humpArchR = humpArchL.translated(Vector(humpWidth/2))

            # Ziptie hole

            zipArcCenterXY = Vector(0, zipHeight/2 - zipWidth/2)
            zipArcXY = arc2D(zipHeight/2, 0, -math.pi, zipArcCenterXY)
            zipHoleXY = zipArcXY.transformed(Matrix().rotatedZ(taperAngle))
            zipHoleXY.add(zipHoleXY.mirroredX().mirroredY())

            zipCenter = humpLFT*0.4 + humpLFG*0.6 - taperOrtho*(zipHeight/2 + taperMargin)
            zipHoleL = Edge(Vector(0, p.x, p.y) + zipCenter for p in zipHoleXY)
            zipHoleR = zipHoleL.translated(Vector(humpWidth/2))

            if zipHoleL[0].z <= arcL[-1].z:
                overlap = taperDir*(zipHoleL[0] - arcL[-1]).magnitude()
                zipHoleL = zipHoleL.translated(overlap)
                zipHoleR = zipHoleL.translated(Vector(humpWidth/2))

            arcR = arcL.translated(Vector(humpWidth/2))
            humpEdgeR = Edge(humpArchR, arcR, zipHoleR, humpRBT).collapsed()

            self.triangles.extend(Face(humpEdgeR).triangulate())
            self.triangles.extend(zipHoleL.meshPairwise(zipHoleR, True))
            self.triangles.extend(humpArchL.meshPairwise(humpArchR))
            self.splitHoles.append(zipHoleL.reversed())

            # Adjust bracket edges

            archR = Edge(archL[0], archR)
            archL = Edge(humpArchL[-1], humpArchR[-1], arcR, zipHoleR[0], zipHoleR[-1], humpRBT)

            self.splitEdge = Edge(humpArchL, archR[0]).reversed()
            self.roofEdge = Edge(a + moveR, archR[-1], archL[-1], humpArchR[0], humpArchL[0])

        self.triangles.extend(archR.meshPairwise(archL))

        if isBackward:
            self.wallEdge = self.wallEdge.mirroredY()
            self.roofEdge = self.roofEdge.mirroredY()
            self.splitEdge = self.splitEdge.mirroredY().reversed()
            self.splitHoles = [h.mirroredY().reversed() for h in self.splitHoles]
            self.triangles = [t.mirroredY().reversed() for t in self.triangles]


class RoofBracket:
    """Bracket on roof with optional PCB mount, snapped to the yz plane."""

    def __init__(self, a, b, refMatrix, side):
        # b<------------a  z
        #    \ ( )| |/     xy
        #     ----| |
        #         |_|

        a = a.yz
        b = b.yz
        ab = b - a

        self.roofEdge = Edge()
        self.splitEdge = Edge()
        self.splitHole = Edge()
        self.triangles = []

        nutAcross = cfg.bracket.nutAcrossFlats
        nutRadius = nutAcross / 3**0.5
        boreRadius = cfg.bracket.counterboreDiameter/2
        boreLength = cfg.bracket.counterboreLength
        holeLength = cfg.bracket.holeLength
        taperAngle = cfg.bracket.taperAngle
        taperMargin = cfg.bracket.taperMargin
        wallMargin = cfg.bracket.wallMargin
        baseMargin = cfg.bracket.baseMargin
        apexMargin = cfg.bracket.apexMargin
        cornerRadius = cfg.bracket.cornerRadius

        # Sketch on yz plane

        taperDir = Vector(0, math.sin(taperAngle), math.cos(taperAngle))
        taperOrtho = Vector(0, taperDir.z, -taperDir.y)
        nutTaperDist = _hexTangentDist(nutRadius, taperAngle - math.pi/2)

        roofOffset = max(boreRadius, nutAcross/2) + baseMargin
        apexOffset = max(boreRadius, nutAcross/2) + apexMargin
        taperOffset = max(boreRadius, nutTaperDist) + taperMargin

        lineB = Line(taperOrtho*taperOffset, taperDir)
        lineF = Line(lineB.pos.mirroredY(), lineB.dir.mirroredY())
        lineG = Line(Vector(0, 0, -apexOffset), Vector(0, 1))
        lineT = Line(Vector(0, 0, roofOffset), Vector(0, 1))

        archLFT = lineF.intersect(lineT)
        archLFG = lineF.intersect(lineG)
        archLBG = lineB.intersect(lineG)
        archLBT = lineB.intersect(lineT)

        archLF = Edge(archLFT, _archCorner(cornerRadius, archLFT, archLFG, archLBG))
        archLB = Edge(_archCorner(cornerRadius, archLFG, archLBG, archLBT), archLBT)

        # Placement

        roofDir = ab.normalized()
        roofOrtho = Vector(0, -roofDir.z, roofDir.y)
        roofAngle = Vector(-ab.y, -ab.z).angle2D()
        roofAlign = Matrix().translated(-lineT.pos).rotatedX(roofAngle)

        moveR = Vector(boreLength + holeLength)

        if cfg.pcb and cfg.pcb.mount:
            bossFG, bossFT, bossBG, bossBT = self._makeBoss(refMatrix)
            bossDir = (bossFT.yz - bossFG.yz).normalized()
            bossOrtho = Vector(0, -bossDir.z, bossDir.y)

            roofLine = Line(a, roofDir)
            apexLine = Line(a + roofOrtho*(lineT.pos - lineG.pos).z, roofDir)
            armLineF = Line(bossFT.yz, bossDir)
            armLineB = Line(bossBT.yz, bossDir)

            armOffset = max(boreRadius, nutRadius) + wallMargin
            armOffsetLine = Line(bossFT.yz + bossOrtho*armOffset, bossDir)

            roofPos = roofLine.intersect(armOffsetLine)
            roofAlign = roofAlign.translated(roofPos)
            archLF = archLF.transformed(roofAlign)
            archLB = archLB.transformed(roofAlign)

            armR = Edge(bossBT, bossBG, bossFG, bossFT)
            armL = Edge(
                roofLine.intersect(armLineB),
                apexLine.intersect(armLineB),
                apexLine.intersect(armLineF),
                roofLine.intersect(armLineF)).translated(moveR)

            archLB = archLB.translated(armL[1].yz - archLB[0])
            archRF = archLF.translated(moveR)
            archRB = archLB.translated(moveR)

            archL = Edge(archLF, armL[2].yz, archLB)
            archR = Edge(archRF, armL[2], archRB)
            faceR = Edge(archRF, armL[2:])

            self.triangles.extend(armR.meshPairwise(armL, True))
            self.triangles.extend(armL[:2].meshPairwise(archRB.reversed()))
            self.roofEdge = Edge(archL[0], archR[0], armL[-1], armL[0], archR[-1], archL[-1])
        else:
            archD = (archLF[0] - archLB[-1]).magnitude()
            roofPos = a + roofDir*(0.85*(ab.magnitude() - archD) + archD/2)
            roofAlign = roofAlign.translated(roofPos)

            archL = Edge(archLF, archLB).transformed(roofAlign)
            archR = archL.translated(moveR)
            faceR = archR

            self.roofEdge = Edge(archL[0], archR[0], archR[-1], archL[-1])

        holeTriangles, holeL, holeR = _screwHole(Vector(), side, False)

        holeTriangles = [t.transformed(roofAlign) for t in holeTriangles]
        holeL = holeL.transformed(roofAlign)
        holeR = holeR.transformed(roofAlign)

        self.triangles.extend(holeTriangles)
        self.triangles.extend(Face(faceR, [holeR]).triangulate())
        self.triangles.extend(archL.meshPairwise(archR))
        self.splitEdge = archL.reversed()
        self.splitHole = holeL.reversed()

    def _makeBoss(self, refMatrix):
        splitAngle = cfg.body.splitAngle
        bossHeight = cfg.pcb.mount.bossHeight
        bossRadius = cfg.pcb.mount.bossDiameter/2
        threadRadius = cfg.pcb.mount.threadDiameter/2
        nutRadius = cfg.pcb.mount.nutDiameter/2
        xOffset = cfg.pcb.mount.xDistToFirstPinky
        yOffset = cfg.pcb.mount.yDistToFirstPinky
        zOffset = cfg.switch.innerHeight

        holeG = uprightHole2D(threadRadius)
        holeT = holeG.translated(Vector(0, 0, bossHeight))
        edgeG = arc2D(bossRadius, 0, math.pi)
        edgeT = edgeG.translated(Vector(0, 0, bossHeight))

        armFG = Vector(bossRadius, -bossRadius)
        armBG = Vector(-bossRadius, -bossRadius)
        armFT = Vector(bossRadius, -nutRadius, bossHeight)
        armBT = Vector(-bossRadius, -nutRadius, bossHeight)

        rotMatrix = Matrix().rotatedZ(-math.tau/4 - splitAngle)
        holeG = holeG.transformed(rotMatrix)
        holeT = holeT.transformed(rotMatrix)
        edgeG = Edge(armFG, edgeG, armBG).transformed(rotMatrix)
        edgeT = Edge(armFT, edgeT, armBT).transformed(rotMatrix)

        offset = Vector(-xOffset, -yOffset, -zOffset)
        holeG = holeG.translated(offset).transformed(refMatrix)
        holeT = holeT.translated(offset).transformed(refMatrix)
        edgeG = edgeG.translated(offset).transformed(refMatrix)
        edgeT = edgeT.translated(offset).transformed(refMatrix)

        self.triangles.extend(holeT.meshPairwise(holeG, True))
        self.triangles.extend(edgeG.meshPairwise(edgeT))
        self.triangles.extend(Face(edgeT, [holeT.reversed()]).triangulate())
        self.triangles.extend(Face(edgeG.reversed(), [holeG]).triangulate())

        return edgeG[0], edgeT[0], edgeG[-1], edgeT[-1]


class FloorBracket:
    """Bracket between lip and floor, snapped to the yz plane."""

    def __init__(self, a, b, c, d, e, side):
        #   _____
        #  /     \
        # e_d     \
        #   | ( )  \
        #   c       \     z
        #     a------->b  xy

        a = a.yz
        b = b.yz
        c = c.yz
        d = d.yz
        e = e.yz

        self.taperEdge = Edge()
        self.splitEdge = Edge()
        self.splitHole = Edge()
        self.triangles = []

        nutAcross = cfg.bracket.nutAcrossFlats
        nutRadius = nutAcross / 3**0.5
        boreRadius = cfg.bracket.counterboreDiameter/2
        boreLength = cfg.bracket.counterboreLength
        holeLength = cfg.bracket.holeLength
        cornerRadius = cfg.bracket.cornerRadius
        taperAngle = cfg.bracket.taperAngle
        taperMargin = cfg.bracket.taperMargin
        wallMargin = cfg.bracket.wallMargin
        baseMargin = cfg.bracket.baseMargin
        apexMargin = cfg.bracket.apexMargin
        extraMargin = cfg.bracket.frontFloorExtraMargin

        # Always construct from front to back

        isBackward = a.y > b.y

        if isBackward:
            a = a.mirroredY()
            b = b.mirroredY()
            c = c.mirroredY()
            d = d.mirroredY()
            e = e.mirroredY()
            extraMargin = 0

        # Sketch on yz plane

        taperDir = Vector(0, math.sin(taperAngle), math.cos(taperAngle))
        taperOrtho = Vector(0, -taperDir.z, taperDir.y)
        nutTaperDist = _hexTangentDist(nutRadius, taperAngle - math.pi/2)

        wallOffset = max(boreRadius, nutRadius) + wallMargin + extraMargin
        baseOffset = max(boreRadius, nutAcross/2) + baseMargin
        apexOffset = max(boreRadius, nutAcross/2) + apexMargin
        taperOffset = max(boreRadius, nutTaperDist) + taperMargin

        lipT = d.z
        bracketG = a.z
        bracketT = bracketG + max(baseOffset + apexOffset, lipT)
        centerZ = bracketG + baseOffset

        lineF = Line(Vector(0, 0, centerZ) + taperOrtho*taperOffset, taperDir)
        lineB = Line(lineF.pos.mirroredY(), lineF.dir.mirroredY())
        lineG = Line(Vector(0, 0, bracketG), Vector(0, 1))
        lineT = Line(Vector(0, 0, bracketT), Vector(0, 1))
        lineLip = Line(Vector(0, 0, lipT), Vector(0, 1))

        archLFG = lineF.intersect(lineLip)
        archLFT = lineF.intersect(lineT)
        archLBT = lineB.intersect(lineT)
        archLBG = lineB.intersect(lineG)

        if bracketT <= lipT:
            raise ValueError("The floor bracket must be taller than the floor lip.")

        cornerRadiusF = min(cornerRadius, bracketT - lipT)
        cornerF = _archCorner(cornerRadiusF, archLBT, archLFT, archLFG)
        cornerB = _archCorner(cornerRadius, archLBG, archLBT, archLFT)
        archL = Edge(archLBG, cornerB, cornerF, archLFG).collapsed()

        # Center position

        centerY = e.y - archL[-1].y

        if centerY - d.y < wallOffset:
            # Avoid e.y < archL[-1].y < d.y
            centerY = max(d.y + wallOffset, centerY + d.y - e.y)

        screwCenter = Vector(0, centerY, centerZ)

        # Edges and triangles

        moveR = Vector(boreLength + holeLength)
        archL = archL.translated(screwCenter.xy)
        archR = archL.translated(moveR)

        faceEdge = Edge(archL, d, c, a).translated(moveR)
        holeTriangles, holeL, holeR = _screwHole(screwCenter, side, True)

        if not archL[-1].isClose(e):
            archL.add(e)
            archR.add(d + moveR, e + moveR)

        self.splitEdge = archL.reversed()
        self.splitHole = holeL.reversed()
        self.taperEdge = Edge(archL[0], archR[0])
        self.lipEdge = Edge(e, d, c, a).translated(moveR)

        self.triangles.extend(archL.meshPairwise(archR))
        self.triangles.extend(Face(faceEdge.collapsed(), [holeR]).triangulate())
        self.triangles.extend(holeTriangles)

        if isBackward:
            self.lipEdge = self.lipEdge.mirroredY()
            self.taperEdge = self.taperEdge.mirroredY().reversed()
            self.splitEdge = self.splitEdge.mirroredY().reversed()
            self.splitHole = self.splitHole.mirroredY().reversed()
            self.triangles = [t.mirroredY().reversed() for t in self.triangles]


def _hexTangentDist(outerRadius, tangentAngle):
    """Return the distance of an angled tangent to the hexagon center."""
    #     .'
    #   .'__ )angle
    # .'/   \
    #   \___/
    return outerRadius * math.cos(abs(tangentAngle) % (math.pi/3) - math.pi/6)


def _archCorner(radius, a, b, c):
    return Edge(Vector(0, p.x, p.y) for p in cornerArc2D(
        radius, Vector(a.y, a.z), Vector(b.y, b.z), Vector(c.y, c.z)))


def _screwHole(centerL, side, isUpright):
    boreRadius = cfg.bracket.counterboreDiameter/2
    boreLength = cfg.bracket.counterboreLength
    holeRadius = cfg.bracket.holeDiameter/2
    holeLength = cfg.bracket.holeLength

    #    +---
    #    | Counterbore
    # ---+
    # Hole
    # ---+
    #    |     z
    #    +---  yx

    holeXY = uprightHole2D(holeRadius) if isUpright else arc2D(holeRadius)
    holeYZ = Edge(Vector(0, -p.x, p.y) for p in holeXY)

    centerR = centerL + Vector(holeLength)
    holeL = holeYZ.translated(centerL)
    holeR = holeYZ.translated(centerR)

    if side == cfg.bracket.nutSide:
        nutAcross = cfg.bracket.nutAcrossFlats
        nutRadius = nutAcross / 3**0.5
        boreXY = Edge(
            Vector(-nutRadius/2, nutAcross/2),
            Vector(-nutRadius),
            Vector(-nutRadius/2, -nutAcross/2),
            Vector(nutRadius/2, -nutAcross/2),
            Vector(nutRadius),
            Vector(nutRadius/2, nutAcross/2))
    else:
        boreXY = uprightHole2D(boreRadius) if isUpright else arc2D(boreRadius)

    boreL = Edge(Vector(0, -p.x, p.y) + centerR for p in boreXY)
    boreR = boreL.translated(Vector(boreLength))

    triangles = Face(boreL.reversed(), [holeR]).triangulate()
    triangles.extend(boreL.meshPairwise(boreR, True))
    triangles.extend(holeL.meshPairwise(holeR, True))

    return triangles, holeL, boreR
