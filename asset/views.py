from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from asset.models import KRW,USD,CNY
# Create your views here.

class AssetView(TemplateView):
    template_name = "asset.html"
    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['activate'] = 'asset'
       context['usds'] = USD.objects.all()
       context['cur_usd'] = USD.objects.latest('id').cash if USD.objects.all() else 0
       context['krws'] = KRW.objects.all()
       context['cur_krw'] = KRW.objects.latest('id').cash if KRW.objects.all() else 0
       context['cnys'] = CNY.objects.all()
       context['cur_cny']= CNY.objects.latest('id').cash  if CNY.objects.all() else 0

       return context
