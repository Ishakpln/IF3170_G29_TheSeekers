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
        position=None,
        orientation=Orientation.WLH,
        truck_index=None,
    ):
        self.id = package_id
        self.dimensions = dimensions
        self.value = value
        self.weight = weight
        self.is_fragile = is_fragile
        self.eta = eta
        self.position = position
        self.orientation = orientation
        self.truck_index = truck_index

    def get_oriented_dimensions(self):
        return self.orientation.apply(self.dimensions)

    def move(self, truck_index, position):
        self.truck_index = truck_index
        self.position = position

    def move_outside(self):
        self.truck_index = None
        self.position = None

    def rotate(self, axis):
        self.orientation = self.orientation.rotated(axis)


class Truck:
    def __init__(self, dimensions, max_capacity):
        self.dimensions = dimensions
        self.max_capacity = max_capacity
