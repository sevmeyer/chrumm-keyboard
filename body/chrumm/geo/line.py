from .epsilon import isZero


class Line:

    __slots__ = "pos", "dir"

    def __init__(self, pos, direction):
        self.pos = pos
        self.dir = direction.normalized()

    def translated(self, vector):
        return Line(self.pos + vector, self.dir)

    def transformed(self, matrix):
        return Line(
            self.pos.transformed(matrix),
            self.dir.transformedNormal(matrix))

    def distance(self, vector):
        """Return the absolute distance to the line."""
        # Distance from point to line 3d formula - Rabbid76
        # https://stackoverflow.com/a/52792014
        closest = self.pos + self.dir * self.dir.dot(vector - self.pos)
        return (closest - vector).magnitude()

    def distance2D(self, vector):
        """Return the signed distance to the line.

        The distance is positive on the clockwise
        side of the line and negative on the other.
        """
        # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
        dir2D = self.dir.normalized2D()
        return dir2D.x*(self.pos.y - vector.y) - dir2D.y*(self.pos.x - vector.x)

    def intersect(self, other):
        # The shortest line between two lines in 3D - Paul Bourke
        # http://paulbourke.net/geometry/pointlineplane/
        delta = (self.pos - other.pos)

        do = delta.dot(other.dir)
        ds = delta.dot(self.dir)
        os = other.dir.dot(self.dir)
        oo = other.dir.dot(other.dir)
        ss = self.dir.dot(self.dir)

        numer = do * os - ds * oo
        denom = ss * oo - os * os

        if isZero(denom):
            raise ZeroDivisionError("Cannot find intersection of parallel lines.")

        muA = numer / denom
        muB = (do + muA*os) / oo

        a = self.pos + self.dir*muA
        b = other.pos + other.dir*muB
        return (a + b) / 2
