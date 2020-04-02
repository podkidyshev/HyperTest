import base64
import binascii

from django.core.files.base import ContentFile
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SkipField

from hypertest.main.models import Test, Result, Question, Answer, TestPass
from hypertest.user.models import VKUser

ID_ERROR_MESSAGES = {
    'required': 'Это поле обязательно',
    'incorrect_type': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
    'invalid': 'Некорректное значение первичного ключа, требуется целое число, получено {typ} = {val}',
    'duplicates': 'Одинаковые {name} в одном родительском объекте'
}


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
    error_message = 'Некорретная строка base64, ожидаемый формат data:image/{формат};base64,{base64}. ' \
                    'Чтобы удалить файл отправьте пустую строку'

    def validate_empty_values(self, data):
        if data == '':
            return True, None
        return super().validate_empty_values(data)

    def to_internal_value(self, data):
        if not isinstance(data, str):
            return super().to_internal_value(data)

        if data.startswith('http') and self.root.instance:
            raise SkipField

        return super().to_internal_value(self.deserialize_base64(data))

    def deserialize_base64(self, data):
        good = False

        if ';base64,' in data and '/' in data:
            ext, base64_str = data.split(';base64,')
            if '/' in ext:
                ext = ext.split('/')[-1]
                try:
                    data = ContentFile(base64.b64decode(base64_str), name='temp.' + ext)
                    good = True
                except binascii.Error:
                    pass

        if not good:
            raise ValidationError(self.error_message)

        return data

    def to_representation(self, value):
        if not value:
            return None

        try:
            url = value.url
        except AttributeError:
            return None

        request = self.context.get('request', None)
        if request is not None:
            return request.scheme + '://' + request.get_host() + '/' + value.url

        return url


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


class AnswerListField(serializers.ListField):
    answer_id_field = serializers.IntegerField()
    representation_serializer = AnswerSerializer()

    def validate_answer_id(self, answer_id):
        try:
            answer_id = self.answer_id_field.to_internal_value(answer_id)
        except ValidationError:
            msg = ID_ERROR_MESSAGES['incorrect_type'].format(typ=answer_id.__class__.__name__, val=answer_id)
            raise ValidationError({'varId': msg})

        if self.parent.instance is not None:
            try:
                answer = Answer.objects.get(answer_id=answer_id, question=self.parent.instance)
            except Answer.DoesNotExist:
                answer = None
        else:
            answer = None

        return answer

    def run_answer_validation(self, data):
        if 'varId' not in data:
            raise ValidationError({'varId': ID_ERROR_MESSAGES['required']})

        answer = self.validate_answer_id(data['varId'])

        serializer = AnswerSerializer(instance=answer, data=data, context=self.root.context)
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
                    errors[idx] = errors[answers_ids[answer_id]] = ID_ERROR_MESSAGES['duplicates'].format(name='varId')
                    continue
                answers_ids[answer_id] = idx
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result

        errors = [prettify_validation_error(errors.get(idx, {})) for idx in range(len(data))]
        raise ValidationError([errors])

    def to_representation(self, data):
        self.representation_serializer.context['request'] = self.context.get('request', None)
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class ResultSerializer(serializers.ModelSerializer):
    resId = serializers.IntegerField(source='result_id')
    resText = serializers.CharField(source='text', max_length=255)
    resDesc = serializers.CharField(source='description', max_length=255, allow_blank=True, required=False)
    resPic = PictureField(source='picture', allow_null=True, default=None, required=False)

    class Meta:
        model = Result
        fields = ['resId', 'resText', 'resDesc', 'resPic']


class ResultListField(serializers.ListField):
    result_id_field = serializers.IntegerField()
    representation_serializer = ResultSerializer()

    def validate_result_id(self, result_id):
        try:
            result_id = self.result_id_field.to_internal_value(result_id)
        except ValidationError:
            msg = ID_ERROR_MESSAGES['incorrect_type'].format(typ=result_id.__class__.__name__, val=result_id)
            raise ValidationError({'resId': msg})

        if self.root.instance is not None:
            try:
                result = Result.objects.get(result_id=result_id, test=self.root.instance)
            except Result.DoesNotExist:
                result = None
        else:
            result = None

        return result

    def run_result_validation(self, data):
        if 'resId' not in data:
            raise ValidationError({'resId': ID_ERROR_MESSAGES['required']})

        result = self.validate_result_id(data['resId'])

        serializer = ResultSerializer(instance=result, data=data, context=self.root.context)
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
                    errors[idx] = errors[results_ids[result_id]] = ID_ERROR_MESSAGES['duplicates'].format(name='resId')
                    continue
                results_ids[result_id] = idx
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result

        errors = [prettify_validation_error(errors.get(idx, {})) for idx in range(len(data))]
        raise ValidationError(errors)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        # hack
        # test_serializer: TestSerializer = self.root
        # test_serializer.results_ids = [result.validated_data['result_id'] for result in data]

        return data

    def to_representation(self, data):
        self.representation_serializer.context['request'] = self.context.get('request', None)
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class QuestionSerializer(serializers.ModelSerializer):
    qId = serializers.IntegerField(source='question_id', required=True, allow_null=False)
    qText = serializers.CharField(source='text', max_length=255, allow_blank=True, required=False)
    qPic = PictureField(source='picture', allow_null=True, default=None, required=False)

    vars = AnswerListField(source='answers')

    class Meta:
        model = Question
        fields = ['qId', 'qText', 'qPic', 'vars']


class QuestionListField(serializers.ListField):
    question_id_field = serializers.IntegerField()
    representation_serializer = QuestionSerializer()

    def validate_result_id(self, question_id):
        try:
            question_id = self.question_id_field.to_internal_value(question_id)
        except ValidationError:
            msg = ID_ERROR_MESSAGES['incorrect_type'].format(typ=question_id.__class__.__name__, val=question_id)
            raise ValidationError({'qId': msg})

        if self.root.instance is not None:
            try:
                question = Question.objects.get(question_id=question_id, test=self.root.instance)
            except Question.DoesNotExist:
                question = None
        else:
            question = None

        return question

    def run_question_validation(self, data):
        if 'qId' not in data:
            raise ValidationError({'qId': ID_ERROR_MESSAGES['required']})

        question = self.validate_result_id(data['qId'])

        serializer = QuestionSerializer(instance=question, data=data, context=self.root.context)
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
                    errors[idx] = errors[questions_ids[question_id]] = ID_ERROR_MESSAGES['duplicates'].format(name='qId')
                    continue
                questions_ids[question_id] = idx
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result

        errors = [prettify_validation_error(errors.get(idx, {})) for idx in range(len(data))]
        raise ValidationError(errors)

    def to_representation(self, data):
        self.representation_serializer.context['request'] = self.context.get('request', None)
        return [self.representation_serializer.to_representation(item) for item in data.all()]


class PassedMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)

        user = self.context['request'].user
        if isinstance(user, VKUser):
            data['passed'] = TestPass.objects.filter(test=self.instance, user=self.context['request'].user).exists()

        return data


class TestSerializer(PassedMixin, serializers.ModelSerializer,):
    isPublished = serializers.BooleanField(source='published', default=False)
    passedCount = serializers.IntegerField(source='passed_count', default=0)

    picture = PictureField(allow_null=True, default=None, required=False)
    results = ResultListField()
    questions = QuestionListField()

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'picture', 'isPublished', 'vip', 'price', 'gender', 'results',
                  'questions', 'user', 'passedCount']
        read_only_fields = ['id', 'user', 'passed_count']

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
    passedCount = serializers.IntegerField(source='passed_count')
    picture = PictureField(allow_null=True, default=None, required=False)

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'picture', 'isPublished', 'vip', 'price', 'gender', 'user',
                  'passedCount']
        read_only_fields = ['id', 'user', 'passedCount']
