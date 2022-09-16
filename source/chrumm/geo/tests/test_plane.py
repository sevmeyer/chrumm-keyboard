import unittest

from ..line import Line
from ..matrix import Matrix
from ..plane import Plane
from ..vector import Vector


PLANE = Plane(Vector(1, 2, 3), Vector(1, 1, 1))


class PlaneTest(unittest.TestCase):

    def test_fromPoints(self):
        a = Vector(1, 2, 4)
        b = Vector(1, 2, 3)
        c = Vector(2, 3, 3)
        plane = Plane.fromPoints(a, b, c)
        self.assertEqual(plane.pos, b)
        self.assertEqual(plane.normal, Vector(1, -1, 0).normalized())

    def test_fromLine2D(self):
        line = Line(Vector(1, 2, 3), Vector(1, 1, 1))
        plane = Plane.fromLine2D(line)
        self.assertEqual(plane.pos, Vector(1, 2, 0))
        self.assertTrue(plane.normal.isClose(Vector(-1, 1).normalized()))

    def test_translated(self):
        plane = PLANE.translated(Vector())
        self.assertEqual(plane.pos, PLANE.pos)
        self.assertEqual(plane.normal, PLANE.normal)

        plane = PLANE.translated(Vector(4, 5, 6))
        self.assertEqual(plane.pos, Vector(5, 7, 9))
        self.assertEqual(plane.normal, PLANE.normal)

    def test_transformed(self):
        plane = PLANE.transformed(Matrix())
        self.assertEqual(plane.pos, PLANE.pos)
        self.assertEqual(plane.normal, PLANE.normal)

        plane = PLANE.transformed(Matrix().mirroredX())
        self.assertEqual(plane.pos, PLANE.pos.mirroredX())
        self.assertEqual(plane.normal, PLANE.normal.mirroredX())

    def test_distance(self):
        plane = Plane(Vector(1, 2, 3), Vector(0, 0, 1))
        self.assertEqual(plane.distance(Vector(0, 0, 3)), 0)
        self.assertEqual(plane.distance(Vector(4, 5, 6)), 3)
        self.assertEqual(plane.distance(Vector(-4, -5, -6)), -9)

    def test_projectNormal(self):
        self.assertTrue(PLANE.projectNormal(Vector(0, 1, 2)).isClose(PLANE.pos))
        self.assertTrue(PLANE.projectNormal(Vector(4, 5, 6)).isClose(PLANE.pos))

    def test_projectX(self):
        plane = Plane(Vector(2, 3, 4), Vector(1, 0, 0))
        self.assertEqual(plane.projectX(Vector(1, 1, 1)), Vector(2, 1, 1))

        plane = Plane(Vector(4, 2, 2), Vector(1, 1, 1))
        self.assertEqual(plane.projectX(Vector(1, 1, 1)), Vector(6, 1, 1))

        plane = Plane(Vector(2, 3, 4), Vector(0, 1, 0))
        with self.assertRaises(ZeroDivisionError):
            plane.projectX(Vector(1, 1, 1))

    def test_projectY(self):
        plane = Plane(Vector(2, 3, 4), Vector(0, 1, 0))
        self.assertEqual(plane.projectY(Vector(1, 1, 1)), Vector(1, 3, 1))

        plane = Plane(Vector(2, 4, 2), Vector(1, 1, 1))
        self.assertEqual(plane.projectY(Vector(1, 1, 1)), Vector(1, 6, 1))

        plane = Plane(Vector(2, 3, 4), Vector(0, 0, 1))
        with self.assertRaises(ZeroDivisionError):
            plane.projectY(Vector(1, 1, 1))

    def test_projectZ(self):
        plane = Plane(Vector(2, 3, 4), Vector(0, 0, 1))
        self.assertEqual(plane.projectZ(Vector(1, 1, 1)), Vector(1, 1, 4))

        plane = Plane(Vector(2, 2, 4), Vector(1, 1, 1))
        self.assertEqual(plane.projectZ(Vector(1, 1, 1)), Vector(1, 1, 6))

        plane = Plane(Vector(2, 3, 4), Vector(1, 0, 0))
        with self.assertRaises(ZeroDivisionError):
            plane.projectZ(Vector(1, 1, 1))

    def test_intersectPlanes(self):
        planeX = Plane(Vector(1, 0, 0), Vector(1, 0, 0))
        planeY = Plane(Vector(0, 2, 0), Vector(0, 1, 0))
        planeZ = Plane(Vector(0, 0, 3), Vector(0, 0, 1))
        self.assertEqual(planeX.intersect(planeY, planeZ), Vector(1, 2, 3))
        with self.assertRaises(ZeroDivisionError):
            planeX.intersect(planeX, planeY)

    def test_intersectLine(self):
        line = Line(Vector(2, 3, 4), Vector(1, 1, 1))
        self.assertEqual(PLANE.intersect(line), Vector(1, 2, 3))

        line = Line(Vector(2, 3, 4), Vector(1, -1, 0))
        with self.assertRaises(ZeroDivisionError):
            PLANE.intersect(line)
