import unittest

from ..segment import Segment
from ..vector import Vector


SEG_ZERO = Segment(Vector(0, 0, 0), Vector(0, 0, 0))
SEG_DIAG = Segment(Vector(1, 2, 3), Vector(3, 4, 5))


class SegmentTest(unittest.TestCase):

    def test_magnitude(self):
        self.assertEqual(SEG_ZERO.magnitude(), 0)
        self.assertAlmostEqual(SEG_DIAG.magnitude(), 12**0.5)

    def test_offset2D(self):
        seg = Segment(Vector(1, 2, 3), Vector(1, 3, 4))

        off = seg.offset2D(0)
        self.assertEqual(off.a, Vector(1, 2, 0))
        self.assertEqual(off.b, Vector(1, 3, 0))

        off = seg.offset2D(2)
        self.assertEqual(off.a, Vector(3, 2, 0))
        self.assertEqual(off.b, Vector(3, 3, 0))

        off = seg.offset2D(-2)
        self.assertEqual(off.a, Vector(-1, 2, 0))
        self.assertEqual(off.b, Vector(-1, 3, 0))

        with self.assertRaises(ZeroDivisionError):
            SEG_ZERO.offset2D(0)

    def test_magnitude2D(self):
        self.assertEqual(SEG_ZERO.magnitude2D(), 0)

        seg = Segment(Vector(1, 2, 3), Vector(1, 2, 5))
        self.assertEqual(seg.magnitude2D(), 0)

        seg = Segment(Vector(1, 2, 3), Vector(2, 3, 5))
        self.assertAlmostEqual(seg.magnitude2D(), 2**0.5)

        seg = Segment(Vector(2, 3, 5), Vector(1, 2, 3))
        self.assertAlmostEqual(seg.magnitude2D(), 2**0.5)

    def test_distance2D(self):
        self.assertEqual(SEG_ZERO.distance2D(Vector()), 0)
        self.assertAlmostEqual(SEG_ZERO.distance2D(Vector(1, 1, 1)), 2**0.5)

        # On segment except z
        self.assertEqual(SEG_DIAG.distance2D(Vector(1, 2, 1)), 0)
        self.assertEqual(SEG_DIAG.distance2D(Vector(2, 3, 1)), 0)
        self.assertEqual(SEG_DIAG.distance2D(Vector(3, 4, 1)), 0)

        # On segment
        self.assertEqual(SEG_DIAG.distance2D(Vector(1, 2, 3)), 0)
        self.assertEqual(SEG_DIAG.distance2D(Vector(2, 3, 4)), 0)
        self.assertEqual(SEG_DIAG.distance2D(Vector(3, 4, 5)), 0)

        # Extended
        self.assertEqual(SEG_DIAG.distance2D(Vector(0, 2, 3)), 1)
        self.assertEqual(SEG_DIAG.distance2D(Vector(1, 1, 3)), 1)
        self.assertEqual(SEG_DIAG.distance2D(Vector(4, 4, 5)), 1)
        self.assertEqual(SEG_DIAG.distance2D(Vector(3, 5, 5)), 1)

        self.assertAlmostEqual(SEG_DIAG.distance2D(Vector(0, 1, 2)), 2**0.5)
        self.assertAlmostEqual(SEG_DIAG.distance2D(Vector(4, 5, 6)), 2**0.5)

    def test_intersect2D(self):
        self.assertEqual(SEG_ZERO.intersect2D(SEG_ZERO), None)
        self.assertEqual(SEG_DIAG.intersect2D(SEG_ZERO), None)

        # Intersecting
        seg = Segment(Vector(3, 2, 1), Vector(1, 4, 3))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=0), Vector(2, 3, 0))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=1), Vector(2, 3, 0))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=2), Vector(2, 3, 0))

        # Touching ends
        seg = Segment(Vector(3, 4, 5), Vector(5, 2, 1))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=0), Vector(3, 4, 0))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=1), Vector(3, 4, 0))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=2), Vector(3, 4, 0))

        # Separate
        seg = Segment(Vector(3, 2, 1), Vector(5, 0, 4))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=0), None)
        self.assertEqual(seg.intersect2D(SEG_DIAG, asLine=1), None)
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=1), Vector(2, 3, 0))
        self.assertEqual(SEG_DIAG.intersect2D(seg, asLine=2), Vector(2, 3, 0))
