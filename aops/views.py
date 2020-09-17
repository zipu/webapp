import json

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, DetailView

from aops.models import Problem
#from maths.models import Document, Klass, Lecture, PastExamPaper
# Create your views here.

class AopsView(TemplateView):
    template_name = "aops/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problems"] = Problem.objects.all()
        return context