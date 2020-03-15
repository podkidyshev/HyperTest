import os

from copy import deepcopy

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from hypertest.main.models import Test, Result, Question, Answer


class HyperTestTestCase(APITestCase):
    url = reverse('tests-list')

    template = {
        'title': 'title',
        'description': 'description',
        'picture': None,
        'published': False,
        'vip': False,
        'price': 1,
        'gender': 0,
        'results': [
            {
                'result_id': 0,
                'text': 'result 0',
                'picture': None,
            },
            {
                'result_id': 1,
                'text': 'result 1',
                'picture': None,
            }
        ],
        'questions': [
            {
                'question_id': 0,
                'text': 'question 0',
                'picture': None,
                'answers': [
                    {
                        'answer_id': 0,
                        'text': 'question 0 answer 0',
                        'result_id': 0
                    },
                    {
                        'answer_id': 1,
                        'text': 'question 0 answer 1',
                        'result_id': None
                    }
                ]
            },
            {
                'question_id': 1,
                'text': 'question 1',
                'picture': None,
                'answers': [
                    {
                        'answer_id': 0,
                        'text': 'question 1 answer 0',
                        'result_id': 0
                    },
                    {
                        'answer_id': 1,
                        'text': 'question 1 answer 1',
                        'result_id': 1
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

    def test_create_and_list(self):
        response_1 = self.client.post(self.url, self.template, format='json')
        self.assertEqual(response_1.status_code, 201)
        response_1_data = response_1.json()
        self.assertEqual(dict(self.template, id=response_1_data['id']), response_1_data)

        self.assert_objects_count(1, 2, 2, 4)

        response_2 = self.client.post(self.url, self.template, format='json')
        self.assertEqual(response_2.status_code, 201)

        self.assert_objects_count(2, 4, 4, 8)

        response_list = self.client.get(self.url)
        self.assertEqual(response_list.status_code, 200)

        data_list = response_list.json()['items']
        self.assertEqual(len(data_list), 2)
        self.assertEqual(data_list[0]['id'], response_2.json()['id'])
        self.assertEqual(data_list[1]['id'], response_1.json()['id'])

    def test_delete(self):
        data_1 = self.client.post(self.url, self.template, format='json').json()
        data_2 = self.client.post(self.url, self.template, format='json').json()

        self.client.delete(reverse('tests-detail', [data_1['id']]))

        self.assert_objects_count(1, 2, 2, 4)

        self.client.delete(reverse('tests-detail', [data_2['id']]))

        self.assert_objects_count(0, 0, 0, 0)

    def test_update(self):
        data = deepcopy(self.template)

        test_id = self.client.post(self.url, data, format='json').json()['id']
        url = reverse('tests-detail', [test_id])
        data['id'] = test_id

        # and create another one to be sure there is no conflicts
        self.client.post(self.url, data, format='json')

        # test delete one answer
        data['questions'][1]['answers'].pop()
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assert_objects_count(2, 4, 4, 7)
        self.assertEqual(data, response.json())

        # test incorrect result_id in answer (and put method)
        data['questions'][1]['answers'][0]['result_id'] = 100500
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'fields': {
                    'questions': [
                        {},
                        {'answers': [{'result_id': 'result_id = 100500 does not exist'}]}
                    ]
                }
            }
        )

        # test required fields
        data['results'].append({})
        data['questions'].append({})
        data['questions'][0]['answers'].append({})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'fields': {
                    'results': [
                        {}, {}, {'result_id': 'Это поле обязательно'}
                    ],
                    'questions': [
                        {'answers': [{}, {}, {'answer_id': 'Это поле обязательно'}]},
                        {'answers': [{'result_id': 'result_id = 100500 does not exist'}]},
                        {'question_id': 'Это поле обязательно'}
                    ]
                }
            }
        )

        # test required fields on top level
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'fields': {
                    'results': 'Обязательное поле.',
                    'title': 'Обязательное поле.',
                    'questions': 'Обязательное поле.'
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

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)

        data = response.json()
        url = reverse('tests-detail', [data['id']])

        # test ignoring url
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['picture'], data['picture'])

        # test delete picture
        data['picture'] = ''
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['picture'], None)
