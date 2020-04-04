import os

from copy import deepcopy

from rest_framework.reverse import reverse

from hypertest.main.models import Test, Result, Question, Answer
from tests.api.client import AuthenticatedTestCase


class AvailableMethodsTestCase(AuthenticatedTestCase):
    url = reverse('tests-list')
    url_my = reverse('tests-my-list')

    def test_tests(self):
        # make it appear in /api/tests/{id} and /api/tests/my/{id}
        test = Test.objects.create(published=True, user=self.user)
        url_test = reverse('tests-detail', [test.id])
        url_my_test = reverse('tests-my-detail', [test.id])

        privacy = [
            ('get', self.url, 200),
            ('post', self.url, 405),
            ('get', url_test, 200),
            ('put', url_test, 405),
            ('patch', url_test, 405),
            ('delete', url_test, 405),

            ('get', self.url_my, 200),
            ('post', self.url_my, 400),
            ('get', url_my_test, 200),
            ('patch', url_my_test, 405),
            ('put', url_my_test, 400),

            # the last one that deletes test
            ('delete', url_my_test, 204)
        ]

        for method, uri, status_code in privacy:
            self.assertEqual(getattr(self.client, method)(uri).status_code, status_code, f'{method, uri, status_code}')


class HyperTestTestCase(AuthenticatedTestCase):
    url = reverse('tests-list')
    url_my = reverse('tests-my-list')

    template = {
        'title': 'title',
        'description': 'description',
        'picture': None,
        'isPublished': True,
        'vip': False,
        'price': 1,
        'gender': 0,
        'results': [
            {
                'resId': 0,
                'resText': 'result 0',
                'resDesc': 'result 0 description',
                'resPic': None,
            },
            {
                'resId': 1,
                'resText': 'result 1',
                'resDesc': 'result 1 description',
                'resPic': None,
            }
        ],
        'questions': [
            {
                'qId': 0,
                'qText': 'question 0',
                'qPic': None,
                'vars': [
                    {
                        'varId': 0,
                        'varText': 'question 0 answer 0',
                        'res': 0
                    },
                    {
                        'varId': 1,
                        'varText': 'question 0 answer 1',
                        'res': None
                    }
                ]
            },
            {
                'qId': 1,
                'qText': 'question 1',
                'qPic': None,
                'vars': [
                    {
                        'varId': 0,
                        'varText': 'question 1 answer 0',
                        'res': 0
                    },
                    {
                        'varId': 1,
                        'varText': 'question 1 answer 1',
                        'res': 1
                    }
                ]
            }
        ],
    }

    with open(os.path.join(os.path.dirname(__file__), 'pic')) as f:
        pic = f.read()

    def assert_objects_count(self, tests_count=None, results_count=None, questions_count=None, answers_count=None):
        if tests_count is not None:
            self.assertEqual(Test.objects.count(), tests_count)
        if results_count is not None:
            self.assertEqual(Result.objects.count(), results_count)
        if questions_count is not None:
            self.assertEqual(Question.objects.count(), questions_count)
        if answers_count is not None:
            self.assertEqual(Answer.objects.count(), answers_count)

    def make_expected_data(self, response_data, template=None):
        template = self.template if template is None else template
        return dict(
            template,
            id=response_data['id'],
            isPublished=False,
            passed=False,
            passedCount=0,
            user=self.user.id
        )

    def test_create(self):
        # creation is not allowed with /api/tests
        self.assertEqual(self.client.post(self.url, self.template, format='json').status_code, 405)

        # you should create tests via /api/tests/my
        response = self.client.post(self.url_my, self.template, format='json')
        self.assertEqual(response.status_code, 201)

        # check response
        response_data = response.json()
        self.assertEqual(response_data, self.make_expected_data(response_data))

        # test that there is correct number of related objects
        self.assert_objects_count(1, 2, 2, 4)

        # create another one and check number of related
        self.client.post(self.url_my, self.template, format='json')
        self.assert_objects_count(2, 4, 4, 8)

    def test_lists(self):
        test_data_1 = self.client.post(self.url_my, self.template, format='json').json()
        test_data_2 = self.client.post(self.url_my, self.template, format='json').json()

        # created tests are not published so they don't appear in /api/tests
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'], [])

        # they appear in /api/tests/my
        response = self.client.get(self.url_my)
        self.assertEqual(response.status_code, 200)
        items = response.json()['items']
        self.assertEqual(items[0]['id'], test_data_2['id'])
        self.assertEqual(items[1]['id'], test_data_1['id'])

    def test_publishing_test(self):
        test = Test.objects.create(published=True, user=self.user)

        url_test = reverse('tests-detail', [test.id])
        url_test_my = reverse('tests-my-detail', [test.id])

        # published test is accessible with both /api/tests and /api/tests/my
        self.assertEqual(len(self.client.get(self.url).json()['items']), 1)
        self.assertEqual(len(self.client.get(self.url_my).json()['items']), 1)
        # and detail
        self.assertEqual(self.client.get(url_test).status_code, 200)
        self.assertEqual(self.client.get(url_test_my).status_code, 200)

        # now unpublish test
        test.published = False
        test.save()

        # when test in not published it is accessible only with /api/tests/my
        self.assertEqual(len(self.client.get(self.url).json()['items']), 0)
        self.assertEqual(len(self.client.get(self.url_my).json()['items']), 1)
        # and detail
        self.assertEqual(self.client.get(url_test).status_code, 404)
        self.assertEqual(self.client.get(url_test_my).status_code, 200)

    def test_delete(self):
        data_1 = self.client.post(self.url_my, self.template, format='json').json()
        data_2 = self.client.post(self.url_my, self.template, format='json').json()

        self.client.delete(reverse('tests-my-detail', [data_1['id']]))

        self.assert_objects_count(1, 2, 2, 4)

        self.client.delete(reverse('tests-my-detail', [data_2['id']]))

        self.assert_objects_count(0, 0, 0, 0)

    def test_update(self):
        data = deepcopy(self.template)

        test_id = self.client.post(self.url_my, data, format='json').json()['id']
        url = reverse('tests-my-detail', [test_id])
        data['id'] = test_id

        # and create another one to be sure there is no conflicts
        self.client.post(self.url_my, data, format='json')

        # test delete one answer
        data['questions'][1]['vars'].pop()
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assert_objects_count(2, 4, 4, 7)
        response_data = response.json()
        expected_data = self.make_expected_data(response_data, template=response_data)
        expected_data['isPublished'] = True
        self.assertEqual(expected_data, response_data)

        # test incorrect result_id in answer (and put method)
        data['questions'][1]['vars'][0]['res'] = 100500
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'errors': {
                    'fields': {
                        'questions': [
                            {},
                            {'vars': [{'res': 'res = 100500 does not exist'}]}
                        ]
                    }
                }
            }
        )

        # test required fields
        data['results'].append({})
        data['questions'].append({})
        data['questions'][0]['vars'].append({})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'errors': {
                    'fields': {
                        'results': [
                            {}, {}, {'resId': 'Это поле обязательно'}
                        ],
                        'questions': [
                            {'vars': [{}, {}, {'varId': 'Это поле обязательно'}]},
                            {'vars': [{'res': 'res = 100500 does not exist'}]},
                            {'qId': 'Это поле обязательно'}
                        ]
                    }
                }
            }
        )

        # test required fields on top level
        response = self.client.post(self.url_my, {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'errors': {
                    'fields': {
                        'results': 'Обязательное поле.',
                        'title': 'Обязательное поле.',
                        'questions': 'Обязательное поле.'
                    }
                }
            }
        )

        # reset current object
        data = deepcopy(self.template)
        data['id'] = test_id
        self.client.post(url, data, format='json')

    def test_picture_upload(self):
        data = {
            'title': 'test',
            'results': [],
            'questions': [],
            'picture': self.pic
        }

        response = self.client.post(self.url_my, data, format='json')
        self.assertEqual(response.status_code, 201)

        data = response.json()
        url = reverse('tests-my-detail', [data['id']])

        # test ignoring url
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['picture'], data['picture'])

        # test delete picture
        data['picture'] = ''
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['picture'], None)
