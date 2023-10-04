def findTriangulationProblems(triangles, outerSegments):
    """Check if triangles make reasonable sense (inefficient)."""

    # Triangles are valid
    # -> Non-zero area
    # -> Not collinear

    for tri in triangles:
        if not tri:
            return "Triangle is not valid."

    # Triangle vertexes match segment vertexes
    # -> No rounding errors
    # -> No new points

    vertexes = []
    for segment in outerSegments:
        for vertex in segment.a, segment.b:
            if vertex not in vertexes:
                vertexes.append(vertex)

    for tri in triangles:
        if tri.a not in vertexes or tri.b not in vertexes or tri.c not in vertexes:
            return "Triangle vertex does not match outer segments."

    # Segments are used an expected number of times
    # -> Unique triangles
    # -> No holes

    outerSortedSegs = [sorted((s.a, s.b)) for s in outerSegments]
    innerSortedSegs = []

    outerCounts = [0]*len(outerSortedSegs)
    innerCounts = []

    for tri in triangles:
        for seg in (tri.a, tri.b), (tri.b, tri.c), (tri.c, tri.a):
            sortedSeg = sorted(seg)

            isOuterSeg = False
            for i, outerSeg in enumerate(outerSortedSegs):
                if sortedSeg == outerSeg:
                    outerCounts[i] += 1
                    isOuterSeg = True

            isInnerSeg = False
            for i, innerSeg in enumerate(innerSortedSegs):
                if sortedSeg == innerSeg:
                    innerCounts[i] += 1
                    isInnerSeg = True

            if not isOuterSeg and not isInnerSeg:
                innerSortedSegs.append(sortedSeg)
                innerCounts.append(1)

    for count in outerCounts:
        if count > 1:
            return "Outer segment is used more than once."

    for count in innerCounts:
        if count != 2:
            return "Inner segment is not used exactly twice."

    return None
