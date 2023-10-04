import unittest

from ..edge import Edge
from ..matrix import Matrix
from ..vector import Vector

from .helper import findTriangulationProblems


EDGE_EMPTY = Edge()
EDGE_SQUARE = Edge(
    Vector(0, 0, 0),
    Vector(1, 0, 1),
    Vector(1, 1, 2),
    Vector(0, 1, 3))


class EdgeTest(unittest.TestCase):

    def test_fromConvexHull2D(self):
        vectors = [
            Vector(0.5, 0, 1),
            Vector(1, 1, 2),
            Vector(1, 0, 3),
            Vector(0.5, 0.5, 4),
            Vector(0, 1, 5),
            Vector(0, 0.5, 6),
            Vector(0, 0, 7)]
        edge = Edge.fromConvexHull2D(vectors)
        self.assertEqual(edge, EDGE_SQUARE.xy)

    def test_toSegments(self):
        # Open
        segs = Edge().toSegments()
        self.assertEqual(len(segs), 0)

        segs = Edge(Vector()).toSegments()
        self.assertEqual(len(segs), 0)

        segs = Edge(Vector(), Vector(1, 2, 3)).toSegments()
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0].a, Vector(0, 0, 0))
        self.assertEqual(segs[0].b, Vector(1, 2, 3))

        # Closed
        segs = Edge().toSegments(True)
        self.assertEqual(len(segs), 0)

        segs = Edge(Vector()).toSegments(True)
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0].a, Vector())
        self.assertEqual(segs[0].b, Vector())

        segs = Edge(Vector(), Vector(1, 2, 3)).toSegments(True)
        self.assertEqual(len(segs), 2)
        self.assertEqual(segs[0].a, Vector(0, 0, 0))
        self.assertEqual(segs[0].b, Vector(1, 2, 3))
        self.assertEqual(segs[1].a, Vector(1, 2, 3))
        self.assertEqual(segs[1].b, Vector(0, 0, 0))

    def test_add(self):
        edge = Edge()
        self.assertEqual(len(edge), 0)

        edge.add([])
        self.assertEqual(len(edge), 0)

        edge.add(Vector(1))
        self.assertEqual(len(edge), 1)
        self.assertEqual(edge[0], Vector(1))

        edge.add([Vector(2)])
        self.assertEqual(len(edge), 2)
        self.assertEqual(edge[0], Vector(1))
        self.assertEqual(edge[1], Vector(2))

        edge.add(Edge(Vector(3)))
        self.assertEqual(len(edge), 3)
        self.assertEqual(edge[0], Vector(1))
        self.assertEqual(edge[1], Vector(2))
        self.assertEqual(edge[2], Vector(3))

        edge.add([Edge(Vector(4)), Edge(Vector(5))])
        self.assertEqual(len(edge), 5)
        self.assertEqual(edge[0], Vector(1))
        self.assertEqual(edge[1], Vector(2))
        self.assertEqual(edge[2], Vector(3))
        self.assertEqual(edge[3], Vector(4))
        self.assertEqual(edge[4], Vector(5))

    def test_mirroredX(self):
        edge = EDGE_SQUARE.mirroredX()
        for i in range(len(edge)):
            self.assertEqual(edge[i], EDGE_SQUARE[i].mirroredX())

    def test_mirroredY(self):
        edge = EDGE_SQUARE.mirroredY()
        for i in range(len(edge)):
            self.assertEqual(edge[i], EDGE_SQUARE[i].mirroredY())

    def test_mirroredZ(self):
        edge = EDGE_SQUARE.mirroredZ()
        for i in range(len(edge)):
            self.assertEqual(edge[i], EDGE_SQUARE[i].mirroredZ())

    def test_reversed(self):
        edge = EDGE_SQUARE.reversed()
        for i in range(len(edge)):
            self.assertEqual(edge[i], EDGE_SQUARE[len(EDGE_SQUARE)-1-i])

    def test_scaled(self):
        edge = EDGE_SQUARE.scaled(0)
        for i in range(len(edge)):
            self.assertEqual(edge[i], Vector())

        edge = EDGE_SQUARE.scaled(1)
        self.assertEqual(edge, EDGE_SQUARE)

        edge = EDGE_SQUARE.scaled(2)
        for i in range(len(edge)):
            self.assertEqual(edge[i], EDGE_SQUARE[i]*2)

    def test_translated(self):
        edge = EDGE_SQUARE.translated(Vector(1, 2, 3))
        for i in range(len(edge)):
            self.assertEqual(edge[i], EDGE_SQUARE[i] + Vector(1, 2, 3))

    def test_transformed(self):
        matrix = Matrix().rotatedX(2**0.5)
        edge = EDGE_SQUARE.transformed(matrix)
        for i in range(len(edge)):
            self.assertEqual(edge[i], EDGE_SQUARE[i].transformed(matrix))

    def test_collapsed(self):
        edge = Edge()
        self.assertEqual(edge.collapsed(), Edge())

        edge = Edge(Vector())
        self.assertEqual(edge.collapsed(), Edge())

        edge = Edge(Vector(), Vector())
        self.assertEqual(edge.collapsed(), Edge())

        edge = Edge(Vector(), Vector(1, 2, 3))
        self.assertEqual(edge.collapsed(), edge)

        edge = Edge(Vector(), Vector(), Vector(1, 2, 3), Vector(1, 2, 3))
        expected = Edge(Vector(), Vector(1, 2, 3))
        self.assertEqual(edge.collapsed(), expected)

        edge = Edge(Vector(), Vector(1, 2, 3), Vector(1, 2, 3), Vector())
        expected = Edge(Vector(), Vector(1, 2, 3))
        self.assertEqual(edge.collapsed(), expected)

    def test_meshPairwise(self):
        tris = Edge().meshPairwise(Edge())
        self.assertEqual(len(tris), 0)

        tris = Edge().meshPairwise(Edge(Vector()))
        self.assertEqual(len(tris), 0)

        tris = Edge().meshPairwise(Edge(Vector(1, 2, 3)))
        self.assertEqual(len(tris), 0)

        tris = Edge(Vector()).meshPairwise(Edge(Vector(1, 2, 3)))
        self.assertEqual(len(tris), 0)

        tris = Edge(Vector()).meshPairwise(Edge(Vector(1, 2, 3), Vector(1, 2, 3)))
        self.assertEqual(len(tris), 0)

        tris = Edge(Vector()).meshPairwise(Edge(Vector(1, 2, 3), Vector(2, 4, 6)))
        self.assertEqual(len(tris), 0)

        tris = Edge(Vector()).meshPairwise(Edge(Vector(1, 3, 4), Vector(-1, 3, 4)))
        self.assertEqual(len(tris), 1)
        self.assertAlmostEqual(tris[0].area(), 5)

        # Closed
        edge0 = Edge(
            Vector(0, 0, 0),
            Vector(1, 0, 0),
            Vector(1, 1, 0),
            Vector(0, 1, 0))
        edge1 = Edge(
            Vector(0, 0, 1),
            Vector(1, 0, 1),
            Vector(1, 1, 1),
            Vector(0, 1, 1))
        tris = edge0.meshPairwise(edge1, isClosed=True)
        segs = edge0.toSegments(True) + edge1.toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 8)
        self.assertAlmostEqual(area, 4)
        self.assertIsNone(findTriangulationProblems(tris, segs))

        # Fanning
        edge0 = Edge(
            Vector(1, 1, 4),
            Vector(2, 1, 4))
        edge1 = Edge(
            Vector(1, 0, 4),
            Vector(2, 0, 4),
            Vector(3, 1, 4),
            Vector(2, 2, 4),
            Vector(1, 2, 4))
        tris = edge0.meshPairwise(edge1)
        segs = Edge(edge0, reversed(edge1)).toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 5)
        self.assertAlmostEqual(area, 2.5)
        self.assertIsNone(findTriangulationProblems(tris, segs))

        # Overlapping and collinear segments
        edge0 = Edge(
            Vector(2, 1, 2),
            Vector(3, 1, 2),
            Vector(4, 2, 2),
            Vector(5, 3, 2),
            Vector(6, 3, 2))
        edge1 = Edge(
            Vector(2, 1, 3),
            Vector(3, 1, 2),
            Vector(4, 2, 2),
            Vector(5, 3, 2),
            Vector(6, 3, 3))
        tris = edge0.meshPairwise(edge1)
        segs = Edge(edge0, reversed(edge1)).toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 2)
        self.assertAlmostEqual(area, 1)
        self.assertIsNone(findTriangulationProblems(tris, segs))

        # Crossing edges
        edge0 = Edge(
            Vector(1, 1, 5),
            Vector(2, 2, 5),
            Vector(3, 1, 5))
        edge1 = Edge(
            Vector(1, 2, 5),
            Vector(2, 1, 5),
            Vector(3, 2, 5))
        tris = edge0.meshPairwise(edge1)
        segs = Edge(edge0, reversed(edge1)).toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 4)
        self.assertAlmostEqual(area, 2)
        self.assertIsNone(findTriangulationProblems(tris, segs))

    def test_meshParallel(self):
        tris = Edge().meshParallel(Edge())
        self.assertEqual(len(tris), 0)

        tris = Edge().meshParallel(Edge(Vector()))
        self.assertEqual(len(tris), 0)

        tris = Edge().meshParallel(Edge(Vector(1, 2, 3)))
        self.assertEqual(len(tris), 0)

        tris = Edge(Vector()).meshParallel(Edge(Vector(1, 2, 3)))
        self.assertEqual(len(tris), 0)

        tris = Edge(Vector()).meshParallel(Edge(Vector(1, 3, 4), Vector(-1, 3, 4)))
        self.assertEqual(len(tris), 1)
        self.assertAlmostEqual(tris[0].area(), 5)

        # Closed
        edge0 = Edge(
            Vector(0, 0, 0),
            Vector(1, 0, 0),
            Vector(1, 1, 0),
            Vector(0, 1, 0))
        edge1 = Edge(
            Vector(0, 0, 1),
            Vector(1, 0, 1),
            Vector(1, 1, 1),
            Vector(0, 1, 1))
        tris = edge0.meshParallel(edge1, isClosed=True)
        segs = edge0.toSegments(True) + edge1.toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 8)
        self.assertAlmostEqual(area, 4)
        self.assertIsNone(findTriangulationProblems(tris, segs))

        # Fanning at end
        edge0 = Edge(
            Vector(1, 1, 4),
            Vector(2, 1, 4))
        edge1 = Edge(
            Vector(1, 0, 4),
            Vector(2, 0, 4),
            Vector(3, 1, 4),
            Vector(2, 2, 4),
            Vector(1, 2, 4))
        tris = edge0.meshParallel(edge1)
        segs = Edge(edge0, reversed(edge1)).toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 5)
        self.assertAlmostEqual(area, 2.5)
        self.assertIsNone(findTriangulationProblems(tris, segs))

        # Fanning in middle
        edge0 = Edge(
            Vector(0, 0, 0),
            Vector(8, 6, 0),
            Vector(16, 0, 0))
        edge1 = Edge(
            Vector(0, 0, 6),
            Vector(4, 3, 6),
            Vector(8, 6, 6),
            Vector(12, 3, 6),
            Vector(16, 0, 6))
        tris = edge0.meshParallel(edge1)
        segs = Edge(edge0, reversed(edge1)).toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 6)
        self.assertAlmostEqual(area, 120)
        self.assertIsNone(findTriangulationProblems(tris, segs))

        normL = Vector(3, -4).normalized()
        normR = Vector(-3, -4).normalized()
        self.assertTrue(tris[0].normal().isClose(normL))
        self.assertTrue(tris[1].normal().isClose(normL))
        self.assertTrue(tris[2].normal().isClose(normL))
        self.assertTrue(tris[3].normal().isClose(normR))
        self.assertTrue(tris[4].normal().isClose(normR))
        self.assertTrue(tris[5].normal().isClose(normR))

    def test_contains2D(self):
        eps = 1e-9
        self.assertTrue(EDGE_SQUARE.contains2D(Vector(eps, eps, 9)))
        self.assertTrue(EDGE_SQUARE.contains2D(Vector(0.5, eps, 9)))
        self.assertTrue(EDGE_SQUARE.contains2D(Vector(eps, 0.5, 9)))
        self.assertTrue(EDGE_SQUARE.contains2D(Vector(1-eps, 1-eps, 9)))

        self.assertFalse(EDGE_SQUARE.contains2D(Vector(-eps, -eps, 9)))
        self.assertFalse(EDGE_SQUARE.contains2D(Vector(0.5, -eps, 9)))
        self.assertFalse(EDGE_SQUARE.contains2D(Vector(-eps, 0.5, 9)))
        self.assertFalse(EDGE_SQUARE.contains2D(Vector(1+eps, 1+eps, 9)))

    def test_distance2D(self):
        self.assertEqual(EDGE_SQUARE.distance2D(Vector(0, 0, 9)), 0)
        self.assertEqual(EDGE_SQUARE.distance2D(Vector(0.5, 0.5, 9)), 0)
        self.assertEqual(EDGE_SQUARE.distance2D(Vector(1, 1, 9)), 0)

        self.assertEqual(EDGE_SQUARE.distance2D(Vector(-1, 0, 9)), 1)
        self.assertEqual(EDGE_SQUARE.distance2D(Vector(0, -1, 9)), 1)

        self.assertEqual(EDGE_SQUARE.distance2D(Vector(2, 1, 9)), 1)
        self.assertEqual(EDGE_SQUARE.distance2D(Vector(1, 2, 9)), 1)

        self.assertAlmostEqual(EDGE_SQUARE.distance2D(Vector(-1, -1, 9)), 2**0.5)
        self.assertAlmostEqual(EDGE_SQUARE.distance2D(Vector(2, 2, 9)), 2**0.5)
