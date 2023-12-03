import math

from .epsilon import isZero


class Vector:

    __slots__ = "x", "y", "z"

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def fromSurfaceNormal(vectors):
        # Calculating a Surface Normal - Newell's Method
        # https://www.khronos.org/opengl/wiki/Calculating_a_Surface_Normal
        x, y, z = 0, 0, 0
        for i in range(len(vectors)):
            p = vectors[i]
            q = vectors[(i+1) % len(vectors)]
            x += (p.y - q.y) * (p.z + q.z)
            y += (p.z - q.z) * (p.x + q.x)
            z += (p.x - q.x) * (p.y + q.y)
        return Vector(x, y, z).normalized()

    def __repr__(self):
        x = f"{self.x:.6f}".rstrip("0").rstrip(".")
        y = f"{self.y:.6f}".rstrip("0").rstrip(".")
        z = f"{self.z:.6f}".rstrip("0").rstrip(".")
        return f"Vector({x}, {y}, {z})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __lt__(self, other):
        if self.x != other.x:
            return self.x < other.x
        if self.y != other.y:
            return self.y < other.y
        return self.z < other.z

    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Vector(self.x*scalar, self.y*scalar, self.z*scalar)

    def __truediv__(self, scalar):
        return Vector(self.x/scalar, self.y/scalar, self.z/scalar)

    @property
    def xy(self):
        return Vector(self.x, self.y, 0)

    @property
    def xz(self):
        return Vector(self.x, 0, self.z)

    @property
    def yz(self):
        return Vector(0, self.y, self.z)

    def mirroredX(self):
        return Vector(-self.x, self.y, self.z)

    def mirroredY(self):
        return Vector(self.x, -self.y, self.z)

    def mirroredZ(self):
        return Vector(self.x, self.y, -self.z)

    def translated(self, vector):
        return self + vector

    def transformed(self, matrix):
        m = matrix.data
        return Vector(
            self.x*m[0] + self.y*m[4] + self.z*m[8] + m[12],
            self.x*m[1] + self.y*m[5] + self.z*m[9] + m[13],
            self.x*m[2] + self.y*m[6] + self.z*m[10] + m[14])

    def transformedNormal(self, matrix):
        m = matrix.data
        return Vector(
            self.x*m[0] + self.y*m[4] + self.z*m[8],
            self.x*m[1] + self.y*m[5] + self.z*m[9],
            self.x*m[2] + self.y*m[6] + self.z*m[10]).normalized()

    def snapped(self):
        """Snap almost-zero coordinates to positive zero exactly."""
        return Vector(
            0 if isZero(self.x) else self.x,
            0 if isZero(self.y) else self.y,
            0 if isZero(self.z) else self.z)

    def normalized(self):
        return self / self.magnitude()

    def cross(self, other):
        return Vector(
            self.y*other.z - self.z*other.y,
            self.z*other.x - self.x*other.z,
            self.x*other.y - self.y*other.x)

    def dot(self, other):
        return self.x*other.x + self.y*other.y + self.z*other.z

    def magnitude(self):
        return (self.x*self.x + self.y*self.y + self.z*self.z)**0.5

    def magSquared(self):
        return self.x*self.x + self.y*self.y + self.z*self.z

    def angleBetween(self, other):
        """Return angle difference to other vector, between 0 and pi."""
        cos = self.normalized().dot(other.normalized())
        return math.acos(max(-1, min(cos, 1)))

    def isClose(self, other):
        return (
            isZero(self.x - other.x) and
            isZero(self.y - other.y) and
            isZero(self.z - other.z))

    def ortho2D(self):
        """Return counterclockwise orthogonal vector."""
        return Vector(-self.y, self.x)

    def normalized2D(self):
        # OPTIMIZED: Inline calculations to avoid function overhead
        magnitude = (self.x*self.x + self.y*self.y)**0.5
        return Vector(self.x/magnitude, self.y/magnitude)

    def magnitude2D(self):
        return (self.x*self.x + self.y*self.y)**0.5

    def magSquared2D(self):
        return self.x*self.x + self.y*self.y

    def angle2D(self):
        """Return angle difference to x axis, between -pi and pi."""
        return math.atan2(self.y, self.x)
