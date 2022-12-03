from django.shortcuts import render
from .models import Shp
from tiff.models import Tiff


def index(request):
    shp = Shp.objects.all()
    tiff = Tiff.objects.all()
    return render(request=request, template_name='base.html', context={'shp': shp, 'tiff': tiff})

# Create your views here.
