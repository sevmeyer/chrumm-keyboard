import logging
import math

from chrumm import cfg

from chrumm.geo import Circle
from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Vector

from .arc import arc2D


log = logging.getLogger(__name__)


class Knob:

    def __init__(self):
        self.triangles = []

        outerRadius = cfg.knob.outerDiameter/2
        outerChamfer = cfg.knob.outerChamfer
        roofThickness = cfg.knob.roofThickness
        shaftHeight = cfg.knob.shaftHeight
        skirtThickness = cfg.knob.skirtThickness
        skirtHeight = cfg.knob.skirtHeight

        # Upside down construction
        #
        # skirtEdgeG        _  grooveEdgeG
        #            |     | |
        # skirtEdgeT |_   _| |
        # shaftEdgeG   | |   |
        # shaftEdgeT   |_|   | grooveEdgeT
        #             ______/  chamferEdge

        radiusT = outerRadius - outerChamfer
        centerG = Vector(0, 0, skirtHeight + shaftHeight + roofThickness)
        shaftG = Vector(0, 0, roofThickness + shaftHeight)
        shaftT = Vector(0, 0, roofThickness)

        grooveSketch = Knob._grooveSketch2D()
        grooveEdgeG = grooveSketch.translated(centerG)
        grooveEdgeT = Edge(Vector(p.x, p.y, p.magnitude() - radiusT) for p in grooveSketch)
        chamferEdge = Edge(p.normalized()*radiusT for p in grooveSketch)

        shaftSketch = Knob._shaftSketch2D()
        shaftEdgeG = shaftSketch.translated(shaftG)
        shaftEdgeT = shaftSketch.translated(shaftT)

        skirtSketch = arc2D(outerRadius - skirtThickness, 0, math.tau)
        skirtEdgeG = skirtSketch.translated(centerG)
        skirtEdgeT = skirtSketch.translated(shaftG)

        self.triangles.extend(Edge(Vector()).meshPairwise(chamferEdge, True))
        self.triangles.extend(chamferEdge.meshPairwise(grooveEdgeT, True))
        self.triangles.extend(grooveEdgeT.meshPairwise(grooveEdgeG, True))

        self.triangles.extend(skirtEdgeG.meshPairwise(skirtEdgeT, True))
        self.triangles.extend(shaftEdgeG.meshPairwise(shaftEdgeT, True))

        self.triangles.extend(Face(shaftEdgeT).triangulate())
        self.triangles.extend(Face(skirtEdgeT, [shaftEdgeG.reversed()]).triangulate())
        self.triangles.extend(Face(grooveEdgeG, [skirtEdgeG.reversed()]).triangulate())

    @staticmethod
    def _grooveSketch2D():
        outerRadius = cfg.knob.outerDiameter/2
        outerChamfer = cfg.knob.outerChamfer
        grooveCount = cfg.knob.grooveCount
        grooveRadius = cfg.knob.grooveDiameter/2
        grooveInset = cfg.knob.grooveInset
        cornerRadius = cfg.knob.grooveCornerRadius

        if grooveCount <= 0:
            return arc2D(outerRadius, 0, math.tau)

        # Check if inset causes overlapping geometry

        tangentHypot = (outerRadius**2 + grooveRadius**2)**0.5
        tangentInset = grooveRadius - (tangentHypot - outerRadius)

        if grooveInset >= tangentInset:
            raise ValueError("knob.grooveInset is too big in relation to knob.grooveDiameter.")

        if grooveInset >= outerChamfer:
            raise ValueError("knob.grooveInset must be less than knob.outerChamfer.")

        # Construct right half of backmost groove segment
        #
        #       corner
        #        .--.
        #      /|    |\ outer
        # __.-'  '--'  \
        # groove        . start

        grooveCenter = Vector(0, outerRadius + grooveRadius - grooveInset)
        shrunkOuterCircle = Circle(Vector(), outerRadius - cornerRadius)
        grownGrooveCircle = Circle(grooveCenter, grooveRadius + cornerRadius)
        cornerCenter = shrunkOuterCircle.intersect2D(grownGrooveCircle)[1]

        segmentSpan = math.tau / grooveCount
        cornerStart = cornerCenter.angle2D()
        grooveStart = (cornerCenter - grooveCenter).angle2D()
        outerStart = math.tau/4 - segmentSpan/2
        outerSpan = -(outerStart - cornerStart)
        grooveSpan = -(math.tau/4 + grooveStart)
        cornerSpan = (grooveCenter - cornerCenter).angle2D() - cornerStart

        segment = Edge(
            arc2D(outerRadius, outerStart, outerSpan),
            arc2D(cornerRadius, cornerStart, cornerSpan, cornerCenter),
            arc2D(grooveRadius, grooveStart, grooveSpan, grooveCenter))

        # Mirror left segment half and repeat around circle

        segment.add(segment.mirroredX().reversed())
        edge = Edge(segment)

        for i in range(1, grooveCount):
            rotation = Matrix().rotatedZ(segmentSpan*i)
            edge.add(segment.transformed(rotation))

        return edge.collapsed()

    @staticmethod
    def _shaftSketch2D():
        shaftAcrossFlat = cfg.knob.shaftAcrossFlat
        shaftRadius = cfg.knob.shaftDiameter/2
        prongRadius = cfg.knob.prongDiameter/2
        prongAngle = math.radians(15)
        relProngPitch = 1/3
        relNotchSize = 2/3

        # Construct right half
        #
        #  -. notch
        #    )
        #   (_.-''. hinge
        # prong   |
        #        /
        #  ___.-' shaft

        # Prong and notch center

        flatY = shaftAcrossFlat - shaftRadius
        flatX = (shaftRadius**2 - flatY**2)**0.5
        flatVertex = Vector(flatX, flatY)

        prongX = flatX * relProngPitch
        prongY = flatY + prongRadius
        prongCenter = Vector(prongX, prongY)

        notchRadius = prongX - prongRadius*(1 - relNotchSize)
        notchOffset = ((prongRadius + notchRadius)**2 - prongX**2)**0.5
        notchCenter = Vector(0, prongY + notchOffset)

        # Rounded hinge

        flatDiagonal = Line(Vector(), flatVertex)
        shaftTangent = Line(flatVertex, flatDiagonal.dir.ortho2D())

        prongDir = Vector(math.cos(prongAngle), math.sin(prongAngle))
        prongTouch = prongCenter - prongDir.ortho2D()*prongRadius
        prongTangent = Line(prongTouch, prongDir)

        bisectPos = shaftTangent.intersect(prongTangent)
        bisectDir = shaftTangent.dir + prongTangent.dir
        hingeBisect = Line(bisectPos, bisectDir)
        hingeCenter = flatDiagonal.intersect(hingeBisect)
        hingeRadius = (hingeCenter - flatVertex).magnitude2D()

        # Arc angles

        notchStart = (prongCenter - notchCenter).angle2D()
        notchSpan = math.pi/2 - notchStart
        prongStart = math.pi/2*3 + prongAngle
        prongSpan = math.pi + notchStart - prongStart
        hingeStart = hingeCenter.angle2D()
        hingeSpan = math.pi/2 + prongAngle - hingeStart
        shaftStart = math.pi/2*3
        shaftSpan = math.pi/2 + hingeStart

        half = Edge(
            arc2D(shaftRadius, shaftStart, shaftSpan),
            arc2D(hingeRadius, hingeStart, hingeSpan, hingeCenter),
            arc2D(prongRadius, prongStart, prongSpan, prongCenter),
            arc2D(notchRadius, notchStart, notchSpan, notchCenter))

        return (half + half.mirroredX().reversed()).collapsed()
