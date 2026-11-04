"""
Geometry basics -- reusable Rhino.Geometry functions for Grasshopper.

Adding a new function with Copilot
-----------------------------------
1. Open this file and select this chat model, then ask Copilot something like:
   "Add a function here, all in Rhino geometry, that builds a <your shape/idea>.
   Follow the same style as create_cone / create_fractal_tree (defaults for
   optional inputs, a docstring listing params, return a Rhino.Geometry object)."
2. Once the function is added, ask Copilot:
   "Give me the Python code to use this function in a Grasshopper GHPython 3
   component, importing it from computational_design_and_fabrication."
3. Copy the snippet Copilot gives you into a GHPython component, wire up the
   inputs as sliders/panels, and set the output variable (e.g. `a`).
"""

import math
import random
import Rhino.Geometry as rg

def create_cone(base_point=None, height=10.0, radius=5.0, cap_bottom=True):
    """
    Build a cone as a Brep.

    base_point : Rhino.Geometry.Point3d -- center of the cone's base circle
    height     : float -- cone height along the base plane's normal (Z by default)
    radius     : float -- base circle radius
    cap_bottom : bool  -- whether to cap the base circle (closed vs open cone)

    Returns a Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    plane = rg.Plane(base_point, rg.Vector3d.ZAxis)
    cone = rg.Cone(plane, height, radius)
    return cone.ToBrep(cap_bottom)

def create_sphere(base_plane1=None, radius=5.0):
    """
    Build a sphere as a Brep.

    base_plane : Rhino.Geometry.Plane -- the plane on which the sphere is centered
    radius     : float -- sphere radius

    Returns a Rhino.Geometry.Brep.
    """
    if base_plane1 is None:
        base_plane1 = rg.Plane.WorldXY

    sphere = rg.Sphere(base_plane1, radius)
    return sphere.ToBrep()

def boolean_difference(brep_a, brep_b):
    """
    Perform a boolean difference operation between two Breps.

    brep_a : Rhino.Geometry.Brep -- the first Brep
    brep_b : Rhino.Geometry.Brep -- the second Brep to subtract from the first

    Returns a list of Rhino.Geometry.Brep resulting from the difference.
    """
    if brep_a is None or brep_b is None:
        raise ValueError("Both brep_a and brep_b must be provided.")

    result = rg.Brep.CreateBooleanDifference(brep_a, brep_b, 0.001)
    return result


def copy_brep_along_z(brep, distance, copy_count):
    """
    Create copies of a Brep, each offset in the +Z direction.

    brep : Rhino.Geometry.Brep -- the Brep to copy
    distance : float -- the Z spacing between consecutive copies
    copy_count : int -- the number of copies to create

    Returns a list of Rhino.Geometry.Brep copies; copy i is moved by distance * (i + 1).
    """
    if brep is None:
        raise ValueError("brep must be provided.")
    if copy_count < 0:
        raise ValueError("copy_count must not be negative.")

    copies = []
    for i in range(1, int(copy_count) + 1):
        copy = brep.DuplicateBrep()
        copy.Transform(rg.Transform.Translation(rg.Vector3d(0, 0, distance * i)))
        copies.append(copy)
    return copies

def create_container(container_type=0, size=30.0, height=30.0):
    """
    Build the outer container hull (0 = Box, 1 = Cylinder, 2 = Pyramid) as a Brep.

    container_type : int   -- 0 for Box, 1 for Cylinder, 2 for 4-sided Pyramid
    size           : float -- width/diameter of the container base
    height         : float -- height of the container along +Z

    Returns a Rhino.Geometry.Brep.
    """
    c_type = int(container_type)
    half = size / 2.0
    base_plane = rg.Plane.WorldXY

    if c_type == 0:
        # 0: Quader / Box (zentriert um 0,0, Boden bei Z=0)
        x_int = rg.Interval(-half, half)
        y_int = rg.Interval(-half, half)
        z_int = rg.Interval(0.0, height)
        box = rg.Box(base_plane, x_int, y_int, z_int)
        return box.ToBrep()

    if c_type == 1:
        # 1: Zylinder (Kreis am Boden mit Radius = half, Höhe = height)
        circle = rg.Circle(base_plane, half)
        cylinder = rg.Cylinder(circle, height)
        return cylinder.ToBrep(True, True)

    if c_type == 2:
        # 2: Vierseitige Pyramide aus 4 Eckpunkten am Boden + 1 Spitze (Apex)
        p0 = rg.Point3d(-half, -half, 0.0)
        p1 = rg.Point3d(half, -half, 0.0)
        p2 = rg.Point3d(half, half, 0.0)
        p3 = rg.Point3d(-half, half, 0.0)
        apex = rg.Point3d(0.0, 0.0, height)

        base_face = rg.Brep.CreateFromCornerPoints(p0, p1, p2, p3, 0.001)
        side1 = rg.Brep.CreateFromCornerPoints(p0, p1, apex, 0.001)
        side2 = rg.Brep.CreateFromCornerPoints(p1, p2, apex, 0.001)
        side3 = rg.Brep.CreateFromCornerPoints(p2, p3, apex, 0.001)
        side4 = rg.Brep.CreateFromCornerPoints(p3, p0, apex, 0.001)

        joined = rg.Brep.JoinBreps([base_face, side1, side2, side3, side4], 0.001)
        return joined[0]

def pack_gravity_spheres(container_type=0, size=30.0, height=30.0,
                         count=15, min_radius=2.0, max_radius=5.0, seed=42):
    c_type = int(container_type)
    count = int(count)

    if c_type not in (0, 1, 2):
        raise ValueError("container_type must be 0, 1, or 2.")
    if size <= 0 or height <= 0:
        raise ValueError("size and height must be positive.")
    if count < 0:
        raise ValueError("count must not be negative.")
    if min_radius <= 0 or max_radius < min_radius:
        raise ValueError("Radius limits must be positive and ordered.")

    rng = random.Random(seed)
    planes = []
    radii = []
    half = size / 2.0

    def support_height(x, y, radius):
        z = radius

        for plane, other_radius in zip(planes, radii):
            dx = x - plane.Origin.X
            dy = y - plane.Origin.Y
            combined = radius + other_radius
            horizontal_sq = dx * dx + dy * dy

            if horizontal_sq <= combined * combined:
                dz = math.sqrt(combined * combined - horizontal_sq)
                z = max(z, plane.Origin.Z + dz)

        return z

    for _ in range(count):
        radius = rng.uniform(min_radius, max_radius)
        best_point = None
        best_z = float("inf")

        for _ in range(50):
            if c_type == 1:
                angle = rng.uniform(0.0, 2.0 * math.pi)
                max_center_radius = half - radius
                distance = math.sqrt(rng.random()) * max_center_radius
                x = distance * math.cos(angle)
                y = distance * math.sin(angle)
            else:
                x = rng.uniform(-half + radius, half - radius)
                y = rng.uniform(-half + radius, half - radius)

            z = support_height(x, y, radius)

            if z > height - radius:
                continue

            if c_type == 0:
                fits_container = (
                    abs(x) <= half - radius
                    and abs(y) <= half - radius
                )
            elif c_type == 1:
                fits_container = (
                    math.sqrt(x * x + y * y) <= half - radius
                )
            else:
                slope = half / height
                side_clearance = radius * math.sqrt(1.0 + slope * slope)
                fits_container = (
                    half - abs(x) - slope * z >= side_clearance
                    and half - abs(y) - slope * z >= side_clearance
                )

            if fits_container and z < best_z:
                best_point = rg.Point3d(x, y, z)
                best_z = z

        if best_point is not None:
            planes.append(rg.Plane(best_point, rg.Vector3d.ZAxis))
            radii.append(radius)

    return planes, radii

def create_box_inside_sphere(plane, radius):
    half_side = radius / math.sqrt(3.0)

    box = rg.Box(
        plane,
        rg.Interval(-half_side, half_side),
        rg.Interval(-half_side, half_side),
        rg.Interval(-half_side, half_side)
    )
    return box.ToBrep()

def populate_shapes(planes, radii):
    shapes = []

    for plane, radius in zip(planes, radii):
        shape = create_box_inside_sphere(plane, radius)
        shapes.append(shape)

    return shapes

