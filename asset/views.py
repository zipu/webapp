from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from asset.models import Cash
# Create your views here.

class AssetView(TemplateView):
    template_name = "asset.html"
    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['activate'] = 'asset'
       context['cash'] = Cash.objects.all()
       
       last = Cash.objects.latest('id')
       context['cur_usd'] = last.usd
       context['cur_krw'] = last.krw
       context['cur_cny']= last.cny
       context['total'] = last.total

       return context
