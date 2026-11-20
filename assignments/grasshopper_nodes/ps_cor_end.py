import math
import random
import Rhino.Geometry as rg

MAX_STITCHES = 3000
STITCH_WIDTH = 1.0
STITCH_HEIGHT = 2.0
CORAL_ITERATIONS = 100
CORAL_SEED = 101


def _relax_stitch_network(points, fixed, springs, linked, iterations, collision_distance):
    for _ in range(iterations):
        for i, j, rest_length, stiffness in springs:
            a = points[i]
            b = points[j]
            dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            if length < 1e-9 or (fixed[i] and fixed[j]):
                continue
            move = stiffness * (length - rest_length) / length
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
                                if fixed[i] and fixed[j]:
                                    continue
                                a = points[i]
                                b = points[j]
                                dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
                                distance_sq = dx * dx + dy * dy + dz * dz
                                if distance_sq < 1e-12 or distance_sq >= collision_distance ** 2:
                                    continue
                                distance = math.sqrt(distance_sq)
                                push = (collision_distance - distance) / distance
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


def _make_mesh(points, faces, anchor):
    mesh = rg.Mesh()
    for point in points:
        mesh.Vertices.Add(
            point[0] + anchor.X,
            point[1] + anchor.Y,
            point[2] + anchor.Z,
        )
    for a, b, c in faces:
        mesh.Faces.AddFace(a, b, c)
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


anchor_point = anchor_point if anchor_point is not None else rg.Point3d(0, 0, 0)
base_chain = int(base_chain) if base_chain is not None else 4
first_round = int(first_round) if first_round is not None else 12
increase = int(increase) if increase is not None else 2
rounds = int(rounds) if rounds is not None else 4

if base_chain < 1 or first_round < 3 or increase < 1 or rounds < 1:
    raise ValueError("base_chain/increase/rounds must be positive and first_round at least 3.")

base_radius = max(0.5, (base_chain * STITCH_WIDTH) / (2.0 * math.pi))
estimated_vertices = first_round
round_count = first_round
for round_index in range(rounds):
    per_stitch = 1 if round_index == 0 else increase
    round_count *= per_stitch
    estimated_vertices += round_count
if estimated_vertices > MAX_STITCHES:
    raise ValueError(
        "ps_cor_end needs {} stitches (limit: {}). Reduce rounds or increase."
        .format(estimated_vertices, MAX_STITCHES)
    )

rng = random.Random(CORAL_SEED)
points = []
fixed = []
springs = []
linked = set()
faces = []
rows = []


def add_spring(i, j, rest_length, stiffness=1.0):
    key = (min(i, j), max(i, j))
    if key not in linked:
        springs.append((i, j, rest_length, stiffness))
        linked.add(key)


def add_face(a, b, c):
    faces.append((a, b, c))
    for i, j in ((a, b), (b, c), (c, a)):
        dx = points[j][0] - points[i][0]
        dy = points[j][1] - points[i][1]
        dz = points[j][2] - points[i][2]
        add_spring(i, j, math.sqrt(dx * dx + dy * dy + dz * dz))


base_ring = []
for index in range(first_round):
    angle = 2.0 * math.pi * index / float(first_round)
    point_index = len(points)
    points.append([
        base_radius * math.cos(angle),
        base_radius * math.sin(angle),
        0.0,
    ])
    fixed.append(True)
    base_ring.append(point_index)

for index in range(first_round):
    add_spring(base_ring[index], base_ring[(index + 1) % first_round], STITCH_WIDTH)
rows.append(base_ring)

for round_index in range(rounds):
    previous = rows[-1]
    per_stitch = 1 if round_index == 0 else increase
    current_count = len(previous) * per_stitch
    current_radius = base_radius + (round_index + 1) * STITCH_HEIGHT * 0.7
    current = []
    parent_children = []

    for parent in previous:
        children = []
        for _ in range(per_stitch):
            child = len(points)
            angle = 2.0 * math.pi * len(current) / float(current_count)
            z_jitter = rng.uniform(-0.35, 0.35) - (round_index + 1) * 0.3
            points.append([
                current_radius * math.cos(angle),
                current_radius * math.sin(angle),
                z_jitter,
            ])
            fixed.append(False)
            children.append(child)
            current.append(child)
            add_spring(parent, child, STITCH_HEIGHT)
        parent_children.append(children)

    for index in range(len(current)):
        add_spring(current[index], current[(index + 1) % len(current)], STITCH_WIDTH)

    for parent_index, children in enumerate(parent_children):
        parent = previous[parent_index]
        for child_index in range(len(children) - 1):
            add_face(parent, children[child_index], children[child_index + 1])
        next_parent = previous[(parent_index + 1) % len(previous)]
        next_child = parent_children[(parent_index + 1) % len(previous)][0]
        add_face(parent, children[-1], next_child)
        add_face(parent, next_child, next_parent)
    rows.append(current)

_relax_stitch_network(
    points,
    fixed,
    springs,
    linked,
    CORAL_ITERATIONS,
    0.9 * STITCH_WIDTH,
)

coral_mesh = _make_mesh(points, faces, anchor_point)
