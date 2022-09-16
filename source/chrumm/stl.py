import io
import struct


def encode(triangles):
    """Encode a list of triangles in the binary STL format."""
    # https://en.wikipedia.org/wiki/STL_(file_format)

    header = b" Made for fellow tinkerers. https://github.com/sevmeyer/chrumm-keyboard "

    with io.BytesIO() as stream:
        stream.write(header.rjust(80, b"\0"))
        stream.write(struct.pack("<I", len(triangles)))

        for triangle in triangles:
            triangle = triangle.snapped()
            for vector in triangle.normal(), triangle.a, triangle.b, triangle.c:
                stream.write(struct.pack("<3f", vector.x, vector.y, vector.z))
            stream.write(b"\0\0")

        return stream.getvalue()
