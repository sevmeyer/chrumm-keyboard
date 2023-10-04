import unittest

from ..matrix import Matrix
from ..triangle import Triangle
from ..vector import Vector


TRI_ZERO = Triangle(Vector(0, 0, 0), Vector(0, 0, 0), Vector(0, 0, 0))
TRI_AXIS = Triangle(Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1))
TRI_DIAG = Triangle(Vector(1, 2, 3), Vector(6, 5, 4), Vector(7, 8, 9))


class TriangleTest(unittest.TestCase):

    def test_bool(self):
        tri = Triangle(
            Vector(1, 0, 0),
            Vector(2, 0, 0),
            Vector(3, 0, 0))
        self.assertFalse(tri)
        self.assertFalse(TRI_ZERO)
        self.assertTrue(TRI_AXIS)

    def test_mirroredX(self):
        tri = TRI_DIAG.mirroredX()
        self.assertEqual(tri.a, Vector(-1, 2, 3))
        self.assertEqual(tri.b, Vector(-6, 5, 4))
        self.assertEqual(tri.c, Vector(-7, 8, 9))

    def test_mirroredY(self):
        tri = TRI_DIAG.mirroredY()
        self.assertEqual(tri.a, Vector(1, -2, 3))
        self.assertEqual(tri.b, Vector(6, -5, 4))
        self.assertEqual(tri.c, Vector(7, -8, 9))

    def test_mirroredZ(self):
        tri = TRI_DIAG.mirroredZ()
        self.assertEqual(tri.a, Vector(1, 2, -3))
        self.assertEqual(tri.b, Vector(6, 5, -4))
        self.assertEqual(tri.c, Vector(7, 8, -9))

    def test_reversed(self):
        tri = TRI_AXIS.reversed()
        self.assertEqual(tri.c, TRI_AXIS.a)
        self.assertEqual(tri.b, TRI_AXIS.b)
        self.assertEqual(tri.a, TRI_AXIS.c)

    def test_translated(self):
        tri = TRI_DIAG.translated(Vector())
        self.assertEqual(tri.a, TRI_DIAG.a)
        self.assertEqual(tri.b, TRI_DIAG.b)
        self.assertEqual(tri.c, TRI_DIAG.c)

        tri = TRI_DIAG.translated(Vector(10, 20, 30))
        self.assertEqual(tri.a, Vector(11, 22, 33))
        self.assertEqual(tri.b, Vector(16, 25, 34))
        self.assertEqual(tri.c, Vector(17, 28, 39))

    def test_transformed(self):
        matrix = Matrix().translated(Vector(10, 20, 30))
        tri = TRI_DIAG.transformed(matrix)
        self.assertEqual(tri.a, Vector(11, 22, 33))
        self.assertEqual(tri.b, Vector(16, 25, 34))
        self.assertEqual(tri.c, Vector(17, 28, 39))

    def test_area(self):
        tri = Triangle(
            Vector(0, 0, 0),
            Vector(3, 0, 0),
            Vector(0, 4, 0))
        self.assertEqual(tri.area(), 6)
        self.assertEqual(TRI_ZERO.area(), 0)
        self.assertAlmostEqual(TRI_AXIS.area(), 3**0.5 / 2)

    def test_circumradius(self):
        self.assertEqual(TRI_ZERO.circumradius(), 0)
        self.assertAlmostEqual(TRI_AXIS.circumradius(), 2**0.5 / 3**0.5)
        self.assertAlmostEqual(TRI_DIAG.circumradius(), 27**0.5 * 35 / 864**0.5)

    def test_normal(self):
        with self.assertRaises(ZeroDivisionError):
            TRI_ZERO.normal()

        tri = Triangle(
            Vector(0, 0, 0),
            Vector(0, 2, 0),
            Vector(0, 0, 2))
        self.assertEqual(tri.normal(), Vector(1, 0, 0))

        tri = Triangle(
            Vector(0, 0, 0),
            Vector(0, 0, 2),
            Vector(0, 2, 0))
        self.assertEqual(tri.normal(), Vector(-1, 0, 0))

        tri = Triangle(
            Vector(0, 0, 0),
            Vector(0, 0, 3),
            Vector(3, 0, 0))
        self.assertEqual(tri.normal(), Vector(0, 1, 0))

        tri = Triangle(
            Vector(0, 0, 0),
            Vector(3, 0, 0),
            Vector(0, 0, 3))
        self.assertEqual(tri.normal(), Vector(0, -1, 0))

        tri = Triangle(
            Vector(0, 0, 0),
            Vector(4, 0, 0),
            Vector(0, 4, 0))
        self.assertEqual(tri.normal(), Vector(0, 0, 1))

        tri = Triangle(
            Vector(0, 0, 0),
            Vector(0, 4, 0),
            Vector(4, 0, 0))
        self.assertEqual(tri.normal(), Vector(0, 0, -1))
