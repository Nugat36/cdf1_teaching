import math
import Rhino.Geometry as rg

MAX_STITCHES = 3000
STITCH_WIDTH = 1.0
STRAND_STITCHES_PER_ROT = 8
RELAX_ITERATIONS = 80


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


def _make_mesh(points, faces):
    mesh = rg.Mesh()
    for point in points:
        mesh.Vertices.Add(point[0], point[1], point[2])
    for a, b, c in faces:
        mesh.Faces.AddFace(a, b, c)
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


cycles = int(cycles) if cycles is not None else 2
rounds_a = int(rounds_a) if rounds_a is not None else 3
mult_a = int(mult_a) if mult_a is not None else 2
rounds_b = int(rounds_b) if rounds_b is not None else 2
mult_b = int(mult_b) if mult_b is not None else 3
ribbon_rows = int(ribbon_rows) if ribbon_rows is not None else 2
ribbon_width = float(ribbon_width) if ribbon_width is not None else 3.5

if cycles < 1 or rounds_a < 1 or rounds_b < 1:
    raise ValueError("cycles, rounds_a and rounds_b must be at least 1.")
if mult_a < 1 or mult_b < 1 or ribbon_rows < 1:
    raise ValueError("mult_a, mult_b and ribbon_rows must be at least 1.")
if ribbon_width <= 0:
    raise ValueError("ribbon_width must be greater than 0.")

turn_multipliers = []
for _ in range(cycles):
    turn_multipliers.extend([mult_a] * rounds_a)
    turn_multipliers.extend([mult_b] * rounds_b)

total_spine = len(turn_multipliers) * STRAND_STITCHES_PER_ROT
row1_count = sum(
    multiplier * STRAND_STITCHES_PER_ROT
    for multiplier in turn_multipliers
)
total_vertices = total_spine + row1_count * ribbon_rows
if total_vertices > MAX_STITCHES:
    raise ValueError(
        "alt_ps needs {} stitches (limit: {}). Reduce cycles, rounds, "
        "multipliers or ribbon_rows.".format(total_vertices, MAX_STITCHES)
    )

row_height = ribbon_width / float(ribbon_rows)
angle_step = (2.0 * math.pi) / float(STRAND_STITCHES_PER_ROT)
points = []
fixed = []
springs = []
linked = set()
faces = []


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


spine_indices = []
spine_multipliers = []
for turn_multiplier in turn_multipliers:
    for _ in range(STRAND_STITCHES_PER_ROT):
        index = len(points)
        points.append([0.0, 0.0, -index * STITCH_WIDTH])
        fixed.append(True)
        spine_indices.append(index)
        spine_multipliers.append(turn_multiplier)
        if index:
            add_spring(index - 1, index, STITCH_WIDTH)

spine_children = []
row1_indices = []
row1_angles = []
row1_zs = []
for spine_position, (spine_index, multiplier) in enumerate(
    zip(spine_indices, spine_multipliers)
):
    base_angle = spine_position * angle_step
    base_z = points[spine_index][2]
    children = []
    for child_number in range(multiplier):
        child_index = len(points)
        fraction = child_number / float(multiplier)
        angle = base_angle + fraction * angle_step
        z = base_z - fraction * STITCH_WIDTH
        points.append([
            row_height * math.cos(angle),
            row_height * math.sin(angle),
            z,
        ])
        fixed.append(False)
        children.append(child_index)
        row1_angles.append(angle)
        row1_zs.append(z)
        add_spring(spine_index, child_index, row_height)
        if row1_indices:
            add_spring(row1_indices[-1], child_index, STITCH_WIDTH)
        row1_indices.append(child_index)
    spine_children.append(children)

for spine_position, spine_index in enumerate(spine_indices):
    children = spine_children[spine_position]
    for child_position in range(len(children) - 1):
        add_face(spine_index, children[child_position], children[child_position + 1])
    if spine_position + 1 < len(spine_indices):
        next_spine = spine_indices[spine_position + 1]
        next_first_child = spine_children[spine_position + 1][0]
        add_face(spine_index, children[-1], next_first_child)
        add_face(spine_index, next_first_child, next_spine)

previous_row = row1_indices
for row_number in range(2, ribbon_rows + 1):
    current_row = []
    radius = row_number * row_height
    for index, parent_index in enumerate(previous_row):
        child_index = len(points)
        angle = row1_angles[index]
        points.append([
            radius * math.cos(angle),
            radius * math.sin(angle),
            row1_zs[index],
        ])
        fixed.append(False)
        current_row.append(child_index)
        add_spring(parent_index, child_index, row_height)
        if index:
            add_spring(current_row[index - 1], child_index, STITCH_WIDTH)

    for index in range(len(previous_row) - 1):
        add_face(previous_row[index], current_row[index], current_row[index + 1])
        add_face(previous_row[index], current_row[index + 1], previous_row[index + 1])
    previous_row = current_row

_relax_stitch_network(
    points,
    fixed,
    springs,
    linked,
    RELAX_ITERATIONS,
    0.9 * STITCH_WIDTH,
)

spiral_mesh = _make_mesh(points, faces)
end_index = spine_indices[-1]
end_strand = rg.Point3d(
    points[end_index][0],
    points[end_index][1],
    points[end_index][2],
)
