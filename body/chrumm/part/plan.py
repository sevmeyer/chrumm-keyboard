import logging
import math
import types

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Plane
from chrumm.geo import Vector

from .boss import Boss
from .layout import Layout


log = logging.getLogger(__name__)


# Orientation
#
#        .---------.
#        |\ HEIGHT  \
#        | \top      \
# DEPTH  | +z --------.
#  back +y  |         |
#         \ |         |
#          \|left     |right
#     front O------- +x WIDTH
#           ground
#
# I'm using the name "ground" instead of "bottom",
# so that each location starts with a unique letter.
# This allows for distinct abbreviations in code.


class Plan:
    """Determine the arrangement of keys, bosses, and reference points.

    The geometry is always constructed on the right side, regardless of the
    side argument. Otherwise, each part would need to be implemented twice.
    The triangles of the left side are mirrored after construction.
    """

    def __init__(self, side):
        self.side = side
        self.points = types.SimpleNamespace()
        self.planes = types.SimpleNamespace()
        self.bosses = types.SimpleNamespace()
        self.layout = Layout()

        # Shorthand
        points = self.points
        planes = self.planes

        splitAngle = cfg.body.splitAngle
        tiltAngle = cfg.body.tiltAngle
        alnumTentAngle = cfg.body.alnumTentAngle
        thumbTentAngle = cfg.body.thumbTentAngle
        pinkyTentAngle = cfg.body.pinkyTentAngle
        alnumBackAngle = cfg.body.alnumBackAngle
        alnumFrontAngle = cfg.body.alnumFrontAngle
        thumbFrontAngle = cfg.body.thumbFrontAngle
        minRoofHeight = cfg.body.minRoofHeight
        minRidgeWidth = cfg.body.minRidgeWidth
        relRidgeTaper = cfg.body.relRidgeTaper
        wallThickness = cfg.body.wallThickness
        roofThickness = cfg.body.roofThickness
        alnumFrontThickness = cfg.body.alnumFrontThickness

        if thumbTentAngle >= alnumTentAngle:
            raise ValueError("body.thumbTentAngle must be less than body.alnumTentAngle")

        # Tent pivot

        creaseOffset = Plan._tentCreaseOffset()

        for key in self.layout.alnum() + self.layout.thumb():
            key.translate(creaseOffset)

        alnumMax = self.layout.maxAlnum().position
        pinkyMin = self.layout.minPinky().position
        pivotPos = (alnumMax + pinkyMin) / 2

        # Alnum tent

        alnumPivotAngle = pinkyTentAngle + (alnumTentAngle - pinkyTentAngle)/2
        alnumPivotMatrix = Matrix().rotatedY(alnumPivotAngle, pivotPos)
        alnumTentMatrix = Matrix().rotatedY(alnumTentAngle, pivotPos)

        planes.alnumIT = Plane.fromZ(-roofThickness).transformed(alnumTentMatrix)
        planes.alnumOT = Plane.fromZ(0).transformed(alnumTentMatrix)
        planes.pivotIB = Plane.fromX(pivotPos.x).transformed(alnumPivotMatrix)
        planes.pivotOB = Plane.fromX(pivotPos.x).transformed(alnumPivotMatrix)

        for key in self.layout.alnum():
            key.transform(alnumTentMatrix)

        # Thumb tent

        thumbPivotAngle = pinkyTentAngle + (thumbTentAngle - pinkyTentAngle)/2
        thumbPivotMatrix = Matrix().rotatedY(thumbPivotAngle, pivotPos)
        thumbTentMatrix = Matrix().rotatedY(thumbTentAngle, pivotPos)

        planes.thumbIT = Plane.fromZ(-roofThickness).transformed(thumbTentMatrix)
        planes.thumbOT = Plane.fromZ(0).transformed(thumbTentMatrix)
        planes.pivotIF = Plane.fromX(pivotPos.x).transformed(thumbPivotMatrix)
        planes.pivotOF = Plane.fromX(pivotPos.x).transformed(thumbPivotMatrix)

        for key in self.layout.thumb():
            key.transform(thumbTentMatrix)

        # Pinky tent

        pinkyTentMatrix = Matrix().rotatedY(pinkyTentAngle, pivotPos)

        planes.pinkyIT = Plane.fromZ(-roofThickness).transformed(pinkyTentMatrix)
        planes.pinkyOT = Plane.fromZ(0).transformed(pinkyTentMatrix)

        for key in self.layout.pinky():
            key.transform(pinkyTentMatrix)

        # Alnum walls

        alnumMinX = min(p.x for key in self.layout.alnum() for p in key.bounds)
        planes.alnumIL = Plane.fromX(alnumMinX)
        planes.alnumOL = Plane.fromX(alnumMinX)

        alnumLinesF = Plan._wallLines2D(self.layout.alnum(), alnumFrontThickness, alnumFrontAngle)
        planes.alnumIF = Plane.fromLine2D(alnumLinesF[0])
        planes.alnumOF = Plane.fromLine2D(alnumLinesF[1])

        # Move thumb cluster against alnum wall

        thumbBounds = [p for key in self.layout.thumb() for p in key.boundsO]
        alnumSlope = alnumLinesF[1].dir.y / alnumLinesF[1].dir.x
        alnumIntercept = alnumLinesF[1].pos.y - alnumLinesF[1].pos.x*alnumSlope
        thumbIntercept = max(p.y - p.x*alnumSlope for p in thumbBounds)
        thumbDelta = Vector(0, alnumIntercept - thumbIntercept)

        if thumbDelta.y < 0:
            log.debug("The %s thumb cluster is moved forward by: %.3f", side, -thumbDelta.y)
            for key in self.layout.thumb():
                key.translate(thumbDelta)

        # Pinky walls

        pinkyLinesR = Plan._wallLines2D(self.layout.pinky(side), wallThickness, math.tau/4)
        planes.pinkyIR = Plane.fromLine2D(pinkyLinesR[0])
        planes.pinkyOR = Plane.fromLine2D(pinkyLinesR[1])

        # Tilt and split

        tiltSplitMatrix = Matrix().rotatedX(tiltAngle).rotatedZ(splitAngle)

        for key in self.layout.all():
            key.transform(tiltSplitMatrix)
        for attr in planes.__dict__:
            setattr(planes, attr, getattr(planes, attr).transformed(tiltSplitMatrix))

        # Vertical walls

        wallAngleB = alnumBackAngle + splitAngle + math.pi
        wallAngleF = thumbFrontAngle + splitAngle

        alnumLinesB = Plan._wallLines2D(self.layout.all(), wallThickness, wallAngleB)
        thumbLinesF = Plan._wallLines2D(self.layout.all(), wallThickness, wallAngleF)

        # Screw boss positions

        def fitBosses(side):
            pinkyKeysB = self.layout.perPinkyCol(0, side)
            pinkyKeysF = self.layout.perPinkyCol(-1, side)
            thumbKeysF = self.layout.thumb(side)
            alnumKeysB = Plan._alnumBossKeys(
                self.layout.perAlnumCol(0, side),
                Plane.fromX(0),
                planes.pivotOF,
                Plane.fromLine2D(alnumLinesB[1]),
                planes.alnumOT)

            # Some boss placements are repeated to account for moved walls.
            bossAlnumB = Plan._fitBoss2D(alnumLinesB, alnumKeysB[0], alnumKeysB[1])
            bossPinkyB = Plan._fitBoss2D(alnumLinesB, pinkyKeysB[-1], pinkyKeysB[-2])
            bossAlnumB = Plan._fitBoss2D(alnumLinesB, alnumKeysB[0], alnumKeysB[1])

            bossThumbF = Plan._fitBoss2D(thumbLinesF, thumbKeysF[0], thumbKeysF[1])
            bossPinkyF = Plan._fitBoss2D(thumbLinesF, pinkyKeysF[-1], pinkyKeysF[-2])
            bossThumbF = Plan._fitBoss2D(thumbLinesF, thumbKeysF[0], thumbKeysF[1])

            return bossAlnumB, bossPinkyB, bossPinkyF, bossThumbF

        # The walls must remain symmetric in order to match in the middle.
        # Because the walls are influenced by the bosses, and the bosses are
        # influenced by the layout, all bosses must be placed for either side.
        fitBosses("right" if side == "left" else "left")  # Discard opposite
        bossAlnumB, bossPinkyB, bossPinkyF, bossThumbF = fitBosses(side)

        planes.alnumIB = Plane.fromLine2D(alnumLinesB[0])
        planes.alnumOB = Plane.fromLine2D(alnumLinesB[1])
        planes.pinkyIF = Plane.fromLine2D(thumbLinesF[0])
        planes.pinkyOF = Plane.fromLine2D(thumbLinesF[1])

        # Final x position

        alnumILB = planes.alnumIL.intersect(planes.alnumIB, planes.alnumIT)
        alnumOLB = planes.alnumOL.intersect(planes.alnumOB, planes.alnumOT)

        boundsDeltaX = -min(p.x for key in self.layout.all() for p in key.bounds)
        splitDeltaX = -min(alnumOLB.x, alnumILB.x) + minRidgeWidth/2
        delta = Vector(max(boundsDeltaX, splitDeltaX))

        for key in self.layout.all():
            key.translate(delta)
        for attr in planes.__dict__:
            setattr(planes, attr, getattr(planes, attr).translated(delta))

        alnumLinesB = [line.translated(delta) for line in alnumLinesB]
        thumbLinesF = [line.translated(delta) for line in thumbLinesF]
        bossAlnumB = bossAlnumB + delta
        bossPinkyB = bossPinkyB + delta
        bossThumbF = bossThumbF + delta
        bossPinkyF = bossPinkyF + delta

        # Thumb left front corner

        thumbBounds = [p for key in self.layout.thumb() for p in key.bounds]
        thumbDirL = Vector(0, 1).transformedNormal(self.layout.thumb("left")[0].matrix)
        thumbDirR = Vector(0, 1).transformedNormal(self.layout.thumb("right")[0].matrix)
        thumbLine = Line(Vector(), thumbDirL.xy + thumbDirR.xy)
        thumbOffset = min(thumbLine.distance2D(p) for p in thumbBounds)
        thumbLine = thumbLine.translated(thumbLine.dir.ortho2D()*-thumbOffset)
        thumbPlanePos = thumbLinesF[0].intersect(thumbLine)
        thumbPlaneNorm = thumbLinesF[0].dir + Vector(1, 0)

        planes.thumbIL = Plane(thumbPlanePos, thumbPlaneNorm)
        planes.thumbOL = Plane(thumbPlanePos, thumbPlaneNorm)

        # Ridge front slope

        thumbLB = planes.alnumOL.intersect(planes.alnumOF, planes.thumbOT).xy
        thumbLF = planes.thumbIL.intersect(planes.pinkyIF, planes.thumbIT).xy

        thumbOLB = planes.alnumOL.intersect(planes.alnumOF, planes.thumbOT)
        thumbILB = planes.alnumIL.intersect(planes.alnumIF, planes.thumbIT)

        slopeLB = Vector(0, thumbLB.y)
        slopeRF = Vector(thumbLB.x, thumbLF.y)
        slopeMid = slopeRF + (slopeLB - slopeRF)*relRidgeTaper

        sweepLine = Line(thumbLB, slopeMid - thumbLB)

        for point in thumbBounds:
            if sweepLine.distance2D(point) > 0:
                sweepLine = Line(sweepLine.pos, point.xy - sweepLine.pos)

        sweepIntersect = sweepLine.intersect(thumbLine)
        ridgeRF = planes.thumbOT.projectZ(min(sweepIntersect, slopeMid))

        points.ridgeIRF = ridgeRF + (thumbILB - thumbOLB)
        points.ridgeORF = ridgeRF

        if points.ridgeORF.x < 0 or points.ridgeIRF.x < 0:
            raise ValueError(
                "The tapered front of the ridge is overlapping itself.\n"
                "  Try to increase body.minRidgeWidth, body.splitAngle,\n"
                "  or decrease body.relRidgeTaper.")

        # Body reference points

        points.alnumILF = planes.alnumIL.intersect(planes.alnumIF, planes.alnumIT)
        points.alnumILB = planes.alnumIL.intersect(planes.alnumIB, planes.alnumIT)
        points.alnumIRF = planes.thumbIT.intersect(planes.alnumIF, planes.alnumIT)
        points.alnumIRB = planes.pivotIB.intersect(planes.alnumIB, planes.alnumIT)
        points.pinkyIRF = planes.pinkyIR.intersect(planes.pinkyIF, planes.pinkyIT)
        points.pinkyIRB = planes.pinkyIR.intersect(planes.alnumIB, planes.pinkyIT)
        points.thumbILF = planes.thumbIL.intersect(planes.pinkyIF, planes.thumbIT)
        points.thumbILB = planes.alnumIL.intersect(planes.alnumIF, planes.thumbIT)
        points.thumbIRF = planes.pivotIF.intersect(planes.pinkyIF, planes.thumbIT)

        points.alnumOLF = planes.alnumOL.intersect(planes.alnumOF, planes.alnumOT)
        points.alnumOLB = planes.alnumOL.intersect(planes.alnumOB, planes.alnumOT)
        points.alnumORF = planes.thumbOT.intersect(planes.alnumOF, planes.alnumOT)
        points.alnumORB = planes.pivotOB.intersect(planes.alnumOB, planes.alnumOT)
        points.pinkyORF = planes.pinkyOR.intersect(planes.pinkyOF, planes.pinkyOT)
        points.pinkyORB = planes.pinkyOR.intersect(planes.alnumOB, planes.pinkyOT)
        points.thumbOLF = planes.thumbOL.intersect(planes.pinkyOF, planes.thumbOT)
        points.thumbOLB = planes.alnumOL.intersect(planes.alnumOF, planes.thumbOT)
        points.thumbORF = planes.pivotOF.intersect(planes.pinkyOF, planes.thumbOT)

        # Final z position

        minKeyZ = min(key.position.z for key in self.layout.all())
        delta = Vector(0, 0, minRoofHeight - minKeyZ)

        for key in self.layout.all():
            key.translate(delta)
        for obj in planes, points:
            for attr in obj.__dict__:
                setattr(obj, attr, getattr(obj, attr).translated(delta))

        # Check z overlaps

        minBodyZ = min(p.z for p in points.__dict__.values())
        minPinZ = min(p.z for key in self.layout.all(side) for p in key.boundsI)

        lipGap = minBodyZ - cfg.floor.lipHeight - cfg.body.innerChamfer
        pinGap = minPinZ + cfg.floor.outerHeight - cfg.floor.innerHeight - cfg.switch.floorMargin

        if lipGap < 0:
            raise ValueError(f"The body overlaps the floor lip by: {-lipGap:.3f}")

        if pinGap < 0:
            raise ValueError(f"The switches overlap the floor by: {-pinGap:.3f}")

        log.debug("Gap between %s body and floor lip: %.3f", side, lipGap)
        log.debug("Gap between %s switches and floor: %.3f", side, pinGap)

        # Bosses

        self.bosses.alnumB = Boss(bossAlnumB, Vector(1), alnumLinesB[0].dir, planes.alnumOT)
        self.bosses.pinkyB = Boss(bossPinkyB, Vector(1), alnumLinesB[0].dir, planes.pinkyOT)
        self.bosses.pinkyF = Boss(bossPinkyF, Vector(1), thumbLinesF[0].dir, planes.pinkyOT)
        self.bosses.thumbF = Boss(bossThumbF, Vector(1), thumbLinesF[0].dir, planes.thumbOT)

        # Palm hitch

        if cfg.palm:
            hitchD = cfg.palm.hitchDepth
            hitchPitch = cfg.palm.hitchScrewPitch
            hitchMargin = cfg.palm.bodyMargin
            hitchTaperAngle = cfg.palm.taperAngle

            pinkyRFG = points.pinkyORF.xy
            thumbLFG = points.thumbOLF.xy

            wallDir = (thumbLFG - pinkyRFG).normalized()
            wallOrtho = wallDir.ortho2D()
            hitchDirL = wallOrtho.transformed(Matrix().rotatedZ(hitchTaperAngle))
            hitchDirR = -wallOrtho.transformed(Matrix().rotatedZ(-hitchTaperAngle))
            hitchOrthoL = hitchDirL.ortho2D()
            hitchOrthoR = hitchDirR.ortho2D()

            hitchB = (thumbLFG + pinkyRFG)/2
            hitchM = hitchB + wallOrtho*(hitchMargin + hitchD/2)
            hitchF = hitchB + wallOrtho*(hitchMargin + hitchD)

            hitchBossL = hitchM + wallDir*hitchPitch/2
            hitchBossR = hitchM - wallDir*hitchPitch/2

            hitchLineB = Line(hitchB, wallDir)
            hitchLineF = Line(hitchF, wallDir)
            hitchLineL = Line(hitchBossL - hitchOrthoL*hitchD/2, hitchDirL)
            hitchLineR = Line(hitchBossR - hitchOrthoR*hitchD/2, hitchDirR)

            points.hitchOLB = hitchLineB.intersect(hitchLineL)
            points.hitchORB = hitchLineB.intersect(hitchLineR)
            points.hitchOLF = hitchLineF.intersect(hitchLineL)
            points.hitchORF = hitchLineF.intersect(hitchLineR)

            self.bosses.hitchL = Boss(hitchBossL, hitchOrthoL)
            self.bosses.hitchR = Boss(hitchBossR, hitchOrthoL)

    @staticmethod
    def _tentCreaseOffset():
        """Additional width to retain the cap top pitch across the tent crease."""
        capHeight = cfg.layout.capTopToPlate
        halfPitch = cfg.layout.columnPitch/2
        halfAngle = (cfg.body.alnumTentAngle - cfg.body.pinkyTentAngle)/2

        pitchHypot = halfPitch / math.cos(halfAngle)
        heightOppo = capHeight / math.cos(halfAngle) * math.sin(halfAngle)

        return Vector(-2*(pitchHypot + heightOppo - halfPitch))

    @staticmethod
    def _wallLines2D(keys, thickness, angle):
        """Return inner and outer wall lines against the key bounds."""
        boundsI = [p.xy for key in keys for p in key.boundsI]
        boundsO = [p.xy for key in keys for p in key.boundsO]

        baseLine = Line(Vector(), Vector(math.cos(angle), math.sin(angle)))
        forward = baseLine.dir
        outward = -forward.ortho2D()

        maxBound = max(boundsI, key=lambda p: baseLine.distance2D(p))
        lineI = Line(maxBound, forward)
        lineO = lineI.translated(outward * thickness)
        overlap = max(lineO.distance2D(p) for p in boundsO)

        if overlap > 0:
            offset = outward*overlap
            lineI = lineI.translated(offset)
            lineO = lineO.translated(offset)

        return [lineI, lineO]

    @staticmethod
    def _alnumBossKeys(keys, planeL, planeR, planeB, planeT):
        """Return key pair closest to the middle of the alnum back plane."""
        pointL = planeL.intersect(planeB, planeT)
        pointR = planeR.intersect(planeB, planeT)
        middle = (pointL + pointR) / 2
        distances = []

        for i, key in enumerate(keys):
            line = Line(Vector(), Vector(0, 1)).transformed(key.matrix)
            intersect = planeB.intersect(line)
            distance = (middle - intersect).magSquared()
            distances.append((distance, i))

        distances.sort()
        return [keys[i] for d, i in distances[:2]]

    @staticmethod
    def _fitBoss2D(wallLines, key0, key1):
        """Find a reasonable boss position between key0 and key1.

        If the boss does not fit, move wallLines to make room.
        """
        # This is a simple brute-force approach. The result
        # is not mathematically perfect, but good enough.
        bossPlacingResolution = 0.5
        wallPlacingResolution = 0.25

        radius = cfg.boss.diameter/2
        margin = cfg.boss.outerWallMargin

        hull0 = Edge.fromConvexHull2D(key0.boundsI)
        hull1 = Edge.fromConvexHull2D(key1.boundsI)

        line0 = Line(Vector(), Vector(0, 1)).transformed(key0.matrix)
        line1 = Line(Vector(), Vector(0, 1)).transformed(key1.matrix)
        line0 = Line(line0.pos.xy, line0.dir.xy)
        line1 = Line(line1.pos.xy, line1.dir.xy)

        forward = wallLines[1].dir
        outward = -forward.ortho2D()

        bossDelta = -outward*(radius + margin)
        wallDelta = outward*wallPlacingResolution

        # Look for a valid boss position parallel to the wall.
        # If no positions is valid, move the wall outward and repeat.
        while True:
            bossLine = wallLines[1].translated(bossDelta)
            intersect0 = bossLine.intersect(line0)
            intersect1 = bossLine.intersect(line1)
            bossMiddle = (intersect0 + intersect1)/2

            # Oscillate around the middle to find a valid position
            for i in range(int(radius / bossPlacingResolution) + 1):
                for step in i, -i:
                    bossPos = bossMiddle + forward*(step*bossPlacingResolution)
                    dist0 = hull0.distance2D(bossPos)
                    dist1 = hull1.distance2D(bossPos)

                    if dist0 >= radius and dist1 >= radius:
                        return bossPos

            wallLines[0] = wallLines[0].translated(wallDelta)
            wallLines[1] = wallLines[1].translated(wallDelta)
