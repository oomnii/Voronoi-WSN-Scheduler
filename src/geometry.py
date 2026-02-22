import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

def field_polygon(width: float, height: float) -> Polygon:
    return box(0.0, 0.0, width, height)

def random_points(n: int, width: float, height: float, rng: np.random.Generator) -> np.ndarray:
    xs = rng.uniform(0, width, size=n)
    ys = rng.uniform(0, height, size=n)
    return np.column_stack([xs, ys])

def _voronoi_finite_polygons_2d(vor: Voronoi, radius: float | None = None):
    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions: list[list[int]] = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max() * 2

    all_ridges: dict[int, list[tuple[int, int, int]]] = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    for p1, region_idx in enumerate(vor.point_region):
        vertices = vor.regions[region_idx]
        if all(v >= 0 for v in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0 and v2 >= 0:
                continue

            t = vor.points[p2] - vor.points[p1]
            t /= (np.linalg.norm(t) + 1e-12)
            n = np.array([-t[1], t[0]])

            midpoint = (vor.points[p1] + vor.points[p2]) / 2
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_vertices.append(far_point.tolist())
            new_region.append(len(new_vertices) - 1)

        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = [v for _, v in sorted(zip(angles, new_region))]
        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)

def bounded_voronoi_cells(points: np.ndarray, boundary: Polygon) -> list[Polygon]:
    if len(points) < 2:
        return [boundary]
    vor = Voronoi(points)
    regions, vertices = _voronoi_finite_polygons_2d(vor, radius=1e6)
    cells: list[Polygon] = []
    for region in regions:
        poly = Polygon(vertices[region])
        clipped = poly.intersection(boundary)
        cells.append(clipped if not clipped.is_empty else Polygon())
    return cells

def voronoi_areas(points: np.ndarray, boundary: Polygon) -> np.ndarray:
    cells = bounded_voronoi_cells(points, boundary)
    return np.array([c.area for c in cells], dtype=float)

def sensing_coverage_union(points: np.ndarray, sensing_radius: float, boundary: Polygon):
    if len(points) == 0:
        return boundary.buffer(0).difference(boundary)
    disks = [Point(float(p[0]), float(p[1])).buffer(float(sensing_radius)) for p in points]
    return unary_union(disks).intersection(boundary)
