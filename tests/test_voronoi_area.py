import numpy as np
from shapely.geometry import box
from src.geometry import voronoi_areas

def test_voronoi_areas_sum_to_boundary_approx():
    boundary = box(0, 0, 100, 100)
    points = np.array([[20,20],[80,20],[20,80],[80,80]], dtype=float)
    areas = voronoi_areas(points, boundary)
    assert abs(float(areas.sum()) - float(boundary.area)) < 1e-6
