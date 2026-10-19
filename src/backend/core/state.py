from copy import deepcopy

from .models import Orientation


class Placement:
    def __init__(
        self,
        package_id,
        position=None,
        orientation=Orientation.WLH,
        truck_id=None,
    ):
        self.package_id = package_id
        self.position = position
        self.orientation = orientation
        self.truck_id = truck_id


class State:
    def __init__(self, placements):
        self.placements = list(placements)

    def get_inside_placements(self):
        return [
            placement
            for placement in self.placements
            if placement.truck_id is not None
            and placement.position is not None
        ]

    def get_outside_placements(self):
        return [
            placement
            for placement in self.placements
            if placement.truck_id is None
            and placement.position is None
        ]

    def get_placements_in_truck(self, truck_id):
        return [
            placement
            for placement in self.placements
            if placement.truck_id == truck_id
            and placement.position is not None
        ]

    def get_placement(self, package_id):
        for placement in self.placements:
            if placement.package_id == package_id:
                return placement

        raise ValueError(f"package {package_id!r} not found in state")

    def copy(self):
        return deepcopy(self)
