import random
from copy import deepcopy

from .models import Axis, Orientation, Position
from .objective import evaluate_state
from .state import State


def _interval_overlap(start_a, size_a, start_b, size_b):
    return max(start_a, start_b) < min(start_a + size_a, start_b + size_b)


def _footprint_overlap(package_a, package_b):
    position_a = package_a.position
    position_b = package_b.position
    size_a = package_a.get_oriented_dimensions()
    size_b = package_b.get_oriented_dimensions()

    return _interval_overlap(
        position_a.x,
        size_a.width,
        position_b.x,
        size_b.width,
    ) and _interval_overlap(
        position_a.y,
        size_a.length,
        position_b.y,
        size_b.length,
    )


def _packages_overlap(package_a, package_b):
    position_a = package_a.position
    position_b = package_b.position
    size_a = package_a.get_oriented_dimensions()
    size_b = package_b.get_oriented_dimensions()

    return (
        _footprint_overlap(package_a, package_b)
        and _interval_overlap(
            position_a.z,
            size_a.height,
            position_b.z,
            size_b.height,
        )
    )


def is_valid_state(state):
    for package in state.packages:
        outside = package.truck_index is None and package.position is None
        inside = package.truck_index is not None and package.position is not None

        if not outside and not inside:
            return False

        if inside:
            if not isinstance(package.truck_index, int):
                return False
            if package.truck_index < 0 or package.truck_index >= len(state.trucks):
                return False

    for truck_index, truck in enumerate(state.trucks):
        packages = state.get_packages_in_truck(truck_index)
        truck_size = truck.dimensions

        if sum(package.weight for package in packages) > truck.max_capacity:
            return False

        for package in packages:
            position = package.position
            size = package.get_oriented_dimensions()

            if position.x < 0 or position.y < 0 or position.z < 0:
                return False
            if position.x + size.width > truck_size.width:
                return False
            if position.y + size.length > truck_size.length:
                return False
            if position.z + size.height > truck_size.height:
                return False

        for index, package_a in enumerate(packages):
            for package_b in packages[index + 1 :]:
                if _packages_overlap(package_a, package_b):
                    return False

        for upper in packages:
            if upper.position.z == 0:
                continue

            has_support = False

            for lower in packages:
                if lower is upper:
                    continue

                lower_size = lower.get_oriented_dimensions()
                lower_top = lower.position.z + lower_size.height

                if lower_top != upper.position.z:
                    continue
                if not _footprint_overlap(lower, upper):
                    continue
                if lower.is_fragile:
                    return False

                has_support = True

            if not has_support:
                return False

    return True


def state_signature(state):
    result = []

    for package in state.packages:
        position = None
        if package.position is not None:
            position = package.position.as_tuple()

        result.append(
            (package.id, package.truck_index, position, package.orientation)
        )

    result.sort(key=lambda item: item[0])
    return tuple(result)


def _find_package(state, package_id):
    for package in state.packages:
        if package.id == package_id:
            return package

    raise ValueError(f"package {package_id!r} not found")


def swap(state, first_package_id, second_package_id, objective_number=1):
    if first_package_id == second_package_id:
        raise ValueError("package ids must be different")

    neighbor = state.copy()
    package_a = _find_package(neighbor, first_package_id)
    package_b = _find_package(neighbor, second_package_id)

    package_a.truck_index, package_b.truck_index = (
        package_b.truck_index,
        package_a.truck_index,
    )
    package_a.position, package_b.position = (
        package_b.position,
        package_a.position,
    )

    if state_signature(neighbor) == state_signature(state):
        return None
    if not is_valid_state(neighbor):
        return None

    evaluate_state(neighbor, objective_number)
    return neighbor


def move(state, package_id, truck_index, position, objective_number=1):
    if (truck_index is None) != (position is None):
        raise ValueError("truck_index and position must both be set or both be None")

    neighbor = state.copy()
    package = _find_package(neighbor, package_id)

    if truck_index is None:
        package.move_outside()
    else:
        package.move(truck_index, position)

    if state_signature(neighbor) == state_signature(state):
        return None
    if not is_valid_state(neighbor):
        return None

    evaluate_state(neighbor, objective_number)
    return neighbor


def rotate(state, package_id, axis, objective_number=1):
    neighbor = state.copy()
    package = _find_package(neighbor, package_id)
    package.rotate(axis)

    if state_signature(neighbor) == state_signature(state):
        return None
    if not is_valid_state(neighbor):
        return None

    evaluate_state(neighbor, objective_number)
    return neighbor


def generate_initial_state(
    trucks,
    packages,
    seed=None,
    placement_probability=0.7,
    max_attempts=100,
    objective_number=1,
):
    rng = random.Random(seed)
    generated_packages = deepcopy(packages)
    state = State(deepcopy(trucks), generated_packages)

    if not state.trucks:
        raise ValueError("at least one truck is required")

    for package in generated_packages:
        package.move_outside()
        package.orientation = rng.choice(list(Orientation))

    order = list(range(len(generated_packages)))
    rng.shuffle(order)

    for index in order:
        package = state.packages[index]

        if rng.random() > placement_probability:
            continue

        for _ in range(max_attempts):
            truck_index = rng.randrange(len(state.trucks))
            truck_size = state.trucks[truck_index].dimensions
            package.orientation = rng.choice(list(Orientation))
            size = package.get_oriented_dimensions()

            if size.width > truck_size.width:
                continue
            if size.length > truck_size.length:
                continue
            if size.height > truck_size.height:
                continue

            package.move(
                truck_index,
                Position(
                    rng.randint(0, truck_size.width - size.width),
                    rng.randint(0, truck_size.length - size.length),
                    0,
                ),
            )

            if is_valid_state(state):
                break

            package.move_outside()

    evaluate_state(state, objective_number)
    return state


def _swap_neighbor(state, rng, objective_number):
    if len(state.packages) < 2:
        return None

    package_a, package_b = rng.sample(state.packages, 2)
    return swap(state, package_a.id, package_b.id, objective_number)


def _move_neighbor(state, rng, objective_number):
    package = rng.choice(state.packages)

    if package.position is not None and rng.random() < 0.2:
        return move(state, package.id, None, None, objective_number)

    truck_index = rng.randrange(len(state.trucks))
    truck_size = state.trucks[truck_index].dimensions
    size = package.get_oriented_dimensions()

    if size.width > truck_size.width:
        return None
    if size.length > truck_size.length:
        return None
    if size.height > truck_size.height:
        return None

    possible_z = [0]

    for lower in state.get_packages_in_truck(truck_index):
        if lower is package or lower.is_fragile:
            continue

        lower_size = lower.get_oriented_dimensions()
        top = lower.position.z + lower_size.height

        if top + size.height <= truck_size.height:
            possible_z.append(top)

    return move(
        state,
        package.id,
        truck_index,
        Position(
            rng.randint(0, truck_size.width - size.width),
            rng.randint(0, truck_size.length - size.length),
            rng.choice(possible_z),
        ),
        objective_number,
    )


def _rotate_neighbor(state, rng, objective_number):
    package = rng.choice(state.packages)
    return rotate(
        state,
        package.id,
        rng.choice(list(Axis)),
        objective_number,
    )


def generate_random_neighbor(
    state,
    objective_number=1,
    seed=None,
    max_attempts=100,
):
    if not state.trucks:
        raise ValueError("state has no trucks")
    if not state.packages:
        raise ValueError("state has no packages")

    rng = random.Random(seed)
    operations = [_move_neighbor, _rotate_neighbor]

    if len(state.packages) >= 2:
        operations.append(_swap_neighbor)

    for _ in range(max_attempts):
        operation = rng.choice(operations)
        neighbor = operation(state, rng, objective_number)

        if neighbor is None:
            continue

        return neighbor

    raise RuntimeError("failed to generate a valid neighbor")


def generate_all_neighbors(state, objective_number=1):
    if not state.trucks:
        raise ValueError("state has no trucks")
    if not state.packages:
        raise ValueError("state has no packages")

    seen = {state_signature(state)}

    for first_index in range(len(state.packages)):
        for second_index in range(first_index + 1, len(state.packages)):
            neighbor = swap(
                state,
                state.packages[first_index].id,
                state.packages[second_index].id,
                objective_number,
            )

            if neighbor is None:
                continue

            signature = state_signature(neighbor)

            if signature in seen:
                continue

            seen.add(signature)
            yield neighbor

    for package_index, original_package in enumerate(state.packages):
        if original_package.position is not None:
            neighbor = move(
                state,
                original_package.id,
                None,
                None,
                objective_number,
            )

            if neighbor is not None:
                signature = state_signature(neighbor)

                if signature not in seen:
                    seen.add(signature)
                    yield neighbor

        size = original_package.get_oriented_dimensions()

        for truck_index, truck in enumerate(state.trucks):
            truck_size = truck.dimensions

            if size.width > truck_size.width:
                continue
            if size.length > truck_size.length:
                continue
            if size.height > truck_size.height:
                continue

            possible_z = {0}

            for lower in state.get_packages_in_truck(truck_index):
                if lower is original_package or lower.is_fragile:
                    continue

                lower_size = lower.get_oriented_dimensions()
                top = lower.position.z + lower_size.height

                if top + size.height <= truck_size.height:
                    possible_z.add(top)

            for x in range(truck_size.width - size.width + 1):
                for y in range(truck_size.length - size.length + 1):
                    for z in sorted(possible_z):
                        neighbor = move(
                            state,
                            original_package.id,
                            truck_index,
                            Position(x, y, z),
                            objective_number,
                        )

                        if neighbor is None:
                            continue

                        signature = state_signature(neighbor)

                        if signature in seen:
                            continue

                        seen.add(signature)
                        yield neighbor

    for package_index in range(len(state.packages)):
        for axis in Axis:
            neighbor = rotate(
                state,
                state.packages[package_index].id,
                axis,
                objective_number,
            )

            if neighbor is None:
                continue

            signature = state_signature(neighbor)

            if signature in seen:
                continue

            seen.add(signature)
            yield neighbor
