import logging

from chrumm import cfg

from chrumm.geo import Edge
from chrumm.geo import Face
from chrumm.geo import Line
from chrumm.geo import Plane
from chrumm.geo import Vector
from chrumm.geo import Triangle

from .arc import cornerArc2D
from .bracket import FlatBracket
from .bracket import CornerBracket
from .cable import CableHole
from .encoder import Encoder


log = logging.getLogger(__name__)


class Body:

    def __init__(self, plan, side, isSplit):
        self.outlineI = Edge()
        self.outlineO = Edge()
        self.faces = []
        self.triangles = []

        wallThickness = cfg.body.wallThickness
        innerChamfer = cfg.body.innerChamfer
        outerChamfer = cfg.body.outerChamfer
        outerCornerRadius = cfg.body.outerCornerRadius
        innerCornerRadius = outerCornerRadius - wallThickness

        if innerChamfer >= innerCornerRadius:
            raise ValueError(f"body.innerChamfer must be less than: {innerCornerRadius:.3f}")

        if innerChamfer >= cfg.boss.cornerRadius:
            raise ValueError("body.innerChamfer must be less than boss.cornerRadius.")

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

        alnumKeys = plan.layout.alnum
        thumbKeys = plan.layout.thumb
        pinkyKeys = plan.layout.pinky

        if side == "right":
            pinkyIRB = plan.points.extraIRB
            pinkyIRF = plan.points.extraIRF
            pinkyORB = plan.points.extraORB
            pinkyORF = plan.points.extraORF
            bossRB = plan.bosses.extraB
            bossRF = plan.bosses.extraF
            pinkyKeys.extend(plan.layout.extra)

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

        # Alnum front wall (=step)

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

        # Cable hole

        cableEdgeI = Edge(bossEdgeLBC[0].xy, bossEdgeLBC[0], alnumILBC, alnumILBC.xy)
        cableEdgeO = Edge(alnumOLBC.xy, alnumOLBC, alnumORBC, alnumORBC.xy)

        if cfg.cable and side == cfg.cable.side:
            cableHole = CableHole(alnumILBC, bossEdgeLBC[0])
            cableEdgeI.add(cableHole.wallEdgeI)
            cableEdgeO.add(cableHole.wallEdgeO)
            floorEdgeIB = Edge(alnumILB.yz, alnumILB, cableHole.wallEdgeI[0]).xy
            floorEdgeOB = Edge(alnumOLB.yz, alnumOLB, cableHole.wallEdgeO[-1]).xy
            self.triangles.extend(cableHole.triangles)
            self.triangles.extend(floorEdgeOB.meshPairwise(floorEdgeIB))
            floorEdge = Edge(cableHole.wallEdgeO[0], cableHole.wallEdgeI[-1])
        else:
            floorEdge = Edge(alnumOLBG, alnumOLBG.yz, alnumILBG.yz, alnumILBG)

        self.faces.append(Face(cableEdgeI))
        self.faces.append(Face(cableEdgeO))

        # Encoder hole

        splitEdgeF = Edge()
        splitEdgeB = Edge()

        encoderEdgeI = Edge(alnumILF.yz, alnumILF, ridgeIRF, ridgeIRF.yz)
        encoderEdgeO = Edge(ridgeORF.yz, ridgeORF, alnumOLF, alnumOLF.yz)

        if cfg.encoder:
            encoderPlaneI = Plane.fromPoints(ridgeIRF, alnumILF, ridgeIRF.yz)
            encoderPlaneO = Plane.fromPoints(ridgeORF, alnumOLF, ridgeORF.yz)
            encoderPos = encoderPlaneO.projectNormal((ridgeIRF + alnumOLF)/2).yz
            encoder = Encoder(encoderPos, encoderPlaneI, encoderPlaneO)

            for p in encoder.roofEdgeI:
                if p.x > 0 and not encoderEdgeI.contains2D(p):
                    raise ValueError(
                        "The encoder does not fit inside the ridge.\n"
                        "  Try to decrease the encoder size, or increase the ridge size.")

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

        # Brackets

        bracketF = None
        bracketT = None
        bracketB = None

        if cfg.bracket:
            lipLimit = cfg.floor.lipHeight + cfg.floor.lipMargin
            bracketPos = cfg.bracket.relRoofPosition

            bracketT = FlatBracket(alnumILF, alnumILBT, bracketPos, side, isSplit, True)
            bracketB = CornerBracket(alnumILBT, alnumILF, alnumILBC, side, isSplit, True)

            alnumLineL = Line(alnumILB, alnumILF - alnumILB)
            bracketTgapR = min(alnumLineL.distance2D(p) for p in bracketT.baseEdge)
            bracketBgapR = alnumILBC.x - bracketB.wallEdge[-1].x
            bracketBgapG = min(p.z for p in bracketB.splitEdge) - lipLimit

            if bracketTgapR < 1e-3:
                log.warning("The %s top bracket does not fit and is omitted.", side)
                bracketT = None

            if bracketBgapR < 1e-3 or bracketBgapG < 1e-3:
                log.warning("The %s back bracket does not fit and is omitted.", side)
                bracketB = None

            if isSplit:
                bracketF = CornerBracket(cornerILFT[-1], ridgeIRF, cornerILFC[-1], side)

                thumbLineL = Line(ridgeIRF, cornerILFT[-1] - ridgeIRF)
                bracketFgapR = min(thumbLineL.distance2D(p) for p in bracketF.roofEdge)
                bracketFgapB = ridgeIRF.y - max(p.y for p in bracketF.splitEdge)
                bracketFgapG = min(p.z for p in bracketF.splitEdge) - lipLimit

                if bracketFgapR < 1e-3 or bracketFgapB < 1e-3 or bracketFgapG < 1e-3:
                    log.warning("The %s front bracket does not fit and is omitted.", side)
                    bracketF = None

        # Ridge

        ridgeEdgeIT = Edge(alnumILBT, alnumILF, alnumILF.yz)
        ridgeEdgeORF = Edge(cornerOLFG[0], cornerOLFC[0], cornerOLFT[0], ridgeORF)
        ridgeEdgeORB = Edge(alnumOLBG, alnumOLBC, alnumOLBT, alnumOLF)
        ridgeEdgeIRB = Edge(alnumILBT, alnumILBC, alnumILBG, alnumILBG.yz)
        ridgeEdgeIRF = Edge(
            cornerILFG[-1].yz, cornerILFG[-1], cornerILFC[-1], cornerILFT[-1],
            ridgeIRF, ridgeIRF.yz)

        splitEdgeF = Edge(cornerILFG[-1], ridgeEdgeORF, splitEdgeF, ridgeIRF)
        splitEdgeB = Edge(
            alnumILF, splitEdgeB, alnumOLF,
            alnumOLBT, alnumOLBC, alnumOLBG, alnumILBG)

        splitHolesF = []
        splitHolesB = []

        if bracketT:
            ridgeEdgeIT.add(bracketT.baseEdge)
            splitEdgeB = Edge(bracketT.splitEdge, splitEdgeB)
            splitHolesB.extend(bracketT.splitHoles)
            self.triangles.extend(bracketT.triangles)

        if bracketB:
            ridgeEdgeILB = Edge(bracketB.roofEdge[0], reversed(bracketB.wallEdge))
            ridgeEdgeIT.add(reversed(bracketB.roofEdge))
            splitEdgeB.add(bracketB.splitEdge)
            splitHolesB.extend(bracketB.splitHoles)
            self.triangles.extend(bracketB.triangles)
        else:
            ridgeEdgeILB = ridgeEdgeIRB.yz
            ridgeEdgeIT.add(alnumILBT.yz)
            splitEdgeB.add(alnumILBC, alnumILBT)

        if bracketF:
            ridgeEdgeILF = Edge(bracketF.wallEdge, bracketF.roofEdge)
            splitEdgeF.add(bracketF.splitEdge)
            splitHolesF.extend(bracketF.splitHoles)
            self.triangles.extend(bracketF.triangles)
        else:
            ridgeEdgeILF = ridgeEdgeIRF.yz
            splitEdgeF.add(cornerILFT[-1], cornerILFC[-1])

        if isSplit:
            self.faces.append(Face(splitEdgeF.yz.collapsed(), splitHolesF))
            self.faces.append(Face(splitEdgeB.yz.collapsed(), splitHolesB))

        self.faces.append(Face(ridgeEdgeIT))
        self.triangles.extend(ridgeEdgeORF.meshPairwise(ridgeEdgeORF.yz))
        self.triangles.extend(ridgeEdgeORB.yz.meshPairwise(ridgeEdgeORB))
        self.triangles.extend(ridgeEdgeILF.meshPairwise(ridgeEdgeIRF))
        self.triangles.extend(ridgeEdgeILB.meshPairwise(ridgeEdgeIRB))

        # Chamfer

        chamferOC = Edge(cornerOLFC, thumbORFC, cornerORFC, cornerORBC, alnumORBC, alnumOLBC)
        chamferOT = Edge(cornerOLFT, thumbORFT, cornerORFT, cornerORBT, alnumORBT, alnumOLBT)
        chamferIC = Edge(
            alnumILBC, bossEdgeLBC, alnumIRBC, bossEdgeRBC, cornerIRBC,
            cornerIRFC, bossEdgeRFC, thumbIRFC, bossEdgeLFC, cornerILFC)
        chamferIT = Edge(
            alnumILBT, bossEdgeLBT, alnumIRBT, bossEdgeRBT, cornerIRBT,
            cornerIRFT, bossEdgeRFT, thumbIRFT, bossEdgeLFT, cornerILFT)

        self.triangles.extend(chamferOC.meshPairwise(chamferOT))
        self.triangles.extend(chamferIC.meshPairwise(chamferIT))

        # Walls

        wallEdgeOC = Edge(cornerOLFC, thumbORFC, cornerORFC, cornerORBC, alnumORBC)
        wallEdgeIC = Edge(
            bossEdgeLBC, alnumIRBC, bossEdgeRBC, cornerIRBC,
            cornerIRFC, bossEdgeRFC, thumbIRFC, bossEdgeLFC, cornerILFC)

        self.triangles.extend(wallEdgeOC.xy.meshPairwise(wallEdgeOC))
        self.triangles.extend(wallEdgeIC.xy.meshPairwise(wallEdgeIC))

        # Boss threads

        self.triangles.extend(bossLB.threadTriangles)
        self.triangles.extend(bossRB.threadTriangles)
        self.triangles.extend(bossRF.threadTriangles)
        self.triangles.extend(bossLF.threadTriangles)

        # Floor face

        floorEdge.add(
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
            hitchRadius = cfg.palm.hitch.cornerRadius
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
