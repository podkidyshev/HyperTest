from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from hypertest.main.models import Test, Result, Question, Answer


class HyperTestTestCase(APITestCase):
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

    def test(self):
        response = self.client.post(reverse('tests-list'), self.template, format='json')
        self.assertEqual(response.status_code, 201)

        self.assertEqual(Test.objects.count(), 1)
        self.assertEqual(Result.objects.count(), 2)
        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Answer.objects.count(), 4)
