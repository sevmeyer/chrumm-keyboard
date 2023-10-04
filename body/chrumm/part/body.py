import logging

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Plane
from chrumm.geo import Vector
from chrumm.geo import Triangle

from .arc import cornerArc2D
from .bracket import CornerBracket
from .bracket import RoofBracket
from .cable import Cable
from .encoder import Encoder


log = logging.getLogger(__name__)


class Body:

    def __init__(self, plan):
        self.outlineI = Edge()
        self.outlineO = Edge()
        self.bracketF = None
        self.bracketB = None
        self.faces = []
        self.triangles = []

        wallThickness = cfg.body.wallThickness
        innerChamfer = cfg.body.innerChamfer
        outerChamfer = cfg.body.outerChamfer
        outerCornerRadius = cfg.body.outerCornerRadius
        innerCornerRadius = outerCornerRadius - wallThickness
        floorLipHeight = cfg.floor.lipHeight + cfg.floor.lipMargin

        if innerChamfer >= innerCornerRadius:
            raise ValueError(f"body.innerChamfer must be less than: {innerCornerRadius:.3f}")

        if innerChamfer >= cfg.boss.innerWallFillet:
            raise ValueError("body.innerChamfer must be less than boss.innerWallFillet.")

        if outerChamfer >= outerCornerRadius:
            raise ValueError("body.outerChamfer must be less than body.outerCornerRadius.")

        # Reference points

        alnumILB = plan.points.alnumILB
        alnumIRB = plan.points.alnumIRB
        pinkyIRB = plan.points.pinkyIRB
        pinkyIRF = plan.points.pinkyIRF
        thumbILF = plan.points.thumbILF
        thumbILB = plan.points.thumbILB
        thumbIRF = plan.points.thumbIRF
        alnumILF = plan.points.alnumILF
        alnumIRF = plan.points.alnumIRF
        ridgeIRF = plan.points.ridgeIRF

        alnumOLB = plan.points.alnumOLB
        alnumORB = plan.points.alnumORB
        pinkyORB = plan.points.pinkyORB
        pinkyORF = plan.points.pinkyORF
        thumbOLF = plan.points.thumbOLF
        thumbORF = plan.points.thumbORF
        thumbOLB = plan.points.thumbOLB
        alnumOLF = plan.points.alnumOLF
        alnumORF = plan.points.alnumORF
        ridgeORF = plan.points.ridgeORF

        bossLB = plan.bosses.alnumB
        bossRB = plan.bosses.pinkyB
        bossRF = plan.bosses.pinkyF
        bossLF = plan.bosses.thumbF

        alnumNorm = plan.planes.alnumOT.normal
        pinkyNorm = plan.planes.pinkyOT.normal
        thumbNorm = plan.planes.thumbOT.normal

        alnumKeys = plan.layout.alnum(plan.side)
        thumbKeys = plan.layout.thumb(plan.side)
        pinkyKeys = plan.layout.pinky(plan.side)

        # Rounded corner edges

        cornerILFG = cornerArc2D(innerCornerRadius, thumbIRF, thumbILF, thumbILF.yz)
        cornerIRFG = cornerArc2D(innerCornerRadius, pinkyIRB, pinkyIRF, thumbILF)
        cornerIRBG = cornerArc2D(innerCornerRadius, alnumIRB, pinkyIRB, pinkyIRF)

        cornerOLFG = cornerArc2D(outerCornerRadius, thumbOLF.yz, thumbOLF, thumbORF)
        cornerORFG = cornerArc2D(outerCornerRadius, thumbOLF, pinkyORF, pinkyORB)
        cornerORBG = cornerArc2D(outerCornerRadius, pinkyORF, pinkyORB, alnumORB)

        cornerILFT = Edge(plan.planes.thumbIT.projectZ(p) for p in cornerILFG)
        cornerIRFT = Edge(plan.planes.pinkyIT.projectZ(p) for p in cornerIRFG)
        cornerIRBT = Edge(plan.planes.pinkyIT.projectZ(p) for p in cornerIRBG)

        cornerOLFT = Edge(plan.planes.thumbOT.projectZ(p) for p in cornerOLFG)
        cornerORFT = Edge(plan.planes.pinkyOT.projectZ(p) for p in cornerORFG)
        cornerORBT = Edge(plan.planes.pinkyOT.projectZ(p) for p in cornerORBG)

        bossEdgeLBT = Edge(plan.planes.alnumIT.projectZ(p) for p in bossLB.wallEdge)
        bossEdgeRBT = Edge(plan.planes.pinkyIT.projectZ(p) for p in bossRB.wallEdge)
        bossEdgeRFT = Edge(plan.planes.pinkyIT.projectZ(p) for p in bossRF.wallEdge)
        bossEdgeLFT = Edge(plan.planes.thumbIT.projectZ(p) for p in bossLF.wallEdge)

        if (bossEdgeRBT[-1].x >= cornerIRBT[0].x
                or bossEdgeRFT[-1].x <= thumbIRF.x
                or bossEdgeLFT[-1].x <= cornerILFT[0].x):
            raise ValueError(
                "A screw boss is overlapping a wall corner.\n"
                "  Try to decrease the boss size,\n"
                "  support.minOverhangAngle, or body.splitAngle.")

        # Alnum front wall (step)

        stepDir = (thumbOLB - alnumOLF).normalized()
        stepCornerRadiusO = outerCornerRadius if outerChamfer > 0 else 0
        stepCornerRadiusI = outerCornerRadius + wallThickness if innerChamfer > 0 else 0

        # Because the chamfer tapers off, its end is scaled up for visual balance.
        alnumILF = _chamfer(ridgeIRF, alnumILF, alnumIRF, alnumNorm, innerChamfer*1.25)
        alnumOLF = _chamfer(ridgeORF, alnumOLF, alnumORF, alnumNorm, outerChamfer*1.25)

        stepChamferPlaneI = Plane.fromPoints(alnumIRF, alnumILF, ridgeIRF)
        stepChamferPlaneO = Plane.fromPoints(alnumORF, alnumOLF, ridgeORF)

        stepCornerArcI = cornerArc2D(stepCornerRadiusI, ridgeIRF, thumbILB, alnumIRF)
        stepCornerArcO = cornerArc2D(stepCornerRadiusO, alnumORF, thumbOLB, ridgeORF)

        stepCornerIG = Edge(plan.planes.thumbIT.projectZ(p) for p in stepCornerArcI)
        stepCornerOG = Edge(plan.planes.thumbOT.projectZ(p) for p in stepCornerArcO)

        stepCornerIT = Edge(stepChamferPlaneI.intersect(Line(p, stepDir)) for p in stepCornerIG)
        stepCornerOT = Edge(stepChamferPlaneO.intersect(Line(p, stepDir)) for p in stepCornerOG)

        stepEdgeIG = Edge(ridgeIRF, stepCornerIG, alnumIRF)
        stepEdgeIT = Edge(ridgeIRF, stepCornerIT, alnumIRF)
        stepEdgeOG = Edge(alnumORF, stepCornerOG, ridgeORF)
        stepEdgeOT = Edge(alnumORF, stepCornerOT, ridgeORF)

        self.triangles.extend(stepEdgeIT.meshPairwise(stepEdgeIG))
        self.triangles.extend(stepEdgeOT.meshPairwise(stepEdgeOG))
        self.triangles.extend(Edge(alnumILF).meshPairwise(stepEdgeIT))
        self.triangles.extend(Edge(alnumOLF).meshPairwise(stepEdgeOT))

        # Outer chamfer

        chamferDownO = Vector(0, 0, -outerChamfer)

        cornerOLFC = cornerOLFT.translated(chamferDownO)
        cornerORFC = cornerORFT.translated(chamferDownO)
        cornerORBC = cornerORBT.translated(chamferDownO)

        thumbORFC = thumbORF + chamferDownO
        alnumORBC = alnumORB + chamferDownO
        alnumOLBC = alnumOLB + chamferDownO

        cornerOLFT = _cornerChamfer(thumbOLF.yz, cornerOLFT, thumbORF, thumbNorm, outerChamfer)
        cornerORFT = _cornerChamfer(thumbORF, cornerORFT, pinkyORB, pinkyNorm, outerChamfer)
        cornerORBT = _cornerChamfer(pinkyORF, cornerORBT, alnumORB, pinkyNorm, outerChamfer)

        thumbORFT = _parallelChamfer(pinkyORF, thumbORF, alnumORF, cornerORFT[0])
        alnumORBT = _parallelChamfer(pinkyORB, alnumORB, alnumORF, cornerORBT[-1])
        alnumOLBT = _parallelChamfer(alnumORB, alnumOLB, alnumOLF, alnumORBT)

        alnumILBG = alnumILB.xy
        alnumOLBG = alnumOLB.xy

        # Inner chamfer

        chamferDownI = Vector(0, 0, -innerChamfer)

        bossEdgeLBC = bossEdgeLBT.translated(chamferDownI)
        bossEdgeRBC = bossEdgeRBT.translated(chamferDownI)
        bossEdgeRFC = bossEdgeRFT.translated(chamferDownI)
        bossEdgeLFC = bossEdgeLFT.translated(chamferDownI)

        cornerIRBC = cornerIRBT.translated(chamferDownI)
        cornerIRFC = cornerIRFT.translated(chamferDownI)
        cornerILFC = cornerILFT.translated(chamferDownI)

        alnumILBC = alnumILB + chamferDownI
        alnumIRBC = alnumIRB + chamferDownI
        thumbIRFC = thumbIRF + chamferDownI

        bossEdgeLBT = _cornerChamfer(alnumILB, bossEdgeLBT, alnumIRB, -alnumNorm, innerChamfer)
        bossEdgeRBT = _cornerChamfer(alnumIRB, bossEdgeRBT, pinkyIRB, -pinkyNorm, innerChamfer)
        bossEdgeRFT = _cornerChamfer(pinkyIRF, bossEdgeRFT, thumbIRF, -pinkyNorm, innerChamfer)
        bossEdgeLFT = _cornerChamfer(thumbIRF, bossEdgeLFT, thumbILF, -thumbNorm, innerChamfer)

        cornerIRBT = _cornerChamfer(alnumIRB, cornerIRBT, pinkyIRF, -pinkyNorm, innerChamfer)
        cornerIRFT = _cornerChamfer(pinkyIRB, cornerIRFT, thumbIRF, -pinkyNorm, innerChamfer)
        cornerILFT = _cornerChamfer(thumbIRF, cornerILFT, thumbILF.yz, -thumbNorm, innerChamfer)

        if cfg.body.thumbTentAngle == cfg.body.pinkyTentAngle:
            alnumIRBT = _parallelChamfer(pinkyIRB, alnumIRB, alnumIRF, cornerIRBT[0])
            alnumILBT = _parallelChamfer(alnumIRB, alnumILB, alnumILF, alnumIRBT)
            thumbIRFT = _parallelChamfer(pinkyIRF, thumbIRF, alnumIRF, cornerIRFT[-1])
        else:
            alnumIRBT = _parallelChamfer(pinkyIRB, alnumIRB, thumbIRF, cornerIRBT[0])
            alnumILBT = _parallelChamfer(alnumIRB, alnumILB, alnumILF, alnumIRBT)
            thumbIRFT = _parallelChamfer(pinkyIRF, thumbIRF, alnumIRB, cornerIRFT[-1])

        # Key plates

        alnumEdgeI = Edge(bossEdgeLBT, alnumIRBT, alnumIRF, alnumILF, alnumILBT)
        pinkyEdgeI = Edge(alnumIRBT, bossEdgeRBT, cornerIRBT, cornerIRFT, bossEdgeRFT, thumbIRFT)
        thumbEdgeI = Edge(thumbIRFT, bossEdgeLFT, cornerILFT, ridgeIRF, stepCornerIG, alnumIRF)

        alnumEdgeO = Edge(alnumOLF, alnumORF, alnumORBT, alnumOLBT)
        pinkyEdgeO = Edge(cornerORFT, cornerORBT, alnumORBT, alnumORF, thumbORFT)
        thumbEdgeO = Edge(cornerOLFT, thumbORFT, alnumORF, stepCornerOG, ridgeORF)

        self.faces.append(Face(alnumEdgeI, [k.roofHoleI for k in alnumKeys]))
        self.faces.append(Face(pinkyEdgeI, [k.roofHoleI for k in pinkyKeys]))
        self.faces.append(Face(thumbEdgeI, [k.roofHoleI for k in thumbKeys]))
        self.faces.append(Face(alnumEdgeO, [k.roofHoleO for k in alnumKeys]))
        self.faces.append(Face(pinkyEdgeO, [k.roofHoleO for k in pinkyKeys]))
        self.faces.append(Face(thumbEdgeO, [k.roofHoleO for k in thumbKeys]))

        self.triangles.append(Triangle(alnumIRF, alnumIRBT, thumbIRFT))

        for key in alnumKeys + pinkyKeys + thumbKeys:
            self.triangles.extend(key.triangles)

        # Encoder hole

        splitEdgeF = Edge()
        splitEdgeB = Edge()

        encoderEdgeI = Edge(alnumILF.yz, alnumILF, ridgeIRF, ridgeIRF.yz)
        encoderEdgeO = Edge(ridgeORF.yz, ridgeORF, alnumOLF, alnumOLF.yz)

        if cfg.encoder:
            encoderRelPos = cfg.encoder.relPosition
            encoderPos = ridgeORF.yz*(1-encoderRelPos) + alnumOLF.yz*encoderRelPos
            encoderPlaneI = Plane.fromPoints(ridgeIRF, alnumILF, ridgeIRF.yz)
            encoderPlaneO = Plane.fromPoints(ridgeORF, alnumOLF, ridgeORF.yz)
            encoder = Encoder(Plane(encoderPos, encoderPlaneO.normal), encoderPlaneI)

            for p in encoder.roofEdgeI:
                if p.x > 0 and not encoderEdgeI.contains2D(p):
                    raise ValueError(
                        "The encoder does not fit inside the ridge.\n"
                        "  Try to adjust the encoder cfg, or increase the ridge size.")

            splitEdgeF.add(encoder.splitEdgeF)
            splitEdgeB.add(encoder.splitEdgeB)
            encoderEdgeI.add(encoder.roofEdgeI)
            encoderEdgeO.add(encoder.roofEdgeO)
            self.triangles.extend(encoder.triangles)
        else:
            splitEdgeF.add(ridgeORF, ridgeIRF)
            splitEdgeB.add(ridgeIRF, ridgeORF)

        self.faces.append(Face(encoderEdgeI))
        self.faces.append(Face(encoderEdgeO))

        # Ridge and brackets

        ridgeEdgeIT = Edge(alnumILBT, alnumILF, alnumILF.yz)
        ridgeEdgeIB = Edge(alnumILBG.yz, alnumILBG, alnumILBC)
        ridgeEdgeOB = Edge(alnumOLBC.yz, alnumOLBC, alnumOLBG, alnumOLBG.yz)
        ridgeEdgeORF = Edge(cornerOLFG[0], cornerOLFC[0], cornerOLFT[0], ridgeORF)
        ridgeEdgeORB = Edge(alnumOLBC, alnumOLBT, alnumOLF)
        ridgeEdgeIRF = Edge(
            cornerILFG[-1].yz, cornerILFG[-1],
            cornerILFC[-1], cornerILFT[-1],
            ridgeIRF, ridgeIRF.yz)
        ridgeEdgeILF = ridgeEdgeIRF.yz

        splitEdgeF = Edge(cornerILFG[-1], ridgeEdgeORF, splitEdgeF, ridgeIRF)
        splitEdgeB = Edge(alnumILF, splitEdgeB, alnumOLF, alnumOLBT, alnumOLBC)

        splitHolesF = []
        splitHolesB = []

        if cfg.bracket:
            bracketF = CornerBracket(cornerILFT[-1], ridgeIRF, cornerILFC[-1], plan.side)
            bracketB = CornerBracket(alnumILBT, alnumILF, alnumILBC, plan.side)
            bracketT = RoofBracket(alnumILBT, alnumILF, plan.layout.pinky()[0].matrix, plan.side)

            # Check if brackets fit

            thumbLineL = Line(ridgeIRF, cornerILFT[-1] - ridgeIRF)
            bracketGapFB = ridgeIRF.y - max(p.y for p in bracketF.splitEdge)
            bracketGapFR = min(thumbLineL.distance2D(p) for p in bracketF.roofEdge)
            bracketGapFG = min(p.z for p in bracketF.splitEdge) - floorLipHeight

            if bracketGapFB < 1e-3 or bracketGapFR < 1e-3 or bracketGapFG < 1e-3:
                raise ValueError("The front bracket does not fit.")

            bracketGapBR = alnumILBC.x - bracketB.wallEdge[-1].x
            bracketGapBG = min(p.z for p in bracketB.splitEdge) - floorLipHeight

            if bracketGapBR < 1e-3 or bracketGapBG < 1e-3:
                raise ValueError("The back bracket does not fit.")

            # Cable hole

            if cfg.cable:
                cable = Cable(bracketB.wallEdge[0], alnumOLBG.y - alnumILBG.y)

                if cable.splitEdgeG[-1].z < 1e-3 or cable.splitEdgeG[0].z < floorLipHeight:
                    raise ValueError("The cable hole does not fit.")

                splitEdgeB.add(cable.splitEdgeT)
                ridgeEdgeOB.add(cable.wallEdgeB)
                ridgeEdgeIB = Edge(cable.wallEdgeF, ridgeEdgeIB)
                splitEdgeBG = Edge(alnumOLBG.yz, alnumILBG.yz, cable.splitEdgeG)
                self.faces.append(Face(splitEdgeBG))
                self.triangles.extend(cable.triangles)
            else:
                splitEdgeB.add(alnumOLBG.yz, alnumILBG.yz)

            # Ridge edges

            ridgeEdgeIT.add(bracketT.roofEdge)
            ridgeEdgeIT.add(reversed(bracketB.roofEdge))
            ridgeEdgeIB.add(reversed(bracketB.wallEdge))
            ridgeEdgeILF = Edge(bracketF.wallEdge, bracketF.roofEdge)

            splitEdgeF.add(bracketF.splitEdge)
            splitEdgeB.add(bracketB.splitEdge)
            splitEdgeB.add(bracketT.splitEdge)

            splitHolesB.extend(bracketB.splitHoles)
            splitHolesB.append(bracketT.splitHole)
            splitHolesF.extend(bracketF.splitHoles)

            self.triangles.extend(bracketB.triangles)
            self.triangles.extend(bracketF.triangles)
            self.triangles.extend(bracketT.triangles)
            self.bracketF = bracketF
            self.bracketB = bracketB
        else:
            ridgeEdgeIT.add(alnumILBT.yz)
            ridgeEdgeIB.add(alnumILBC.yz)
            splitEdgeB.add(alnumOLBG.yz, alnumILBG.yz, alnumILBC, alnumILBT)
            splitEdgeF.add(cornerILFT[-1], cornerILFC[-1])

        self.faces.append(Face(splitEdgeF.yz.collapsed(), splitHolesF))
        self.faces.append(Face(splitEdgeB.yz.collapsed(), splitHolesB))
        self.faces.append(Face(ridgeEdgeOB))
        self.faces.append(Face(ridgeEdgeIT))
        self.faces.append(Face(ridgeEdgeIB.collapsed()))

        self.triangles.extend(ridgeEdgeORF.meshPairwise(ridgeEdgeORF.yz))
        self.triangles.extend(ridgeEdgeORB.yz.meshPairwise(ridgeEdgeORB))
        self.triangles.extend(ridgeEdgeILF.meshPairwise(ridgeEdgeIRF))

        # Chamfer

        chamferIC = Edge(
            bracketB.wallEdge[-1] if cfg.bracket else alnumILBC.yz,
            alnumILBC, bossEdgeLBC, alnumIRBC, bossEdgeRBC, cornerIRBC,
            cornerIRFC, bossEdgeRFC, thumbIRFC, bossEdgeLFC, cornerILFC)

        chamferIT = Edge(
            bracketB.roofEdge[0] if cfg.bracket else alnumILBT.yz,
            alnumILBT, bossEdgeLBT, alnumIRBT, bossEdgeRBT, cornerIRBT,
            cornerIRFT, bossEdgeRFT, thumbIRFT, bossEdgeLFT, cornerILFT)

        chamferOC = Edge(cornerOLFC, thumbORFC, cornerORFC, cornerORBC, alnumORBC, alnumOLBC)
        chamferOT = Edge(cornerOLFT, thumbORFT, cornerORFT, cornerORBT, alnumORBT, alnumOLBT)

        self.triangles.extend(chamferOC.meshPairwise(chamferOT))
        self.triangles.extend(chamferIC.meshPairwise(chamferIT))

        # Walls

        wallEdgeOC = Edge(
            cornerOLFC, thumbORFC, cornerORFC,
            cornerORBC, alnumORBC, alnumOLBC)

        wallEdgeIC = Edge(
            alnumILBC, bossEdgeLBC, alnumIRBC, bossEdgeRBC, cornerIRBC,
            cornerIRFC, bossEdgeRFC, thumbIRFC, bossEdgeLFC, cornerILFC)

        self.triangles.extend(wallEdgeOC.xy.meshPairwise(wallEdgeOC))
        self.triangles.extend(wallEdgeIC.xy.meshPairwise(wallEdgeIC))

        # Boss threads

        self.triangles.extend(bossLB.threadTriangles)
        self.triangles.extend(bossRB.threadTriangles)
        self.triangles.extend(bossRF.threadTriangles)
        self.triangles.extend(bossLF.threadTriangles)

        # Floor face

        floorEdge = Edge(
            alnumOLBG, alnumOLBG.yz, alnumILBG.yz, alnumILBG,
            bossEdgeLBC, alnumIRB, bossEdgeRBC, cornerIRBG,
            cornerIRFG, bossEdgeRFC, thumbIRF, bossEdgeLFC, cornerILFG,
            thumbILF.yz, thumbOLF.yz, cornerOLFG, thumbORF,
            cornerORFG, cornerORBG, alnumORB)

        self.faces.append(Face(floorEdge.xy.collapsed().reversed(), [
            bossLB.threadHole,
            bossRB.threadHole,
            bossRF.threadHole,
            bossLF.threadHole]))

        # Floor outlines

        self.outlineO.add(thumbOLF.yz, cornerOLFG)
        self.outlineI.add(
            alnumILB.yz, alnumILB, bossEdgeLBC, bossEdgeRBC, cornerIRBG,
            cornerIRFG, bossEdgeRFC, bossEdgeLFC, cornerILFG, thumbILF.yz)

        if cfg.palm:
            hitchRadius = cfg.palm.hitchCornerRadius
            hitchOLB = plan.points.hitchOLB
            hitchORB = plan.points.hitchORB
            hitchOLF = plan.points.hitchOLF
            hitchORF = plan.points.hitchORF
            self.outlineO.add(
                cornerArc2D(hitchRadius, thumbOLF, hitchOLB, hitchOLF),
                cornerArc2D(hitchRadius, hitchOLB, hitchOLF, hitchORF),
                cornerArc2D(hitchRadius, hitchOLF, hitchORF, hitchORB),
                cornerArc2D(hitchRadius, hitchORF, hitchORB, cornerORFG[0]))

        self.outlineO.add(cornerORFG, cornerORBG, alnumOLB, alnumOLB.yz)
        self.outlineO = self.outlineO.xy.collapsed()
        self.outlineI = self.outlineI.xy.collapsed().reversed()


def _chamfer(a, b, c, normal, chamferSize):
    """Project points onto normal plane and return chamfer offset."""
    #   c
    #  /
    # b-->?
    #  \
    #   a

    # Project lines onto normal plane
    plane = Plane(b, normal)
    ab = Line(b, b - plane.projectNormal(a))
    bc = Line(b, plane.projectNormal(c) - b)

    # Move lines inward
    ab = ab.translated(normal.cross(ab.dir).normalized()*chamferSize)
    bc = bc.translated(normal.cross(bc.dir).normalized()*chamferSize)

    try:
        return ab.intersect(bc)
    except ZeroDivisionError:
        return ab.pos


def _parallelChamfer(a, b, c, prevChamfer):
    """Extend existing chamfer to coplanar edge."""
    #    c
    #   /
    #  ?<----prevChamfer
    # b-----a

    parallel = Line(prevChamfer, b - a)
    cutoff = Line(b, c - b)
    return parallel.intersect(cutoff)


def _cornerChamfer(prevPoint, corner, nextPoint, normal, chamferSize):
    """Return chamfered corner edge"""
    edge = Edge()
    for i, b in enumerate(corner):
        a = corner[i-1] if i > 0 else prevPoint
        c = corner[i+1] if i < len(corner)-1 else nextPoint
        edge.add(_chamfer(a, b, c, normal, chamferSize))
    return edge
