import math

from chrumm import cfg

from chrumm.geo import Matrix
from chrumm.geo import Vector

from .key import KeyFactory


class Layout:
    """Arrange keys and provide access to named key groups."""

    def __init__(self):
        self._fingers = []
        self._thumb = []

        colPitch = cfg.layout.columnPitch
        rowPitch = cfg.layout.rowPitch
        fingerStagger = cfg.layout.fingerStagger
        thumbCaps = cfg.layout.thumbCaps
        pinkyMargin = cfg.layout.thumbPinkyMargin
        capWidth = cfg.cap.width
        capDepth = cfg.cap.depth

        factory = KeyFactory()

        # Finger keys

        row = 0
        while row < len(fingerStagger):
            col = 0
            self._fingers.append([])
            for staggers in fingerStagger[row]:
                self._fingers[-1].append([])
                for stagger in staggers:
                    key = None
                    if stagger is not None:
                        pos = Vector(col*colPitch, -row*rowPitch + stagger)
                        key = factory.make(capWidth, capDepth)
                        key.translate(pos)
                    self._fingers[-1][-1].append(key)
                    col += 1
            row += 1

        # Thumb keys from right to left

        refKey = self.pinkyCol(0)[-1]
        pivotPos = refKey.capPivotL - Vector(pinkyMargin)

        for thumbW, thumbD, degrees in reversed(thumbCaps):
            key = factory.make(thumbW, thumbD)
            key.transform(Matrix().rotatedZ(math.radians(degrees)))
            key.translate(pivotPos - key.capPivotR)
            self._thumb.insert(0, key)
            pivotPos = key.capPivotL

    @property
    def all(self):
        return self.alnum + self.pinky + self.thumb + self.extra

    @property
    def thumb(self):
        return [key for key in self._thumb if key]

    @property
    def alnum(self):
        return [key for row in self._fingers for key in row[0] if key]

    @property
    def pinky(self):
        return [key for row in self._fingers for key in row[1] if key]

    @property
    def extra(self):
        return [key for row in self._fingers for key in row[2] if key]

    def alnumRow(self, index):
        return [key for key in self._fingers[index][0] if key]

    def pinkyRow(self, index):
        return [key for key in self._fingers[index][1] if key]

    def extraRow(self, index):
        return [key for key in self._fingers[index][2] if key]

    def alnumCol(self, index):
        return [row[0][index] for row in self._fingers if row[0][index]]

    def pinkyCol(self, index):
        return [row[1][index] for row in self._fingers if row[1][index]]

    def extraCol(self, index):
        return [row[2][index] for row in self._fingers if row[2][index]]

    def perAlnumCol(self, index):
        return [self.alnumCol(c)[index] for c in range(len(self._fingers[0][0]))]

    def perPinkyCol(self, index):
        return [self.pinkyCol(c)[index] for c in range(len(self._fingers[0][1]))]

    def perExtraCol(self, index):
        return [self.extraCol(c)[index] for c in range(len(self._fingers[0][2]))]
