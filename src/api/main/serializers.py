from typing import Type

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from hypertest.main.models import Test, Result, Question, Answer, TestPass
from hypertest.user.models import VKUser

from api.main.fields import PictureField
from api.common import prettify_validation_error


ID_ERROR_MESSAGES = {
    'required': 'Это поле обязательно',
    'incorrect_type': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
    'invalid': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
    'duplicates': 'Одинаковые {name} в одном родительском объекте'
}


class TestElementListField(serializers.ListField):
    id_field = serializers.IntegerField()

    def __init__(self, serializer, id_field_name, model_id_field_name, parent_field_name, errors_hack=False,
                 *args, **kwargs):

        self.serializer: Type[serializers.ModelSerializer] = serializer
        self.model = getattr(self.serializer, 'Meta').model

        self.id_field_name: str = id_field_name
        self.model_if_field_name: str = model_id_field_name
        self.parent_field_name: str = parent_field_name
        self.errors_hack: bool = errors_hack

        super().__init__(*args, **kwargs)

        self.representation_serializer = self.serializer(context=self.root.context)
        self.representation_serializer.parent = self

    def validate_id_field(self, value):
        try:
            value = self.id_field.to_internal_value(value)
        except ValidationError:
            msg = ID_ERROR_MESSAGES['incorrect_type'].format(typ=value.__class__.__name__, val=value)
            raise ValidationError({self.id_field_name: msg})

        if self.root.instance is not None:
            lookup = {
                self.model_if_field_name: value,
                self.parent_field_name: self.parent.instance
            }
            try:
                obj = self.model.objects.get(**lookup)
            except self.model.DoesNotExist:
                obj = None

            return obj

    def run_obj_validation(self, data):
        if self.id_field_name not in data:
            raise ValidationError({self.id_field_name: ID_ERROR_MESSAGES['required']})

        obj = self.validate_id_field(data[self.id_field_name])

        serializer = self.serializer(instance=obj, data=data, context=self.root.context)
        serializer.parent = self
        serializer.is_valid(True)

        return serializer

    def run_child_validation(self, data):
        objects = []
        errors = {}
        objects_ids = {}

        for idx, item in enumerate(data):
            try:
                validated_obj = self.run_obj_validation(item)
                objects.append(validated_obj)

                obj_id = validated_obj.validated_data[self.model_if_field_name]
                if obj_id in objects_ids:
                    msg = ID_ERROR_MESSAGES['duplicates'].format(name=self.id_field_name)
                    errors[idx] = errors[objects_ids[obj_id]] = msg
                    continue
                objects_ids[obj_id] = idx

            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return objects

        errors = [prettify_validation_error(errors.get(idx, {})) for idx in range(len(data))]

        # god damn
        if self.errors_hack:
            errors = [errors]

        raise ValidationError(errors)

    def to_representation(self, data):
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class AnswerSerializer(serializers.ModelSerializer):
    varId = serializers.IntegerField(source='answer_id', required=True, allow_null=False)
    varText = serializers.CharField(source='text', required=True, allow_blank=False)

    res = serializers.IntegerField(allow_null=True, write_only=True, required=True)

    class Meta:
        model = Answer
        fields = ['varId', 'res', 'varText']

    def validate_res(self, res):
        if res is None:
            return res

        if res not in self.root.results_ids:
            raise ValidationError('res = {} does not exist'.format(res))

        return res

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['res'] = instance.result.result_id if instance.result else None
        return data


class QuestionSerializer(serializers.ModelSerializer):
    qId = serializers.IntegerField(source='question_id', required=True, allow_null=False)
    qText = serializers.CharField(source='text', max_length=255, allow_blank=True, required=False)
    qPic = PictureField(source='picture', allow_null=True, default=None, required=False)

    vars = TestElementListField(AnswerSerializer, 'varId', 'answer_id', 'question', True, source='answers')

    class Meta:
        model = Question
        fields = ['qId', 'qText', 'qPic', 'vars']


class ResultSerializer(serializers.ModelSerializer):
    resId = serializers.IntegerField(source='result_id')
    resText = serializers.CharField(source='text', max_length=255)
    resDesc = serializers.CharField(source='description', max_length=255, allow_blank=True, required=False)
    resPic = PictureField(source='picture', allow_null=True, default=None, required=False)

    class Meta:
        model = Result
        fields = ['resId', 'resText', 'resDesc', 'resPic']


class PassedMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)

        user = self.context['request'].user
        if isinstance(user, VKUser):
            data['passed'] = TestPass.objects.filter(test_id=data['id'], user=user).exists()

        return data


class TestSerializer(PassedMixin, serializers.ModelSerializer,):
    isPublished = serializers.BooleanField(source='published', default=False)
    passedCount = serializers.IntegerField(source='passed_count', default=0, read_only=True)

    picture = PictureField(allow_null=True, default=None, required=False)
    # results = ResultListField()
    results = TestElementListField(ResultSerializer, 'resId', 'result_id', 'test')
    # questions = QuestionListField()
    questions = TestElementListField(QuestionSerializer, 'qId', 'question_id', 'test')

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'picture', 'isPublished', 'vip', 'price', 'gender', 'results',
                  'questions', 'user', 'passedCount']
        read_only_fields = ['id', 'user', 'passedCount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results_ids = []

    def to_internal_value(self, data):
        if 'results' in data:
            self.results_ids = [obj['resId'] for obj in data['results'] if 'resId' in obj]
        return super().to_internal_value(data)

    def validate(self, attrs):
        user = self.context['request'].user
        attrs['user'] = user

        # on creation test could be only published=False
        if not self.instance:
            attrs['published'] = False

        # set publish_date if it is test publishing
        if self.instance and attrs['published']:
            attrs['publish_date'] = timezone.now()

        return attrs

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
        Result.objects.filter(~Q(id__in=results_ids), test=test).delete()
        results_objects = {}
        for result in results:
            result.validated_data['test'] = test
            result_obj = result.save()
            results_objects[result_obj.result_id] = result_obj

        # manage questions
        questions_ids = [question.validated_data['question_id'] for question in questions]
        Question.objects.filter(~Q(id__in=questions_ids), test=test).delete()
        questions_objects = {}
        for question in questions:
            question.validated_data['test'] = test
            answers = question.validated_data.pop('answers', [])
            question_obj = question.save()
            questions_objects[question_obj.question_id] = question_obj, answers

        # manage answers
        for question, answers in questions_objects.values():
            answer_ids = [answer.validated_data['answer_id'] for answer in answers]
            Answer.objects.filter(~Q(id__in=answer_ids), question=question).delete()
            for answer in answers:
                answer.validated_data['question'] = question
                if 'res' in answer.validated_data:
                    result_id = answer.validated_data.pop('res')
                    answer.validated_data['result'] = results_objects[result_id] if result_id is not None else None
                answer.save()

        return test


class TestShortSerializer(PassedMixin, serializers.ModelSerializer):
    isPublished = serializers.BooleanField(source='published', default=False)
    passedCount = serializers.IntegerField(source='passed_count', read_only=True)
    picture = PictureField(allow_null=True, default=None, required=False)

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'picture', 'isPublished', 'vip', 'price', 'gender', 'user',
                  'passedCount']
        read_only_fields = ['id', 'user', 'passedCount']
