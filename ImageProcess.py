# -*- coding: utf-8 -*-
import os
import tempfile
from subprocess import check_output
from subprocess import call
from osgeo import gdal
import threading
from geoserver.catalog import Catalog
import geoserver.util
import shutil
import time

class ImageProcess(threading.Thread):
    # 데이터가 존재하는 폴더
    dataDir = '/Users/jsKim-pc/Desktop/SJ_Univ'
    # 영역을 GML로 저장하는 폴더
    areaDataDir = '/Users/jsKim-pc/Desktop/SJ_Univ'
    tempFolder = ''

    def __init__(self, id, data_1, data_2, dataArea):
        super(ImageProcess, self).__init__()
        print time.strftime("%Y%m%d_%H%M%S")
        # TODO: 과거 데이터를 구분
        self.resId = id

        # data_1이 상대적 과거 데이터
        if data_1 > data_2:
            self.data_1 = data_2
            self.data_2 = data_1
        else:
            self.data_1 = data_1
            self.data_2 = data_2

        self.dataArea = dataArea

    def run(self):
        # 임시폴더 생성
        tempName = ''
        for i in range(1, 6):
            tempName += next(tempfile._get_candidate_names())

        self.tempFolder = os.path.join(self.dataDir, tempName)
        os.mkdir(self.tempFolder)

        self.clipImage()
        self.changeSrs()
        self.calcDiff()
        self.classifyDiff()
        self.sieveDiff()
        self.polygonize()
        self.exportSelPolygon()
        self.simplifyPolygon()
        self.uploadGS()

    # TODO: 영역 클리핑 / GML 사용 / gdalwarp
    def clipImage(self):
        areaFile = os.path.join(self.areaDataDir, '{}.gml'.format(self.dataArea))

        inputData_1 = os.path.join(self.dataDir, '{}.tif'.format(self.data_1))
        outputData_1 = os.path.join(self.tempFolder, '{}_clip.tif'.format(self.data_1))

        # TODO: -crop_to_cutline 사용시 데이터 손실 발생
        command_1 = 'gdalwarp -cutline {} -tr 0.000010184343659 -0.000010184343659' \
                    ' {} {}'.format(areaFile, inputData_1, outputData_1)
        rc = check_output(command_1.decode(), shell=True)
        print rc

        inputData_2 = os.path.join(self.dataDir, '{}.tif'.format(self.data_2))
        outputData_2 = os.path.join(self.tempFolder, '{}_clip.tif'.format(self.data_2))

        command_2 = 'gdalwarp -cutline {} -tr 0.000010184343659 -0.000010184343659' \
                    ' {} {}'.format(areaFile, inputData_2, outputData_2)
        rc = check_output(command_2.decode(), shell=True)
        print rc

    # 좌표계 변환 / gdalwarp
    def changeSrs(self):
        inputData_1 = os.path.join(self.tempFolder, '{}_clip.tif'.format(self.data_1))
        outputData_1 = os.path.join(self.tempFolder, '{}_5187.tif'.format(self.data_1))

        command_1 = 'gdalwarp -s_srs EPSG:4326 -t_srs EPSG:5187 {} {}'\
            .format(inputData_1, outputData_1)
        rc = check_output(command_1.decode(), shell=True)
        print rc

        inputData_2 = os.path.join(self.tempFolder, '{}_clip.tif'.format(self.data_2))
        outputData_2 = os.path.join(self.tempFolder, '{}_5187.tif'.format(self.data_2))

        command_2 = 'gdalwarp -s_srs EPSG:4326 -t_srs EPSG:5187 {} {}' \
            .format(inputData_2, outputData_2)
        rc = check_output(command_2.decode(), shell=True)
        print rc

    # 잔차분석 / gdal_calc
    def calcDiff(self):
        check_res = self.checkImageSize()
        suffix = ''
        if not check_res:
            suffix = '_Fix'

        imageData_1 = os.path.join(self.tempFolder, '{}_5187.tif'.format(self.data_2))
        imageData_2 = os.path.join(self.tempFolder, '{}_5187{}.tif'.format(self.data_1, suffix))
        outputData = os.path.join(self.tempFolder, 'diff.tif')

        command = 'gdal_calc.py -A {} -B {} --outfile={} --calc="A-B"'.format(imageData_1, imageData_2, outputData)
        # rc = check_output(command.decode(), shell=True)
        rc = call(command.decode(), shell=True)
        print rc

    # 이미지 사이즈 체크 및 크기 변환 / gdal_translate
    def checkImageSize(self):
        imageData_1 = gdal.Open(os.path.join(self.tempFolder, '{}_5187.tif'.format(self.data_1)))
        imageData_2 = gdal.Open(os.path.join(self.tempFolder, '{}_5187.tif'.format(self.data_2)))

        result = True

        if imageData_1.RasterXSize == imageData_2.RasterXSize and imageData_1.RasterYSize == imageData_2.RasterYSize:
            pass
        else:
            command = 'gdal_translate -outsize {0} {1} {2}_5187.tif {2}_5187_Fix.tif'\
                .format(imageData_2.RasterXSize, imageData_2.RasterYSize, os.path.join(self.tempFolder, self.data_1))
            rc = check_output(command.decode(), shell=True)
            print rc
            result = False

        return result

    # 절/성토지 분류 / gdal_calc
    def classifyDiff(self):
        inputData = os.path.join(self.tempFolder, 'diff.tif')
        ignoreRange = '1'
        outputDate = os.path.join(self.tempFolder, 'diff_classify.tif')

        command = 'gdal_calc.py -A {0} --outfile={1} --calc="(A<=-{2})*1 + ((A>-{2})&(A<{2}))*2 + (A>={2})*3"'\
            .format(inputData, outputDate, ignoreRange)
        # rc = check_output(command.decode(), shell=True)
        rc = call(command.decode(), shell=True)
        print rc

    # 작은 영역 정리 / gdal_sieve
    def sieveDiff(self):
        inputData = os.path.join(self.tempFolder, 'diff_classify.tif')
        ignoreRange = '30'
        outputData = os.path.join(self.tempFolder, 'diff_classify_sieve.tif')

        command = 'gdal_sieve.py -st {} {} {}'.format(ignoreRange, inputData, outputData)
        rc = check_output(command.decode(), shell=True)
        print rc

    # 폴리곤화 / gdal_polygonize
    def polygonize(self):
        inputData = os.path.join(self.tempFolder, 'diff_classify_sieve.tif')
        outputData = os.path.join(self.tempFolder, 'diff_polygon.shp')

        command = 'gdal_polygonize.py {} -f "ESRI Shapefile" {}'.format(inputData, outputData)
        rc = check_output(command.decode(), shell=True)
        print rc

    # 필요한 폴리곤 추출 / ogr2ogr
    def exportSelPolygon(self):
        inputData = os.path.join(self.tempFolder, 'diff_polygon.shp')
        sql = 'select * from diff_polygon where DN in (1, 3)'
        outputData = os.path.join(self.tempFolder, 'diff_sel_polygon.shp')

        command = 'ogr2ogr -sql "{}" {} {}'.format(sql, outputData, inputData)
        rc = check_output(command.decode(), shell=True)
        print rc

    # 단순화 / ogr2ogr
    def simplifyPolygon(self):
        inputData = os.path.join(self.tempFolder, 'diff_sel_polygon.shp')
        degree = '0.86'
        outputData = os.path.join(self.tempFolder, 'diff_simplify.shp')

        command = 'ogr2ogr -simplify {} {} {}'.format(degree, outputData, inputData)
        rc = check_output(command.decode(), shell=True)
        print rc

    # GeoServer 등록
    def uploadGS(self):
        shpFile = os.path.join(self.tempFolder, 'diff_simplify')

        cat = Catalog("http://localhost:8080/geoserver/rest", username="admin", password="geoserver")
        gsWorkspace = cat.get_workspace("SJ")
        shapefileData = geoserver.util.shapefile_and_friends(shpFile)

        # TODO: 레이어명 구분이 필요
        layerName = self.resId
        # layerName = time.strftime("%Y%m%d_%H%M%S")
        cat.create_featurestore(layerName, shapefileData, gsWorkspace)

        cat.reload()

        layer = cat.get_layer(layerName)
        diffStyle = cat.get_style('SJ:diff_style')

        if diffStyle is not None:
            layer._set_default_style('SJ:diff_style')
            cat.save(layer)

        # shutil.rmtree(self.tempFolder)

# if __name__ == '__main__':
#     ImageProcess()

