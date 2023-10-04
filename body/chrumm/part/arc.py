import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Vector


def arc2D(radius, startAngle=0, spanAngle=math.tau, center=Vector()):
    if radius < 1e-6:
        return Edge(center)

    # https://en.wikipedia.org/wiki/Sagitta_(geometry)
    maxChordHeight = cfg.quality.maxChordHeight
    maxHeightAngle = math.acos(1 - maxChordHeight/radius) * 2
    maxChordAngle = min(cfg.quality.maxChordAngle, maxHeightAngle)

    spanAngle = max(-math.tau, min(spanAngle, math.tau))
    chordCount = math.ceil(abs(spanAngle) / maxChordAngle)
    chordAngle = spanAngle / chordCount
    pointCount = chordCount

    # Avoid duplicate start and end points of a full circle
    if abs(abs(spanAngle) - math.tau) > 1e-6:
        pointCount += 1

    edge = Edge()
    for i in range(pointCount):
        angle = startAngle + i*chordAngle
        x = center.x + radius*math.cos(angle)
        y = center.y + radius*math.sin(angle)
        edge.add(Vector(x, y))
    return edge


def cornerArc2D(radius, a, b, c):
    #   a
    #  /
    # b(
    #  \
    #   c
    aDir = (a - b).normalized2D()
    cDir = (c - b).normalized2D()
    sign = 1 if cDir.cross(aDir).z > 0 else -1

    cornerAngle = math.acos(aDir.dot(cDir))
    arcAngle = (math.pi - cornerAngle)*sign
    startAngle = (aDir.ortho2D()*sign).angle2D()

    centerDist = radius / math.sin(cornerAngle/2)
    centerDir = (aDir + cDir).normalized2D()
    centerPos = b.xy + centerDir*centerDist
    return arc2D(radius, startAngle, arcAngle, centerPos)


def uprightHole2D(radius):
    """Return hole shape intended for upright FFF 3D printing."""
    #   _____  <- Clean top bridge
    #  /     \  <- Straight tangent
    # :   +   :  <- Circular bottom
    # :       :
    #  '-...-'

    if cfg.support:
        angle = cfg.support.holeTaperAngle
        if angle > 0:
            arc = arc2D(radius, math.tau/4 + angle, math.tau - 2*angle)
            top = Vector(-radius * math.sin(angle/2) / math.cos(angle/2), radius)
            return Edge(top, arc, top.mirroredX())

    return arc2D(radius, 0, math.tau)


def uprightHalfHole2D(radius):
    """Return upper hole sketch intended for upright FFF 3D printing."""
    #   _____  <- Clean top bridge
    #  /     \  <- Straight tangent
    # :   +   :  <- Circular sides

    if cfg.support:
        angle = cfg.support.holeTaperAngle
        if angle > 0:
            arc = arc2D(radius, 0, math.tau/8)
            arc.add(Vector(radius * math.sin(angle/2) / math.cos(angle/2), radius))
            return Edge(arc, arc.mirroredX().reversed())

    return arc2D(radius, 0, math.pi)
