import datetime


def ts(timestamp: str) -> datetime.datetime:
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")


def inventory_data(table_name):
    return [{'meta_table': table_name,
              'job': 'j1',
              'job_identifier': 'j1_1',
              'job_result_item': '{file: 1}',
              'processing_start': ts('2023-01-01 10:00:00'),
              'processing_end': ts('2023-01-01 11:00:00'),
              'batch_id_start': 0,
              'batch_id_end': 4,
              'batch_weight': 8,
              'batch_count': 5,
              'attempt': 1,
              'status': 'succeeded',
              'config': {"foo": "bar"},
              'logging': 'log1'},
             {'meta_table': table_name,
              'job': 'j2',
              'job_identifier': 'j2_1',
              'job_result_item': '{file: 2}',
              'processing_start': ts('2023-01-01 12:00:00'),
              'processing_end': ts('2023-01-01 13:00:00'),
              'batch_id_start': 5,
              'batch_id_end': 8,
              'batch_weight': 23,
              'batch_count': 4,
              'attempt': 1,
              'status': 'running',
              'config': {"bar": "foo"},
              'logging': 'log2'}]

META = [{'id': 0, 'item': 'f0', 'weight': 0},
        {'id': 1, 'item': 'f1', 'weight': 2},
        {'id': 2, 'item': 'f2', 'weight': 4},
        {'id': 3, 'item': 'f3', 'weight': 6},
        {'id': 4, 'item': 'f4', 'weight': 8},
        {'id': 5, 'item': 'f5', 'weight': 10},
        {'id': 6, 'item': 'f6', 'weight': 12},
        {'id': 7, 'item': 'f7', 'weight': 14},
        {'id': 8, 'item': 'f8', 'weight': 16},
        {'id': 9, 'item': 'f9', 'weight': 18}]
