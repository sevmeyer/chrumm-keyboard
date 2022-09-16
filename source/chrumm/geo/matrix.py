import math


class Matrix:

    __slots__ = "data"

    def __init__(self, data=(
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0)):
        self.data = data

    @staticmethod
    def fromAlignment(sourceDir, targetDir):
        """Return a rotation matrix that aligns the source to the target vector."""
        # Calculate Rotation Matrix to align Vector A to Vector B - Jur van den Berg
        # https://math.stackexchange.com/a/476311
        sourceDir = sourceDir.normalized()
        targetDir = targetDir.normalized()

        if sourceDir.isClose(targetDir):
            return Matrix()
        if sourceDir.isClose(-targetDir):
            return Matrix().mirroredX()

        c = sourceDir.cross(targetDir)
        d = sourceDir.dot(targetDir)
        skew = Matrix((
            0.0,  c.z, -c.y, 0.0,
            -c.z, 0.0,  c.x, 0.0,
            c.y, -c.x,  0.0, 0.0,
            0.0,  0.0,  0.0, 0.0))
        return Matrix() + skew + skew*skew*(1 / (1 + d))

    def __add__(self, other):
        return Matrix(tuple(a + b for a, b in zip(self.data, other.data)))

    def __sub__(self, other):
        return Matrix(tuple(a - b for a, b in zip(self.data, other.data)))

    def __mul__(self, other):
        if not isinstance(other, Matrix):
            return Matrix(tuple(a * other for a in self.data))

        # https://en.wikipedia.org/wiki/Matrix_multiplication
        s = self.data
        o = other.data
        return Matrix((
            s[0]*o[0] + s[1]*o[4] + s[2]*o[8] + s[3]*o[12],
            s[0]*o[1] + s[1]*o[5] + s[2]*o[9] + s[3]*o[13],
            s[0]*o[2] + s[1]*o[6] + s[2]*o[10] + s[3]*o[14],
            s[0]*o[3] + s[1]*o[7] + s[2]*o[11] + s[3]*o[15],
            s[4]*o[0] + s[5]*o[4] + s[6]*o[8] + s[7]*o[12],
            s[4]*o[1] + s[5]*o[5] + s[6]*o[9] + s[7]*o[13],
            s[4]*o[2] + s[5]*o[6] + s[6]*o[10] + s[7]*o[14],
            s[4]*o[3] + s[5]*o[7] + s[6]*o[11] + s[7]*o[15],
            s[8]*o[0] + s[9]*o[4] + s[10]*o[8] + s[11]*o[12],
            s[8]*o[1] + s[9]*o[5] + s[10]*o[9] + s[11]*o[13],
            s[8]*o[2] + s[9]*o[6] + s[10]*o[10] + s[11]*o[14],
            s[8]*o[3] + s[9]*o[7] + s[10]*o[11] + s[11]*o[15],
            s[12]*o[0] + s[13]*o[4] + s[14]*o[8] + s[15]*o[12],
            s[12]*o[1] + s[13]*o[5] + s[14]*o[9] + s[15]*o[13],
            s[12]*o[2] + s[13]*o[6] + s[14]*o[10] + s[15]*o[14],
            s[12]*o[3] + s[13]*o[7] + s[14]*o[11] + s[15]*o[15]))

    def mirroredX(self):
        return self * Matrix((
            -1.0, 0.0, 0.0, 0.0,
            0.0,  1.0, 0.0, 0.0,
            0.0,  0.0, 1.0, 0.0,
            0.0,  0.0, 0.0, 1.0))

    def mirroredY(self):
        return self * Matrix((
            1.0,  0.0, 0.0, 0.0,
            0.0, -1.0, 0.0, 0.0,
            0.0,  0.0, 1.0, 0.0,
            0.0,  0.0, 0.0, 1.0))

    def mirroredZ(self):
        return self * Matrix((
            1.0, 0.0,  0.0, 0.0,
            0.0, 1.0,  0.0, 0.0,
            0.0, 0.0, -1.0, 0.0,
            0.0, 0.0,  0.0, 1.0))

    def rotatedX(self, angle, center=None):
        # https://en.wikipedia.org/wiki/Rotation_matrix
        cos = math.cos(angle)
        sin = math.sin(angle)
        rotation = Matrix((
            1.0,  0.0, 0.0, 0.0,
            0.0,  cos, sin, 0.0,
            0.0, -sin, cos, 0.0,
            0.0,  0.0, 0.0, 1.0))
        if center is None:
            return self * rotation
        return self.translated(-center).__mul__(rotation).translated(center)

    def rotatedY(self, angle, center=None):
        # https://en.wikipedia.org/wiki/Rotation_matrix
        cos = math.cos(angle)
        sin = math.sin(angle)
        rotation = Matrix((
            cos, 0.0, -sin, 0.0,
            0.0, 1.0,  0.0, 0.0,
            sin, 0.0,  cos, 0.0,
            0.0, 0.0,  0.0, 1.0))
        if center is None:
            return self * rotation
        return self.translated(-center).__mul__(rotation).translated(center)

    def rotatedZ(self, angle, center=None):
        # https://en.wikipedia.org/wiki/Rotation_matrix
        cos = math.cos(angle)
        sin = math.sin(angle)
        rotation = Matrix((
            cos,  sin, 0.0, 0.0,
            -sin, cos, 0.0, 0.0,
            0.0,  0.0, 1.0, 0.0,
            0.0,  0.0, 0.0, 1.0))
        if center is None:
            return self * rotation
        return self.translated(-center).__mul__(rotation).translated(center)

    def translated(self, vector):
        return self * Matrix((
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            vector.x, vector.y, vector.z, 1.0))
