import math

from .matrix import Matrix
from .triangle import Triangle
from .vector import Vector


class Face:
    """Coplanar 3D polygon with deferred triangulation."""

    def __init__(self, edge, holes=[]):
        """Store polygon data for deferred triangulation.

        Requirements:
            No duplicate points
            No intersections
            No nested holes
            Points are reasonably coplanar
            Opposite point order for edge and holes
        Args:
            edge (list[Vector])
            holes (list[list[Vector]])
        """
        self.edge = edge
        self.holes = holes

    def triangulate(self):
        """Triangulate the stored polygon.

        Returns:
            list[Triangle]
        """
        # Triangulation by Ear Clipping - David Eberly
        # https://www.geometrictools.com/Documentation/TriangulationByEarClipping.pdf
        points = list(self.edge)
        polyIndexes = list(range(len(points)))
        holeIndexes = []

        for hole in self.holes:
            if hole:
                holeIndexes.append(list(range(len(points), len(hole) + len(points))))
                points.extend(hole)

        normal = Vector.fromSurfaceNormal(self.edge)
        uprightMatrix = Matrix.fromAlignment(normal, Vector(0, 0, 1))
        uprightPoints = [p.transformed(uprightMatrix).xy for p in points]

        polyIndexes = Face._mergeHoles(uprightPoints, polyIndexes, holeIndexes)
        triangles = Face._cutEars(uprightPoints, polyIndexes)
        triangles = Face._flipTriangles(uprightPoints, triangles)

        return [Triangle(points[i], points[j], points[k]) for i, j, k in triangles]

    @staticmethod
    def _mergeHoles(points, polyIndexes, holeIndexes):
        orderedHoles = []

        # Reorder each hole to start at the rightmost point
        for hole in holeIndexes:
            start = max(range(len(hole)), key=lambda i: points[hole[i]])
            orderedHoles.append(hole[start:] + hole[:start])

        # Connect each hole to a visible point on the right
        for hole in sorted(orderedHoles, key=lambda h: points[h[0]], reverse=True):
            vis = None

            # Construct rightward search triangle abc
            #             .c
            # _____     .'/
            #      |  .' /
            # hole |.'  /
            # _____a---b--> ray
            #         /
            #  polygon

            a = points[hole[0]]  # Rightward ray origin
            b = Vector(math.inf)  # Ray intersection with polygon
            c = Vector(math.inf)  # Rightmost end of intersected segment
            for i in range(len(polyIndexes)):
                j = (i+1) % len(polyIndexes)
                p = points[polyIndexes[i]]
                q = points[polyIndexes[j]]
                if p.y == a.y == q.y:
                    if a.x < p.x and a.x < q.x:
                        if p.x < q.x and p.x < b.x:
                            b, c, vis = p, p, i
                        elif q.x < b.x:
                            b, c, vis = q, q, j
                elif p.y <= a.y <= q.y:
                    x = p.x - (p.y - a.y)*(q.x - p.x)/(q.y - p.y)
                    if a.x < x < b.x:
                        b = Vector(x, a.y)
                        if p.x > q.x:
                            c, vis = p, i
                        else:
                            c, vis = q, j

            # Check for better point inside search triangle
            if b != c:
                if c.y < b.y:
                    # Ensure triangle is counter-clockwise
                    b, c = c, b

                aDir = (b - a).normalized2D()
                bDir = (c - b).normalized2D()
                cDir = (a - c).normalized2D()
                minDist = math.inf

                for i in range(len(polyIndexes)):
                    p = points[polyIndexes[i]]
                    isInTriangle = (
                        aDir.x*(a.y - p.y) - aDir.y*(a.x - p.x) < -1e-6 and
                        bDir.x*(b.y - p.y) - bDir.y*(b.x - p.x) < -1e-6 and
                        cDir.x*(c.y - p.y) - cDir.y*(c.x - p.x) < -1e-6)
                    if isInTriangle:
                        o = points[polyIndexes[(i-1) % len(polyIndexes)]]
                        q = points[polyIndexes[(i+1) % len(polyIndexes)]]
                        isReflex = (p.x - o.x)*(q.y - p.y) - (q.x - p.x)*(p.y - o.y) < 0
                        if isReflex:
                            dist = (p.x - a.x)*(p.x - a.x) + (p.y - a.y)*(p.y - a.y)
                            if dist < minDist:
                                minDist = dist
                                vis = i

            polyIndexes = polyIndexes[:vis+1] + hole + [hole[0]] + polyIndexes[vis:]

        return polyIndexes

    @staticmethod
    def _cutEars(points, polyIndexes):  # TODO: Optimize
        remaining = list(polyIndexes)
        triangles = []

        for _ in range(len(remaining) - 2):
            for i in range(len(remaining)):
                ear = (
                    remaining[i-1],
                    remaining[i],
                    remaining[(i+1) % len(remaining)])

                a = points[ear[0]]
                b = points[ear[1]]
                c = points[ear[2]]

                aDir = (b - a).normalized2D()
                bDir = (c - b).normalized2D()
                cDir = (a - c).normalized2D()

                earHeight = cDir.y*(c.x - b.x) - cDir.x*(c.y - b.y)
                if earHeight < 1e-6:
                    continue

                isEmpty = True
                for j in remaining:
                    if j in ear:
                        continue
                    p = points[j]
                    isInEar = (
                        aDir.x*(a.y - p.y) - aDir.y*(a.x - p.x) < 1e-6 and
                        bDir.x*(b.y - p.y) - bDir.y*(b.x - p.x) < 1e-6 and
                        cDir.x*(c.y - p.y) - cDir.y*(c.x - p.x) < 1e-6)
                    if isInEar:
                        isEmpty = False
                        break

                if isEmpty:
                    triangles.append(ear)
                    del remaining[i]
                    break

        return triangles

    @staticmethod
    def _flipTriangles(points, triangles):  # TODO: Merge with _cutEars
        class LinkedTriangle:  # TODO: Independent class
            """Triangle with references to its neighbors in counterclockwise order."""

            __slots__ = "indexes", "neighbors", "angles"

            def __init__(self, indexes):
                self.indexes = indexes
                self.neighbors = [None, None, None]
                self.cacheAngles()

            def cacheAngles(self):
                a = points[self.indexes[0]]
                b = points[self.indexes[1]]
                c = points[self.indexes[2]]

                abAngle = math.atan2(b.y - a.y, b.x - a.x)
                bcAngle = math.atan2(c.y - b.y, c.x - b.x)
                caAngle = math.atan2(a.y - c.y, a.x - c.x)

                self.angles = [
                    (caAngle + math.pi - abAngle) % math.tau,
                    (abAngle + math.pi - bcAngle) % math.tau,
                    (bcAngle + math.pi - caAngle) % math.tau]

            def opposite(self, i, j):
                if self.indexes[1] == i and self.indexes[0] == j:
                    return 2
                if self.indexes[2] == i and self.indexes[1] == j:
                    return 0
                if self.indexes[0] == i and self.indexes[2] == j:
                    return 1
                return None

            def link(self, other):
                for n in (0, 1, 2):
                    o = other.opposite(self.indexes[n], self.indexes[n-2])
                    if o is not None:
                        self.neighbors[n] = other
                        other.neighbors[o-2] = self
                        return

            def flip(self):
                for n, neig in enumerate(self.neighbors):
                    if neig is None:
                        continue

                    o = neig.opposite(self.indexes[n], self.indexes[n-2])

                    # https://en.wikipedia.org/wiki/Delaunay_triangulation
                    if self.angles[n-1] + neig.angles[o] < math.pi + 1e-6:
                        continue

                    tempIndexes = [self.indexes[n-1], neig.indexes[o], self.indexes[n-2]]
                    self.indexes = [neig.indexes[o], self.indexes[n-1], neig.indexes[o-1]]
                    neig.indexes = tempIndexes

                    tempNeighbors = [self, neig.neighbors[o], self.neighbors[n-2]]
                    self.neighbors = [neig, self.neighbors[n-1], neig.neighbors[o-1]]
                    neig.neighbors = tempNeighbors

                    if self.neighbors[2]:
                        self.neighbors[2].link(self)
                    if neig.neighbors[2]:
                        neig.neighbors[2].link(neig)

                    self.cacheAngles()
                    neig.cacheAngles()
                    return True

                return False

        # Populate
        links = []
        for indexes in triangles:
            link = LinkedTriangle(indexes)
            for other in links:
                link.link(other)
            links.append(link)

        # Flip
        isChanged = True
        while isChanged:
            isChanged = False
            for link in links:
                isChanged |= link.flip()

        return [link.indexes for link in links]
