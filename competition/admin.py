from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django import forms
from django.utils.translation import ugettext_lazy as _

from preferences.admin import PreferencesAdmin

from jmbo.admin import ModelBaseAdmin, ModelBaseAdminForm

from competition.models import Competition, CompetitionEntry, \
        CompetitionPreferences, CompetitionAnswerOption


class CompetitionAnswerOptionAdminFormSet(BaseInlineFormSet):
    
    def clean(self):
        cleaned_data = super(CompetitionAnswerOptionAdminFormSet, self).clean()
        if any(self.errors):
            return
        if self.instance:
            has_options = False
            for form in self.forms:
                if form.cleaned_data and not form.cleaned_data['DELETE']:
                    has_options = True
                    break
            if has_options:
                # check that answer type is multichoice if there are answer options
                if self.instance.answer_type != 'multiple_choice_selection':
                    raise forms.ValidationError(_("If you want to specify multiple choice answers, you need to set the answer type to 'Multiple choice selection'."))
                # check that there is a question if answers are specified
                if not self.instance.question:
                    raise forms.ValidationError(_("You cannot have answers without a question."))
                # check that not both multichoice and a correct free text answer are specified
                if self.instance.correct_answer:
                    raise forms.ValidationError(_("You cannot provide both a correct free text answer and answer options. Only provide answers relevant to the selected answer type."))
            else:
                # multichoice requires answer options to be set
                if self.instance.answer_type == 'multiple_choice_selection':
                    raise forms.ValidationError(_("The answer type is set to 'Multiple choice selection' but there are no answer options."))
        return cleaned_data
    

class CompetitionAdminForm(ModelBaseAdminForm):

    def clean(self):
        cleaned_data = super(CompetitionAdminForm, self).clean()
        at = cleaned_data['answer_type']
        # check that file upload had max file size set
        if at == 'file_upload' and not cleaned_data['max_file_size']:
            raise forms.ValidationError(_("You need to specify a maximum file size."))
        if at == 'free_text_input' or at == 'multiple_choice_selection':
            # check that there is a question if an answer is required
            if not cleaned_data['question']:
                raise forms.ValidationError(_("You cannot have an answer without a question."))
            # check that answer types match up
            if cleaned_data['correct_answer'] and at == 'multiple_choice_selection':
                raise forms.ValidationError(_("You specified a correct free text answer, but the answer type is not set to 'Free text input'."))
        # check that an answer type has been specified if there is a question
        if not at and cleaned_data['question']:
            raise forms.ValidationError(_("You need to specify an answer type for the question."))
        return cleaned_data


class CompetitionAnswerOptionAdmin(admin.StackedInline):
    model = CompetitionAnswerOption
    formset = CompetitionAnswerOptionAdminFormSet


class CompetitionAdmin(ModelBaseAdmin):
    inlines = (CompetitionAnswerOptionAdmin, )
    form = CompetitionAdminForm
    list_display = ('title', 'start_date', 'end_date', 'description', '_entries', '_get_absolute_url', '_actions')

    def __init__(self, *args, **kwargs):
        super(CompetitionAdmin, self).__init__(*args, **kwargs)
        one_liners = (('start_date', 'end_date'), )
        # magic that should go into ModelBaseAdmin at later stage
        for line in one_liners:
            for field in line:
                try:
                    fields = self.fieldsets[0][1]['fields']
                    i = fields.index(field)
                    self.fieldsets[0][1]['fields'] = fields[0:i] + \
                        fields[i + 1:]
                except:
                    continue
        self.fieldsets[0][1]['fields'] += one_liners
        
        question_fieldset = (('Competition question', {
            'fields': ('question', 'question_blurb', 'answer_type', 'correct_answer', 'max_file_size'),
            }), )
        for field in question_fieldset[0][1]['fields']:
            try:
                fields = self.fieldsets[0][1]['fields']
                i = fields.index(field)
                self.fieldsets[0][1]['fields'] = fields[0:i] + \
                    fields[i + 1:]
            except:
                continue
        self.fieldsets = self.fieldsets[0:1] + question_fieldset + self.fieldsets[1:]

    def _entries(self, obj):
        return CompetitionEntry.objects.filter(competition=obj).count()
    _entries.short_description = 'No. entries'

    
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(CompetitionEntry)
admin.site.register(CompetitionPreferences, PreferencesAdmin)
