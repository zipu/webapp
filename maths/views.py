import json

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.core import serializers
from django.http import JsonResponse

from maths.models import Document, Klass
# Create your views here.

class DocumentView(TemplateView):
    template_name = "document.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = Document.objects.all()
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
    