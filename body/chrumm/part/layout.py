import math

from chrumm import cfg

from chrumm.geo import Matrix
from chrumm.geo import Vector

from .key import KeyFactory


class Layout:
    """Arrange keys and provide access to named key groups."""

    def __init__(self):
        self._fingersL = []
        self._fingersR = []
        self._thumbL = []
        self._thumbR = []

        colPitch = cfg.layout.columnPitch
        rowPitch = cfg.layout.rowPitch
        staggers = cfg.layout.fingerStaggers
        thumbUnits = cfg.layout.thumbUnits
        thumbAngles = cfg.layout.thumbAngles
        thumbOffsets = cfg.layout.thumbOffsets

        factory = KeyFactory()

        # Sanity check

        for row in staggers:
            if len(row) != 4 or any(len(row[i]) != len(staggers[0][i]) for i in range(4)):
                raise ValueError("Malformed layout.fingerStaggers.")

        if (len(thumbUnits) != 2
                or len(thumbAngles) != 2
                or len(thumbUnits[0]) != len(thumbAngles[0])
                or len(thumbUnits[1]) != len(thumbAngles[1])):
            raise ValueError("Malformed layout.thumbUnits or layout.thumbAngles.")

        # Fingers

        def initFingers(target, sign):
            row = 0
            while row < len(staggers):
                target.append([])
                col = 0
                for group in staggers[row][::sign][2:]:
                    target[-1].append([])
                    for stagger in group[::sign]:
                        key = None

                        if type(stagger) != list:
                            stagger = [stagger]

                        if stagger:
                            dx = stagger[0]*sign if len(stagger) > 1 else 0
                            dy = stagger[1] if len(stagger) > 1 else stagger[0]
                            pos = Vector(col*colPitch + dx, -row*rowPitch + dy)
                            key = factory.make()
                            key.translate(pos)

                        target[-1][-1].append(key)
                        col += 1
                row += 1

        initFingers(self._fingersR, 1)
        initFingers(self._fingersL, -1)

        # Thumbs

        def initThumb(target, side, index, sign):
            units = thumbUnits[index][::sign]
            angles = thumbAngles[index][::sign]
            offset = thumbOffsets[index]

            startPos = self.alnumCol(-1, side)[-1].capPivotR
            pivotPos = startPos - Vector(offset[0], rowPitch + offset[1])

            for unit, angle in zip(units, angles):
                key = factory.make(unit)
                key.transform(Matrix().rotatedZ(math.radians(angle)))
                key.translate(pivotPos - key.capPivotR)
                target.insert(0, key)
                pivotPos = key.capPivotL

        initThumb(self._thumbL, "left", 0, 1)
        initThumb(self._thumbR, "right", 1, -1)

    def all(self, side="both"):
        return self.alnum(side) + self.pinky(side) + self.thumb(side)

    def alnum(self, side="both"):
        return self._group(0, side)

    def pinky(self, side="both"):
        return self._group(1, side)

    def alnumCol(self, index, side="both"):
        return self._col(0, index, side)

    def pinkyCol(self, index, side="both"):
        return self._col(1, index, side)

    def perAlnumCol(self, index, side="both"):
        return self._perCol(0, index, side)

    def perPinkyCol(self, index, side="both"):
        return self._perCol(1, index, side)

    def maxAlnum(self, side="both"):
        return max(self.alnum(side), key=lambda k: k.position)

    def minPinky(self, side="both"):
        return min(self.pinky(side), key=lambda k: k.position)

    def thumb(self, side="both"):
        keys = []
        if side != "left":
            keys += self._thumbR
        if side != "right":
            keys += self._thumbL
        return [key for key in keys if key]

    def _halves(self, side="both"):
        halves = []
        if side != "left":
            halves.append(self._fingersR)
        if side != "right":
            halves.append(self._fingersL)
        return halves

    def _group(self, group, side):
        keys = []
        for half in self._halves(side):
            keys.extend(key for row in half for key in row[group] if key)
        return keys

    def _col(self, group, index, side):
        keys = []
        for half in self._halves(side):
            keys.extend(row[group][index] for row in half if row[group][index])
        return keys

    def _perCol(self, group, index, side):
        keys = []
        for half in self._halves(side):
            cols = len(half[0][group])
            keys.extend(self._col(group, c, side)[index] for c in range(cols))
        return keys
