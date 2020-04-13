import os

from copy import deepcopy

from rest_framework.reverse import reverse

from hypertest.main.models import Test, Result, Question, Answer, TestPass
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
            ('put', url_my_test, 403),  # test is published so it cannot be updated

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

    def test_short_serializer(self):
        data = self.client.post(self.url_my, self.template, format='json').json()
        test = Test.objects.get(pk=data['id'])
        test.published = True
        test.save()

        for url in [self.url, self.url_my]:
            list_data = self.client.get(url).json()['items'][0]
            expected_data = self.make_expected_data(list_data)
            expected_data.pop('questions')
            expected_data.pop('results')
            expected_data['isPublished'] = True
            self.assertEqual(list_data, expected_data)

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
        data['isPublished'] = False

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
        self.assertEqual(self.make_expected_data(response_data, template=response_data), response_data)

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

    def test_pass_test(self):
        test = Test.objects.create(user=self.user, published=False)
        url_pass = reverse('tests-pass', [test.id])

        # user can pass his own test even if it is not published
        self.client.post(url_pass)
        test.refresh_from_db()
        self.assertEqual(test.passed_count, 1)

        # test that it ignores repeated passes
        self.client.post(url_pass)
        test.refresh_from_db()
        self.assertEqual(test.passed_count, 1)

        # test that non-owner can't pass not-published test
        self.change_user()
        response = self.client.post(url_pass)
        self.assertEqual(response.status_code, 404)

    def test_filters(self):
        test = Test.objects.create(user=self.user, published=True)
        TestPass.objects.create(user=self.user, test=test)

        results = [
            (self.url, 1),
            (self.url + '?isPublished=0', 0),
            (self.url + '?passed=0', 0),
            (self.url + '?passed=1&isPublished=0', 0),
            (self.url + '?passed=1&isPublished=1', 1),
        ]

        results_another_user = [
            (self.url, 1),
            (self.url + '?isPublished=0', 0),
            (self.url + '?passed=0', 1),
            (self.url + '?passed=1&isPublished=0', 0),
            (self.url + '?passed=1&isPublished=1', 0),
        ]

        def _check_filter(_uri, _count):
            self.assertEqual(len(self.client.get(_uri).json()['items']), _count)

        for uri, count in results:
            _check_filter(uri, count)

        self.change_user()

        for uri, count in results_another_user:
            _check_filter(uri, count)

    def test_update_permission(self):
        # on creation test is not published
        data = self.client.post(self.url_my, self.template, format='json').json()
        self.assertEqual(data['isPublished'], False)

        url_my_test = reverse('tests-my-detail', [data['id']])

        data = self.client.put(url_my_test, self.template, format='json').json()
        self.assertEqual(data['isPublished'], True)

        # you cannot update published test
        response = self.client.put(url_my_test, self.template, format='json')
        self.assertEqual(response.status_code, 403)


class PassedTestsTestCase(AuthenticatedTestCase):
    url_passed = reverse('tests-passed-list')

    def test_passed_view(self):
        test_1 = Test.objects.create(title='test 1')
        test_2 = Test.objects.create(title='test 2')

        # firstly test is not passed
        self.assertEqual(self.client.get(self.url_passed).json()['items'], [])

        TestPass.objects.create(test=test_1, user=self.user)

        # now test presents in response
        response = self.client.get(self.url_passed).json()
        self.assertEqual(len(response['items']), 1)
        self.assertEqual(response['items'][0]['id'], test_1.id)

        # second test is not passed
        self.assertEqual(self.client.get(reverse('tests-passed-detail', [test_2.id])).status_code, 404)

        # now test view sorting
        TestPass.objects.create(test=test_2, user=self.user)
        response = self.client.get(self.url_passed).json()
        self.assertEqual(len(response['items']), 2)
        self.assertEqual(response['items'][0]['id'], test_2.id)
