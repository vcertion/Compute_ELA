#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'zyx'
__date__ = '2022/2/7 18:06'

import csv
import math
import operator
from osgeo import gdal, gdal_array, osr, gdalnumeric,ogr
import os
import fiona
import numpy as np
import collections
from osgeo import gdal, gdal_array, osr, gdalnumeric
import shapefile
import sys
import shapely.geometry
from shapely.geometry import LineString, shape, mapping
from shapely.geometry import MultiLineString
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

try:
    import Image
    import ImageDraw
except:
    from PIL import Image, ImageDraw


def usage():
    print("""
    usage of 3DArea.py:
    geotiff    (input)  geotif files
    shp        (input)  shapefile to clip the geotif 
    l          (input)  side length of geotif
    interval   (input)  Elevation interpolation
    br         (input)  balance ratio 
    csvfile    (output) the ELA of shps
""")
    sys.exit(-1)


def image2Array(i):
    """
    将一个Python图像库的数组转换为一个gdal_array图片
    """
    a = gdal_array.numpy.frombuffer(i.tobytes(), 'b')
    a.shape = i.im.size[1], i.im.size[0]
    return a


def world2Pixel(geoMatrix, x, y):
    """
    使用GDAL库的geomatrix对象((gdal.GetGeoTransform()))计算地理坐标的像素位置
    """
    ulx = geoMatrix[0]
    uly = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    rtnX = geoMatrix[2]
    rtnY = geoMatrix[4]
    pixel = int((x - ulx) / xDist)
    line = int((uly - y) / abs(yDist))
    return (pixel, line)


def OpenArray(array, prototype_ds=None, xoff=0, yoff=0):
    ds = gdal_array.OpenArray(array)

    if ds is not None and prototype_ds is not None:
        if type(prototype_ds).__name__ == 'str':
            prototype_ds = gdal.Open(prototype_ds)
        if prototype_ds is not None:
            gdal_array.CopyDatasetInfo(prototype_ds, ds, xoff=xoff, yoff=yoff)
    return ds
def Cla_Area(plane,srcArray,index,l):
    area=[0]
    for i in range(0, len(index[0])):
        x = index[0][i]
        y = index[1][i]
        b_center = srcArray[x][y]
        if b_center>plane:
            continue
        else:
            a = l
            b = abs(srcArray[x - 1][y - 1] - srcArray[x - 1][y])
            AB = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            a = l
            b = abs(srcArray[x - 1][y] - srcArray[x - 1][y + 1])
            BC = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            b = abs(srcArray[x][y - 1] - b_center)
            a = l
            DE = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            b = abs(srcArray[x][y + 1] - b_center)
            a = l
            EF = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            a = l
            b = abs(srcArray[x + 1][y - 1] - srcArray[x + 1][y])
            GH = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            a = l
            b = abs(srcArray[x + 1][y] - srcArray[x + 1][y + 1])
            HI = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            a = l
            b = abs(srcArray[x - 1][y - 1] - srcArray[x][y - 1])
            AD = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            b = abs(srcArray[x - 1][y] - b_center)
            a = l
            BE = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            a = l
            b = abs(srcArray[x - 1][y + 1] - srcArray[x][y + 1])
            CF = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            a = l
            b = abs(srcArray[x][y - 1] - srcArray[x + 1][y - 1])
            DG = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            b = abs(srcArray[x + 1][y] - b_center)
            a = l
            EH = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            a = l
            b = abs(srcArray[x][y + 1] - srcArray[x + 1][y + 1])
            FI = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            b = abs(srcArray[x - 1][y - 1] - b_center)
            a = 2 * math.pow(l, 2)
            a = math.pow(a, 1 / 2)
            EA = math.pow((math.pow(a, 2) + math.pow(b, 2)), 1 / 2) / 2

            b = abs(srcArray[x - 1][y + 1] - b_center)
            a = 2 * math.pow(l, 2)
            a = math.pow(a, 1 / 2)
            EC = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            b = abs(srcArray[x + 1][y - 1] - b_center)
            a = 2 * math.pow(l, 2)
            a = math.pow(a, 1 / 2)
            EG = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            b = abs(srcArray[x + 1][y + 1] - b_center)
            a = 2 * math.pow(l, 2)
            a = math.pow(a, 1 / 2)
            EI = math.pow(math.pow(a, 2) + math.pow(b, 2), 1 / 2) / 2

            p = (EA + AB + BE) / 2
            s1 = math.pow(p * (p - EA) * (p - AB) * (p - BE), 1 / 2)

            p = (BE + BC + EC) / 2
            s2 = math.pow(p * (p - BE) * (p - BC) * (p - EC), 1 / 2)

            p = (AD + DE + EA) / 2
            s3 = math.pow(p * (p - AD) * (p - DE) * (p - EA), 1 / 2)

            p = (EC + CF + EF) / 2
            s4 = math.pow(p * (p - EC) * (p - CF) * (p - EF), 1 / 2)

            p = (DE + DG + EG) / 2
            s5 = math.pow(p * (p - DE) * (p - DG) * (p - EG), 1 / 2)

            p = (EF + FI + EI) / 2
            s6 = math.pow(p * (p - EF) * (p - FI) * (p - EI), 1 / 2)

            p = (EG + EH + GH) / 2
            s7 = math.pow(p * (p - EG) * (p - EH) * (p - GH), 1 / 2)

            p = (EH + EI + HI) / 2
            s8 = math.pow(p * (p - EH) * (p - EI) * (p - HI), 1 / 2)

            s = s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8
            area.append(s)
    area_sum = sum(area)
    return int(area_sum)

def Target_ELA(shp,geoTrans,srcArray,l,interval,br):
    # 将图层扩展转换为图片像素坐标
    global target_dem
    # 为图片创建一个新的geomatrix对象以便附加地理参照数据
    geoTrans = list(geoTrans)
    # 在一个空白的8字节黑白掩膜图片上把点映射为像元绘制边界线&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
    MASK = np.ones((srcArray.shape[0], srcArray.shape[1]), dtype='b')

    mask_part = np.zeros((srcArray.shape[0], srcArray.shape[1]), dtype='b')
    Nparts = len(shp.parts)
    # print(Nparts)
    index = shp.parts
    # print(index)
    Npoints = len(shp.points)
    index.append(Npoints)
    for j in range(Nparts):
        pixels = []
        for k in range(index[j], index[j + 1]):
            p = shp.points[k]  ########################################
            pixels.append(world2Pixel(geoTrans, p[0], p[1]))

        # print(pixels.append)
        # print(geoTrans[5])
        if (j == 0):
            rasterPoly = Image.new("L", (srcArray.shape[1], srcArray.shape[0]), 1)
            # 使用PIL创建一个空白图片用于绘制多边形
            rasterize = ImageDraw.Draw(rasterPoly)
            rasterize.polygon(pixels, 0)
            # 使用PIL图片转换为Numpy掩膜数组
            mask = image2Array(rasterPoly)  ####????????????????????????????????????????????????????????????????
        else:
            rasterPoly = Image.new("L", (srcArray.shape[1], srcArray.shape[0]), 0)
            # 使用PIL创建一个空白图片用于绘制多边形
            rasterize = ImageDraw.Draw(rasterPoly)
            rasterize.polygon(pixels, 1)
            # 使用PIL图片转换为Numpy掩膜数组
            mask = image2Array(rasterPoly)  ####????????????????????????????????????????????????????????????????
        mask_part += mask
    MASK *= mask_part
        # 根据掩膜图层对图像进行裁剪
    # for i in recds:################################################################3
    index2=np.where(MASK==0)
    if len(index2[0])==0:
        return -9999
    MASK=np.where(MASK>1,0,MASK)
    area=[]
    dems=[]
    for i in range(0,len(index2[0])):
        x=index2[0][i]
        y=index2[1][i]
        b_center=srcArray[x][y]
        dems.append(b_center)
    mindem=min(dems)-interval
    maxdem=max(dems)+interval
    for plane in range(mindem,maxdem,interval):
        area.append(Cla_Area(plane,srcArray,index2,l))

    list_dem=[]
    startdem=mindem+interval/2
    while startdem>mindem and startdem<maxdem:
        list_dem.append(startdem)
        startdem=startdem+interval

    #AA
    superf_total=max(area)
    resta=[int(x)-int(y) for (x,y) in zip(area[1:], area[0:])]
    multiplicacion=[int(x)*int (y) for (x,y) in zip (resta,list_dem)]
    finalmulti=sum(multiplicacion)
    resultAA=int(int(finalmulti)/int(superf_total))

    #AABR
    refinf=mindem
    valores_multi = []
    valorAABR = [x * (y - refinf) for (x, y) in zip(resta, list_dem)]
    for valoracion in valorAABR:
        if valoracion < 0:
            valores_multi.append(int(valoracion * br))
        else:
            valores_multi.append(int(valoracion))
    valorAABRfinal = sum(valores_multi)
    while valorAABRfinal > 0:
        refinf = refinf + interval
        valores_multi = []
        valorAABR = [x * (y - refinf) for (x, y) in zip(resta, list_dem)]
        for valoracion in valorAABR:
            if valoracion < 0:
                valores_multi.append(valoracion * br)
            else:
                valores_multi.append(valoracion)
        valorAABRfinal = sum(valores_multi)
    result = refinf - (interval / 2)

    return result

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
    if len(sys.argv) < 3:
        usage()

    # 将数据源作为gdal_array载入
    raster = sys.argv[1]  # tif路径
    shp = sys.argv[2]  # shp文件路径
    l=sys.argv[3]
    interval=sys.argv[4]
    br=sys.argv[5]
    output = sys.argv[6]  # 输出路径

    srcArray = gdal_array.LoadFile(raster)

    # 同时载入gdal库的图片从而获取geotransform
    srcImage = gdal.Open(raster)
    geoTrans = srcImage.GetGeoTransform()
    # 使用PyShp库打开shp文件
    r = shapefile.Reader(shp)
    # print(r.shape())
    shapes = r.shapes()
    recds = r.records()
    ShpNum = r.numRecords

    out=os.path.splitext(output)[0]
    f=open(out+'.csv','w',newline='')
    csvwriter=csv.writer(f)
    csvwriter.writerow(["ID","ELA"])

    ELA=[]
    l=int(l)
    interval=int(interval)
    br=float(br)
    pool = ProcessPoolExecutor(4)
    for i in range(0,len(shapes)):
        ELA.append([pool.submit(Target_ELA,r.shape(i), geoTrans,srcArray,l,interval,br),recds[i].RGIId])
    pool.shutdown(wait=True)
    for j in range(0,len(ELA)):
        csvwriter.writerow([ELA[j][1],ELA[j][0].result()])

if __name__ == "__main__":
    main()