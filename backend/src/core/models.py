from enum import Enum


class Dimensions:
    def __init__(self, width, length, height):
        self.width = width
        self.length = length
        self.height = height

    def as_tuple(self):
        return self.width, self.length, self.height


class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def as_tuple(self):
        return self.x, self.y, self.z


class Axis(Enum):
    X = "x"
    Y = "y"
    Z = "z"


class Orientation(Enum):
    WLH = (0, 1, 2)
    WHL = (0, 2, 1)
    LWH = (1, 0, 2)
    LHW = (1, 2, 0)
    HWL = (2, 0, 1)
    HLW = (2, 1, 0)

    def apply(self, dimensions):
        original = dimensions.as_tuple()
        result = [original[index] for index in self.value]
        return Dimensions(*result)

    def rotated(self, axis):
        axis = Axis(axis)
        order = list(self.value)

        if axis == Axis.X:
            order[1], order[2] = order[2], order[1]
        elif axis == Axis.Y:
            order[0], order[2] = order[2], order[0]
        else:
            order[0], order[1] = order[1], order[0]

        return Orientation(tuple(order))


class Package:
    def __init__(
        self,
        package_id,
        dimensions,
        value,
        weight,
        is_fragile,
        eta,
    ):
        self.id = package_id
        self.dimensions = dimensions
        self.value = value
        self.weight = weight
        self.is_fragile = is_fragile
        self.eta = eta


class Truck:
    def __init__(self, truck_id, dimensions, max_capacity):
        self.id = truck_id
        self.dimensions = dimensions
        self.max_capacity = max_capacity


class Problem:
    def __init__(self, trucks, packages):
        self.trucks = list(trucks)
        self.packages = list(packages)
        self.trucks_by_id = {truck.id: truck for truck in self.trucks}
        self.packages_by_id = {package.id: package for package in self.packages}

        if len(self.trucks_by_id) != len(self.trucks):
            raise ValueError("truck ids must be unique")
        if len(self.packages_by_id) != len(self.packages):
            raise ValueError("package ids must be unique")

    def get_truck(self, truck_id):
        if truck_id not in self.trucks_by_id:
            raise ValueError(f"truck {truck_id!r} not found")

        return self.trucks_by_id[truck_id]

    def get_package(self, package_id):
        if package_id not in self.packages_by_id:
            raise ValueError(f"package {package_id!r} not found")

        return self.packages_by_id[package_id]
