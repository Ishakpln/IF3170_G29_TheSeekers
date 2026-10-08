import random

from .models import Axis, Orientation, Position
from .state import Placement, State


def _oriented_dimensions(problem, placement):
    package = problem.get_package(placement.package_id)
    return placement.orientation.apply(package.dimensions)


def _interval_overlap(start_a, size_a, start_b, size_b):
    return max(start_a, start_b) < min(start_a + size_a, start_b + size_b)


def _footprint_overlap(problem, placement_a, placement_b):
    position_a = placement_a.position
    position_b = placement_b.position
    size_a = _oriented_dimensions(problem, placement_a)
    size_b = _oriented_dimensions(problem, placement_b)

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


def _placements_overlap(problem, placement_a, placement_b):
    position_a = placement_a.position
    position_b = placement_b.position
    size_a = _oriented_dimensions(problem, placement_a)
    size_b = _oriented_dimensions(problem, placement_b)

    return (
        _footprint_overlap(problem, placement_a, placement_b)
        and _interval_overlap(
            position_a.z,
            size_a.height,
            position_b.z,
            size_b.height,
        )
    )


def is_valid_state(problem, state):
    placement_ids = [placement.package_id for placement in state.placements]

    if len(placement_ids) != len(set(placement_ids)):
        return False
    if set(placement_ids) != set(problem.packages_by_id):
        return False

    for placement in state.placements:
        position = placement.position
        outside = placement.truck_id is None and position is None
        inside = placement.truck_id is not None and position is not None

        if not outside and not inside:
            return False
        if not isinstance(placement.orientation, Orientation):
            return False

        if inside:
            if placement.truck_id not in problem.trucks_by_id:
                return False
            if not isinstance(position, Position):
                return False
            if not all(isinstance(value, int) for value in position.as_tuple()):
                return False

    for truck in problem.trucks:
        placements = state.get_placements_in_truck(truck.id)
        loaded_weight = sum(
            problem.get_package(placement.package_id).weight
            for placement in placements
        )

        if loaded_weight > truck.max_capacity:
            return False

        for placement in placements:
            position = placement.position
            size = _oriented_dimensions(problem, placement)

            if position.x < 0 or position.y < 0 or position.z < 0:
                return False
            if position.x + size.width > truck.dimensions.width:
                return False
            if position.y + size.length > truck.dimensions.length:
                return False
            if position.z + size.height > truck.dimensions.height:
                return False

        for index, placement_a in enumerate(placements):
            for placement_b in placements[index + 1 :]:
                if _placements_overlap(problem, placement_a, placement_b):
                    return False

        for upper in placements:
            upper_position = upper.position

            if upper_position.z == 0:
                continue

            has_support = False

            for lower in placements:
                if lower is upper:
                    continue

                lower_position = lower.position
                lower_size = _oriented_dimensions(problem, lower)
                lower_top = lower_position.z + lower_size.height

                if lower_top != upper_position.z:
                    continue
                if not _footprint_overlap(problem, lower, upper):
                    continue
                if problem.get_package(lower.package_id).is_fragile:
                    return False

                has_support = True

            if not has_support:
                return False

    return True


def state_signature(state):
    result = []

    for placement in state.placements:
        position = placement.position
        position_tuple = position.as_tuple() if position is not None else None
        result.append(
            (
                placement.package_id,
                placement.truck_id,
                position_tuple,
                placement.orientation,
            )
        )

    result.sort(key=lambda item: item[0])
    return tuple(result)


def swap(problem, state, first_package_id, second_package_id):
    if first_package_id == second_package_id:
        raise ValueError("package ids must be different")

    neighbor = state.copy()
    placement_a = neighbor.get_placement(first_package_id)
    placement_b = neighbor.get_placement(second_package_id)

    placement_a.truck_id, placement_b.truck_id = (
        placement_b.truck_id,
        placement_a.truck_id,
    )
    placement_a.position, placement_b.position = (
        placement_b.position,
        placement_a.position,
    )

    if state_signature(neighbor) == state_signature(state):
        return None
    if not is_valid_state(problem, neighbor):
        return None

    return neighbor


def move(problem, state, package_id, truck_id, position):
    if (truck_id is None) != (position is None):
        raise ValueError("truck_id and position must both be set or both be None")
    if truck_id is not None:
        problem.get_truck(truck_id)

    neighbor = state.copy()
    placement = neighbor.get_placement(package_id)
    placement.truck_id = truck_id
    placement.position = position

    if state_signature(neighbor) == state_signature(state):
        return None
    if not is_valid_state(problem, neighbor):
        return None

    return neighbor


def rotate(problem, state, package_id, axis):
    neighbor = state.copy()
    placement = neighbor.get_placement(package_id)
    placement.orientation = placement.orientation.rotated(axis)

    if state_signature(neighbor) == state_signature(state):
        return None
    if not is_valid_state(problem, neighbor):
        return None

    return neighbor


def generate_initial_state(
    problem,
    seed=None,
    placement_probability=0.7,
    max_attempts=100,
):
    if not problem.trucks:
        raise ValueError("at least one truck is required")

    rng = random.Random(seed)
    placements = [
        Placement(
            package.id,
            orientation=rng.choice(list(Orientation)),
        )
        for package in problem.packages
    ]
    state = State(placements)
    order = list(range(len(placements)))
    rng.shuffle(order)

    for index in order:
        placement = state.placements[index]

        if rng.random() > placement_probability:
            continue

        for _ in range(max_attempts):
            truck = rng.choice(problem.trucks)
            placement.orientation = rng.choice(list(Orientation))
            size = _oriented_dimensions(problem, placement)

            if size.width > truck.dimensions.width:
                continue
            if size.length > truck.dimensions.length:
                continue
            if size.height > truck.dimensions.height:
                continue

            placement.truck_id = truck.id
            placement.position = Position(
                rng.randint(0, truck.dimensions.width - size.width),
                rng.randint(0, truck.dimensions.length - size.length),
                0,
            )

            if is_valid_state(problem, state):
                break

            placement.truck_id = None
            placement.position = None

    return state


def _swap_neighbor(problem, state, rng):
    if len(state.placements) < 2:
        return None

    placement_a, placement_b = rng.sample(state.placements, 2)
    return swap(
        problem,
        state,
        placement_a.package_id,
        placement_b.package_id,
    )


def _move_neighbor(problem, state, rng):
    placement = rng.choice(state.placements)

    if placement.position is not None and rng.random() < 0.2:
        return move(problem, state, placement.package_id, None, None)

    truck = rng.choice(problem.trucks)
    size = _oriented_dimensions(problem, placement)

    if size.width > truck.dimensions.width:
        return None
    if size.length > truck.dimensions.length:
        return None
    if size.height > truck.dimensions.height:
        return None

    possible_z = [0]

    for lower in state.get_placements_in_truck(truck.id):
        if lower.package_id == placement.package_id:
            continue
        if problem.get_package(lower.package_id).is_fragile:
            continue

        lower_position = lower.position
        lower_size = _oriented_dimensions(problem, lower)
        top = lower_position.z + lower_size.height

        if top + size.height <= truck.dimensions.height:
            possible_z.append(top)

    return move(
        problem,
        state,
        placement.package_id,
        truck.id,
        Position(
            rng.randint(0, truck.dimensions.width - size.width),
            rng.randint(0, truck.dimensions.length - size.length),
            rng.choice(possible_z),
        ),
    )


def _rotate_neighbor(problem, state, rng):
    placement = rng.choice(state.placements)
    return rotate(
        problem,
        state,
        placement.package_id,
        rng.choice(list(Axis)),
    )


def generate_random_neighbor(problem, state, seed=None, max_attempts=100):
    if not problem.trucks:
        raise ValueError("problem has no trucks")
    if not state.placements:
        raise ValueError("state has no placements")

    rng = random.Random(seed)
    operations = [_move_neighbor, _rotate_neighbor]

    if len(state.placements) >= 2:
        operations.append(_swap_neighbor)

    for _ in range(max_attempts):
        operation = rng.choice(operations)
        neighbor = operation(problem, state, rng)

        if neighbor is not None:
            return neighbor

    raise RuntimeError("failed to generate a valid neighbor")


def generate_all_neighbors(problem, state):
    if not problem.trucks:
        raise ValueError("problem has no trucks")
    if not state.placements:
        raise ValueError("state has no placements")

    seen = {state_signature(state)}

    for first_index in range(len(state.placements)):
        for second_index in range(first_index + 1, len(state.placements)):
            neighbor = swap(
                problem,
                state,
                state.placements[first_index].package_id,
                state.placements[second_index].package_id,
            )

            if neighbor is None:
                continue

            signature = state_signature(neighbor)

            if signature not in seen:
                seen.add(signature)
                yield neighbor

    for original_placement in state.placements:
        if original_placement.position is not None:
            neighbor = move(
                problem,
                state,
                original_placement.package_id,
                None,
                None,
            )

            if neighbor is not None:
                signature = state_signature(neighbor)

                if signature not in seen:
                    seen.add(signature)
                    yield neighbor

        size = _oriented_dimensions(problem, original_placement)

        for truck in problem.trucks:
            if size.width > truck.dimensions.width:
                continue
            if size.length > truck.dimensions.length:
                continue
            if size.height > truck.dimensions.height:
                continue

            possible_z = {0}

            for lower in state.get_placements_in_truck(truck.id):
                if lower.package_id == original_placement.package_id:
                    continue
                if problem.get_package(lower.package_id).is_fragile:
                    continue

                lower_position = lower.position
                lower_size = _oriented_dimensions(problem, lower)
                top = lower_position.z + lower_size.height

                if top + size.height <= truck.dimensions.height:
                    possible_z.add(top)

            for x in range(truck.dimensions.width - size.width + 1):
                for y in range(truck.dimensions.length - size.length + 1):
                    for z in sorted(possible_z):
                        neighbor = move(
                            problem,
                            state,
                            original_placement.package_id,
                            truck.id,
                            Position(x, y, z),
                        )

                        if neighbor is None:
                            continue

                        signature = state_signature(neighbor)

                        if signature not in seen:
                            seen.add(signature)
                            yield neighbor

    for placement in state.placements:
        for axis in Axis:
            neighbor = rotate(
                problem,
                state,
                placement.package_id,
                axis,
            )

            if neighbor is None:
                continue

            signature = state_signature(neighbor)

            if signature not in seen:
                seen.add(signature)
                yield neighbor
