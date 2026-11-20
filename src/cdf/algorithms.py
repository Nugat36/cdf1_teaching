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
import Rhino.Geometry as rg
import random

def create_fractal_tree(
    base_point=None,
    base_plane=None,
    length=10.0,
    angle=25.0,
    length_factor=0.7,
    depth=8,
    branch_count=2,
):
    """
    Build a fractal (recursively branching) tree as a list of line segments.

    base_point    : Rhino.Geometry.Point3d -- start point of the trunk
    base_plane    : Rhino.Geometry.Plane   -- plane whose YAxis is the trunk
                     direction and ZAxis is the branching rotation axis
    length        : float -- trunk length
    angle         : float -- angle in degrees between sibling branches
    length_factor : float -- length multiplier applied at each new generation
    depth         : int   -- number of recursive branching generations
    branch_count  : int   -- number of branches spawned at each node

    Returns a list of Rhino.Geometry.Line.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)
    if base_plane is None:
        base_plane = rg.Plane.WorldXY

    lines = []

    def _grow(start, direction, branch_length, remaining_depth):
        if remaining_depth <= 0 or branch_length <= 1e-6:
            return

        end = start + direction * branch_length
        lines.append(rg.Line(start, end))

        if branch_count <= 1:
            offsets = [0.0]
        else:
            span = angle * (branch_count - 1)
            offsets = [-span / 2.0 + i * angle for i in range(branch_count)]

        for offset in offsets:
            rotated_direction = rg.Vector3d(direction)
            rotated_direction.Rotate(math.radians(offset), base_plane.ZAxis)
            _grow(end, rotated_direction, branch_length * length_factor, remaining_depth - 1)

    _grow(base_point, base_plane.YAxis, length, depth)

    return lines


def create_crochet_pseudosphere(
    rounds=4,
    first_round=12,
    increase=3,
    base_chain=4,
    stitch_width=1.0,
    stitch_height=2.0,
    iterations=150,
    seed=1,
    max_stitches=1500,
):
    """Build a crocheted hyperbolic form ("pseudosphere") as a mesh.

    The function follows the crochet pattern step by step:
      1. a small ring made of chain stitches,
      2. a first round of double crochets into the ring,
      3. more rounds, where every stitch gets `increase` new stitches.

    Each stitch is one mesh vertex. After every new round the stitches are
    relaxed like small springs: a stitch wants to keep its width and its
    height, and two stitches cannot be in the same place. Each round has more
    stitches than a flat circle has room for, so the surface has to ruffle.

    Params:
        rounds (int): Number of rounds worked into the ring. Default 4.
            Stitch count is multiplied by `increase` every round, so keep
            this low (5 rounds with increase 3 is already 972 stitches).
        first_round (int): Stitches in the first round. Default 12.
        increase (int): New stitches worked into each stitch. Default 3.
            1 gives a tube, 2 gives soft ruffles, 3 gives dense ruffles.
        base_chain (int): Chain stitches in the starting ring. Default 4.
            Only sets the size of the hole in the middle.
        stitch_width (float): Width of one stitch. Default 1.0.
        stitch_height (float): Height of one round. Default 2.0
            (a double crochet is about twice as tall as it is wide).
        iterations (int): Relaxation steps after each round. Default 150.
            More steps give a smoother result but take longer.
        seed (int): Seed for the small random offsets that let the surface
            ruffle. Same seed gives the same shape. Default 1.
        max_stitches (int): Safety limit on stitches in a single round.
            Rounds that would exceed it are skipped, so the form stops
            growing instead of freezing Rhino. Default 1500.

    Returns:
        Rhino.Geometry.Mesh: The crocheted surface. Each vertex is the top
        of one stitch, each ring of vertices is one round.
    """
    rng = random.Random(seed)

    points = []    # [x, y, z] of every stitch
    fixed = []     # True for stitches that must not move (the starting ring)
    springs = []   # (i, j, rest_length, stiffness)
    linked = set() # pairs joined by a spring, these are skipped in collision
    faces = []     # (a, b, c) vertex indices

    def add_spring(i, j, rest, stiffness):
        springs.append((i, j, rest, stiffness))
        linked.add((min(i, j), max(i, j)))

    # ------------------------------------------------------------------
    # 1 + 2. Starting ring (the joined chain). It stays fixed at the origin.
    # ------------------------------------------------------------------
    ring_radius = base_chain * stitch_width / (2.0 * math.pi)
    ring = []
    for i in range(first_round):
        angle = 2.0 * math.pi * i / first_round
        points.append([ring_radius * math.cos(angle),
                       ring_radius * math.sin(angle),
                       0.0])
        fixed.append(True)
        ring.append(i)

    # ------------------------------------------------------------------
    # Relaxation: springs keep stitch sizes, collisions keep stitches apart.
    # ------------------------------------------------------------------
    collision_distance = 0.9 * stitch_width

    def relax(steps):
        for _ in range(steps):
            # springs
            for i, j, rest, stiffness in springs:
                a = points[i]
                b = points[j]
                dx = b[0] - a[0]
                dy = b[1] - a[1]
                dz = b[2] - a[2]
                length = math.sqrt(dx * dx + dy * dy + dz * dz)
                if length < 1e-9:
                    continue
                move = stiffness * (length - rest) / length
                if fixed[i] and fixed[j]:
                    continue
                if fixed[i]:
                    b[0] -= dx * move
                    b[1] -= dy * move
                    b[2] -= dz * move
                elif fixed[j]:
                    a[0] += dx * move
                    a[1] += dy * move
                    a[2] += dz * move
                else:
                    move *= 0.5
                    a[0] += dx * move
                    a[1] += dy * move
                    a[2] += dz * move
                    b[0] -= dx * move
                    b[1] -= dy * move
                    b[2] -= dz * move

            # collisions: sort stitches into a grid, compare only neighbours
            cell = collision_distance
            grid = {}
            for index, p in enumerate(points):
                key = (int(math.floor(p[0] / cell)),
                       int(math.floor(p[1] / cell)),
                       int(math.floor(p[2] / cell)))
                grid.setdefault(key, []).append(index)

            for (cx, cy, cz), members in grid.items():
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        for oz in (-1, 0, 1):
                            others = grid.get((cx + ox, cy + oy, cz + oz))
                            if not others:
                                continue
                            for i in members:
                                for j in others:
                                    if j <= i:
                                        continue
                                    if fixed[i] and fixed[j]:
                                        continue
                                    if (i, j) in linked:
                                        continue
                                    a = points[i]
                                    b = points[j]
                                    dx = b[0] - a[0]
                                    dy = b[1] - a[1]
                                    dz = b[2] - a[2]
                                    d2 = dx * dx + dy * dy + dz * dz
                                    if d2 >= cell * cell or d2 < 1e-12:
                                        continue
                                    dist = math.sqrt(d2)
                                    push = (cell - dist) / dist
                                    if fixed[i]:
                                        b[0] += dx * push
                                        b[1] += dy * push
                                        b[2] += dz * push
                                    elif fixed[j]:
                                        a[0] -= dx * push
                                        a[1] -= dy * push
                                        a[2] -= dz * push
                                    else:
                                        push *= 0.5
                                        a[0] -= dx * push
                                        a[1] -= dy * push
                                        a[2] -= dz * push
                                        b[0] += dx * push
                                        b[1] += dy * push
                                        b[2] += dz * push

    # ------------------------------------------------------------------
    # 3 + 4. Work the rounds. Round 1 puts one stitch on each ring position,
    # every later round puts `increase` stitches into each stitch.
    # ------------------------------------------------------------------
    grow_from = {}  # stitch index -> index of the stitch it was worked into

    for round_index in range(rounds):
        per_stitch = 1 if round_index == 0 else increase
        if len(ring) * per_stitch > max_stitches:
            break  # next round would be too big, stop at the last one that fits
        new_ring = []
        children_of = []

        for parent in ring:
            p = points[parent]

            # growth direction: continue the line from grandparent to parent
            if parent in grow_from:
                g = points[grow_from[parent]]
                direction = [p[0] - g[0], p[1] - g[1], p[2] - g[2]]
            else:
                direction = [p[0], p[1], 0.0]
            size = math.sqrt(sum(c * c for c in direction)) or 1.0
            direction = [c / size for c in direction]

            children = []
            for _ in range(per_stitch):
                jitter = 0.3 * stitch_width
                points.append([
                    p[0] + direction[0] * stitch_height + rng.uniform(-jitter, jitter),
                    p[1] + direction[1] * stitch_height + rng.uniform(-jitter, jitter),
                    p[2] + direction[2] * stitch_height + rng.uniform(-jitter, jitter),
                ])
                fixed.append(False)
                child = len(points) - 1
                grow_from[child] = parent
                children.append(child)
                new_ring.append(child)
                # the post of the stitch
                add_spring(parent, child, stitch_height, 1.0)
            children_of.append(children)

        count = len(new_ring)
        for k in range(count):
            # top of the round: every stitch is one stitch_width wide
            add_spring(new_ring[k], new_ring[(k + 1) % count], stitch_width, 1.0)
            # weak spring to the stitch after next, keeps the round smooth
            if count > 4:
                add_spring(new_ring[k], new_ring[(k + 2) % count],
                           2.0 * stitch_width, 0.15)

        # faces between the old round and the new round
        parents = len(ring)
        for j in range(parents):
            children = children_of[j]
            next_parent = ring[(j + 1) % parents]
            next_child = children_of[(j + 1) % parents][0]
            for k in range(len(children) - 1):
                faces.append((ring[j], children[k], children[k + 1]))
            faces.append((ring[j], children[-1], next_child))
            faces.append((ring[j], next_child, next_parent))

        ring = new_ring
        relax(iterations)

    # ------------------------------------------------------------------
    # Build the Rhino mesh
    # ------------------------------------------------------------------
    mesh = rg.Mesh()
    for p in points:
        mesh.Vertices.Add(p[0], p[1], p[2])
    for a, b, c in faces:
        mesh.Faces.AddFace(a, b, c)
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh

# ======================================================================
# Tangent sphere growth
# ======================================================================


def random_unit_vector():
    """Return a random direction on the unit sphere."""
    z = random.uniform(-1.0, 1.0)
    t = random.uniform(0.0, 2.0 * math.pi)
    r = math.sqrt(1.0 - z * z)
    return rg.Vector3d(r * math.cos(t), r * math.sin(t), z)


def rotate_vector(v, axis, angle_rad):
    """Rotate vector v around axis by angle (radians).

    Params:
        v (Rhino.Geometry.Vector3d): Vector to rotate. It is not changed.
        axis (Rhino.Geometry.Vector3d): Rotation axis.
        angle_rad (float): Rotation angle in radians.

    Returns:
        Rhino.Geometry.Vector3d: The rotated copy of v.
    """
    # 1.1 -- copy the input vector and the axis
    vv = rg.Vector3d(v)
    ax = rg.Vector3d(axis)

    # 1.2 -- the axis must be unit length
    ax.Unitize()

    # 1.3 -- build a Rhino rotation transform around the world origin
    xform = rg.Transform.Rotation(
        angle_rad,
        ax,
        rg.Point3d.Origin,
    )

    # 1.4 -- apply the transform to the vector (in place)
    vv.Transform(xform)

    return vv


def random_deflect(dir_vec, angle_max):
    """Deflect a direction vector by a random small rotation.

    Idea:
      - build a plane perpendicular to the direction,
      - pick a random axis in that plane,
      - rotate by a random angle up to angle_max.

    Params:
        dir_vec (Rhino.Geometry.Vector3d): Direction to deflect.
        angle_max (float): Largest deflection angle in radians.

    Returns:
        Rhino.Geometry.Vector3d: The deflected direction.
    """
    # 1.5 -- copy and unitize the incoming direction
    d = rg.Vector3d(dir_vec)
    d.Unitize()

    # choose a helper vector that is not (nearly) parallel to d
    helper = rg.Vector3d(0, 0, 1)
    if abs(rg.Vector3d.Multiply(d, helper)) > 0.95:
        helper = rg.Vector3d(0, 1, 0)

    # 1.6 -- build a perpendicular frame U, V around d
    U = rg.Vector3d.CrossProduct(d, helper)
    U.Unitize()
    V = rg.Vector3d.CrossProduct(d, U)
    V.Unitize()

    # 1.7 -- pick a random axis in the perpendicular plane
    phi = random.uniform(0.0, 2.0 * math.pi)
    axis = U * math.cos(phi) + V * math.sin(phi)

    # 1.8 -- rotate by a random angle up to angle_max
    ang = random.uniform(0.0, angle_max)
    return rotate_vector(d, axis, ang)


def cell_key(pt, cs):
    """Map a 3D point to a grid cell index (ix, iy, iz) for cell size cs."""
    return (
        int(math.floor(pt.X / cs)),
        int(math.floor(pt.Y / cs)),
        int(math.floor(pt.Z / cs)),
    )


def neighbor_keys(k):
    """Yield the 27 cell keys around and including cell k (3x3x3)."""
    x, y, z = k
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                yield (x + dx, y + dy, z + dz)


def can_place_tangent(center, r_child, grid, cs, eps=1e-6):
    """Check whether a sphere can be placed without overlapping others.

    Touching is allowed, overlapping is not. Two spheres overlap when
        distance < r_child + r_existing - eps

    Params:
        center (Rhino.Geometry.Point3d): Center of the new sphere.
        r_child (float): Radius of the new sphere.
        grid (dict): Spatial hash, cell key -> list of (center, radius).
        cs (float): Cell size of the grid.
        eps (float): Tolerance so touching spheres count as free. Default 1e-6.

    Returns:
        bool: True if the sphere fits.
    """
    k = cell_key(center, cs)

    # 2.2 -- only check spheres in nearby grid cells
    for nk in neighbor_keys(k):
        if nk not in grid:
            continue

        for (c2, r2) in grid[nk]:
            # 2.1 -- overlap rule
            if center.DistanceTo(c2) < (r_child + r2 - eps):
                return False

    return True


def add_to_grid(center, radius, grid, cs):
    """Store (center, radius) in its grid cell for fast lookup later."""
    key = cell_key(center, cs)
    # 2.3 -- store center and radius
    grid.setdefault(key, []).append((center, radius))


def grow_tangent_spheres(
    seed_pt=None,
    seed_radius=5.0,
    iterations=30,
    radius_decay=0.92,
    branch_chance=0.2,
    angle_max=0.8,
    min_radius=0.5,
    seed_dir=None,
    seed=None,
):
    """Grow a branching chain of touching spheres from a seed sphere.

    Every generation, each tip places one child sphere (sometimes two) that
    touches its parent. The child is a bit smaller and points in a slightly
    deflected direction. Children that would overlap an existing sphere are
    retried in another direction; growth stops when nothing fits anymore.

    Params:
        seed_pt (Rhino.Geometry.Point3d): Start point. Default world origin.
        seed_radius (float): Radius of the first sphere. Default 5.0.
        iterations (int): Maximum number of generations. Default 30.
        radius_decay (float): Shrink factor per generation. Default 0.92.
        branch_chance (float): Chance (0-1) that a tip gets a second child.
            Default 0.2.
        angle_max (float): Largest deflection per generation, in radians.
            Default 0.8. Below about 0.6 a second child never fits beside
            its sibling, so the growth does not branch.
        min_radius (float): Stop growing a branch when spheres get smaller
            than this. Default 0.5.
        seed_dir (Rhino.Geometry.Vector3d): Initial direction. None picks a
            random one. Default None.
        seed (int): Random seed; the same seed gives the same result.
            None gives a new result every time. Default None.

    Returns:
        tuple: (spheres, lines, tip_points)
            spheres    -- list of Rhino.Geometry.Sphere
            lines      -- list of Rhino.Geometry.Line, parent to child
            tip_points -- list of Rhino.Geometry.Point3d, the last tips
    """
    if seed_pt is None:
        seed_pt = rg.Point3d(0, 0, 0)
    if seed is not None:
        random.seed(seed)

    # STEP 3 -- initial direction: use seed_dir if given, otherwise random
    if seed_dir:
        # 3.1 -- copy and unitize seed_dir
        d0 = rg.Vector3d(seed_dir)
        d0.Unitize()
    else:
        d0 = random_unit_vector()

    spheres, lines = [], []

    # 4.1 -- cell size for the spatial hash. Two spheres can only collide
    # when their centers are closer than the sum of their radii, which is
    # at most 2 * seed_radius. With cells at least that big, checking the
    # 3x3x3 neighbouring cells is enough to find every possible collision.
    cell_size = max(2.0 * seed_radius, 2.0 * min_radius)

    grid = {}

    # 4.2 -- create the seed sphere and store it in the grid
    spheres.append(rg.Sphere(seed_pt, seed_radius))
    add_to_grid(seed_pt, seed_radius, grid, cell_size)

    # 4.3 -- tips are the active growth states: (point, direction, radius)
    tips = [(seed_pt, d0, seed_radius)]

    for i in range(iterations):

        new_tips = []

        # 4.4 -- grow from each active tip
        for (pt, d, r_parent) in tips:

            # child radius shrinks
            r_child = r_parent * radius_decay
            if r_child < min_radius:
                continue

            # 4.5 -- branching: usually 1 child, sometimes 2
            n_children = 1 + (1 if random.random() < branch_chance else 0)

            for c in range(n_children):

                # 4.6 -- try up to 20 directions to find a free placement
                for t in range(20):

                    # new direction = deflected parent direction
                    d_child = random_deflect(d, angle_max)
                    d_child.Unitize()

                    # 4.7 -- tangency rule:
                    # distance between centers = r_parent + r_child
                    step = r_parent + r_child
                    new_pt = pt + d_child * step

                    # 4.8 -- accept only if nothing overlaps
                    if can_place_tangent(new_pt, r_child, grid, cell_size, eps=1e-4):

                        spheres.append(rg.Sphere(new_pt, r_child))
                        add_to_grid(new_pt, r_child, grid, cell_size)

                        # connection line from parent to child
                        lines.append(rg.Line(pt, new_pt))

                        # the child becomes a new tip
                        new_tips.append((new_pt, d_child, r_child))
                        break  # placed, stop trying

        # 4.9 -- stop early if nothing new could be placed
        if not new_tips:
            break

        tips = new_tips

    # STEP 5 -- output only the tip points
    tip_points = [pt for (pt, d, r) in tips]

    return spheres, lines, tip_points



import math
import Rhino.Geometry as rg

# Feste interne Konstanten
MAX_STITCHES = 3000
STITCH_WIDTH = 1.0
STRAND_STITCHES_PER_ROT = 8
RELAX_ITERATIONS = 80


def _relax_stitch_network(points, fixed, springs, linked, iterations, collision_distance):
    for _ in range(iterations):
        for i, j, rest, stiffness in springs:
            a = points[i]
            b = points[j]
            dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            if length < 1e-9 or (fixed[i] and fixed[j]):
                continue
            move = stiffness * (length - rest) / length
            if fixed[i]:
                b[0] -= dx * move; b[1] -= dy * move; b[2] -= dz * move
            elif fixed[j]:
                a[0] += dx * move; a[1] += dy * move; a[2] += dz * move
            else:
                move *= 0.5
                a[0] += dx * move; a[1] += dy * move; a[2] += dz * move
                b[0] -= dx * move; b[1] -= dy * move; b[2] -= dz * move

        grid = {}
        for index, point in enumerate(points):
            key = (
                int(math.floor(point[0] / collision_distance)),
                int(math.floor(point[1] / collision_distance)),
                int(math.floor(point[2] / collision_distance)),
            )
            grid.setdefault(key, []).append(index)

        for (cx, cy, cz), members in grid.items():
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        others = grid.get((cx + ox, cy + oy, cz + oz), ())
                        for i in members:
                            for j in others:
                                if j <= i or (i, j) in linked:
                                    continue
                                a = points[i]
                                b = points[j]
                                dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
                                dist_sq = dx * dx + dy * dy + dz * dz
                                if dist_sq < 1e-12 or dist_sq >= collision_distance ** 2:
                                    continue
                                dist = math.sqrt(dist_sq)
                                push = (collision_distance - dist) / dist
                                if fixed[i]:
                                    b[0] += dx * push; b[1] += dy * push; b[2] += dz * push
                                elif fixed[j]:
                                    a[0] -= dx * push; a[1] -= dy * push; a[2] -= dz * push
                                else:
                                    push *= 0.5
                                    a[0] -= dx * push; a[1] -= dy * push; a[2] -= dz * push
                                    b[0] += dx * push; b[1] += dy * push; b[2] += dz * push


def alt_ps(cycles, rounds_a, mult_a, rounds_b, mult_b, ribbon_rows, ribbon_width):
    turn_multipliers = []
    for _ in range(cycles):
        turn_multipliers.extend([mult_a] * rounds_a)
        turn_multipliers.extend([mult_b] * rounds_b)

    total_spine = len(turn_multipliers) * STRAND_STITCHES_PER_ROT
    row1_count = sum(m * STRAND_STITCHES_PER_ROT for m in turn_multipliers)
    total_vertices = total_spine + (row1_count * ribbon_rows)

    if total_vertices > MAX_STITCHES:
        raise ValueError(
            f"Spirale braucht {total_vertices} Stitches (Limit: {MAX_STITCHES})."
        )

    points, fixed, springs, faces = [], [], [], []
    linked = set()

    def add_spring(i, j, rest, stiffness=1.0):
        springs.append((i, j, rest, stiffness))
        linked.add((min(i, j), max(i, j)))

    row_height = float(ribbon_width) / float(ribbon_rows)

    # 1. Vertikale Mittelachse (Reihe 0) ab (0, 0, 0)
    spine_indices, spine_mults = [], []
    for turn_mult in turn_multipliers:
        for _ in range(STRAND_STITCHES_PER_ROT):
            idx = len(points)
            points.append([0.0, 0.0, -idx * STITCH_WIDTH])
            fixed.append(True)
            spine_indices.append(idx)
            spine_mults.append(turn_mult)
            if idx > 0:
                add_spring(idx - 1, idx, STITCH_WIDTH)

    # 2. Reihe 1: Vervielfältigung entlang der Mittelachse
    spine_children = []
    row1_indices, row1_angles, row1_zs = [], [], []
    angle_step = (2.0 * math.pi) / float(STRAND_STITCHES_PER_ROT)

    for s_pos, (s_idx, mult) in enumerate(zip(spine_indices, spine_mults)):
        base_angle = s_pos * angle_step
        base_z = points[s_idx][2]
        children = []

        for k in range(mult):
            c_idx = len(points)
            sub_angle = base_angle + (k / float(mult)) * angle_step
            sub_z = base_z - (k / float(mult)) * STITCH_WIDTH
            points.append([
                row_height * math.cos(sub_angle),
                row_height * math.sin(sub_angle),
                sub_z,
            ])
            fixed.append(False)
            children.append(c_idx)
            row1_angles.append(sub_angle)
            row1_zs.append(sub_z)

            add_spring(s_idx, c_idx, row_height)
            if row1_indices:
                add_spring(row1_indices[-1], c_idx, STITCH_WIDTH)
            row1_indices.append(c_idx)

        spine_children.append(children)

    for s_pos, s_idx in enumerate(spine_indices):
        children = spine_children[s_pos]
        for k in range(len(children) - 1):
            faces.append((s_idx, children[k], children[k + 1]))
        if s_pos + 1 < len(spine_indices):
            next_spine = spine_indices[s_pos + 1]
            next_first = spine_children[s_pos + 1][0]
            faces.append((s_idx, children[-1], next_first))
            faces.append((s_idx, next_first, next_spine))

    # 3. Weitere Reihen in die Tiefe (falls ribbon_rows > 1)
    prev_row = row1_indices
    for r in range(2, ribbon_rows + 1):
        curr_row = []
        radius = r * row_height
        for i, parent_idx in enumerate(prev_row):
            c_idx = len(points)
            ang = row1_angles[i]
            points.append([radius * math.cos(ang), radius * math.sin(ang), row1_zs[i]])
            fixed.append(False)
            add_spring(parent_idx, c_idx, row_height)
            if curr_row:
                add_spring(curr_row[-1], c_idx, STITCH_WIDTH)
            curr_row.append(c_idx)

        for i in range(len(prev_row) - 1):
            faces.append((prev_row[i], curr_row[i], curr_row[i + 1]))
            faces.append((prev_row[i], curr_row[i + 1], prev_row[i + 1]))
        prev_row = curr_row

    _relax_stitch_network(points, fixed, springs, linked, RELAX_ITERATIONS, 0.9 * STITCH_WIDTH)

    mesh = rg.Mesh()
    for p in points:
        mesh.Vertices.Add(p[0], p[1], p[2])
    for a, b, c in faces:
        mesh.Faces.AddFace(a, b, c)
    mesh.Normals.ComputeNormals()
    mesh.Compact()

    end = points[spine_indices[-1]]
    return mesh, rg.Point3d(end[0], end[1], end[2])


import math
import random
import Rhino.Geometry as rg

# Feste interne Konstanten
MAX_STITCHES = 3000
STITCH_WIDTH = 1.0
STITCH_HEIGHT = 2.0
CORAL_ITERATIONS = 100
CORAL_SEED = 101


def _relax_stitch_network(points, fixed, springs, linked, iterations, collision_distance):
    for _ in range(iterations):
        for i, j, rest, stiffness in springs:
            a = points[i]
            b = points[j]
            dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            if length < 1e-9 or (fixed[i] and fixed[j]):
                continue
            move = stiffness * (length - rest) / length
            if fixed[i]:
                b[0] -= dx * move; b[1] -= dy * move; b[2] -= dz * move
            elif fixed[j]:
                a[0] += dx * move; a[1] += dy * move; a[2] += dz * move
            else:
                move *= 0.5
                a[0] += dx * move; a[1] += dy * move; a[2] += dz * move
                b[0] -= dx * move; b[1] -= dy * move; b[2] -= dz * move

        grid = {}
        for index, point in enumerate(points):
            key = (
                int(math.floor(point[0] / collision_distance)),
                int(math.floor(point[1] / collision_distance)),
                int(math.floor(point[2] / collision_distance)),
            )
            grid.setdefault(key, []).append(index)

        for (cx, cy, cz), members in grid.items():
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        others = grid.get((cx + ox, cy + oy, cz + oz), ())
                        for i in members:
                            for j in others:
                                if j <= i or (i, j) in linked:
                                    continue
                                a = points[i]
                                b = points[j]
                                dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
                                dist_sq = dx * dx + dy * dy + dz * dz
                                if dist_sq < 1e-12 or dist_sq >= collision_distance ** 2:
                                    continue
                                dist = math.sqrt(dist_sq)
                                push = (collision_distance - dist) / dist
                                if fixed[i]:
                                    b[0] += dx * push; b[1] += dy * push; b[2] += dz * push
                                elif fixed[j]:
                                    a[0] -= dx * push; a[1] -= dy * push; a[2] -= dz * push
                                else:
                                    push *= 0.5
                                    a[0] -= dx * push; a[1] -= dy * push; a[2] -= dz * push
                                    b[0] += dx * push; b[1] += dy * push; b[2] += dz * push


def ps_cor_end(anchor_point, base_chain, first_round, increase, rounds):
    if anchor_point is None:
        anchor_point = rg.Point3d(0, 0, 0)
    elif not isinstance(anchor_point, rg.Point3d):
        raise TypeError(
            "anchor_point must be a Rhino.Geometry.Point3d; received {}. "
            "Connect Node 1's end_strand output to this input."
            .format(type(anchor_point).__name__)
        )

    # Stitch-Budget vorab prüfen
    count = first_round
    rc = first_round
    for r_idx in range(rounds):
        rc *= 1 if r_idx == 0 else increase
        count += rc
    if count > MAX_STITCHES:
        raise ValueError(
            f"Pseudosphere braucht {count} Stitches (Limit: {MAX_STITCHES})."
        )

    rng = random.Random(CORAL_SEED)
    points, fixed, springs, faces, rows = [], [], [], [], []
    linked = set()

    def add_spring(i, j, rest, stiffness=1.0):
        springs.append((i, j, rest, stiffness))
        linked.add((min(i, j), max(i, j)))

    # Runde 0: Geschlossener Basis-Ring um den Ankerpunkt
    base_radius = max(0.5, (base_chain * STITCH_WIDTH) / (2.0 * math.pi))
    ring_0 = []
    for i in range(first_round):
        ang = (2.0 * math.pi / first_round) * i
        idx = len(points)
        points.append([base_radius * (math.cos(ang) - 1.0), base_radius * math.sin(ang), 0.0])
        fixed.append(True)  # Basis-Ring bleibt am unteren Ende der Spirale verankert
        ring_0.append(idx)

    for i in range(first_round):
        add_spring(ring_0[i], ring_0[(i + 1) % first_round], STITCH_WIDTH)
    rows.append(ring_0)

    # Wachstumsrunden (geschlossener Kreis -> hyperbolische Rüschen)
    for r_idx in range(rounds):
        previous = rows[-1]
        per_stitch = 1 if r_idx == 0 else increase
        curr_count = len(previous) * per_stitch
        curr_radius = base_radius + (r_idx + 1) * STITCH_HEIGHT * 0.7
        current = []
        parent_children = []

        for parent in previous:
            children = []
            for _ in range(per_stitch):
                c_idx = len(points)
                ang = (2.0 * math.pi / curr_count) * len(current)
                z_jit = rng.uniform(-0.35, 0.35) - (r_idx + 1) * 0.3
                points.append([curr_radius * math.cos(ang), curr_radius * math.sin(ang), z_jit])
                fixed.append(False)
                children.append(c_idx)
                current.append(c_idx)
                add_spring(parent, c_idx, STITCH_HEIGHT)
            parent_children.append(children)

        # Geschlossene Ring-Federn
        for i in range(len(current)):
            add_spring(current[i], current[(i + 1) % len(current)], STITCH_WIDTH)

        # Mesh-Faces (geschlossen)
        for p_pos, children in enumerate(parent_children):
            parent = previous[p_pos]
            for k in range(len(children) - 1):
                faces.append((parent, children[k], children[k + 1]))
            next_parent = previous[(p_pos + 1) % len(previous)]
            next_child = parent_children[(p_pos + 1) % len(previous)][0]
            faces.append((parent, children[-1], next_child))
            faces.append((parent, next_child, next_parent))

        rows.append(current)

    _relax_stitch_network(points, fixed, springs, linked, CORAL_ITERATIONS, 0.9 * STITCH_WIDTH)

    mesh = rg.Mesh()
    for p in points:
        mesh.Vertices.Add(p[0] + anchor_point.X, p[1] + anchor_point.Y, p[2] + anchor_point.Z)
    for a, b, c in faces:
        mesh.Faces.AddFace(a, b, c)
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh
