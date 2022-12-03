import os
import psycopg2
import zipfile
import glob
import geopandas as gpd
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from sqlalchemy import create_engine
from geoalchemy2 import Geometry, WKTElement
from geo.Geoserver import Geoserver


class Shp(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=150, blank=True)
    file = models.FileField(upload_to='%Y/%m/%d')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')

# creating a connection to database using psycopg2
conn = psycopg2.connect(database='tailand', user='postgres', password='137412020', host='localhost', port='5432')
cursor = conn.cursor()


@receiver(post_save, sender=Shp)
def publish_data(sender, instance, created, **kwargs):
    file = instance.file.path
    file_format = os.path.basename(file).split('.')[-1]
    file_name = os.path.basename(file).split('.')[0]
    file_path = os.path.dirname(file)
    print(file_path)
    conn_str = 'postgresql://postgres:137412020@localhost:5432/tailand'

    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(file_path)

    os.remove(file)

    shp = glob.glob(r'{}/**/*.shp'.format(file_path), recursive=True)[0]

    print('----------------------------', shp)
    gdf = gpd.read_file(shp)
    gdf.crs = 4326
    epsg = gdf.crs.to_epsg()
    # crs_name = str(gdf.crs.srs)
    # epsg = int(crs_name.replace('epsg:', ''))
    # if epsg in None:
    #     epsg = 4326

    geom_type = gdf.geom_type[0]
    engine = create_engine(conn_str)
    gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=epsg))
    gdf.drop('geometry', 1, inplace=True)
    gdf.to_sql(file_name, engine, 'data', if_exists='replace', index=False,
               dtype={'geom': Geometry('Geometry', srid=epsg)})

    os.remove(shp)

    geo.create_featurestore(store_name='geoApp', workspace='shp_tut', db='tailand', host='localhost',
                            pg_user='postgres', pg_password='137412020', schema='data')
    geo.publish_featurestore(workspace='shp_tut', store_name='geoApp', pg_table=file_name)


@receiver(post_delete, sender=Shp)
def delete_data(sender, instance, **kwargs):
    # to delete the table from the postgresql DB
    table_name = instance.name.capitalize()
    sql = f'''DROP TABLE data."{table_name}"'''
    print('--------------------------------------', sql)
    cursor.execute(sql)
    conn.commit()
    conn.close()
    # to delete the associated layer from geoserver
    geo.delete_layer(layer_name=instance.name, workspace='shp_tut')

