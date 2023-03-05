from typing import List, Tuple, Any


def single_column_result_to_list(result_column: List[Tuple[Any]]) -> List[Any]:
    return [x[0] for x in result_column]