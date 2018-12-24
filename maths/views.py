import json

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.core import serializers
from django.http import JsonResponse

from maths.models import File
# Create your views here.

class IndexView(TemplateView):
    template_name = "index.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["files"] = File.objects.all()
        return context
    
    
    def get(self, request, *args, **kwargs):
        # 페이지 로딩 후 ajax로 문서정보 전달
        if request.is_ajax():
            if request.GET.get('action') == 'init':
                data = json.dumps(list(File.objects.all().values(
                    'title','course','category','difficulty',
                    'file_location','key_location','note','tag'
                )))

            return JsonResponse(data, safe=False)
        
        return super(IndexView, self).get(request, *args, **kwargs)
    




    