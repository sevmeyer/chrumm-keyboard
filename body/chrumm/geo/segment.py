from .epsilon import isZero
from .vector import Vector


class Segment:

    __slots__ = "a", "b"

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def magnitude(self):
        return (self.b - self.a).magnitude()

    def offset2D(self, distance):
        offset = (self.a - self.b).ortho2D().normalized2D() * distance
        return Segment(self.a.xy + offset, self.b.xy + offset)

    def magnitude2D(self):
        return (self.a - self.b).magnitude2D()

    def distance2D(self, vector):
        # Minimum Distance between a Point and a Line - Paul Bourke
        # http://paulbourke.net/geometry/pointlineplane/
        a = self.a
        b = self.b

        # OPTIMIZED: Avoid Vector init, inline 2D calculations
        numer = (vector.x - a.x)*(b.x - a.x) + (vector.y - a.y)*(b.y - a.y)
        denom = (b.x - a.x)**2 + (b.y - a.y)**2
        u = max(0, min(numer / denom, 1)) if denom != 0 else 0
        return ((a.x + u*(b.x - a.x) - vector.x)**2 +
                (a.y + u*(b.y - a.y) - vector.y)**2)**0.5

    def intersect2D(self, other, asLine=0):
        """Return intersection of segments, or None if they do not intersect.

        Args:
            asLine (int): Treat neither segment (0), the other segment (1),
                or both segments (2) as infinite lines.
        """
        # Intersection point of two line segments in 2 dimensions - Paul Bourke
        # http://paulbourke.net/geometry/pointlineplane/
        assert 0 <= asLine <= 2
        a = self.a
        b = self.b
        c = other.a
        d = other.b

        # OPTIMIZED: Avoid Vector init, inline 2D calculations
        denom = (d.y - c.y)*(b.x - a.x) - (d.x - c.x)*(b.y - a.y)
        if not isZero(denom):
            abPos = ((d.x - c.x)*(a.y - c.y) - (d.y - c.y)*(a.x - c.x)) / denom
            if (asLine == 2 or 0 <= abPos <= 1):
                cdPos = ((b.x - a.x)*(a.y - c.y) - (b.y - a.y)*(a.x - c.x)) / denom
                if (asLine >= 1 or 0 <= cdPos <= 1):
                    return Vector(a.x + (b.x - a.x)*abPos, a.y + (b.y - a.y)*abPos)
        return None
