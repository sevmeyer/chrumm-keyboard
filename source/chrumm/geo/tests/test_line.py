import unittest

from ..line import Line
from ..matrix import Matrix
from ..vector import Vector


LINE = Line(Vector(1, 2, 3), Vector(1, 1, 1))


class LineTest(unittest.TestCase):

    def test_translated(self):
        line = LINE.translated(Vector())
        self.assertEqual(line.pos, LINE.pos)
        self.assertEqual(line.dir, LINE.dir)

        line = LINE.translated(Vector(4, 5, 6))
        self.assertEqual(line.pos, Vector(5, 7, 9))
        self.assertEqual(line.dir, LINE.dir)

    def test_transformed(self):
        line = LINE.transformed(Matrix())
        self.assertEqual(line.pos, LINE.pos)
        self.assertEqual(line.dir, LINE.dir)

        line = LINE.transformed(Matrix().mirroredX())
        self.assertEqual(line.pos, LINE.pos.mirroredX())
        self.assertEqual(line.dir, LINE.dir.mirroredX())

    def test_distance(self):
        line = Line(Vector(1, 2, 3), Vector(1, 0, 0))
        self.assertEqual(line.distance(Vector(1, 2, 3)), 0)
        self.assertEqual(line.distance(Vector(1, 1, 3)), 1)
        self.assertEqual(line.distance(Vector(1, 3, 3)), 1)
        self.assertEqual(line.distance(Vector(1, 2, 1)), 2)
        self.assertEqual(line.distance(Vector(1, 2, 5)), 2)

    def test_distance2D(self):
        self.assertEqual(LINE.distance2D(Vector(1, 2, 1)), 0)
        self.assertAlmostEqual(LINE.distance2D(Vector(3, 2, 1)), 2**0.5)
        self.assertAlmostEqual(LINE.distance2D(Vector(1, 4, 1)), -2**0.5)

    def test_intersect(self):
        with self.assertRaises(ZeroDivisionError):
            lineX = Line(Vector(), Vector(1, 0, 0))
            lineX.intersect(lineX)

        lineX = Line(Vector(), Vector(1, 0, 0))
        lineY = Line(Vector(), Vector(0, 1, 0))
        self.assertEqual(lineX.intersect(lineY), Vector())

        lineX = Line(Vector(0, 2, 2), Vector(1, 0, 1))
        lineY = Line(Vector(1, 1, 3), Vector(0, 1, 0))
        self.assertEqual(lineX.intersect(lineY), Vector(1, 2, 3))

        # Skew
        lineX = Line(Vector(0, 0, 0), Vector(1, 0, 0))
        lineY = Line(Vector(0, 0, 2), Vector(0, 1, 0))
        self.assertEqual(lineX.intersect(lineY), Vector(0, 0, 1))
