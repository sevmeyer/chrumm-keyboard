from .epsilon import isZero


class Triangle:

    __slots__ = "a", "b", "c"

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def __bool__(self):
        return not isZero(self.area())

    def mirroredX(self):
        return Triangle(
            self.a.mirroredX(),
            self.b.mirroredX(),
            self.c.mirroredX())

    def mirroredY(self):
        return Triangle(
            self.a.mirroredY(),
            self.b.mirroredY(),
            self.c.mirroredY())

    def mirroredZ(self):
        return Triangle(
            self.a.mirroredZ(),
            self.b.mirroredZ(),
            self.c.mirroredZ())

    def reversed(self):
        return Triangle(self.c, self.b, self.a)

    def translated(self, vector):
        return Triangle(
            self.a + vector,
            self.b + vector,
            self.c + vector)

    def transformed(self, matrix):
        return Triangle(
            self.a.transformed(matrix),
            self.b.transformed(matrix),
            self.c.transformed(matrix))

    def snapped(self):
        return Triangle(
            self.a.snapped(),
            self.b.snapped(),
            self.c.snapped())

    def area(self):
        # https://en.wikipedia.org/wiki/Triangle#Using_vectors
        ab = self.b - self.a
        ac = self.c - self.a
        return ab.cross(ac).magnitude() / 2

    def circumradius(self):
        # https://en.wikipedia.org/wiki/Circumcenter#Higher_dimensions
        ca = self.a - self.c
        cb = self.b - self.c
        numer = ca.magnitude() * cb.magnitude() * (ca - cb).magnitude()
        denom = 2 * ca.cross(cb).magnitude()
        return 0 if isZero(denom) else numer/denom

    def normal(self):
        ab = self.b - self.a
        ac = self.c - self.a
        return ab.cross(ac).normalized()
