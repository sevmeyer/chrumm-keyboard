import unittest

from math import pi as PI

from ..matrix import Matrix
from ..vector import Vector


# Based on considerations in chrumm.geo.epsilon
EPS_NONZERO = 1e-5
EPS_ZERO = 1e-7

MAT_ZERO = Matrix((0,)*16)
MAT_DIAG = Matrix(tuple(range(1, 17)))


class VectorTest(unittest.TestCase):

    def test_init(self):
        self.assertEqual(Vector(), Vector(0, 0, 0))
        self.assertEqual(Vector(1), Vector(1, 0, 0))
        self.assertEqual(Vector(1, 2), Vector(1, 2, 0))
        self.assertEqual(Vector(1, 2, 3), Vector(1, 2, 3))

    def test_fromSurfaceNormal(self):
        with self.assertRaises(ZeroDivisionError):
            Vector.fromSurfaceNormal([])
        with self.assertRaises(ZeroDivisionError):
            Vector.fromSurfaceNormal([Vector()])
        with self.assertRaises(ZeroDivisionError):
            Vector.fromSurfaceNormal([Vector(), Vector(1, 2, 3)])
        with self.assertRaises(ZeroDivisionError):
            Vector.fromSurfaceNormal([Vector(), Vector(1, 1, 1), Vector(2, 2, 2)])

        vectors = [Vector(0, 0, 0), Vector(1, 0, 0), Vector(0, 1, 0)]
        self.assertEqual(Vector.fromSurfaceNormal(vectors), Vector(0, 0, 1))

        vectors = [Vector(0, 0, 0), Vector(0, 1, 0), Vector(1, 0, 0)]
        self.assertEqual(Vector.fromSurfaceNormal(vectors), Vector(0, 0, -1))

        vectors = [Vector(1, 2, 3), Vector(2, 3, 4), Vector(1, 2, 5)]
        normal = Vector.fromSurfaceNormal(vectors)
        self.assertAlmostEqual(normal.x, 0.5**0.5)
        self.assertAlmostEqual(normal.y, -0.5**0.5)
        self.assertEqual(normal.z, 0)

        vectors = [Vector(1, 2, 3), Vector(1, 2, 5), Vector(2, 3, 4)]
        normal = Vector.fromSurfaceNormal(vectors)
        self.assertAlmostEqual(normal.x, -0.5**0.5)
        self.assertAlmostEqual(normal.y, 0.5**0.5)
        self.assertEqual(normal.z, 0)

    def test_eq(self):
        self.assertTrue(Vector(1, 2, 3) == Vector(1, 2, 3))
        self.assertFalse(Vector(1, 1, 1) == Vector(0, 1, 1))
        self.assertFalse(Vector(1, 1, 1) == Vector(1, 0, 1))
        self.assertFalse(Vector(1, 1, 1) == Vector(1, 1, 0))

    def test_lt(self):
        self.assertTrue(Vector(1, 3, 3) < Vector(2, 2, 2))
        self.assertTrue(Vector(1, 1, 3) < Vector(1, 2, 2))
        self.assertTrue(Vector(1, 1, 1) < Vector(1, 1, 2))
        self.assertFalse(Vector(2, 2, 2) < Vector(1, 3, 3))
        self.assertFalse(Vector(1, 2, 2) < Vector(1, 1, 3))
        self.assertFalse(Vector(1, 1, 2) < Vector(1, 1, 1))

    def test_neg(self):
        self.assertEqual(-Vector(), Vector())
        self.assertEqual(-Vector(1, 2, 3), Vector(-1, -2, -3))

    def test_add(self):
        self.assertEqual(Vector(1, 2, 3) + Vector(), Vector(1, 2, 3))
        self.assertEqual(Vector(1, 2, 3) + Vector(4, 5, 6), Vector(5, 7, 9))

    def test_sub(self):
        self.assertEqual(Vector(1, 2, 3) - Vector(), Vector(1, 2, 3))
        self.assertEqual(Vector(1, 2, 3) - Vector(4, 5, 6), Vector(-3, -3, -3))

    def test_mul(self):
        self.assertEqual(Vector(1, 2, 3) * 0, Vector(0, 0, 0))
        self.assertEqual(Vector(1, 2, 3) * 0.5, Vector(0.5, 1, 1.5))
        self.assertEqual(Vector(1, 2, 3) * 2, Vector(2, 4, 6))
        self.assertEqual(Vector(1, 2, 3) * -2, Vector(-2, -4, -6))

    def test_truediv(self):
        with self.assertRaises(ZeroDivisionError):
            Vector(1, 2, 3) / 0
        self.assertEqual(Vector(1, 2, 3) / 0.5, Vector(2, 4, 6))
        self.assertEqual(Vector(1, 2, 3) / 1, Vector(1, 2, 3))
        self.assertEqual(Vector(1, 2, 3) / 2, Vector(0.5, 1, 1.5))
        self.assertEqual(Vector(1, 2, 3) / -2, Vector(-0.5, -1, -1.5))

    def test_transformed(self):
        self.assertEqual(Vector(1, 2, 3).transformed(Matrix()), Vector(1, 2, 3))
        self.assertEqual(Vector(1, 2, 3).transformed(MAT_ZERO), Vector())
        self.assertEqual(Vector(1, 2, 3).transformed(MAT_DIAG), Vector(51, 58, 65))

    def test_transformedNormal(self):
        with self.assertRaises(ZeroDivisionError):
            Vector(1, 2, 3).transformedNormal(MAT_ZERO)

        vector = Vector(2, 3, 6).transformedNormal(Matrix())
        self.assertAlmostEqual(vector.x, 2 / 7)
        self.assertAlmostEqual(vector.y, 3 / 7)
        self.assertAlmostEqual(vector.z, 6 / 7)

        vector = Vector(1, 2, 3).transformedNormal(MAT_DIAG)
        self.assertAlmostEqual(vector.x, 38 / 5880**0.5)
        self.assertAlmostEqual(vector.y, 44 / 5880**0.5)
        self.assertAlmostEqual(vector.z, 50 / 5880**0.5)

    def test_snapped(self):
        self.assertEqual(Vector().snapped(), Vector())

        vector = Vector(EPS_NONZERO, -EPS_NONZERO, EPS_NONZERO)
        self.assertEqual(vector.snapped(), vector)

        vector = Vector(EPS_ZERO, -EPS_ZERO, EPS_ZERO)
        self.assertEqual(vector.snapped(), Vector(0, 0, 0))

    def test_normalized(self):
        with self.assertRaises(ZeroDivisionError):
            Vector().normalized()
        self.assertEqual(Vector(2, 3, 6).normalized(), Vector(2/7, 3/7, 6/7))

    def test_cross(self):
        self.assertEqual(Vector().cross(Vector()), Vector())
        self.assertEqual(Vector(1, 2, 3).cross(Vector()), Vector())
        self.assertEqual(Vector(1, 2, 3).cross(Vector(4, 5, 6)), Vector(-3, 6, -3))

    def test_dot(self):
        self.assertEqual(Vector().dot(Vector()), 0)
        self.assertEqual(Vector(1, 2, 3).dot(Vector()), 0)
        self.assertEqual(Vector(1, 2, 3).dot(Vector(4, 5, 6)), 32)

    def test_magnitude(self):
        self.assertEqual(Vector().magnitude(), 0)
        self.assertEqual(Vector(2, 3, 6).magnitude(), 7)

    def test_magSquared(self):
        self.assertEqual(Vector().magSquared(), 0)
        self.assertEqual(Vector(2, 3, 6).magSquared(), 49)

    def test_angleBetween(self):
        with self.assertRaises(ZeroDivisionError):
            Vector().angleBetween(Vector())

        start = Vector(1, 1, 0)
        self.assertAlmostEqual(start.angleBetween(start), 0)
        self.assertAlmostEqual(start.angleBetween(Vector(1, 1, 2**0.5)), PI*0.25)
        self.assertAlmostEqual(start.angleBetween(Vector(0, 0, 1)), PI*0.5)
        self.assertAlmostEqual(start.angleBetween(Vector(-1, -1, 2**0.5)), PI*0.75)
        self.assertAlmostEqual(start.angleBetween(Vector(-1, -1, 0)), PI)
        self.assertAlmostEqual(start.angleBetween(Vector(-1, -1, -2**0.5)), PI*0.75)
        self.assertAlmostEqual(start.angleBetween(Vector(0, 0, -1)), PI*0.5)
        self.assertAlmostEqual(start.angleBetween(Vector(1, 1, -2**0.5)), PI*0.25)

    def test_isClose(self):
        self.assertTrue(Vector().isClose(Vector()))

        eps = EPS_ZERO
        self.assertTrue(Vector(1, 20, 300).isClose(Vector(1+eps, 20, 300)))
        self.assertTrue(Vector(1, 20, 300).isClose(Vector(1, 20-eps, 300)))
        self.assertTrue(Vector(1, 20, 300).isClose(Vector(1, 20, 300+eps)))
        self.assertTrue(Vector(1, 20, 300).isClose(Vector(1-eps, 20+eps, 300-eps)))

        eps = EPS_NONZERO
        self.assertFalse(Vector(1, 20, 300).isClose(Vector(1+eps, 20, 300)))
        self.assertFalse(Vector(1, 20, 300).isClose(Vector(1, 20-eps, 300)))
        self.assertFalse(Vector(1, 20, 300).isClose(Vector(1, 20, 300+eps)))
        self.assertFalse(Vector(1, 20, 300).isClose(Vector(1-eps, 20+eps, 300-eps)))

    def test_ortho2D(self):
        self.assertEqual(Vector().ortho2D(), Vector())
        self.assertEqual(Vector(1, 2, 3).ortho2D(), Vector(-2, 1, 0))

    def test_normalized2D(self):
        with self.assertRaises(ZeroDivisionError):
            Vector().normalized2D()
        self.assertEqual(Vector(3, 4, 6).normalized2D(), Vector(3/5, 4/5, 0))

    def test_magnitude2D(self):
        self.assertEqual(Vector().magnitude2D(), 0)
        self.assertEqual(Vector(3, 4, 6).magnitude2D(), 5)

    def test_magSquared2D(self):
        self.assertEqual(Vector().magSquared2D(), 0)
        self.assertEqual(Vector(3, 4, 6).magSquared2D(), 25)

    def test_angle2D(self):
        self.assertAlmostEqual(Vector(1, 0, 0).angle2D(), 0)
        self.assertAlmostEqual(Vector(1, 1, 1).angle2D(), PI*0.25)
        self.assertAlmostEqual(Vector(0, 2, 2).angle2D(), PI*0.5)
        self.assertAlmostEqual(Vector(-3, 3, 3).angle2D(), PI*0.75)
        self.assertAlmostEqual(Vector(-4, 0, 4).angle2D(), PI)
        self.assertAlmostEqual(Vector(-5, -5, 5).angle2D(), -PI*0.75)
        self.assertAlmostEqual(Vector(0, -6, 6).angle2D(), -PI*0.5)
        self.assertAlmostEqual(Vector(7, -7, 7).angle2D(), -PI*0.25)
