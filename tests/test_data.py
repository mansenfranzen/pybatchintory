import datetime


def ts(timestamp: str) -> datetime.datetime:
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")


INVENTORY = [{'meta_table': 'test_meta',
              'job': 'j1',
              'job_identifier': 'j1_1',
              'job_result': '{file: 1}',
              'processing_start': ts('2023-01-01 10:00:00'),
              'processing_end': ts('2023-01-01 11:00:00'),
              'meta_id_start': 0,
              'meta_id_end': 4,
              'weight': 8,
              'count': 5,
              'attempt': 1,
              'status': 'succeeded',
              'config': {"foo": "bar"},
              'logging': 'log1'},
             {'meta_table': 'test_meta',
              'job': 'j2',
              'job_identifier': 'j2_1',
              'job_result': '{file: 2}',
              'processing_start': ts('2023-01-01 12:00:00'),
              'processing_end': ts('2023-01-01 13:00:00'),
              'meta_id_start': 5,
              'meta_id_end': 8,
              'weight': 23,
              'count': 4,
              'attempt': 1,
              'status': 'running',
              'config': {"bar": "foo"},
              'logging': 'log2'}]
