#!/usr/bin/env python3

# Copyright 2020 Severin Meyer
# Distributed under the Boost Software License 1.0
# See LICENSE.txt or https://www.boost.org/LICENSE_1_0.txt


"""
Converts SVG polygons to DXF outlines with rounded corners.
The element order is preserved. Supported SVG elements are:
  <path> (lines only)
  <circle>

The stroke width sets the corner radius.
The stroke color sets the counterclockwise kerf offset:
  #f00 = negative
  #0f0 = positive

A <rect> element with the stroke color #00f overrides the
corner radius of all contained corners with its stroke width.
"""


import argparse
import math

import ezdxf
import svgpathtools
import xml.etree


def writeChords(dxf, arc, chordHeight, isCCW=True):
	if arc.radius <= 0.0 or chordHeight <= 0.0 or arc.start_angle == arc.end_angle:
		return

	absRadians = math.radians(360.0 - (arc.start_angle - arc.end_angle) % 360.0)
	arcRadians = absRadians if isCCW else -2.0*math.pi + absRadians

	maxStep    = 2.0 * math.acos(1.0 - chordHeight/arc.radius)
	chordCount = math.ceil(abs(arcRadians / maxStep))
	chordStep  = arcRadians / chordCount

	points = [arc.start_point]
	for i in range(1, chordCount):
		radians = arc.start_angle_rad + i*chordStep
		x = arc.center.x + arc.radius*math.cos(radians)
		y = arc.center.y + arc.radius*math.sin(radians)
		points.append((x,y))
	points.append(arc.end_point)

	for i in range(len(points)-1):
		prevPoint = points[i]
		nextPoint = points[i+1]
		dxf.add_line(prevPoint, nextPoint)


def writeCircle(dxf, center, radius, chordHeight=None):
	if radius <= 0.0:
		return

	if chordHeight is None:
		dxf.add_circle(center, radius)
	else:
		arc = ezdxf.math.ConstructionArc(center, radius, 0.0, 360.0)
		writeChords(dxf, arc, chordHeight)


def writeCornerArc(dxf, arc, chordHeight):
	if arc.radius <= 0.0 or arc.start_angle == arc.end_angle:
		return

	isCCW = (arc.end_angle - arc.start_angle) % 360.0 < 180.0

	if chordHeight is None:
		dxf.add_arc(arc.center, arc.radius,
			arc.start_angle if isCCW else arc.end_angle,
			arc.end_angle   if isCCW else arc.start_angle)
	else:
		writeChords(dxf, arc, chordHeight, isCCW)


def getCornerArc(prevPoint, midPoint, nextPoint, radius, offset):
	up = (midPoint - nextPoint).normalize()
	dn = (midPoint - prevPoint).normalize()
	isCCW = dn.x*up.y - up.x*dn.y < 0.0

	halfAngle  = math.sin(dn.angle_between(up) / 2.0)
	centerDir  = (up + dn).normalize()
	centerDist = radius / halfAngle
	centerPos  = midPoint - centerDir*centerDist

	arcRadius = radius + (offset if isCCW else -offset)
	arcStart  = dn.orthogonal(not isCCW).angle_deg % 360.0
	arcEnd    = up.orthogonal(    isCCW).angle_deg % 360.0

	if arcRadius < 0.0:
		centerPos += centerDir * (arcRadius/halfAngle)
		arcRadius = 0.0

	return ezdxf.math.ConstructionArc(centerPos, arcRadius, arcStart, arcEnd)


def writeRoundedPolygon(dxf, shape, radii, offset, chordHeight=None):
	if len(shape) < 3:
		raise ValueError('Not enough polygon vertices')

	arcs = []
	for i in range(len(shape)):
		arcs.append(getCornerArc(
			shape[(i-1) % len(shape)],
			shape[i],
			shape[(i+1) % len(shape)],
			radii[i],
			offset))

	for i in range(len(arcs)):
		prevArc = arcs[i]
		nextArc = arcs[(i+1) % len(arcs)]
		dxf.add_line(prevArc.end_point, nextArc.start_point)
		writeCornerArc(dxf, nextArc, chordHeight)


def getRadius(point, globalRadius, localRadius, blueRects):
	if globalRadius is not None:
		return globalRadius
	for x, y, w, h, r in blueRects:
		if x <= point[0] <= x+w and y <= point[1] <= y+h:
			return r
	return localRadius


def toFloat(attrib):
	return float(attrib.strip('em ex px pt pc cm mm in'))


def toStyleDict(attrib):
	style = {}
	if attrib:
		for item in attrib.strip(';').split(';'):
			key, value = item.split(':')
			style[key.strip()] = value.strip()
	return style


def writeDxf(svgName, dxfName, kerfWidth=None, chordHeight=None, globalRadius=None):
	svgRoot = xml.etree.ElementTree.parse(svgName).getroot()
	svgHeight = toFloat(svgRoot.attrib['height'])
	kerfWidth = 0.0 if kerfWidth is None else kerfWidth
	blueRects = []

	dxfDoc = ezdxf.new('R12')
	dxfSpace = dxfDoc.modelspace()
	for elem in svgRoot.iter():
		attr   = elem.attrib
		style  = toStyleDict(attr.get('style', ''))
		radius = attr.get('stroke-width', '1.0')
		radius = toFloat(style.get('stroke-width', radius))
		stroke = attr.get('stroke', '')
		stroke = style.get('stroke', stroke).lower()

		isRed    = stroke in ('#f00', '#ff0000', 'red')
		isGreen  = stroke in ('#0f0', '#00ff00', 'lime')
		isBlue   = stroke in ('#00f', '#0000ff', 'blue')
		isRect   = elem.tag == '{http://www.w3.org/2000/svg}rect'
		isPath   = elem.tag == '{http://www.w3.org/2000/svg}path'
		isCircle = elem.tag == '{http://www.w3.org/2000/svg}circle'

		if isBlue and isRect:
			w = toFloat(attr['width'])
			h = toFloat(attr['height'])
			x = toFloat(attr['x'])
			y = svgHeight - toFloat(attr['y']) - h
			blueRects.append((x, y, w, h, radius))

		if isRed or isGreen:
			offset = kerfWidth / (-2.0 if isRed else 2.0)

			if isPath:
				d = svgpathtools.parse_path(attr.get('d'))
				shape = ezdxf.math.Shape2d()
				radii = []
				for segment in d:
					x = segment.start.real
					y = svgHeight - segment.start.imag
					shape.append((x, y))
					radii.append(getRadius((x, y), globalRadius, radius, blueRects))
				writeRoundedPolygon(dxfSpace, shape, radii, offset, chordHeight)

			if isCircle:
				x = toFloat(attr['cx'])
				y = svgHeight - toFloat(attr['cy'])
				r = toFloat(attr['r'])
				writeCircle(dxfSpace, (x,y), r+offset, chordHeight)
	dxfDoc.saveas(dxfName)


def main():
	parser = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-c', metavar='HEIGHT', type=float, default=None,
		help='split arcs and circles into chord segments')
	parser.add_argument('-k', metavar='WIDTH', type=float, default=None,
		help='add kerf offset to outlines')
	parser.add_argument('-r', metavar='RADIUS', type=float, default=None,
		help='override radius for all rounded corners')
	parser.add_argument('SVG', help='input SVG file')
	parser.add_argument('DXF', help='output DXF file, overwrites existing')
	args = parser.parse_args()
	writeDxf(args.SVG, args.DXF, args.k, args.c, args.r)


if __name__ == '__main__':
	main()
