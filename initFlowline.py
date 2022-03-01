#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'zjm'
__date__ = '2021/9/14 18:06'

import operator

from osgeo import gdal, gdal_array, osr, gdalnumeric,ogr
import sys
import collections
import fiona
import os
import math
import multiprocessing
import shapely.geometry
from shapely.geometry import LineString, shape, mapping
from shapely.geometry import MultiLineString
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def usage():
  print("""
  usage initFlowline.py:
  
    inputfile    (input)  line files
    outputfiles  (output) the longest line in the inputfile

""")
  sys.exit(-1)

def get_ogr_driver(filepath):
    """
    通过文件扩展名，获取矢量数据读写驱动
    """
    filename, file_extension = os.path.splitext(filepath)
    extension = file_extension[1:]

    ogr_driver_count = ogr.GetDriverCount()
    for idx in range(ogr_driver_count):
        driver = ogr.GetDriver(idx)
        driver_extension = driver.GetMetadataItem(str("DMD_EXTENSION")) or ""
        driver_extensions = driver.GetMetadataItem(str("DMD_EXTENSIONS")) or ""

        if extension == driver_extension or extension in driver_extensions:
            return driver

def main():
    """
    获取最长线段最为主流线
    :return:
    """
    inputFile = sys.argv[1]
    outputFile =sys.argv[2]
    RGIId_old=''
    RGIId_new=''
    p = []
    index=[]
    dist=[]
    isfirst=True

    source_file=fiona.open(inputFile, mode="r")
    #编辑线段属性
    # attr=collections.OrderedDict()
    # attr['RGIId']='str:14'
    # schema={'properties':attr}
    # schema.update({"geometry": "LineString"})
    schema = {"geometry": "LineString",'properties':{'RGIId':'str:14','Length':'float'}}
    driver = get_ogr_driver(filepath='result.shp')
    destination_file=fiona.open(outputFile,mode="w",driver=driver.GetName(),schema=schema,crs=source_file.crs,
                                encodings=source_file.encoding)
    for record in source_file:
        geom = record.get("geometry")
        input_geom = shape(geom)
        attributes = record.get("properties")
        if isfirst:
            #判断是否为第一次读入数据
            RGIId_old = RGIId_new = attributes.get("RGIId")
            p.append(input_geom)
            isfirst = False
        else:
            RGIId_new = attributes.get("RGIId")
            if RGIId_old != RGIId_new :
                #利用bug最高点与最低点的连接会出现多次
                line = max(p, key=p.count)
                point=[line.xy[0][-1],line.xy[1][-1]]
                for i in range(0,len(p)):
                    if point == [p[i].xy[0][-1], p[i].xy[1][-1]]:
                        dist.append(p[i].length)
                        index.append(i)
                a=dist.index(max(dist))
                b=index[a]
                line2 = p[b]
                # line2 = p[dist.index(max(dist))]
                if len(line2.xy[0])==0:
                    line2=line
                dist.clear()
                index=[]
                centerline_dict = {
                    "geometry": mapping(line2),
                    "properties": {
                        'RGIId':RGIId_old,
                        'Length':line2.length
                    }
                }
                destination_file.write(centerline_dict)
                RGIId_old = RGIId_new
                p = []
                p.append(input_geom)
            else:
                p.append(input_geom)
    line = max(p, key=p.count)
    point = [line.xy[0][-1], line.xy[1][-1]]
    for i in range(0, len(p)):
        if point == [p[i].xy[0][-1], p[i].xy[1][-1]]:
            dist.append(p[i].length)
            index.append(i)
    line2 = p[index[dist.index(max(dist))]]
    # line2 = p[dist.index(max(dist))]
    if len(line2.xy[0]) == 0:
        line2 = line
    dist.clear()
    centerline_dict = {
        "geometry": mapping(line2),
        "properties": {
            'RGIId': RGIId_old,
            'Length': line2.length
        },
    }
    destination_file.write(centerline_dict)
if __name__ == "__main__":
    main()