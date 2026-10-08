from copy import deepcopy


class State:
    def __init__(self, trucks, packages, value=0):
        if isinstance(trucks, (list, tuple)):
            self.trucks = list(trucks)
        else:
            self.trucks = [trucks]

        self.packages = packages
        self.value = value

    def get_inside_packages(self):
        return [
            package
            for package in self.packages
            if package.truck_index is not None and package.position is not None
        ]

    def get_outside_packages(self):
        return [
            package
            for package in self.packages
            if package.truck_index is None and package.position is None
        ]

    def get_packages_in_truck(self, truck_index):
        return [
            package
            for package in self.packages
            if package.truck_index == truck_index and package.position is not None
        ]

    def copy(self):
        return deepcopy(self)
