"""Provide float comparisons with an epsilon threshold."""
# Comparing floats is notoriously cumbersome. To keep it
# simple, this project uses an absolute epsilon of 1e-6.
#
# Considerations:
# - The base unit is 1mm.
# - The maximum expected scale is 1m (1e+3).
# - The minimum expected scale is 1um (1e-3).
# - STL stores 32bit floats with a machine epsilon of ~1e-7.
#   Points that are considered separate during construction
#   should not collapse to identical coordinates in STL.
# - Geometric comparisons should be consistent across the
#   working space. Whether two points are considered separate
#   should not depend on their proximity to the origin.
#   Therefore, a relative comparison is problematic:
#     math.isclose(100.0000001, 100.0000002) -> False
#     math.isclose(101.0000001, 101.0000002) -> True
#
# References:
# https://randomascii.wordpress.com/2012/02/25/comparing-floating-point-numbers-2012-edition/
# https://peps.python.org/pep-0485/
# https://numpy.org/doc/stable/reference/generated/numpy.isclose.html


def isZero(n):
    return abs(n) < 1e-6
