import base64

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from hypertest.main.models import Test, TestResult, TestQuestion, TestQuestionAnswer


def prettify_validation_error(err_detail):
    if isinstance(err_detail, list):
        return err_detail[0]
    elif isinstance(err_detail, str):
        return err_detail

    errors = {}

    for field, value in err_detail.items():
        if isinstance(value, str):
            errors[field] = value
            continue

        if isinstance(value, list) and len(value):
            errors[field] = value[0]

    return errors


class PictureField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            data = base64.decodebytes(data.encode('UTF-8'))
        return super().to_internal_value(data)


class TestQuestionAnswerSerializer(serializers.ModelSerializer):
    result_id = serializers.IntegerField(allow_null=True, write_only=True, required=True)

    class Meta:
        model = TestQuestionAnswer
        fields = ['answer_id', 'result_id', 'text']

    def validate_result_id(self, result_id):
        if result_id is None:
            return result_id

        if result_id not in self.root.results_ids:
            raise ValidationError('result_id = {} does not exist'.format(result_id))

        return result_id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['result_id'] = instance.result.result_id if instance.result else None
        return data


class TestQuestionAnswerListField(serializers.ListField):
    id_error_messages = {
        'required': 'Это поле обязательно',
        'incorrect_type': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
        'invalid': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
        'duplicates': 'Одинаковые answer_id в одном объекте question'
    }
    answer_id_field = serializers.IntegerField()
    representation_serializer = TestQuestionAnswerSerializer()

    def validate_answer_id(self, answer_id):
        try:
            answer_id = self.answer_id_field.to_internal_value(answer_id)
        except ValidationError:
            msg = self.id_error_messages['incorrect_type'].format(typ=answer_id.__class__.__name__, val=answer_id)
            raise ValidationError({'answer_id': msg})

        if self.parent.instance is not None:
            try:
                answer = TestQuestionAnswer.objects.get(answer_id=answer_id, question=self.parent.instance)
            except TestQuestionAnswer.DoesNotExist:
                answer = None
        else:
            answer = None

        return answer

    def run_answer_validation(self, data):
        if 'answer_id' not in data:
            raise ValidationError({'answer_id': self.id_error_messages['required']})

        answer = self.validate_answer_id(data['answer_id'])

        serializer = TestQuestionAnswerSerializer(instance=answer, data=data, context=self.root.context)
        serializer.parent = self.parent
        serializer.is_valid(True)

        return serializer

    def run_child_validation(self, data):
        result = []
        errors = {}
        answers_ids = {}

        for idx, item in enumerate(data):
            try:
                validated_answer = self.run_answer_validation(item)
                result.append(validated_answer)

                # validate no result_id duplicates
                answer_id = validated_answer.validated_data['answer_id']
                if answer_id in answers_ids:
                    errors[idx] = errors[answers_ids[answer_id]] = self.id_error_messages['duplicates']
                    continue
                answers_ids[answer_id] = idx
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result

        errors = [prettify_validation_error(errors.get(idx, {})) for idx in range(len(data))]
        raise ValidationError([errors])

    def to_representation(self, data):
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class TestResultSerializer(serializers.ModelSerializer):
    picture = PictureField(allow_null=True, default=None, required=False)

    class Meta:
        model = TestResult
        fields = ['result_id', 'text', 'picture']


class TestResultListField(serializers.ListField):
    id_error_messages = {
        'required': 'Это поле обязательно',
        'incorrect_type': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
        'invalid': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
        'duplicates': 'Одинаковые result_id в запросе'
    }
    result_id_field = serializers.IntegerField()
    representation_serializer = TestResultSerializer()

    def validate_result_id(self, result_id):
        try:
            result_id = self.result_id_field.to_internal_value(result_id)
        except ValidationError:
            msg = self.id_error_messages['incorrect_type'].format(typ=result_id.__class__.__name__, val=result_id)
            raise ValidationError({'result_id': msg})

        if self.root.instance is not None:
            try:
                result = TestResult.objects.get(result_id=result_id, test=self.root.instance)
            except TestResult.DoesNotExist:
                result = None
        else:
            result = None

        return result

    def run_result_validation(self, data):
        if 'result_id' not in data:
            raise ValidationError({'result_id': self.id_error_messages['required']})

        result = self.validate_result_id(data['result_id'])

        serializer = TestResultSerializer(instance=result, data=data, context=self.root.context)
        serializer.parent = self
        serializer.is_valid(True)

        return serializer

    def run_child_validation(self, data):
        result = []
        errors = {}
        results_ids = {}

        for idx, item in enumerate(data):
            try:
                validated_result = self.run_result_validation(item)
                result.append(validated_result)

                # validate no result_id duplicates
                result_id = validated_result.validated_data['result_id']
                if result_id in results_ids:
                    errors[idx] = errors[results_ids[result_id]] = self.id_error_messages['duplicates']
                    continue
                results_ids[result_id] = idx
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result

        errors = [prettify_validation_error(errors.get(idx, {})) for idx in range(len(data))]
        raise ValidationError([errors])

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        # hack
        test_serializer: TestSerializer = self.root
        test_serializer.results_ids = [result.validated_data['result_id'] for result in data]

        return data

    def to_representation(self, data):
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class TestQuestionSerializer(serializers.ModelSerializer):
    picture = PictureField(allow_null=True, default=None, required=False)
    answers = TestQuestionAnswerListField()

    class Meta:
        model = TestQuestion
        fields = ['question_id', 'text', 'picture', 'answers']


class TestQuestionListField(serializers.ListField):
    id_error_messages = {
        'required': 'Это поле обязательно',
        'incorrect_type': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
        'invalid': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
        'duplicates': 'Одинаковые question_id в запросе'
    }
    question_id_field = serializers.IntegerField()
    representation_serializer = TestQuestionSerializer()

    def validate_result_id(self, question_id):
        try:
            question_id = self.question_id_field.to_internal_value(question_id)
        except ValidationError:
            msg = self.id_error_messages['incorrect_type'].format(typ=question_id.__class__.__name__, val=question_id)
            raise ValidationError({'question_id': msg})

        if self.root.instance is not None:
            try:
                question = TestQuestion.objects.get(question_id=question_id, test=self.root.instance)
            except TestQuestion.DoesNotExist:
                question = None
        else:
            question = None

        return question

    def run_question_validation(self, data):
        if 'question_id' not in data:
            raise ValidationError({'question_id': self.id_error_messages['required']})

        question = self.validate_result_id(data['question_id'])

        serializer = TestQuestionSerializer(instance=question, data=data, context=self.root.context)
        serializer.parent = self
        serializer.is_valid(True)

        return serializer

    def run_child_validation(self, data):
        result = []
        errors = {}
        questions_ids = {}

        for idx, item in enumerate(data):
            try:
                validated_question = self.run_question_validation(item)
                result.append(validated_question)

                # validate no result_id duplicates
                question_id = validated_question.validated_data['question_id']
                if question_id in questions_ids:
                    errors[idx] = errors[questions_ids[question_id]] = self.id_error_messages['duplicates']
                    continue
                questions_ids[question_id] = idx
            except ValidationError as e:
                print(e.detail)
                errors[idx] = e.detail

        if not errors:
            return result

        errors = [prettify_validation_error(errors.get(idx, {})) for idx in range(len(data))]
        raise ValidationError([errors])

    def to_representation(self, data):
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class TestSerializer(serializers.ModelSerializer):
    picture = PictureField(allow_null=True, default=None, required=False)
    results = TestResultListField()
    questions = TestQuestionListField()

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'picture', 'published', 'vip', 'price', 'gender', 'results',
                  'questions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results_ids = []

    @property
    def _writable_fields(self):
        yield self.fields['results']
        for field_name, field in self.fields.items():
            if not field.read_only and field_name != 'results':
                yield field

    def save(self, **kwargs):
        results = self.validated_data.pop('results', [])
        questions = self.validated_data.pop('questions', [])

        test = super().save(**kwargs)

        # manage results
        results_ids = [result.validated_data['result_id'] for result in results]
        TestResult.objects.filter(~Q(id__in=results_ids), test=test).delete()
        results_objects = {}
        for result in results:
            result.validated_data['test'] = test
            result_obj = result.save()
            results_objects[result_obj.result_id] = result_obj

        # manage questions
        # all_answers = list(chain(question.validated_data.pop('answers', []) for question in questions))
        questions_ids = [question.validated_data['question_id'] for question in questions]
        TestQuestion.objects.filter(~Q(id__in=questions_ids), test=test).delete()
        questions_objects = {}
        for question in questions:
            question.validated_data['test'] = test
            answers = question.validated_data.pop('answers', [])
            question_obj = question.save()
            questions_objects[question_obj.question_id] = question_obj, answers

        # manage answers
        for question, answers in questions_objects.values():
            answer_ids = [answer.validated_data['answer_id'] for answer in answers]
            TestQuestionAnswer.objects.filter(~Q(id__in=answer_ids), question=question).delete()
            for answer in answers:
                answer.validated_data['question'] = question
                if 'result_id' in answer.validated_data:
                    result_id = answer.validated_data.pop('result_id')
                    answer.validated_data['result'] = results_objects[result_id]
                answer.save()

        return test
