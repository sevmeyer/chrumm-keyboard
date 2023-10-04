import logging
import multiprocessing

from chrumm import __version__
from chrumm import cfg
from chrumm import pcb
from chrumm import stl

from chrumm.part import Body
from chrumm.part import Floor
from chrumm.part import Knob
from chrumm.part import Palm
from chrumm.part import Plan
from chrumm.part import Support


log = logging.getLogger(__name__)


def make(jsonStrings, threads, isKnobOnly):
    """Generate files, based on JSON configuration strings.

    Args:
        jsonStrings (list[str]): List of JSON strings.
        threads (int): Number of threads to use.
        isKnobOnly (bool): Generate the encoder knob only.
    Returns:
        dict[str, bytes|str]: A dict of file names and data.
    """
    files = {}

    # Parse parameters

    log.info("Parsing configuration parameters...")
    cfg._init(jsonStrings)

    if cfg.maker != "chrumm " + __version__:
        log.warning("The parameters are intended for %s", cfg.maker)

    if hasattr(cfg.quality, "bumpscosity"):
        responses = {
            0: "Where did all of the bumpscosity go?",
            1: "Only a single bumpscosit. It will have to do.",
            12: "Just a light breeze of bumpscosity, not bad.",
            50: "Ah, quite a pleasant amount of bumpscosity.",
            76: "The bumpscosity is really getting up there, isn't it?",
            100: "Who turned up the bumpscosity so high?",
            1000: "A thousand?! How can you stand this much bumpscosity?"}
        if cfg.quality.bumpscosity in responses:
            log.debug(responses[cfg.quality.bumpscosity])

    # Generate knob

    if cfg.knob:
        files["rotary-knob.stl"] = stl.toBytes(Knob().triangles)

    if isKnobOnly:
        return files

    # Generate parts

    log.info("Constructing reference points...")
    planR = Plan("right")
    planL = Plan("left")

    log.info("Constructing keyboard parts...")
    parts = {}
    parts["body-right"] = Body(planR)
    parts["body-left"] = Body(planL)
    parts["floor-right"] = Floor(planR, parts["body-right"])
    parts["floor-left"] = Floor(planL, parts["body-left"])

    if cfg.palm:
        parts["palm-right"] = Palm(planR)
        parts["palm-left"] = Palm(planL)

    if cfg.support:
        parts["support-right"] = Support(planR)
        parts["support-left"] = Support(planL)

    if cfg.pcb:
        files["pcb-positions.kicad_mod"] = pcb.toKiCadFootprint(planR, planL)

    # Triangulate faces

    # The face objects are accumulated in a flat list, so that
    # they can be passed to Pool and triangulated in parallel.
    faces = [face for part in parts.values() for face in part.faces]

    if threads <= 1:
        log.info("Triangulating %i faces without multithreading...", len(faces))
        faceTriangles = [face.triangulate() for face in faces]
    else:
        log.info("Triangulating %i faces with %i threads...", len(faces), threads)
        with multiprocessing.Pool(processes=threads) as pool:
            faceTriangles = pool.map(type(faces[0]).triangulate, faces)

    # Combine triangles

    triangles = {}

    for name, part in parts.items():
        triangles[name] = list(part.triangles)
        for face in part.faces:
            triangles[name].extend(faceTriangles.pop(0))
        if "left" in name:
            triangles[name] = [t.mirroredX().reversed() for t in triangles[name]]

    # Generate files

    for name in parts.keys():
        files[name + ".stl"] = stl.toBytes(triangles[name])

    return files
