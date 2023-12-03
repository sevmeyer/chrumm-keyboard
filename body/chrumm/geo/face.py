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
            Opposite point order for edge and holes
            Reasonably coplanar points
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
        realPoints = list(self.edge)
        polyIndexes = list(range(len(realPoints)))
        holeIndexes = []

        for hole in self.holes:
            if hole:
                holeStart = len(realPoints)
                holeEnd = holeStart + len(hole)
                holeIndexes.append(list(range(holeStart, holeEnd)))
                realPoints.extend(hole)

        surfaceNormal = Vector.fromSurfaceNormal(self.edge)
        uprightMatrix = Matrix.fromAlignment(surfaceNormal, Vector(0, 0, 1))
        uprightPoints = [p.transformed(uprightMatrix).xy for p in realPoints]

        Face._mergeHoles(uprightPoints, polyIndexes, holeIndexes)
        triangles = Face._cutEars(uprightPoints, polyIndexes)
        Face._flipTriangles(uprightPoints, triangles)

        return [Triangle(
            realPoints[i],
            realPoints[j],
            realPoints[k]) for i, j, k in triangles]

    @staticmethod
    def _mergeHoles(points, polyIndexes, holeIndexes):
        # Triangulation by Ear Clipping - David Eberly
        # https://www.geometrictools.com/Documentation/TriangulationByEarClipping.pdf

        # Reorder each hole to start at the rightmost point
        orderedHoles = []
        for hole in holeIndexes:
            start = max(range(len(hole)), key=lambda i: points[hole[i]])
            orderedHoles.append(hole[start:] + hole[:start])

        # Sort holes from right to left
        orderedHoles.sort(key=lambda h: points[h[0]], reverse=True)

        # Connect each hole to a visible point on the right
        for hole in orderedHoles:
            vis = None

            # Determine rightward search triangle abc
            #             .c
            # _____     .'/
            #      |  .' /
            # hole |.'  /
            # _____a---b--> ray
            #         /
            #  polygon

            a = points[hole[0]]   # Rightward ray origin
            b = Vector(math.inf)  # Ray intersection with polygon
            c = Vector(math.inf)  # Rightmost end of intersected segment
            for i in range(len(polyIndexes)):
                j = (i + 1) % len(polyIndexes)
                p = points[polyIndexes[i]]  # Polygon segment start
                q = points[polyIndexes[j]]  # Polygon segment end
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
                # Ensure triangle is counterclockwise
                if c.y < b.y:
                    b, c = c, b

                aDir = (b - a).normalized2D()
                bDir = (c - b).normalized2D()
                cDir = (a - c).normalized2D()
                minDist = math.inf

                for i in range(len(polyIndexes)):
                    p = points[polyIndexes[i]]
                    isInside = (
                        aDir.x*(a.y - p.y) - aDir.y*(a.x - p.x) < -1e-6 and
                        bDir.x*(b.y - p.y) - bDir.y*(b.x - p.x) < -1e-6 and
                        cDir.x*(c.y - p.y) - cDir.y*(c.x - p.x) < -1e-6)
                    if isInside:
                        o = points[polyIndexes[(i - 1) % len(polyIndexes)]]
                        q = points[polyIndexes[(i + 1) % len(polyIndexes)]]
                        isReflex = (p.x - o.x)*(q.y - p.y) - (q.x - p.x)*(p.y - o.y) < 0
                        if isReflex:
                            dist = (p.x - a.x)*(p.x - a.x) + (p.y - a.y)*(p.y - a.y)
                            if dist < minDist:
                                minDist = dist
                                vis = i

            # Merge hole (vis -> hole -> hole[0] -> vis)
            polyIndexes.insert(vis, polyIndexes[vis])
            polyIndexes.insert(vis+1, hole[0])
            polyIndexes[vis+1:vis+1] = hole

    @staticmethod
    def _cutEars(points, polyIndexes):
        remaining = list(polyIndexes)
        cache = [None] * len(remaining)
        ears = []

        for _ in range(len(remaining) - 2):
            for i in range(len(remaining)):
                # Cache reusable calculations
                if cache[i] is None:
                    ear = [
                        remaining[i - 1],
                        remaining[i],
                        remaining[(i + 1) % len(remaining)]]

                    a = points[ear[0]]
                    b = points[ear[1]]
                    c = points[ear[2]]

                    aDir = (b - a).normalized2D()
                    bDir = (c - b).normalized2D()
                    cDir = (a - c).normalized2D()

                    aDot = aDir.y*a.x - aDir.x*a.y + 1e-6
                    bDot = bDir.y*b.x - bDir.x*b.y + 1e-6
                    cDot = cDir.y*c.x - cDir.x*c.y + 1e-6

                    earHeight = cDir.x*b.y - cDir.y*b.x + cDot
                    cache[i] = ear, aDir, bDir, cDir, aDot, bDot, cDot, earHeight
                else:
                    ear, aDir, bDir, cDir, aDot, bDot, cDot, earHeight = cache[i]

                if earHeight < 0:
                    continue

                # Check if any point is inside ear
                isInside = False
                for j in remaining:
                    if j in ear:
                        continue
                    p = points[j]
                    isInside = (
                        cDir.y*p.x - cDir.x*p.y < cDot and
                        bDir.y*p.x - bDir.x*p.y < bDot and
                        aDir.y*p.x - aDir.x*p.y < aDot)
                    if isInside:
                        break

                # Cut empty ear
                if not isInside:
                    ears.append(ear)
                    del remaining[i]
                    del cache[i]
                    cache[i - 1] = None
                    cache[i % len(cache)] = None
                    break

        return ears

    @staticmethod
    def _flipTriangles(points, triangles):
        # Map counterclockwise edges to triangles for a fast lookup
        lookup = {(t[i-1], t[i]): t for t in triangles for i in (0, 1, 2)}
        remaining = set(lookup.keys())

        while remaining:
            a, b = remaining.pop()

            # c<---- b
            #  \ 0 // \
            #   \ // 1 \
            #    a ---->d

            try:
                tri0 = lookup[(a, b)]
                tri1 = lookup[(b, a)]
            except KeyError:
                continue

            c = tri0[tri0.index(a) - 1]
            d = tri1[tri1.index(b) - 1]

            da = points[a] - points[d]
            db = points[b] - points[d]
            dc = points[c] - points[d]

            # https://en.wikipedia.org/wiki/Delaunay_triangulation
            isDelaunay = (
                (da.x*da.x + da.y*da.y) * (db.x*dc.y-dc.x*db.y) -
                (db.x*db.x + db.y*db.y) * (da.x*dc.y-dc.x*da.y) +
                (dc.x*dc.x + dc.y*dc.y) * (da.x*db.y-db.x*da.y)) < 1e-6

            if isDelaunay:
                continue

            # Flip triangles in-place
            tri0[tri0.index(b)] = d
            tri1[tri1.index(a)] = c

            # Remap edges
            del lookup[(a, b)]
            del lookup[(b, a)]

            lookup[(d, c)] = tri0
            lookup[(c, a)] = tri0
            lookup[(a, d)] = tri0
            lookup[(c, d)] = tri1
            lookup[(d, b)] = tri1
            lookup[(b, c)] = tri1

            # Revisit neighboring edges
            remaining.add((c, a))
            remaining.add((a, d))
            remaining.add((d, b))
            remaining.add((b, c))
