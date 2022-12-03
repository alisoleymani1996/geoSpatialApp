from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from geo.Geoserver import Geoserver

geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')


class Tiff(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=150, blank=True, null=True)
    file = models.FileField(upload_to='%Y/%m/%d')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


@receiver(post_save, sender=Tiff)
def publish_data(sender, instance, created, **kwargs):
    geo.create_coveragestore(layer_name=instance.name, path=instance.file.path, workspace='tiff_files')
    geo.create_coveragestyle(style_name=instance.name, workspace='tiff_files', raster_path=instance.file.path)
    geo.publish_style(layer_name=instance.name, style_name=instance.name, workspace='tiff_files')


@receiver(post_delete, sender=Tiff)
def delete_data(sender, instance, **kwargs):
    geo.delete_layer(layer_name=instance.name, workspace='tiff_files')
