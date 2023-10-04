import unittest

from ..circle import Circle
from ..line import Line
from ..vector import Vector


CIRCLE_ZERO = Circle(Vector(0, 0, 0), 0)
CIRCLE_UNIT = Circle(Vector(0, 0, 0), 1)


class CircleTest(unittest.TestCase):

    def test_intersectLine2D(self):
        # Separate
        line = Line(Vector(0, 2, 3), Vector(1, 1, 1))
        points = CIRCLE_UNIT.intersect2D(line)
        self.assertEqual(len(points), 0)

        # Zero tangent
        line = Line(Vector(), Vector(1, 1, 1))
        points = CIRCLE_ZERO.intersect2D(line)
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0], Vector())

        # Tangent
        line = Line(Vector(1, 0, 4), Vector(0, 1, 2))
        points = CIRCLE_UNIT.intersect2D(line)
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0], Vector(1, 0, 0))

        # Intersection
        line = Line(Vector(), Vector(1, 1, 1))
        points = CIRCLE_UNIT.intersect2D(line)
        self.assertEqual(len(points), 2)
        self.assertTrue(points[0].isClose(Vector(-0.5**0.5, -0.5**0.5)))
        self.assertTrue(points[1].isClose(Vector(0.5**0.5, 0.5**0.5)))

    def test_intersectCircle2D(self):
        points = CIRCLE_ZERO.intersect2D(CIRCLE_ZERO)
        self.assertEqual(len(points), 0)

        # Inside
        circle = Circle(Vector(0, 0, 3), 2)
        points = CIRCLE_UNIT.intersect2D(circle)
        self.assertEqual(len(points), 0)

        # Separate
        circle = Circle(Vector(4, 4, 3), 2)
        points = CIRCLE_UNIT.intersect2D(circle)
        self.assertEqual(len(points), 0)

        # Tangent
        circle = Circle(Vector(4.5**0.5, 4.5**0.5, 3), 2)
        points = CIRCLE_UNIT.intersect2D(circle)
        self.assertEqual(len(points), 1)
        self.assertTrue(points[0].isClose(Vector(0.5**0.5, 0.5**0.5)))

        # Intersection
        circle = Circle(Vector(1, 1, 3), 1)
        points = CIRCLE_UNIT.intersect2D(circle)
        self.assertEqual(len(points), 2)
        self.assertTrue(points[0].isClose(Vector(0, 1, 0)))
        self.assertTrue(points[1].isClose(Vector(1, 0, 0)))
