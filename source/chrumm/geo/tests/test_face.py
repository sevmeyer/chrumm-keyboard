import unittest

from ..edge import Edge
from ..face import Face
from ..vector import Vector

from .helper import findTriangulationProblems


class FaceTest(unittest.TestCase):

    def test_triangulate_simple(self):
        #          9--------8
        #          |        |
        # 11------10    .3  |
        #            .-' |  |
        #    1--2  2'    |  7
        #    |  |   '.   |  |
        #    0  3     1  |  |
        #             |  |  |
        #    2--3     0  4  6
        #    |  |         .'
        # 0--1  4--------5

        edge = Edge(
            Vector(10, 10),
            Vector(20, 10),
            Vector(20, 20),
            Vector(30, 20),
            Vector(30, 10),
            Vector(60, 10),
            Vector(70, 20),
            Vector(70, 40),
            Vector(70, 60),
            Vector(40, 60),
            Vector(40, 50),
            Vector(10, 50))
        hole0 = Edge(
            Vector(20, 30),
            Vector(20, 40),
            Vector(30, 40),
            Vector(30, 30))
        hole1 = Edge(
            Vector(50, 20),
            Vector(50, 30),
            Vector(40, 40),
            Vector(60, 50),
            Vector(60, 20))

        # Without holes
        tris = Face(edge).triangulate()
        segs = edge.toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 10)
        self.assertAlmostEqual(area, 2550)
        self.assertIsNone(findTriangulationProblems(tris, segs))

        # With holes
        tris = Face(edge, [hole0, hole1]).triangulate()
        segs = edge.toSegments(True) + hole0.toSegments(True) + hole1.toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 23)
        self.assertAlmostEqual(area, 2100)
        self.assertIsNone(findTriangulationProblems(tris, segs))

    def test_triangulate_vertical(self):
        edge = Edge(
            Vector(-10, 0, -10),
            Vector(10, 0, -10),
            Vector(10, 0, 10),
            Vector(-10, 0, 10))

        tris = Face(edge).triangulate()
        segs = edge.toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 2)
        self.assertAlmostEqual(area, 400)
        self.assertIsNone(findTriangulationProblems(tris, segs))

    def test_triangulate_flipDelaunay(self):
        #    3
        #     \   Prefer diagonal
        #      \  (0, 2) over (1, 3)
        #       \
        # 0     2
        #  '. .'
        #    1

        edge = Edge(
            Vector(10, 20),
            Vector(20, 10),
            Vector(30, 20),
            Vector(20, 50))

        tris = Face(edge).triangulate()
        segs = edge.toSegments(True)
        areas = sorted(t.area() for t in tris)
        self.assertEqual(len(tris), 2)
        self.assertAlmostEqual(areas[0], 100)
        self.assertAlmostEqual(areas[1], 300)
        self.assertIsNone(findTriangulationProblems(tris, segs))

    def test_triangulate_sliverEar(self):
        #       2--1
        #     .'   |  Avoid sliver
        # 4--3     |  ear (2, 3, 5)
        # |        |
        # 5        |
        #          |
        #          0

        edge = Edge(
            Vector(50, 10),
            Vector(50, 50),
            Vector(40, 50),
            Vector(29.999, 40),
            Vector(20, 40),
            Vector(20, 30))

        tris = Face(edge).triangulate()
        segs = edge.toSegments(True)
        for tri in tris:
            self.assertGreater(tri.area(), 25)
        self.assertEqual(len(tris), 4)
        self.assertIsNone(findTriangulationProblems(tris, segs))

    def test_triangulate_alignedHoles(self):
        # 3--------------2
        #                |
        #    0--1  0--1  |
        #     h2|   h3|  |
        #    3--2  3--2  |
        #                |
        #    0--1  0--1  |
        #     h0|   h1|  |
        #    3--2  3--2  |
        #                |
        # 0--------------1

        edge = Edge(Vector(10, 10), Vector(60, 10), Vector(60, 60), Vector(10, 60))
        hole0 = Edge(Vector(20, 30), Vector(30, 30), Vector(30, 20), Vector(20, 20))
        hole1 = Edge(Vector(40, 30), Vector(50, 30), Vector(50, 20), Vector(40, 20))
        hole2 = Edge(Vector(20, 50), Vector(30, 50), Vector(30, 40), Vector(20, 40))
        hole3 = Edge(Vector(40, 50), Vector(50, 50), Vector(50, 40), Vector(40, 40))

        tris = Face(edge, [hole0, hole1, hole2, hole3]).triangulate()
        segs = (
            edge.toSegments(True)
            + hole0.toSegments(True)
            + hole1.toSegments(True)
            + hole2.toSegments(True)
            + hole3.toSegments(True))
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 26)
        self.assertAlmostEqual(area, 2100)
        self.assertIsNone(findTriangulationProblems(tris, segs))

    def test_triangulate_holeBridgeOrder(self):
        # 2
        #  '.
        #    '.
        #      '.
        #   1    '.
        #   |'.    '.
        #   0  2     '.
        #        1     '.
        #        |'.  1  '.
        #        0  2 |'.  '.
        #             0  2   '.
        # 0--------------------1

        edge = Edge(Vector(10, 10), Vector(80, 10), Vector(10, 80))
        hole0 = Edge(Vector(20, 40), Vector(20, 50), Vector(30, 40))
        hole1 = Edge(Vector(35, 25), Vector(35, 35), Vector(45, 25))
        hole2 = Edge(Vector(50, 20), Vector(50, 30), Vector(60, 20))

        tris = Face(edge, [hole0, hole1, hole2]).triangulate()
        segs = (
            edge.toSegments(True)
            + hole0.toSegments(True)
            + hole1.toSegments(True)
            + hole2.toSegments(True))
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 16)
        self.assertAlmostEqual(area, 2300)
        self.assertIsNone(findTriangulationProblems(tris, segs))

    def test_triangulate_collinearDiagonalHoles(self):
        # Data based on fixed bug
        #                    3
        #                    |
        #              .3    |
        #            2'      |
        # 0      .3   \  .0  2
        #  \   2'      1' .-'
        #   \   \  .0  .-'
        #    \   1' .-'
        #     \  .-'
        #      1'

        edge = Edge(
            Vector(10, -83),
            Vector(28, -137),
            Vector(129, -114),
            Vector(131, -55))
        hole0 = Edge(
            Vector(85.940795579, -103.214712478),
            Vector(72.494488685, -106.319037028),
            Vector(69.390164135, -92.872730134),
            Vector(82.836471029, -89.768405584))
        hole1 = Edge(
            Vector(104.453826809, -98.940642445),
            Vector(91.007519915, -102.044966995),
            Vector(87.903195366, -88.598660101),
            Vector(101.349502260, -85.494335551))

        tris = Face(edge, [hole0, hole1]).triangulate()
        segs = edge.toSegments(True) + hole0.toSegments(True) + hole1.toSegments(True)
        area = sum(t.area() for t in tris)
        self.assertEqual(len(tris), 14)
        self.assertAlmostEqual(area, 6094.62)
        self.assertIsNone(findTriangulationProblems(tris, segs))
