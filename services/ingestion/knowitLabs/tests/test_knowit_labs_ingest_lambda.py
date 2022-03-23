from knowitlabs.knowit_labs_ingest_lambda import handler
from responses import RequestsMock, GET
from pytest import fixture
from json import loads, dumps


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


@fixture
def knowit_labs_test_data():
    data = {
        'references': {
            'User': {
                'fdsa': {
                    'name': 'Test Testerson',
                    'username': 'test.tester'
                }
            },
            'Post': {
                'asdf': {
                    'id': 'asdf',
                    'creatorId': 'fdsa',
                    'title': 'Test blog 3000',
                    'detectedLanguage': 'en',
                    'uniqueSlug': 'test-blog-3000-asdf',
                    'createdAt': 1577833200000,
                    'updatedAt': 1577833200000,
                    'firstPublishedAt': 1577833200000,
                    'latestPublishedAt': 1577833200000,
                    'virtuals': {
                        'wordCount': 1000,
                        'readingTime': 1.0,
                        'totalClapCount': 10,
                        'recommends': 5,
                        'responsesCreatedCount': 2
                    }
                },
                '1234': {
                    'id': '1234',
                    'creatorId': 'fdsa',
                    'title': 'Test blog 3000',
                    'detectedLanguage': 'en',
                    'uniqueSlug': 'test-blog-3000-1234',
                    'createdAt': 1577833200000,
                    'updatedAt': 1577833200000,
                    'firstPublishedAt': 1577833200000,
                    'latestPublishedAt': 1577833200000,
                    'virtuals': {
                        'wordCount': 1000,
                        'readingTime': 1.0,
                        'totalClapCount': 10,
                        'recommends': 5,
                        'responsesCreatedCount': 2
                    }
                }
            }
        }
    }

    return {
        'https://knowitlabs.no/archive': '<a href="https://knowitlabs.no/archive/2020"></a>',
        'https://knowitlabs.no/archive/2020': '<a href="https://knowitlabs.no/archive/2020/01"></a>',
        'https://knowitlabs.no/archive/2020/01': f'<script>// <![CDATA[\nwindow["obvInit"]({dumps(data)})]]</script>'
    }


@fixture(autouse=True)
def setup_test_data(mocked_responses, knowit_labs_test_data):
    for url, data in knowit_labs_test_data.items():
        mocked_responses.add(GET, url, body=data, status=200)

    yield None


def test_handler_data(s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    expected = {
        'medium_id': 'asdf',
        'author_name': 'Test Testerson',
        'author_username': 'test.tester',
        'title': 'Test blog 3000',
        'created_at': 1577833200,
        'updated_at': 1577833200,
        'first_published_at': 1577833200,
        'latest_published_at': 1577833200,
        'word_count': 1000,
        'reading_time': 1.0,
        'total_claps': 10,
        'total_unique_claps': 5,
        'language': 'en',
        'url': 'https://knowitlabs.no/test-blog-3000-asdf',
        'comments_count': 2
    }

    assert all([expected[k] == v for k, v, in data['data'][0].items()])
