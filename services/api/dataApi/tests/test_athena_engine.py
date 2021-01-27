import common.services.athena_engine as engine


def add_dummy_data(bucket, prefix):
    dummy = [
        f'{prefix}/dummy.txt',
        f'{prefix}/dummy2.txt',
        f'{prefix}/dummy3.txt',
        f'{prefix}/dummy4.txt',
        f'{prefix}/dummy5.txt',
        f'{prefix}/dummy6.txt',
    ]
    for item in dummy:
        bucket.put_object(Body='some data', Key=item)


def test_empty_staging_dir_after_query(s3_bucket):
    some_sql = "select * from dev_level_1_database.yr_weather"
    add_dummy_data(s3_bucket, "query")

    objects_before = len(list(s3_bucket.objects.filter(Prefix="query")))
    engine.execute(some_sql)
    objects_after = len(list(s3_bucket.objects.filter(Prefix="query")))

    assert objects_before == 7
    assert objects_after == 0
