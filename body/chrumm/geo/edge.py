import collections
import math

from .segment import Segment
from .triangle import Triangle
from .vector import Vector


class Edge(collections.UserList):
    """A flat list of Vectors with additional convenience functions."""

    def __init__(self, *args):
        super().__init__()
        self.add(*args)

    @staticmethod
    def fromConvexHull2D(vectors):
        # Another efficient algorithm for convex hulls in two dimensions - A. M. Andrew
        # https://wikibooks.org/wiki/Algorithm_Implementation/Geometry/Convex_hull/Monotone_chain
        vectors = sorted(v.xy for v in vectors)
        lower = []
        upper = []

        for v in vectors:
            while len(lower) >= 2 and (lower[-2] - v).cross(lower[-1] - v).z <= 0:
                lower.pop()
            lower.append(v)

        for v in reversed(vectors):
            while len(upper) >= 2 and (upper[-2] - v).cross(upper[-1] - v).z <= 0:
                upper.pop()
            upper.append(v)

        return Edge(lower[:-1], upper[:-1])

    def toSegments(self, isClosed=False):
        vecCount = len(self.data)
        segCount = vecCount - 1 + bool(isClosed)
        return [Segment(self.data[i], self.data[(i+1) % vecCount]) for i in range(segCount)]

    def add(self, *args):
        for arg in args:
            if isinstance(arg, Vector):
                self.data.append(arg)
            else:
                self.add(*arg)

    @property
    def xy(self):
        return Edge(v.xy for v in self.data)

    @property
    def xz(self):
        return Edge(v.xz for v in self.data)

    @property
    def yz(self):
        return Edge(v.yz for v in self.data)

    def mirroredX(self):
        return Edge(v.mirroredX() for v in self.data)

    def mirroredY(self):
        return Edge(v.mirroredY() for v in self.data)

    def mirroredZ(self):
        return Edge(v.mirroredZ() for v in self.data)

    def reversed(self):
        return Edge(reversed(self.data))

    def scaled(self, scalar, center=Vector()):
        return Edge((v - center)*scalar + center for v in self.data)

    def translated(self, vector):
        return Edge(v + vector for v in self.data)

    def transformed(self, matrix):
        return Edge(v.transformed(matrix) for v in self.data)

    def snapped(self):
        return Edge(p.snapped() for p in self.data)

    def collapsed(self, threshold=1e-3):
        """Remove segments that are shorter than the threshold."""
        return Edge(s.a for s in self.toSegments(True) if s.magnitude() >= threshold)

    def meshPairwise(self, other, isClosed=False):
        """Triangulate each pair of edge segments in order.

        Edges may overlap. If one edge has more segments
        than the other, its remaining segments are
        connected to the last point of the shorter edge.
        """
        triangles = []

        selfLen = len(self.data)
        otherLen = len(other.data)

        selfEnd = selfLen - 1 + int(isClosed)
        otherEnd = otherLen - 1 + int(isClosed)

        for i in range(max(otherEnd, selfEnd)):
            a = self.data[min(selfEnd, i) % selfLen]
            b = self.data[min(selfEnd, i+1) % selfLen]
            c = other.data[min(otherEnd, i+1) % otherLen]
            d = other.data[min(otherEnd, i) % otherLen]

            # There are two possible pairs of triangles:
            #  --d----c->  --d----c->  other
            #    |1 / |      | \ 3|
            #    | / 0|      |2 \ |
            #  --a----b->  --a----b->  self

            abc = Triangle(a, b, c)
            cda = Triangle(c, d, a)
            abd = Triangle(a, b, d)
            dbc = Triangle(d, b, c)

            # Lookup table to determine which triangles
            # to use, based on which are valid
            valid = bool(dbc)*8 + bool(abd)*4 + bool(cda)*2 + bool(abc)
            table = (
                0b0000, 0b0000, 0b0000, 0b0001,
                0b0000, 0b0001, 0b0010, 0b0011,
                0b0000, 0b0001, 0b0010, 0b0011,
                0b0100, 0b1100, 0b1100, 0b0011)
            bits = table[valid]

            if valid == 0b1111:
                # https://en.wikipedia.org/wiki/Delaunay_triangulation
                abcAngle = (a - b).angleBetween(c - b)
                cdaAngle = (c - d).angleBetween(a - d)
                # The epsilon is not necessary, but it prevents
                # irregular quad diagonals due to rounding errors.
                if abcAngle + cdaAngle > math.pi + 1e-6:
                    bits = 0b1100

            if bits & 0b0001:
                triangles.append(abc)
            if bits & 0b0010:
                triangles.append(cda)
            if bits & 0b0100:
                triangles.append(abd)
            if bits & 0b1000:
                triangles.append(dbc)

        return triangles

    def meshParallel(self, other, isClosed=False):
        """Triangulate reasonably parallel, non-intersecting edges

        Minimize the normal deviation between subsequent triangles.
        In the case of multiple candidates, prioritize equilaterality.
        """
        triangles = []

        selfLen = len(self.data)
        otherLen = len(other.data)

        selfEnd = selfLen - 1 + int(isClosed)
        otherEnd = otherLen - 1 + int(isClosed)

        i = 0
        j = 0
        while i < selfEnd or j < otherEnd:
            a = self.data[min(selfEnd, i) % selfLen]
            b = self.data[min(selfEnd, i+1) % selfLen]
            c = other.data[min(otherEnd, j+1) % otherLen]
            d = other.data[min(otherEnd, j) % otherLen]

            abd = Triangle(a, b, d)
            acd = Triangle(a, c, d)

            if i >= selfEnd:
                triangles.append(acd)
                j += 1
                continue
            if j >= otherEnd:
                triangles.append(abd)
                i += 1
                continue

            # Choose the triangle with the smaller normal deviation,
            # if the difference is significant enough.
            if triangles:
                prevNorm = triangles[-1].normal()
                abdDev = abd.normal().angleBetween(prevNorm)
                acdDev = acd.normal().angleBetween(prevNorm)
                if abdDev < acdDev - math.tau/16:
                    triangles.append(abd)
                    i += 1
                    continue
                if acdDev < abdDev - math.tau/16:
                    triangles.append(acd)
                    j += 1
                    continue

            # Otherwise, choose the most equilateral triangle,
            # based on the circumcircle (Delaunay).
            if abd.circumradius() < acd.circumradius() + 1e-6:
                triangles.append(abd)
                i += 1
            else:
                triangles.append(acd)
                j += 1

        return triangles

    def contains2D(self, vector):
        """Check if the vector is inside the simple closed edge.

        Vectors on the exact edge may or may not be considered inside.
        """
        # Point Inclusion in Polygon Test - W. Randolph Franklin
        # https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
        isIn = False
        for i in range(len(self.data)):
            a = self.data[i-1]
            b = self.data[i]
            if (a.y > vector.y) != (b.y > vector.y):
                if vector.x < (b.x - a.x) * (vector.y - a.y) / (b.y - a.y) + a.x:
                    isIn = not isIn
        return isIn

    def distance2D(self, vector):
        """Return the minimum distance to the simple closed edge."""
        if self.contains2D(vector):
            return 0
        return min(s.distance2D(vector) for s in self.toSegments(True))
