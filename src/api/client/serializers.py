import base64

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from hypertest.main.models import Test, TestResult, TestQuestion


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

        if isinstance(value, list) and len(value) and isinstance(value[0], str):
            errors[field] = value[0]

    return errors


class PictureField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            data = base64.decodebytes(data.encode('UTF-8'))
        return super().to_internal_value(data)


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

        try:
            result = TestResult.objects.get(result_id=result_id)
        except TestResult.DoesNotExist:
            result = None

        return result

    def run_result_validation(self, data):
        if 'result_id' not in data:
            raise ValidationError({'result_id': self.id_error_messages['required']})

        result = self.validate_result_id(data['result_id'])

        serializer = TestResultSerializer(instance=result, data=data, context=self.root.context)
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

    def to_representation(self, data):
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class TestQuestionSerializer(serializers.ModelSerializer):
    picture = PictureField(allow_null=True, default=None, required=False)

    class Meta:
        model = TestQuestion
        fields = ['question_id', 'text', 'picture']


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

        try:
            question = TestQuestion.objects.get(question_id=question_id)
        except TestQuestion.DoesNotExist:
            question = None

        return question

    def run_question_validation(self, data):
        if 'question_id' not in data:
            raise ValidationError({'question_id': self.id_error_messages['required']})

        question = self.validate_result_id(data['question_id'])

        serializer = TestQuestionSerializer(instance=question, data=data, context=self.root.context)
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

    def save(self, **kwargs):
        results = self.validated_data.pop('results', [])
        questions = self.validated_data.pop('questions', [])

        test = super().save(**kwargs)

        # manage results
        results_ids = [result.validated_data['result_id'] for result in results]
        TestResult.objects.filter(~Q(id__in=results_ids), test=test).delete()
        for result in results:
            result.validated_data['test'] = test
            result.save()

        # manage questions
        questions_ids = [question.validated_data['question_id'] for question in questions]
        TestQuestion.objects.filter(~Q(id__in=questions_ids), test=test).delete()
        for question in questions:
            question.validated_data['test'] = test
            question.save()

        return test
