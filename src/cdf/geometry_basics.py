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

def create_hollow_container(
        container_type=0, size=30.0, height=30.0, wall_thickness=1.0):
    """Build a closed hollow box, cylinder, or four-sided pyramid as a Brep.

    The inner cavity matches the original container dimensions. The outer
    shell grows outward from that boundary.
    """
    c_type = int(container_type)
    if c_type not in (0, 1, 2):
        raise ValueError("container_type must be 0, 1, or 2.")
    if size <= 0 or height <= 0:
        raise ValueError("size and height must be positive.")
    if wall_thickness <= 0:
        raise ValueError("wall_thickness must be positive.")

    half = size / 2.0
    thickness = float(wall_thickness)

    if c_type == 0:
        outer = rg.Box(
            rg.Plane.WorldXY,
            rg.Interval(-half - thickness, half + thickness),
            rg.Interval(-half - thickness, half + thickness),
            rg.Interval(-thickness, height + thickness)
        ).ToBrep()
        inner = rg.Box(
            rg.Plane.WorldXY,
            rg.Interval(-half, half),
            rg.Interval(-half, half),
            rg.Interval(0.0, height)
        ).ToBrep()
    elif c_type == 1:
        outer_plane = rg.Plane(
            rg.Point3d(0.0, 0.0, -thickness), rg.Vector3d.ZAxis)
        outer = rg.Cylinder(
            rg.Circle(outer_plane, half + thickness),
            height + 2.0 * thickness
        ).ToBrep(True, True)
        inner = rg.Cylinder(
            rg.Circle(rg.Plane.WorldXY, half), height
        ).ToBrep(True, True)
    else:
        inner = create_container(2, size, height)
        outer_half = (
            half * (height + 2.0 * thickness) / (height + thickness)
            + thickness
        )
        outer = create_container(
            2, 2.0 * outer_half, height + 2.0 * thickness)
        if not outer.Transform(
                rg.Transform.Translation(0.0, 0.0, -thickness)):
            raise RuntimeError("Could not move the outer pyramid shell.")

    inner.Flip()
    outer.Append(inner)

    if not outer.IsValid or not outer.IsSolid:
        raise RuntimeError(
            "The hollow container did not create a valid solid Brep.")

    return outer


def create_hollow_box_container(
        size=30.0, height=30.0, wall_thickness=1.0, container_type=0):
    """Backward-compatible wrapper for the hollow container function."""
    return create_hollow_container(
        container_type, size, height, wall_thickness)

def pack_gravity_spheres(container_type=0, size=30.0, height=30.0,
                         count=15, seed=42,
                         min_radius=10.0, max_radius=35.0):
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

        for _ in range(500):
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

def perforate_spheres(planes, radii, seed=42):
    shapes = []
    rng = random.Random(seed)
    extra_length = 1.0
    min_hole_diameter_ratio = 0.25
    max_hole_diameter_ratio = 0.45

    for index, (plane, radius) in enumerate(zip(planes, radii)):
        sphere = create_sphere(plane, radius)
        if index % 5 == 0:
            shapes.append(sphere)
            continue
        hole_diameter_ratio = rng.uniform(
            min_hole_diameter_ratio, max_hole_diameter_ratio)

        angle = rng.uniform(0.0, 2.0 * math.pi)
        direction_z = rng.uniform(-1.0, 1.0)
        direction_xy = math.sqrt(1.0 - direction_z * direction_z)

        axis = rg.Vector3d(
                direction_xy * math.cos(angle),
                direction_xy * math.sin(angle),
                direction_z
        )

        cutter_radius = radius * hole_diameter_ratio
        cutter_length = 2.0 * radius + 2.0 * extra_length
        cutter_start = plane.Origin - axis * (radius + extra_length)
        cutter_plane = rg.Plane(cutter_start, axis)

        cutter_type = rng.choice(("cylinder", "cross"))

        if cutter_type == "cylinder":
            cutter_circle = rg.Circle(cutter_plane, cutter_radius)
            cutter = rg.Cylinder(
                cutter_circle,
                cutter_length
            ).ToBrep(True, True)
        else:
            arm_half_width = cutter_radius * 0.35
            cross_coordinates = [
                (-arm_half_width, -cutter_radius),
                (arm_half_width, -cutter_radius),
                (arm_half_width, -arm_half_width),
                (cutter_radius, -arm_half_width),
                (cutter_radius, arm_half_width),
                (arm_half_width, arm_half_width),
                (arm_half_width, cutter_radius),
                (-arm_half_width, cutter_radius),
                (-arm_half_width, arm_half_width),
                (-cutter_radius, arm_half_width),
                (-cutter_radius, -arm_half_width),
                (-arm_half_width, -arm_half_width),
            ]
            cross_points = [
                cutter_plane.PointAt(x, y)
                for x, y in cross_coordinates
            ]
            cross_points.append(cross_points[0])
            cross_curve = rg.PolylineCurve(cross_points)
            cross_extrusion = rg.Extrusion.Create(
                cross_curve, cutter_length, True)
            if cross_extrusion is None:
                raise RuntimeError("Could not create the cross-shaped cutter.")
            cutter = cross_extrusion.ToBrep()

        result = boolean_difference(sphere, cutter)

        if not result:
            raise RuntimeError("Boolean cut failed for a sphere.")

        shapes.extend(result)

    return shapes

def bake_brep_with_material(
        brep, material_name, rgb, roughness=0.5, opacity=1.0,
        source_label="brep"):
    import System
    import Rhino
    import Rhino.DocObjects as rd
    from System.Drawing import Color

    if brep is None:
        raise ValueError("brep must be provided.")
    if len(rgb) != 3 or any(value < 0 or value > 255 for value in rgb):
        raise ValueError("rgb must contain three values from 0 to 255.")
    if not 0.0 <= roughness <= 1.0:
        raise ValueError("roughness must be between 0.0 and 1.0.")
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("opacity must be between 0.0 and 1.0.")

    doc = Rhino.RhinoDoc.ActiveDoc
    if doc is None:
        raise RuntimeError("No active Rhino document.")

    if isinstance(brep, System.Guid):
        source_object = doc.Objects.FindId(brep)
        if source_object is None:
            raise ValueError(
                "{} is a Rhino object ID that does not exist in the active "
                "document.".format(source_label)
            )
        source_geometry = source_object.Geometry
        if not isinstance(source_geometry, rg.Brep):
            raise TypeError(
                "{} is a Rhino object ID, but the object is not a Brep."
                .format(source_label)
            )
        brep = source_geometry.DuplicateBrep()

    if not isinstance(brep, rg.Brep):
        raise TypeError(
            "{} must be a Rhino.Geometry.Brep or Rhino object ID; received {}."
            .format(source_label, type(brep).__name__)
        )

    material_index = doc.Materials.Find(material_name, True)

    if material_index >= 0:
        material = rd.Material(doc.Materials[material_index])
    else:
        material = rd.Material()
        material.Name = material_name

    material.DiffuseColor = Color.FromArgb(
        int(rgb[0]), int(rgb[1]), int(rgb[2])
    )
    material.Shine = (1.0 - roughness) * rd.Material.MaxShine
    material.Transparency = 1.0 - opacity

    if material_index >= 0:
        if not doc.Materials.Modify(material, material_index, True):
            raise RuntimeError("Could not update the Rhino material.")
    else:
        material_index = doc.Materials.Add(material)
        if material_index < 0:
            raise RuntimeError("Could not add the Rhino material.")

    attributes = rd.ObjectAttributes()
    attributes.MaterialSource = rd.ObjectMaterialSource.MaterialFromObject
    attributes.MaterialIndex = material_index

    object_id = doc.Objects.AddBrep(brep, attributes)
    if object_id == System.Guid.Empty:
        raise RuntimeError("Could not add the Brep to the Rhino document.")

    return object_id

def bake_breps_with_material_ids(breps, material_ids):
    if len(breps) != len(material_ids):
        raise ValueError("There must be one material ID per Brep.")

    palette = [
        ("Matcha Wolle", (120, 150, 70), 0.90, 1.00),
        ("Waschbeton", (190, 190, 185), 0.95, 1.00),
        ("Mid-century Kunststoff", (225, 105, 35), 0.22, 1.00),
        ("Dunkle Eiche", (65, 38, 25), 0.75, 1.00),
        ("Milchglas", (155, 205, 220), 0.30, 0.55),
    ]

    object_ids = []

    for brep_index, (brep, material_id) in enumerate(
            zip(breps, material_ids)):
        index = int(material_id)

        if index != material_id or index < 0 or index >= len(palette):
            raise ValueError("Material IDs must be whole numbers from 0 to 4.")

        material_name, rgb, roughness, opacity = palette[index]
        object_id = bake_brep_with_material(
            brep,
            material_name,
            rgb,
            roughness,
            opacity,
            source_label="sphere_breps[{}]".format(brep_index)
        )
        object_ids.append(object_id)

    return object_ids

def bake_glass_box(brep):
    """Bake a box Brep with a transparent pale-blue Rhino material."""
    return bake_brep_with_material(
        brep,
        "CDF Clear Glass",
        (190, 225, 240),
        roughness=0.08,
        opacity=0.12,
        source_label="box_brep"
    )

def bake_composition_with_material_ids(box_brep, sphere_breps, material_ids):
    """Bake the glass box and all spheres with their selected materials."""
    if box_brep is None:
        raise ValueError("box_brep must be provided.")
    if len(sphere_breps) != len(material_ids):
        raise ValueError("There must be one material ID per sphere Brep.")

    box_id = bake_glass_box(box_brep)
    sphere_ids = bake_breps_with_material_ids(sphere_breps, material_ids)
    return box_id, sphere_ids

def bake_composition_on_button(
        box_brep, sphere_breps, material_ids, bake):
    """Bake the glass container and spheres only when the button is pressed."""
    if not bake:
        return None

    return bake_composition_with_material_ids(
        box_brep, sphere_breps, material_ids)


def bake_composition_from_parameters_on_button(
        container_type, size, height, wall_thickness,
        sphere_breps, material_ids, bake):
    """Create and bake the glass container and spheres when requested."""
    if not bake:
        return None

    box_brep = create_hollow_container(
        container_type, size, height, wall_thickness)
    return bake_composition_with_material_ids(
        box_brep, sphere_breps, material_ids)