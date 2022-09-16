from .epsilon import isZero
from .line import Line


class Circle:

    __slots__ = "center", "radius"

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def intersect2D(self, other):
        """Return a list of 0, 1, or 2 vectors"""
        if isinstance(other, Circle):
            return self._intersectCircle2D(other)
        if isinstance(other, Line):
            return self._intersectLine2D(other)
        raise NotImplementedError()

    def _intersectLine2D(self, line):
        # Intersection of a Line and a Sphere (or circle) - Paul Bourke
        # http://paulbourke.net/geometry/circlesphere/
        center = self.center.xy
        linePos = line.pos.xy
        lineDir = line.dir.normalized2D()

        b = 2*lineDir.dot(linePos - center)
        c = (center.magSquared2D()
             + linePos.magSquared2D()
             - 2*center.dot(linePos)
             - self.radius**2)
        exp = b**2 - 4*c

        if isZero(exp):
            return [linePos + lineDir*(-b/2)]
        if exp < 0:
            return []

        uNeg = (-b - exp**0.5) / 2
        uPos = (-b + exp**0.5) / 2
        return [linePos + lineDir*uNeg, linePos + lineDir*uPos]

    def _intersectCircle2D(self, other):
        # Intersection of two circles - Paul Bourke
        # http://paulbourke.net/geometry/circlesphere/
        a = self.center.xy
        b = other.center.xy

        pitch = (b - a).magnitude2D()
        isSeparate = pitch > self.radius + other.radius
        isInside = pitch < abs(self.radius - other.radius)

        if isZero(pitch) or isSeparate or isInside:
            return []

        midDir = (b - a).normalized()
        midDist = (self.radius**2 - other.radius**2 + pitch**2) / (2*pitch)
        midPos = a + midDir*midDist
        chordHalf = (self.radius**2 - midDist**2)**0.5

        if isZero(chordHalf):
            return [midPos]

        chordOffset = midDir.ortho2D() * chordHalf
        return [midPos + chordOffset, midPos - chordOffset]
