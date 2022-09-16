from .epsilon import isZero
from .line import Line
from .vector import Vector


class Plane:

    __slots__ = "pos", "normal"

    def __init__(self, pos, normal):
        self.pos = pos
        self.normal = normal.normalized()

    @staticmethod
    def fromX(x):
        return Plane(Vector(x, 0, 0), Vector(1, 0, 0))

    @staticmethod
    def fromY(y):
        return Plane(Vector(0, y, 0), Vector(0, 1, 0))

    @staticmethod
    def fromZ(z):
        return Plane(Vector(0, 0, z), Vector(0, 0, 1))

    @staticmethod
    def fromPoints(a, b, c):
        return Plane(b, (b - a).cross(c - a))

    @staticmethod
    def fromLine2D(line):
        """Return vertical plane along the line."""
        return Plane(line.pos.xy, line.dir.ortho2D())

    def translated(self, vector):
        return Plane(self.pos + vector, self.normal)

    def transformed(self, matrix):
        return Plane(
            self.pos.transformed(matrix),
            self.normal.transformedNormal(matrix))

    def distance(self, vector):
        """Return signed distance in the direction of the normal."""
        return (vector - self.pos).dot(self.normal)

    def projectNormal(self, vector):
        return self._intersectLine(Line(vector, self.normal))

    def projectX(self, vector):
        if isZero(self.normal.x):
            raise ZeroDivisionError("Plane is parallel to the x axis.")

        xDist = self.normal.dot(self.pos - vector) / self.normal.x
        return Vector(vector.x + xDist, vector.y, vector.z)

    def projectY(self, vector):
        if isZero(self.normal.y):
            raise ZeroDivisionError("Plane is parallel to the y axis.")

        yDist = self.normal.dot(self.pos - vector) / self.normal.y
        return Vector(vector.x, vector.y + yDist, vector.z)

    def projectZ(self, vector):
        if isZero(self.normal.z):
            raise ZeroDivisionError("Plane is parallel to the z axis.")

        zDist = self.normal.dot(self.pos - vector) / self.normal.z
        return Vector(vector.x, vector.y, vector.z + zDist)

    def intersect(self, other1, other2=None):
        if isinstance(other1, Plane) and isinstance(other2, Plane):
            return self._intersectPlanes(other1, other2)
        if isinstance(other1, Line):
            return self._intersectLine(other1)
        raise NotImplementedError()

    def _intersectPlanes(self, other1, other2):
        # Intersection of three planes - Paul Bourke
        # http://paulbourke.net/geometry/pointlineplane/
        dot1 = other1.normal.dot(other1.pos)
        dot2 = other2.normal.dot(other2.pos)
        dot3 = self.normal.dot(self.pos)

        cross23 = other2.normal.cross(self.normal)
        cross31 = self.normal.cross(other1.normal)
        cross12 = other1.normal.cross(other2.normal)

        numer = cross23*dot1 + cross31*dot2 + cross12*dot3
        denom = other1.normal.dot(cross23)

        if isZero(denom):
            raise ZeroDivisionError("Cannot find intersection of parallel planes.")

        return numer / denom

    def _intersectLine(self, line):
        # Intersection of a plane and a line - Paul Bourke
        # http://paulbourke.net/geometry/pointlineplane/
        numer = self.normal.dot(self.pos - line.pos)
        denom = self.normal.dot(line.dir)

        if isZero(denom):
            raise ZeroDivisionError("Cannot find intersection of parallel line.")

        return line.pos + line.dir*(numer / denom)
