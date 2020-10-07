import json

from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.generic import TemplateView, DetailView
from django.core.paginator import Paginator

from aops.models import Problem, Topic, Category
#from maths.models import Document, Klass, Lecture, PastExamPaper
# Create your views here.

class AopsView(TemplateView):
    template_name = "aops/index.html"

    def get(self, request, *args, **kwargs):
        problems = Problem.objects.all()
        params = dict(request.GET)
        # 검색식 필터링
        if params.get('category'):
            query = Q(category__name=params['category'][0])
            for q in params['category'][1:]:
                query |= Q(category__name=q)
            problems = problems.filter(query)

        if params.get('topic'):
            query = Q(topic__name=params['topic'][0])
            for q in params['topic'][1:]:
                query |= Q(topic__name=q)
            problems = problems.filter(query)
            
        if params.get('difficulty'):
            query = Q(difficulty=params['difficulty'][0])
            for q in params['difficulty'][1:]:
                query |= Q(difficulty=q)
            problems = problems.filter(query)

        if params.get('year'):
            query = Q(year=params['year'][0])
            for q in params['year'][1:]:
                query |= Q(year=q)
            problems = problems.filter(query)

        num_pagination = 10 #페이지내이션 갯수
        paginator = Paginator(problems, 10)
        
        context = {}
        page_obj = paginator.get_page(kwargs['page'])
        context["page_obj"] = page_obj
        context["topics"] = Topic.objects.values('name')
        context["categories"] = Category.objects.values('name')
        context["years"] = Problem.objects.all().order_by('-year').distinct().values_list('year')
        context["is_paginated"] = True if paginator.num_pages > 1 else False
        
        start = int(page_obj.number/num_pagination)*num_pagination
        context["page_range"] = range(max(1,start), min(start+num_pagination, paginator.num_pages+1))

        
        
        return render(request, "aops/index.html", context)