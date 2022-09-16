import math

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Matrix
from chrumm.geo import Vector

from .arc import arc2D


class Encoder:
    """Construct an EC11/12 rotary encoder hole."""

    def __init__(self, pos, roofPlaneI, roofPlaneO):
        self.triangles = []
        self.roofEdgeI = Edge()
        self.roofEdgeO = Edge()
        self.splitEdgeF = Edge()
        self.splitEdgeB = Edge()

        width = cfg.encoder.width
        depth = cfg.encoder.depth
        holeRadius = cfg.encoder.holeDiameter/2
        holeHeight = cfg.encoder.holeHeight
        holeChamfer = cfg.encoder.holeChamfer

        # Edges

        holeArc = arc2D(holeRadius, math.tau/4, -math.pi)
        holeEdgeT = holeArc.scaled(1 + holeChamfer/holeRadius)
        holeEdgeC = holeArc.translated(Vector(0, 0, -holeChamfer))
        holeEdgeG = holeArc.translated(Vector(0, 0, -holeHeight))

        boxEdgeT = Edge(
            Vector(0, depth/2, -holeHeight),
            Vector(width/2, depth/2, -holeHeight))

        if cfg.encoder.pinNotch:
            notchWidth = cfg.encoder.pinNotch.width
            notchDepth = cfg.encoder.pinNotch.depth
            notchAngle = cfg.encoder.pinNotch.taperAngle
            notchInset = notchDepth / math.cos(notchAngle) * math.sin(notchAngle)

            # The notches are added to the shorter sides, which
            # is the expected pin location of EC11/12 encoders.
            if width <= depth:
                # o-o notch
                #    \
                #     o-o box
                # y     |
                # zx    |

                boxEdgeT = Edge(
                    Vector(0, depth/2 + notchDepth, -holeHeight),
                    Vector(notchWidth/2 - notchInset, depth/2 + notchDepth, -holeHeight),
                    Vector(notchWidth/2, depth/2, -holeHeight),
                    Vector(width/2, depth/2, -holeHeight))
            else:
                # o--o box
                #    |
                #    o.
                # y    'o notch
                # zx    |

                boxEdgeT = Edge(
                    Vector(0, depth/2, -holeHeight),
                    Vector(width/2, depth/2, -holeHeight),
                    Vector(width/2, notchWidth/2, -holeHeight),
                    Vector(width/2 + notchDepth, notchWidth/2 - notchInset, -holeHeight))

        boxEdgeT.add(boxEdgeT.mirroredY().reversed())

        # Align edges to the reference planes

        align = Matrix.fromAlignment(Vector(0, 0, 1), roofPlaneO.normal).translated(pos)

        holeEdgeT = holeEdgeT.transformed(align)
        holeEdgeC = holeEdgeC.transformed(align)
        holeEdgeG = holeEdgeG.transformed(align)

        boxEdgeT = boxEdgeT.transformed(align)
        boxEdgeG = Edge(roofPlaneI.intersect(Line(p, roofPlaneO.normal)) for p in boxEdgeT)

        # Edges and triangles

        edges = [boxEdgeG, boxEdgeT, holeEdgeG, holeEdgeC, holeEdgeT]

        self.splitEdgeF.add(e[-1] for e in reversed(edges))
        self.splitEdgeB.add(e[0] for e in edges)
        self.roofEdgeI.add(boxEdgeG.reversed())
        self.roofEdgeO.add(holeEdgeT)

        self.triangles.extend(holeEdgeG.meshPairwise(holeEdgeC))
        self.triangles.extend(holeEdgeC.meshPairwise(holeEdgeT))
        self.triangles.extend(boxEdgeG.meshPairwise(boxEdgeT))
        self.triangles.extend(Face(boxEdgeT + holeEdgeG.reversed()).triangulate())
