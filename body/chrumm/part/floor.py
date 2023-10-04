import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Segment
from chrumm.geo import Vector

from .arc import cornerArc2D
from .bracket import FloorBracket
from .bumper import Bumper


class Floor:

    def __init__(self, plan, body):
        self.faces = []
        self.triangles = []

        outerHeight = cfg.floor.outerHeight
        innerHeight = cfg.floor.innerHeight
        innerChamfer = cfg.floor.innerChamfer
        lipThickness = cfg.floor.lipThickness
        lipHeight = cfg.floor.lipHeight
        lipMargin = cfg.floor.lipMargin

        lipT = Vector(0, 0, lipHeight)
        floorOG = Vector(0, 0, -outerHeight)
        floorIG = Vector(0, 0, floorOG.z + innerHeight)
        chamferT = Vector(0, 0, floorIG.z + innerChamfer)

        lipSketchI = _naiveOffset2D(body.outlineI, -lipMargin - lipThickness)
        lipSketchO = _naiveOffset2D(body.outlineI, -lipMargin)
        chamferSketch = _naiveOffset2D(body.outlineI, -lipMargin - lipThickness - innerChamfer)

        # Wall profile edges
        #
        #   4-3
        #   | |
        #   | 2--1
        #   5    |
        #  /     |
        # 6      |
        #        0

        profile = [
            body.outlineO.translated(floorOG),
            body.outlineO,
            lipSketchO,
            lipSketchO.translated(lipT),
            lipSketchI.translated(lipT),
            lipSketchI.translated(chamferT),
            chamferSketch.translated(floorIG)]

        # Face edges

        floorEdge = profile[0].reversed()
        innerEdge = Edge()
        splitEdge = Edge()
        bodyEdge = Edge()
        lipEdge = Edge()

        floorHoles = []
        innerHoles = []
        splitHoles = []
        bodyHoles = []

        # Optional parts

        if cfg.bracket:
            bracketF = FloorBracket(
                profile[6][0],
                profile[6][-1],
                profile[5][0],
                profile[4][0],
                profile[3][0],
                plan.side)

            bracketB = FloorBracket(
                profile[6][-1],
                profile[6][0],
                profile[5][-1],
                profile[4][-1],
                profile[3][-1],
                plan.side)

            # Check if front brackets overlap

            sketchFG = Edge(Vector(p.y, p.z) for p in bracketF.splitEdge)
            sketchFT = Edge(Vector(p.y, p.z) for p in body.bracketF.splitEdge)

            for point in sketchFT:
                if sketchFG.contains2D(point):
                    raise ValueError(
                        "The front brackets overlap.\n"
                        "  Try to increase bracket.frontFloorExtraMargin, or\n"
                        "  raise the front with a more negative body.tiltAngle.")

            # Check if cable overlaps

            if cfg.cable:
                sketchBG = Edge(Vector(p.y, p.z) for p in bracketB.splitEdge)
                sketchBT = Edge(Vector(p.y, p.z) for p in body.bracketB.splitEdge)

                for point in _naiveOffset2D(sketchBT, -cfg.cable.diameter):
                    if sketchBG.contains2D(point):
                        raise ValueError(
                            "The cable overlaps the back floor brackets.\n"
                            "  Try to decrease cable.gripHumpHeight, or\n"
                            "  increase the body or floor height.")

            # Integrate brackets

            for i, edge in enumerate(profile[3:7]):
                profile[-(i+1)][0] = bracketF.lipEdge[-(i+1)]
                profile[-(i+1)][-1] = bracketB.lipEdge[-(i+1)]

            innerEdge.add(bracketB.taperEdge)
            innerEdge.add(bracketF.taperEdge)
            splitEdge.add(e[0] for e in profile[:3])
            splitEdge.add(bracketF.splitEdge)
            splitEdge.add(bracketB.splitEdge)
            splitEdge.add(e[-1] for e in reversed(profile[:3]))
            splitHoles.append(bracketF.splitHole)
            splitHoles.append(bracketB.splitHole)

            self.triangles.extend(bracketF.triangles)
            self.triangles.extend(bracketB.triangles)
        else:
            splitEdge.add(e[0] for e in profile)
            splitEdge.add(e[-1] for e in reversed(profile))

        if cfg.floor.hexHoles:
            hexMargin = cfg.floor.hexHoles.wallMargin
            hexBorder = _naiveOffset2D(profile[-1], -hexMargin, True)
            hexagons = _hexGrid2D(hexBorder)
            hexagonsI = [h.translated(floorIG) for h in hexagons]
            hexagonsO = [h.translated(floorOG) for h in hexagons]

            innerHoles.extend(h.reversed() for h in hexagonsI)
            floorHoles.extend(hexagonsO)

            for hexI, hexO in zip(hexagonsI, hexagonsO):
                self.triangles.extend(hexI.meshPairwise(hexO, True))

        if cfg.bumper:
            bumperInset = cfg.bumper.margin + cfg.bumper.diameter/2

            thumbOLF = plan.points.thumbORF
            pinkyORF = plan.points.pinkyORF
            pinkyORB = plan.points.pinkyORB
            alnumOLB = plan.points.alnumOLB

            bumperRF = _cornerBumper(alnumOLB, pinkyORB, pinkyORF, bumperInset)
            bumperRB = _cornerBumper(pinkyORB, pinkyORF, thumbOLF, bumperInset)
            bumperLF = Bumper(profile[0][0] + Vector(0, bumperInset), True)
            bumperLB = Bumper(profile[0][-1] - Vector(0, bumperInset), True)

            floorHoles.append(bumperRF.floorEdge)
            floorHoles.append(bumperRB.floorEdge)

            splitEdge.add(bumperLB.splitEdge)
            splitEdge.add(bumperLF.splitEdge)
            floorEdge.add(bumperLF.floorEdge)
            floorEdge.add(bumperLB.floorEdge)

            self.triangles.extend(bumperRF.triangles)
            self.triangles.extend(bumperRB.triangles)
            self.triangles.extend(bumperLF.triangles)
            self.triangles.extend(bumperLB.triangles)

        # Bosses

        bosses = [
            plan.bosses.alnumB,
            plan.bosses.thumbF,
            plan.bosses.pinkyB,
            plan.bosses.pinkyF]

        if cfg.palm:
            bosses.append(plan.bosses.hitchL)
            bosses.append(plan.bosses.hitchR)

        for boss in bosses:
            bodyHoles.append(boss.clearanceHole)
            floorHoles.append(boss.headHole)
            self.triangles.extend(boss.headTriangles)

        # Triangles

        innerEdge.add(profile[-1])
        bodyEdge.add(profile[1], reversed(profile[2]))
        lipEdge.add(profile[3], reversed(profile[4]))

        # HACK: Fill gaps caused by brackets
        profile[2] = Edge(profile[2][0].yz, profile[2], profile[2][-1].yz)
        profile[3] = Edge(profile[3][0].yz, profile[3], profile[3][-1].yz)

        for i in 0, 2, 4, 5:
            self.triangles.extend(profile[i].meshPairwise(profile[i+1]))

        self.faces.append(Face(splitEdge.collapsed(), splitHoles))
        self.faces.append(Face(floorEdge, floorHoles))
        self.faces.append(Face(bodyEdge, bodyHoles))
        self.faces.append(Face(lipEdge.collapsed()))
        self.faces.append(Face(innerEdge, innerHoles))


def _cornerBumper(a, b, c, bumperInset):
    """Place bumper into rounded corner with the correct margin."""
    cornerRadius = cfg.body.outerCornerRadius

    aDir = (a - b).normalized2D()
    cDir = (c - b).normalized2D()

    cornerAngle = math.acos(aDir.dot(cDir))
    cornerDiag = cornerRadius / math.sin(cornerAngle/2)
    bumperDiag = bumperInset / math.sin(cornerAngle/2)

    diagOverlap = (cornerDiag - cornerRadius) - (bumperDiag - bumperInset)
    bumperDiag += max(0, diagOverlap)
    bumperDir = (aDir + cDir).normalized2D()

    return Bumper(b + bumperDir*bumperDiag)


def _naiveOffset2D(edge, distance, isClosed=False, minSegLength=1e-3):
    """Grow or shrink a simple polygon edge by the given distance.

    Note that the robust offsetting of arbitrary polygons is non-trivial
    and out of scope for this function. Avoid overly sharp angles. Avoid
    offset distances that cause a fundamental change of the topology.
    One simple polygon is returned.
    """
    def connect(segments):
        """Connect segments at their intersections as lines."""
        for i in range(len(segments)):
            seg0 = segments[i-1]
            seg1 = segments[i]
            middle = seg0.intersect2D(seg1, asLine=2)
            if middle is None:
                middle = (seg0.b + seg1.a) / 2
            seg0.b = middle
            seg1.a = middle

    if abs(distance) < 1e-6:
        return edge

    # Offset segments
    segments = edge.toSegments(True)
    offset = [s.offset2D(distance) for s in segments]
    if not isClosed:
        offset[-1] = segments[-1].offset2D(0)

    # Extend and reconnect offset segments.
    # In case of a sharp angle, the intersection
    # will be far away from the original point.
    connect(offset)

    # Reorder segments to start at a point that
    # is not part of a self-intersecting loop
    startIndex = 0
    for i, startSegment in enumerate(offset):
        isTooClose = False
        for segment in segments:
            if segment.distance2D(startSegment.a) < abs(distance) - 1e-6:
                isTooClose = True
                break
        if not isTooClose:
            startIndex = i
            break
    offset = offset[startIndex:] + offset[:startIndex]

    # Cut off self-intersecting loops
    i = 0
    while i < len(offset):
        segment = offset[i]
        cutPos = None
        cutDist = None
        cutIndex = None
        for j in range(i+2, len(offset) - int(i == 0)):
            pos = segment.intersect2D(offset[j])
            if pos is not None:
                dist = (pos - segment.a).magSquared()
                if cutDist is None or dist < cutDist:
                    cutPos = pos
                    cutDist = dist
                    cutIndex = j
        if cutIndex is not None:
            del offset[i+1:cutIndex]
            offset[i].b = cutPos
            offset[i+1].a = cutPos
        i += 1

    # Remove segments that are too short
    offset = [s for s in offset if s.magnitude2D() >= minSegLength]
    connect(offset)

    # Reorder segments to start near the original start point
    distances = [(s.a - edge[0]).magSquared() for s in offset]
    minIndex = distances.index(min(distances))
    offset = offset[minIndex:] + offset[:minIndex]

    return Edge(s.a for s in offset)


def _hexGrid2D(edge):
    """Fill polygon edge with a hexagon grid.

    If a hexagon does not fit completely, then scale it down
    toward the vertex that is furthest inside the polygon.
    """
    minDiameter = cfg.floor.hexHoles.minDiameter
    maxDiameter = cfg.floor.hexHoles.maxDiameter
    cornerRadius = cfg.floor.hexHoles.cornerRadius
    xOffset = cfg.floor.hexHoles.xOffset
    yOffset = cfg.floor.hexHoles.yOffset
    holeMargin = cfg.floor.hexHoles.holeMargin

    hexagons = []
    segments = edge.toSegments(True)

    minX = min(p.x for p in edge)
    maxX = max(p.x for p in edge)
    minY = min(p.y for p in edge)
    maxY = max(p.y for p in edge)

    maxRadius = maxDiameter/2
    minRadius = maxRadius/2 * 3**0.5

    xPitch = 3*maxRadius + holeMargin * 3**0.5
    yPitch = 2*minRadius + holeMargin

    xStart = minX + maxRadius + xOffset
    yStart = minY + minRadius + yOffset - yPitch

    row = 0
    x = xStart
    y = yStart
    while y < maxY + minRadius:
        while x < maxX + maxRadius:
            center = Vector(x, y)
            hexagon = Edge(
                Vector(x - maxRadius, y),
                Vector(x - maxRadius/2, y - minRadius),
                Vector(x + maxRadius/2, y - minRadius),
                Vector(x + maxRadius, y),
                Vector(x + maxRadius/2, y + minRadius),
                Vector(x - maxRadius/2, y + minRadius))

            # Increment before possible continue statments
            x += xPitch

            # Check if hexagon is completely inside or outside (cheap)
            centerDist = min(s.distance2D(center) for s in segments)
            if centerDist >= maxRadius:
                if edge.contains2D(center):
                    hexagons.append(hexagon)
                continue

            # Scale down partially contained hexagon (expensive)
            bestFactor = 0.0
            bestCenter = None
            pointsInHex = [p for p in edge if hexagon.contains2D(p)]

            for i, scaleCenter in enumerate(hexagon):
                if not edge.contains2D(scaleCenter):
                    continue

                minFactor = 1.0

                # Find scale factor to exclude all polygon points
                #   _____
                #  /     \. ray
                # /     p'\
                # \   .'  /
                #  \.'   /
                #   c----  scaleCenter
                if pointsInHex:
                    for point in pointsInHex:
                        if point.isClose(scaleCenter):
                            continue
                        ray = Segment(scaleCenter, point)
                        for j in range(1, len(hexagon) - 1):
                            hexSegment = Segment(hexagon[i-j-1], hexagon[i-j])
                            rayIntersect = hexSegment.intersect2D(ray, asLine=1)
                            if rayIntersect is None:
                                continue
                            pointDist = (point - scaleCenter).magnitude()
                            rayDist = (rayIntersect - scaleCenter).magnitude()
                            minFactor = min(pointDist / rayDist, minFactor)

                # Find scale factor to exclude all polygon segments
                #    _____ diag
                #   /    /\
                # -/----p--\-- segment
                #  \   /   /
                #   \ /   /
                #    c----  scaleCenter
                for j in range(1, len(hexagon)):
                    diag = Segment(scaleCenter, hexagon[i-j])
                    for segment in segments:
                        point = diag.intersect2D(segment)
                        if point is None:
                            continue
                        pointDist = (point - scaleCenter).magnitude()
                        diagDist = diag.magnitude2D()
                        minFactor = min(pointDist / diagDist, minFactor)

                if minFactor > bestFactor:
                    bestFactor = minFactor
                    bestCenter = scaleCenter

            # Add scaled hexagon
            if maxDiameter*bestFactor >= minDiameter:
                hexagons.append(hexagon.scaled(bestFactor, bestCenter))

        row += 1
        x = xStart + xPitch/2*(row % 2)
        y = yStart + yPitch/2*row

    if cornerRadius > 0:
        hexagons = [Edge(cornerArc2D(
            cornerRadius,
            hexagon[i-2],
            hexagon[i-1],
            hexagon[i]) for i in range(6)) for hexagon in hexagons]

    return hexagons
