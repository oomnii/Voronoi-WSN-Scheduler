import numpy as np
from shapely.geometry import box
from src.scheduling import schedule_by_voronoi_threshold

def test_threshold_zero_keeps_all():
    boundary = box(0, 0, 100, 100)
    points = np.array([[10,10],[90,10],[10,90],[90,90],[50,50]], dtype=float)
    active, backups = schedule_by_voronoi_threshold(points, boundary, threshold_area=0.0)
    assert active.sum() == len(points)
    assert len(backups) == 0
