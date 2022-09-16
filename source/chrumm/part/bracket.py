import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Vector

from .arc import arc2D


class CornerBracket:
    """Bracket between wall and roof, snapped to the yz plane."""

    def __init__(self, a, b, c, side, withScrewHole=True, withZiptieHole=False):
        #   a------->b
        # c   @  / z
        # |_____/  xy

        a = a.yz
        b = b.yz
        c = c.yz

        self.wallEdge = Edge()
        self.roofEdge = Edge()
        self.splitEdge = Edge()
        self.splitHoles = []
        self.triangles = []

        boreRadius = cfg.bracket.counterboreDiameter/2
        nutAcross = cfg.bracket.nutAcrossFlats
        boreLength = cfg.bracket.counterboreLength
        holeLength = cfg.bracket.holeLength
        bridgeThickness = cfg.bracket.bridgeThickness
        taperAngle = cfg.bracket.taperAngle
        taperMargin = cfg.bracket.taperMargin
        wallMargin = cfg.bracket.wallMargin
        roofMargin = cfg.bracket.roofMargin

        # Sketch on yz plane
        #
        #    a----------->b roofDir
        #  roof ^      ^
        # Ortho |     / taperDir
        #       +--->/
        #    taper  /
        #    Ortho

        sign = 1 if a.y < b.y else -1
        wallDir = Vector(0, 0, 1)
        wallOrtho = Vector(0, -sign, 0)
        roofDir = (b - a).normalized()
        roofOrtho = Vector(0, -sign*roofDir.z, sign*roofDir.y)
        taperDir = Vector(0, sign*math.sin(taperAngle), math.cos(taperAngle))
        taperOrtho = Vector(0, sign*taperDir.z, -sign*taperDir.y)

        maxRadius = max(boreRadius, nutAcross/2)
        bridgeOffset = maxRadius + bridgeThickness
        roofOffset = maxRadius + roofMargin
        wallOffset = maxRadius + wallMargin
        wallOffsetLine = Line(c - wallOrtho*wallOffset, wallDir)
        roofOffsetLine = Line(a - roofOrtho*roofOffset, roofDir)
        center = roofOffsetLine.intersect(wallOffsetLine)
        width = holeLength + boreLength

        wallLine = Line(c, wallDir)
        roofLine = Line(a, roofDir)
        taperLine = Line(center + taperOrtho*(maxRadius + taperMargin), taperDir)
        bridgeLine = Line(center - Vector(0, 0, bridgeOffset), Vector(0, 1))

        # Edges and triangles

        holesR = []

        if withZiptieHole and cfg.bracket.ziptieHole:
            zipWidth = cfg.bracket.ziptieHole.width
            zipHeight = cfg.bracket.ziptieHole.height
            zipMargin = cfg.bracket.ziptieHole.margin

            zipB = center.y + sign*(maxRadius + zipMargin + zipWidth)
            zipG = center.z - bridgeOffset + zipMargin

            taperLine = Line(Vector(0, zipB, zipG) + taperOrtho*zipMargin, taperDir)
            zipCenter = Vector(0, zipB - sign*zipWidth/2, zipG + zipHeight/2)

            zipTriangles, zipL, zipR = _ziptieHole(zipCenter)
            self.triangles.extend(zipTriangles)
            holesR.append(zipR.reversed())
            self.splitHoles.append(zipL)

        archL = Edge(
            wallLine.intersect(bridgeLine),
            taperLine.intersect(bridgeLine),
            taperLine.intersect(roofLine))

        if sign == 1:
            archL.reverse()
            archR = archL.translated(Vector(width))
            edgeR = archR + Edge(c, a).translated(Vector(width))
            self.wallEdge = Edge(archL[-1], archR[-1], edgeR[-2])
            self.roofEdge = Edge(edgeR[-1], archR[0], archL[0])
        else:
            archR = archL.translated(Vector(width))
            edgeR = archR + Edge(a, c).translated(Vector(width))
            self.wallEdge = Edge(archL[0], archR[0], edgeR[-1])
            self.roofEdge = Edge(edgeR[-2], archR[-1], archL[-1])

        holeTriangles, holeL, boreR = _screwHole(center, side)

        if withScrewHole:
            holesR.append(boreR)
            self.triangles.extend(holeTriangles)
            self.splitHoles.append(holeL.reversed())

        faceR = Face(edgeR.reversed().collapsed(), holesR)
        self.triangles.extend(archR.meshPairwise(archL))
        self.triangles.extend(faceR.triangulate())
        self.splitEdge = archL


class FlatBracket:
    """Standalone bracket on the floor or roof, snapped to the yz plane."""

    def __init__(self, a, b, relPos, side, withScrewHole=True, withZiptieHole=False):
        # a--------->b
        #   \  @  / z
        #    \___/  xy

        a = a.yz
        b = b.yz

        self.baseEdge = Edge()
        self.splitEdge = Edge()
        self.splitHoles = []
        self.triangles = []

        boreRadius = cfg.bracket.counterboreDiameter/2
        nutAcross = cfg.bracket.nutAcrossFlats
        boreLength = cfg.bracket.counterboreLength
        holeLength = cfg.bracket.holeLength
        bridgeThickness = cfg.bracket.bridgeThickness
        taperAngle = cfg.bracket.taperAngle
        taperMargin = cfg.bracket.taperMargin
        roofMargin = cfg.bracket.roofMargin
        floorMargin = cfg.bracket.floorMargin

        sign = 1 if a.y < b.y else -1
        maxRadius = max(boreRadius, nutAcross/2)

        # Sketch on yz plane

        abDir = (b - a).normalized()
        abOrtho = Vector(0, -abDir.z, abDir.y)
        taperDir = Vector(0, math.sin(taperAngle), sign*math.cos(taperAngle))
        taperOrtho = Vector(0, sign*taperDir.z, -sign*taperDir.y)

        lineB = Line(taperOrtho*(maxRadius + taperMargin), taperDir)
        lineF = Line(lineB.pos.mirroredY(), lineB.dir.mirroredY())

        if sign == 1:
            lineT = Line(abOrtho*(maxRadius + roofMargin), abDir)
            lineG = Line(Vector(0, 0, -maxRadius - bridgeThickness), Vector(0, 1))

            if withZiptieHole and cfg.bracket.ziptieHole:
                zipWidth = cfg.bracket.ziptieHole.width
                zipHeight = cfg.bracket.ziptieHole.height
                zipMargin = cfg.bracket.ziptieHole.margin

                zipB = 0 + sign*(maxRadius + zipMargin + zipWidth)
                zipG = 0 - (maxRadius + roofMargin) + zipMargin

                zipDelta = Vector(0, zipB - sign*zipWidth/2, zipG + zipHeight/2)
                lineB = Line(Vector(0, zipB, zipG) + taperOrtho*zipMargin, taperDir)
        else:
            lineT = Line(abOrtho*(maxRadius + floorMargin), abDir)
            lineG = Line(Vector(0, 0, maxRadius + bridgeThickness), Vector(0, 1))

        # Relative center

        holesR = []
        archL = Edge(
            lineT.intersect(lineB),
            lineG.intersect(lineB),
            lineG.intersect(lineF),
            lineT.intersect(lineF))

        abDist = (b - a).magnitude()
        archDist = (archL[-1] - archL[0]).magnitude()
        relDist = (abDist - archDist)*relPos

        if sign == 1:
            center = a + abDir*relDist - archL[-1]

            if withZiptieHole and cfg.bracket.ziptieHole:
                zipTriangles, zipL, zipR = _ziptieHole(center + zipDelta)
                self.triangles.extend(zipTriangles)
                self.splitHoles.append(zipL)
                holesR.append(zipR.reversed())
        else:
            center = a + abDir*relDist - archL[0]

        # Edges and triangles

        archL = archL.translated(center)
        archR = archL.translated(Vector(boreLength + holeLength))
        holeTriangles, holeL, boreR = _screwHole(center, side)

        self.baseEdge = Edge(archL[0], archR[0], archR[-1], archL[-1])
        self.splitEdge = Edge(archL)

        if withScrewHole:
            holesR.append(boreR)
            self.splitHoles.append(holeL.reversed())
            self.triangles.extend(holeTriangles)

        if sign == 1:
            self.baseEdge.reverse()
            self.triangles.extend(archR.meshPairwise(archL))
            self.triangles.extend(Face(archR.reversed(), holesR).triangulate())
        else:
            self.splitEdge.reverse()
            self.triangles.extend(archL.meshPairwise(archR))
            self.triangles.extend(Face(archR, [boreR]).triangulate())


def _screwHole(centerL, side):
    boreLength = cfg.bracket.counterboreLength
    holeLength = cfg.bracket.holeLength
    holeRadius = cfg.bracket.holeDiameter/2

    # Hole shape intended for FFF 3D printing
    #   ____  <- Clean bridge at top
    #  /    \  <- 45 degree tangent
    # :      :  <- Regular lower circle
    # :      : z
    #  '-..-'  xy

    arcXY = arc2D(holeRadius, math.radians(135), math.radians(270))
    arcYZ = Edge(Vector(0, -p.x, p.y) for p in arcXY)
    bridgeB = Vector(0, arcYZ[0].y - (holeRadius - arcYZ[0].z), holeRadius)
    bridgeF = Vector(0, -bridgeB.y, bridgeB.z)
    holeYZ = Edge(bridgeB, arcYZ, bridgeF)

    # Side profile
    #    +---
    #    | Counterbore
    # ---+
    # Hole
    # ---+
    #    |    z
    #    +--- yx

    centerR = centerL + Vector(holeLength)
    holeL = holeYZ.translated(centerL)
    holeR = holeYZ.translated(centerR)

    if side == cfg.bracket.nutSide:
        nutAcross = cfg.bracket.nutAcrossFlats
        nutRadius = nutAcross / 3**0.5
        hexagonYZ = Edge(
            Vector(0, nutRadius/2, nutAcross/2),
            Vector(0, nutRadius),
            Vector(0, nutRadius/2, -nutAcross/2),
            Vector(0, -nutRadius/2, -nutAcross/2),
            Vector(0, -nutRadius),
            Vector(0, -nutRadius/2, nutAcross/2))
        boreL = hexagonYZ.translated(centerR)
        triangles = Face(boreL.reversed(), [holeR]).triangulate()
    else:
        boreRadius = cfg.bracket.counterboreDiameter/2
        boreScale = boreRadius / holeRadius
        boreL = Edge(p*boreScale + centerR for p in holeYZ)
        triangles = holeR.meshPairwise(boreL, True)

    boreR = boreL.translated(Vector(boreLength))
    triangles.extend(boreL.meshPairwise(boreR, True))
    triangles.extend(holeL.meshPairwise(holeR, True))

    return triangles, holeL, boreR


def _ziptieHole(centerL):
    width = cfg.bracket.ziptieHole.width
    length = cfg.bracket.counterboreLength + cfg.bracket.holeLength
    height = cfg.bracket.ziptieHole.height
    humpHeight = cfg.bracket.ziptieHole.humpHeight

    # Rounded hole sides
    #  .----
    # : \45deg  z
    # : /45deg  xy
    #  '----

    sideRadius = height / (2*math.sin(math.tau/8))
    sideArcXY = arc2D(sideRadius, -math.tau/8, math.tau/4)
    sideArcYZ = Edge(Vector(0, p.x + width/2 - sideRadius, p.y) for p in sideArcXY)
    holeShape = Edge(sideArcYZ, sideArcYZ.mirroredY().reversed())

    # Inner hump to distribute stress accross layers
    # |::::::|::::::|
    # |::''     ''::|
    # |' ..::|::.. '|
    #  .:::::|:::::.  z
    # |::::::|::::::| yx

    humpArc = arc2D(length, math.tau/16*3, math.tau/16)
    humpScaleX = length / humpArc[0].x
    humpScaleZ = humpHeight / (humpArc[-1].y - humpArc[0].y)

    edges = []
    for p in humpArc:
        x = humpScaleX * p.x
        z = humpScaleZ * (p.y - humpArc[0].y)
        edges.append(holeShape.translated(centerL + Vector(x, 0, z)))

    triangles = []
    for i in range(len(edges) - 1):
        triangles.extend(edges[i].meshPairwise(edges[i+1], True))

    return triangles, edges[-1], edges[0]
