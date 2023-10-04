import unittest

from math import pi as PI

from ..matrix import Matrix
from ..vector import Vector


MAT_ZERO = Matrix((0,)*16)
MAT_EVEN = Matrix(tuple(range(2, 33, 2)))
MAT_ODD = Matrix(tuple(range(1, 32, 2)))


class MatrixTest(unittest.TestCase):

    def test_fromAlignment(self):
        a = Vector(1, 9, 2).normalized()
        b = Vector(3, 8, 7).normalized()
        matrix = Matrix.fromAlignment(a, a)
        self.assertTrue(a.transformed(matrix).isClose(a))
        matrix = Matrix.fromAlignment(a, b)
        self.assertTrue(a.transformed(matrix).isClose(b))

    def test_add(self):
        expected = tuple(a+b for a, b in zip(MAT_ODD.data, MAT_EVEN.data))
        self.assertEqual((MAT_ODD + MAT_ZERO).data, MAT_ODD.data)
        self.assertEqual((MAT_ODD + MAT_EVEN).data, expected)

    def test_sub(self):
        expected = (-1,)*16
        self.assertEqual((MAT_ODD - MAT_ZERO).data, MAT_ODD.data)
        self.assertEqual((MAT_ODD - MAT_EVEN).data, expected)

    def test_mulScalar(self):
        expected = tuple(n*2 for n in MAT_ODD.data)
        self.assertEqual((MAT_ODD * 0).data, MAT_ZERO.data)
        self.assertEqual((MAT_ODD * 2).data, expected)

    def test_mulMatrix(self):
        oddMulEven = (
            304, 336, 368, 400,
            752, 848, 944, 1040,
            1200, 1360, 1520, 1680,
            1648, 1872, 2096, 2320)
        self.assertEqual((Matrix() * Matrix()).data, Matrix().data)
        self.assertEqual((MAT_ODD * MAT_ZERO).data, MAT_ZERO.data)
        self.assertEqual((MAT_ODD * MAT_EVEN).data, oddMulEven)

    def test_mirroredX(self):
        matrix = Matrix().mirroredX()
        self.assertEqual(Vector(1, 2, 3).transformed(matrix), Vector(-1, 2, 3))

    def test_mirroredY(self):
        matrix = Matrix().mirroredY()
        self.assertEqual(Vector(1, 2, 3).transformed(matrix), Vector(1, -2, 3))

    def test_mirroredZ(self):
        matrix = Matrix().mirroredZ()
        self.assertEqual(Vector(1, 2, 3).transformed(matrix), Vector(1, 2, -3))

    def test_rotatedX(self):
        matrix = Matrix().rotatedX(0)
        vector = Vector(1, 2, 3).transformed(matrix)
        self.assertEqual(vector, Vector(1, 2, 3))

        matrix = Matrix().rotatedX(PI/2, Vector(1, 2, 3))
        vector = Vector(1, 2, 3).transformed(matrix)
        self.assertAlmostEqual(vector.x, 1)
        self.assertAlmostEqual(vector.y, 2)
        self.assertAlmostEqual(vector.z, 3)

        vector = Vector(2, 3, 4).transformed(matrix)
        self.assertAlmostEqual(vector.x, 2)
        self.assertAlmostEqual(vector.y, 1)
        self.assertAlmostEqual(vector.z, 4)

    def test_rotatedY(self):
        matrix = Matrix().rotatedY(0)
        vector = Vector(1, 2, 3).transformed(matrix)
        self.assertEqual(vector, Vector(1, 2, 3))

        matrix = Matrix().rotatedY(PI/2, Vector(1, 2, 3))
        vector = Vector(1, 2, 3).transformed(matrix)
        self.assertAlmostEqual(vector.x, 1)
        self.assertAlmostEqual(vector.y, 2)
        self.assertAlmostEqual(vector.z, 3)

        vector = Vector(2, 3, 4).transformed(matrix)
        self.assertAlmostEqual(vector.x, 2)
        self.assertAlmostEqual(vector.y, 3)
        self.assertAlmostEqual(vector.z, 2)

    def test_rotatedZ(self):
        matrix = Matrix().rotatedZ(0)
        vector = Vector(1, 2, 3).transformed(matrix)
        self.assertEqual(vector, Vector(1, 2, 3))

        matrix = Matrix().rotatedZ(PI/2, Vector(1, 2, 3))
        vector = Vector(1, 2, 3).transformed(matrix)
        self.assertAlmostEqual(vector.x, 1)
        self.assertAlmostEqual(vector.y, 2)
        self.assertAlmostEqual(vector.z, 3)

        vector = Vector(2, 3, 4).transformed(matrix)
        self.assertAlmostEqual(vector.x, 0)
        self.assertAlmostEqual(vector.y, 3)
        self.assertAlmostEqual(vector.z, 4)

    def test_translated(self):
        matrix = Matrix().translated(Vector(1, 2, 3))
        self.assertEqual(Vector(1, 2, 3).transformed(matrix), Vector(2, 4, 6))
