Tools
=====

Run the Python scripts with the `-h` option to check their usage.
They depend on [ezdxf], [svgpathtools], and [numpy-stl], which can
be installed locally with:

	pip install --user ezdxf numpy-stl svgpathtools

[ezdxf]: https://github.com/mozman/ezdxf
[numpy-stl]: https://github.com/WoLpH/numpy-stl
[svgpathtools]: https://github.com/mathandy/svgpathtools


Make DXF
--------

Convert SVG polygons to optimized DXF paths with rounded corners:

	python3 svg-to-dxf.py in.svg out.dxf

If necessary, apply a kerf offset:

	python3 svg-to-dxf.py -k 0.1 in.svg out.dxf

For Blender, arcs can be converted to evenly sized chord segments:

	python3 svg-to-dxf.py -c 0.01 in.svg out.dxf


Slice STL
---------

Slice STL objects along the z axis for manual cutting:

	python3 slice-stl.py -s 6.0 in.stl out.dxf
