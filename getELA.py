#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'zjm'
__date__ = '2021/9/14 18:06'

import operator
from osgeo import gdal, gdal_array, osr, gdalnumeric,ogr
import os
import fiona
import csv
import numpy as np
import collections
from osgeo import gdal, gdal_array, osr, gdalnumeric
import shapefile
import sys
import shapely.geometry
from shapely.geometry import LineString, shape, mapping
from shapely.geometry import MultiLineString

try:
    import Image
    import ImageDraw
except:
    from PIL import Image, ImageDraw


def usage():
    print("""
  usage clip.py <geotif> <shp> <outgeotiff> [options]

    geotiff    (input)  geotif files
    shp        (input)  Glacial contour file
    lines      (input)  Glacier streamline file
    csvfiles   (input)  ELA
    outlines   (output) the clipped line files
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

def test(shp,geoTrans,srcArray,source,target_dem):
    # 将图层扩展转换为图片像素坐标
    line_new=[]
    minX, minY, maxX, maxY = shp.bbox
    # print(r.bbox)
    ulX, ulY = world2Pixel(geoTrans, minX, maxY)
    lrX, lrY = world2Pixel(geoTrans, maxX, minY)
    # 计算新图片的尺寸
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)
    clip = srcArray[ulY:lrY, ulX:lrX]
    # Create pixel offset to pass to new image Projection info
    xoffset = ulX
    yoffset = ulY
    # print("Xoffset, Yoffset = (%f, %f)" % (xoffset, yoffset))
    # 为图片创建一个新的geomatrix对象以便附加地理参照数据
    geoTrans = list(geoTrans)
    geoTrans[0] = minX
    geoTrans[3] = maxY
    # 在一个空白的8字节黑白掩膜图片上把点映射为像元绘制边界线&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
    MASK = np.ones((pxHeight, pxWidth), dtype='b')

    mask_part = np.zeros((pxHeight, pxWidth), dtype='b')
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
            rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
            # 使用PIL创建一个空白图片用于绘制多边形
            rasterize = ImageDraw.Draw(rasterPoly)
            rasterize.polygon(pixels, 0)
            # 使用PIL图片转换为Numpy掩膜数组
            mask = image2Array(rasterPoly)  ####????????????????????????????????????????????????????????????????
        else:
            rasterPoly = Image.new("L", (pxWidth, pxHeight), 0)
            # 使用PIL创建一个空白图片用于绘制多边形
            rasterize = ImageDraw.Draw(rasterPoly)
            rasterize.polygon(pixels, 1)
            # 使用PIL图片转换为Numpy掩膜数组
            mask = image2Array(rasterPoly)  ####????????????????????????????????????????????????????????????????
        mask_part += mask
    MASK *= mask_part
        # 根据掩膜图层对图像进行裁剪
    # for i in recds:################################################################3
    MASK=np.where(MASK>1,0,MASK)
    try:
        clip = gdal_array.numpy.choose(MASK, (clip, 0)).astype(gdal_array.numpy.float32)
    except:
        print("")
    clip_re=np.where(clip<=target_dem,clip,0)
    geom=source.get('geometry')
    line=shape(geom)
    for j in range(0,len(line.xy[0])):
        pp=world2Pixel(geoTrans,line.xy[0][j],line.xy[1][j])
        try:
            dem=clip_re[pp[1],pp[0]]
        except:
            continue
        if dem!=0:
            start=j
            break
    try:
        for k in range(start,len(line.xy[0])):
            line_new.append((line.xy[0][k],line.xy[1][k]))
    except:
        print("")
    if len(line_new)>2:
        lineString=shapely.geometry.multilinestring.MultiLineString([line_new])
        return lineString
    else:
        return shapely.geometry.multilinestring.MultiLineString()
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
    print('*** Clip the geotif file using the shapefile ***')
    print('*** Copyright 2021 Jianmin Zhou, v1.0 14-Sep-2021 ***')
    if len(sys.argv) < 3:
        usage()

    # 将数据源作为gdal_array载入
    raster = sys.argv[1]  # tif路径
    shp = sys.argv[2]  # shp文件路径
    lines=sys.argv[3]
    csvfile=sys.argv[4]
    output = sys.argv[5]  # 输出路径
    srcArray = gdal_array.LoadFile(raster)

    souce_file=fiona.open(lines,mode='r')
    #编辑线段属性
    attr=collections.OrderedDict()
    attr['RGIId']='str:14'
    # attr['GLIMSId']='str:14'
    schema={'properties':attr}
    schema.update({"geometry": "LineString"})
    driver = get_ogr_driver(filepath='result.shp')
    destination_file=fiona.open(output,mode="w",driver=driver.GetName(),schema=schema,crs=souce_file.crs,
                                encodings=souce_file.encoding)
    reader=csv.reader(open(csvfile, 'r'))
    datas=[]
    for data in reader:
        datas.append(data[0])
        datas.append(data[1])
    # 同时载入gdal库的图片从而获取geotransform
    srcImage = gdal.Open(raster)
    geoTrans = srcImage.GetGeoTransform()
    # 使用PyShp库打开shp文件
    r = shapefile.Reader(shp)
    # print(r.shape())
    shapes = r.shapes()
    recds = r.records()
    ShpNum = r.numRecords
    records=[]
    RGIIds=[]
    for record in souce_file:
        records.append(record)
        RGIIds.append(record.get("properties").get("RGIId"))
    for i in range(0,len(shapes)):
        RGIId=recds[i].RGIId
        try:
            index=RGIIds.index(RGIId)
        except:
            # print("missing{0}".format(RGIId))
            continue
        k=datas.index(RGIId)
        line=test(r.shape(i), geoTrans,srcArray,records[index],float(datas[k+1]))
        centerline_dict = {
            "geometry": mapping(line),
            "properties": {
                'RGIId': RGIId
            },
        }
        destination_file.write(centerline_dict)

if __name__ == "__main__":
    main()