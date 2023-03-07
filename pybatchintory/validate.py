"""This module contains validation functions."""
from typing import Union

from pybatchintory.logging import logger


def id_min_greater_equals_max_meta_id(
        id_user_min: int,
        id_meta_max: int
) -> bool:
    """Check if user provided `id_min` is greater equals the max id value from
    meta table.

    """

    if id_user_min >= id_meta_max:
        logger.info(f"User provided `id_min` ({id_user_min}) is greater than "
                    f"max id from meta table ({id_meta_max}).")
        return True

    return False


def max_inventory_id_greater_equals_max_meta_id(
        id_inventory_max: int,
        id_meta_max: int
) -> bool:
    """Check if max meta id from inventory table is greater equals the max id
    value from meta table.

    """

    if id_inventory_max >= id_meta_max:
        logger.info(f"Max id from inventory table ({id_inventory_max}) is "
                    f"greater equals max id from meta table ({id_meta_max}")
        return True

    return False


def acquire_batch_is_invalid(id_user_min: Union[float, int],
                             id_meta_max: int,
                             id_inventory_max: int) -> bool:
    checks = [
        id_min_greater_equals_max_meta_id(
            id_user_min=id_user_min,
            id_meta_max=id_meta_max),
        max_inventory_id_greater_equals_max_meta_id(
            id_inventory_max=id_inventory_max,
            id_meta_max=id_meta_max)
    ]

    return any(checks)
