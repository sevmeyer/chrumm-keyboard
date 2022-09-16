import logging
import multiprocessing

from chrumm import __version__
from chrumm import cfg
from chrumm import stl

from chrumm.part import Body
from chrumm.part import Floor
from chrumm.part import Knob
from chrumm.part import Palm
from chrumm.part import Plan


log = logging.getLogger(__name__)


def make(jsonStrings, threads, isSplit, isKnobOnly):
    """Generate STLs, based on JSON configuration strings.

    If a configuration parameter appears multiple times,
    then its latest value is used.

    Args:
        jsonStrings (list[str]): List of JSON strings.
        threads (int): Number of threads to use.
        isSplit (bool): Split into halves for smaller printbeds.
        isKnobOnly (bool): Generate the encoder knob only.
    Returns:
        dict[str, bytes]: A dict of named STL objects
    """
    stls = {}

    # Parameters

    log.info("Parsing configuration parameters...")
    cfg._init(jsonStrings)

    if cfg.maker.name != "chrumm" or cfg.maker.version != __version__:
        log.warning(
            "The parameters are intended for %s %s",
            cfg.maker.name,
            cfg.maker.version)

    if hasattr(cfg.quality, "bumpscosity"):
        bumpscosity = {
            0: "Where did all of the bumpscosity go?",
            1: "Only a single bumpscosit. It will have to do.",
            12: "Just a light breeze of bumpscosity, not bad.",
            50: "Ah, quite a pleasant amount of bumpscosity.",
            76: "Well, the bumpscosity is really getting up there, isn't it?",
            100: "Who turned up the bumpscosity so high?",
            1000: "A thousand?! How can you stand this much bumpscosity?"}
        if cfg.quality.bumpscosity in bumpscosity:
            log.debug(bumpscosity[cfg.quality.bumpscosity])

    # Knob

    if cfg.knob:
        stls["knob"] = stl.encode(Knob().triangles)

    if isKnobOnly:
        return stls

    # Parts

    log.info("Constructing reference points...")
    plan = Plan()

    log.info("Constructing keyboard parts...")
    parts = {}

    parts["body-right"] = Body(plan, "right", isSplit)
    parts["body-left"] = Body(plan, "left", isSplit)
    parts["floor-right"] = Floor(plan, parts["body-right"], "right", isSplit)
    parts["floor-left"] = Floor(plan, parts["body-left"], "left", isSplit)

    if cfg.palm:
        parts["palm-right"] = Palm(plan, "right")
        parts["palm-left"] = Palm(plan, "left")

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

    # Generate STLs

    if not isSplit:
        for name in "body", "floor":
            stls[name] = stl.encode(
                triangles[name + "-right"] +
                triangles[name + "-left"])

    for name in parts.keys():
        if isSplit or "palm" in name:
            stls[name] = stl.encode(triangles[name])

    return stls
