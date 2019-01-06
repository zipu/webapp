import json

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, DetailView
from django.core import serializers
from django.http import JsonResponse

from maths.models import Document, Klass, Lecture, PastExamPaper
# Create your views here.

class DocumentView(TemplateView):
    template_name = "document.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = Document.objects.order_by('-reputation')
        context['activate'] = 'document'
        return context
    
    
    def get(self, request, *args, **kwargs):
        # 페이지 로딩 후 ajax로 문서정보 전달
        if request.GET and request.is_ajax():
            pk = int(request.GET.get('pk'))
            if request.GET.get('action') == 'delete':
                try:
                    Document.objects.get(pk=pk).delete()
                    data = {'success': True}
                except:
                    data = {'success': False}

            elif request.GET.get('action') == 'reputation':
                try:
                    obj = Document.objects.get(pk=pk)
                    obj.reputation = obj.reputation + int(request.GET.get('value'))
                    obj.save()
                    data = {'success':True, 'reputation': obj.reputation}
                except:
                    data = {'success': False}

            return JsonResponse(data)
        
        return super(DocumentView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST and request.is_ajax():
            try:
                pk = int(request.POST.get('pk'))
                doc = Document.objects.get(pk=pk)
                doc.key = request.FILES['file']
                doc.save()
                data = {'success': True, 'keyurl': doc.key.name}
            except:
                data = {'success': False}
            
            return JsonResponse(data)    



class KlassView(TemplateView):
    template_name = "klass.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["klasses"] = Klass.objects.all().order_by('-status','-pub_date')
        context['activate'] = 'klass'
        return context
    

class KlassDetailView(DetailView):
    template_name = "klassdetail.html"
    model=Klass
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate'] = 'klass'
        lectures = kwargs['object'].lecture.through.objects\
                   .filter(klass_id=kwargs['object'].id).order_by('id')
        context['selected_lectures'] = [lecture.lecture for lecture in lectures]
        context['lectures'] = Lecture.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        # 페이지 로딩 후 ajax로 문서정보 전달
        if request.GET and request.is_ajax():
            klass = Klass.objects.get(pk=kwargs['pk'])
            if 'lecture_id' in request.GET:
                lecture = Lecture.objects.get(pk=request.GET.get('lecture_id'))
            
            data = {'success': False}
            if request.GET.get('action') == 'delete':
                try:
                    klass.lecture.remove(lecture)
                    data['success'] = True
                except:
                    pass

            elif request.GET.get('action') == 'close':
                try:
                    klass.status = False
                    klass.save()
                    data['success'] = True
                except:
                    pass

            elif request.GET.get('action') == 'add_lecture':
                try:
                    klass.lecture.add(lecture)
                    data['success'] = True
                except:
                    pass

            return JsonResponse(data)
        return super(KlassDetailView, self).get(request, *args, **kwargs)

class ExamView(TemplateView):
    template_name = "pastexam.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exams"] = PastExamPaper.objects.all().order_by('exam')
        context['activate'] = 'exam'
        return context

class ExamDetailView(DetailView):
    template_name = "pastexamdetail.html"
    model=PastExamPaper
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate'] = 'exam'
        papers = kwargs['object'].paper.through.objects\
                   .filter(pastexampaper_id=kwargs['object'].id).order_by('id')
        context['selected_papers'] = [paper.document for paper in papers]
        context['papers'] = Document.objects.filter(category='Exam')
        return context

    def get(self, request, *args, **kwargs):
        # 페이지 로딩 후 ajax로 문서정보 전달
        if request.GET and request.is_ajax():
            exam = PastExamPaper.objects.get(pk=kwargs['pk'])
            if 'paper_id' in request.GET:
                paper = Document.objects.get(pk=request.GET.get('paper_id'))
            data = {'success': False}
            
            if request.GET.get('action') == 'add_paper':
                try:
                    exam.paper.add(paper)
                    data['success'] = True
                except:
                    pass

            return JsonResponse(data)
        return super(ExamDetailView, self).get(request, *args, **kwargs)
    