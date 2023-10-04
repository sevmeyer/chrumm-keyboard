# Generate Gerber files and pack them into
# a zip archive in the current directory.
#
# Usage: python3 chrumm-plot.py
#
# Written for KiCad 7, based on fab plugins (Jan 2023):
# Aisler  https://github.com/AislerHQ/PushForKiCad
# PCBWay  https://github.com/pcbway/PCBWay-Plug-in-for-Kicad
# JLCPCB  https://github.com/bennymeg/JLC-Plugin-for-KiCad

import shutil
import tempfile
import pcbnew as pcb


layerNames = (
    "F_Cu",
    "B_Cu",
    "F_Mask",
    "B_Mask",
    "F_SilkS",
    "B_SilkS",
    "Edge_Cuts")


def getRealSize(board):
    # The native board.GetBoardEdgesBoundingBox()
    # returns rendering bounds, not mechanical bounds.
    # https://forum.kicad.info/t/pcbnew-getboardedgesboundingbox-anomaly/28313
    minX = float("inf")
    minY = float("inf")
    maxX = float("-inf")
    maxY = float("-inf")
    for drawing in board.GetDrawings():
        if drawing.GetLayer() == pcb.Edge_Cuts and type(drawing) is pcb.PCB_SHAPE:
            box = drawing.GetBoundingBox()
            line = drawing.GetWidth()
            minX = min(minX, box.GetOrigin().x + line/2)
            minY = min(minY, box.GetOrigin().y + line/2)
            maxX = max(maxX, box.GetEnd().x - line/2)
            maxY = max(maxY, box.GetEnd().y - line/2)
    return maxX - minX, maxY - minY


with tempfile.TemporaryDirectory() as tempDir:
    board = pcb.LoadBoard("chrumm.kicad_pcb")

    # Settings

    settings = board.GetDesignSettings()
    settings.m_SolderMaskMargin = 0
    settings.m_SolderMaskMinWidth = 0

    # Layers

    plotter = pcb.PLOT_CONTROLLER(board)
    options = plotter.GetPlotOptions()
    options.SetOutputDirectory(tempDir)
    options.SetUseGerberX2format(True)
    options.SetUseGerberAttributes(True)
    options.SetUseGerberProtelExtensions(False)
    options.SetIncludeGerberNetlistInfo(True)
    options.SetDisableGerberMacros(False)
    options.SetScale(1)
    options.SetAutoScale(False)
    options.SetMirror(False)
    options.SetUseAuxOrigin(True)
    options.SetPlotFrameRef(False)
    options.SetPlotViaOnMaskLayer(False)
    options.SetSubtractMaskFromSilk(False)
    options.SetSketchPadLineWidth(pcb.FromMM(0.1))
    options.SetDrillMarksType(pcb.DRILL_MARKS_NO_DRILL_SHAPE)

    for name in layerNames:
        layer = getattr(pcb, name)
        if board.IsLayerEnabled(layer):
            plotter.SetLayer(layer)
            plotter.OpenPlotfile(name, pcb.PLOT_FORMAT_GERBER, "")
            plotter.PlotLayer()
            plotter.ClosePlot()

    # Drills

    drillMetric = False
    drillMirror = False
    drillMinHeader = True
    drillOffset = board.GetDesignSettings().GetAuxOrigin()
    drillMergeNPTH = False
    drillExcellonFile = True
    drillMapFile = False

    driller = pcb.EXCELLON_WRITER(board)
    driller.SetFormat(drillMetric)
    driller.SetOptions(drillMirror, drillMinHeader, drillOffset, drillMergeNPTH)
    driller.CreateDrillandMapFilesSet(tempDir, drillExcellonFile, drillMapFile)

    # Zip

    rev = board.GetTitleBlock().GetRevision()
    size = getRealSize(board)
    width = f"{pcb.ToMM(size[0]):.3f}".rstrip("0").rstrip(".")
    height = f"{pcb.ToMM(size[1]):.3f}".rstrip("0").rstrip(".")
    zipName = f"chrumm-gerber-{rev}-{width}x{height}mm"

    shutil.make_archive(zipName, "zip", tempDir)
    print("Wrote", zipName + ".zip")
