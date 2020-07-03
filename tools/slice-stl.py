#!/usr/bin/env python3

# Copyright 2020 Severin Meyer
# Distributed under the Boost Software License 1.0
# See LICENSE.txt or https://www.boost.org/LICENSE_1_0.txt


"""
Slices STL objects along the z-axis
and writes the slices to a DXF file.

Limitations:
  - Potentially slow
  - Arbitrary order and direction of polygons
"""


import argparse
import math

import ezdxf
import stl


def isClose2D(p0, p1, epsilon):
	return abs(p0[0]-p1[0]) < epsilon and abs(p0[1]-p1[1]) < epsilon


def isCollinear2D(p0, p1, p2):
	# https://math.stackexchange.com/a/405970
	det = p0[0]*(p1[1]-p2[1]) + p1[0]*(p2[1]-p0[1]) + p2[0]*(p0[1]-p1[1])
	return abs(det) < 0.0001 # Should produce reasonable results


def getLineSlice2D(x0, y0, z0, x1, y1, z1, z):
	zDiff = z1 - z0
	if math.isclose(zDiff, 0.0): # Parallel
		return None
	zFac = (z - z0) / zDiff
	if zFac < 0.0 or zFac > 1.0: # No intersection
		return None
	return (x0 + (x1-x0)*zFac, y0 + (y1-y0)*zFac)


def getTriangleSlices2D(triangles, z, epsilon):
	slices = []
	for x0, y0, z0, x1, y1, z1, x2, y2, z2 in triangles:
		points = []
		points.append(getLineSlice2D(x0, y0, z0, x1, y1, z1, z))
		points.append(getLineSlice2D(x1, y1, z1, x2, y2, z2, z))
		points.append(getLineSlice2D(x2, y2, z2, x0, y0, z0, z))
		line = tuple(p for p in points if p is not None)
		if len(line) == 2 and not isClose2D(line[0], line[1], epsilon):
			slices.append(line)
	return slices


def getUniqueLines(lines, epsilon): # Slow
	uniques = []
	for a0, a1 in [sorted(line) for line in lines]:
		isUnique = True
		for b0, b1 in uniques:
			if isClose2D(a0, b0, epsilon) and isClose2D(a1, b1, epsilon):
				isUnique = False
				break
		if isUnique:
			uniques.append((a0, a1))
	return uniques


def getOrderedLines2D(lines, epsilon): # Slow
	remaining = getUniqueLines(lines, epsilon)
	ordered = []
	currLine = None
	startPoint = None
	while remaining:
		if currLine is None:
			currLine = remaining.pop()
			startPoint = currLine[0]
			ordered.append(currLine)
		else:
			nextLine = None
			for remLine in remaining:
				if isClose2D(currLine[1], remLine[0], epsilon):
					nextLine = (currLine[1], remLine[1])
					remaining.remove(remLine)
					break
				if isClose2D(currLine[1], remLine[1], epsilon):
					nextLine = (currLine[1], remLine[0])
					remaining.remove(remLine)
					break
			if nextLine is not None:
				if isClose2D(nextLine[1], startPoint, epsilon):
					nextLine = (nextLine[0], startPoint)
				ordered.append(nextLine)
			currLine = nextLine
	return ordered


def getMergedLines2D(lines, epsilon):
	merged = []
	for line in lines:
		if merged:
			a0, a1 = merged[-1]
			b0, b1 = line
			if isClose2D(a1, b0, epsilon) and isCollinear2D(a0, a1, b1):
				merged[-1] = (a0, b1)
				continue
		merged.append(line)
	return merged


def getSnappedLines(lines, digits):
	snapped = []
	for line in lines:
		snapped.append(tuple(tuple(round(c, digits) for c in p) for p in line))
	return snapped


def sliceStl(stlName, dxfName, sliceHeight, zBegin, zEnd, digits):
	mesh = stl.mesh.Mesh.from_file(stlName)
	zEnd = max(max(z) for z in mesh.z) if zEnd is None else zEnd
	epsilon = 10.0**-digits

	dxfDoc = ezdxf.new('R12')
	dxfSpace = dxfDoc.modelspace()
	z = zBegin
	while z < zEnd:
		zRound = round(z, digits)
		lines = getTriangleSlices2D(mesh, zRound, epsilon)
		lines = getOrderedLines2D(lines, epsilon)
		lines = getMergedLines2D(lines, epsilon)
		lines = getSnappedLines(lines, digits)
		for a, b in lines:
			dxfSpace.add_line((a[0], a[1], zRound), (b[0], b[1], zRound))
		z += sliceHeight
	dxfDoc.saveas(dxfName)


def main():
	parser = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-s', metavar='HEIGHT', type=float, required=True,
		help='slice height')
	parser.add_argument('-b', metavar='ZPOS', type=float, default=0.0,
		help='begin slicing at this position (0.0)')
	parser.add_argument('-e', metavar='ZPOS', type=float, default=None,
		help='end slicing at this position')
	parser.add_argument('-d', metavar='DIGITS', type=int, default=3,
		help='digits after decimal point for DXF (3)')
	parser.add_argument('STL', help='input STL file')
	parser.add_argument('DXF', help='output DXF file, overwrites existing')
	args = parser.parse_args()
	sliceStl(args.STL, args.DXF, args.s, args.b, args.e, args.d)


if __name__ == '__main__':
	main()
