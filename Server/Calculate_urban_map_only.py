import os, sys
import numpy as np
from osgeo import gdal
from gdalconst import *
import osr
import csv
import pandas as pd

def open_raster(imgName):
    dset = gdal.Open(imgName, GA_ReadOnly)
    bandList = []
    dataList = []
    if dset is None:
        print("not found", imgName)
    if dset is not None:
        bandList = dset.GetRasterBand(1)
        dataList = bandList.ReadAsArray()
    YSize = dset.RasterYSize
    XSize = dset.RasterXSize
    geotrans=dset.GetGeoTransform()
    proj=dset.GetProjection()
    return dataList, XSize, YSize, geotrans, proj

def save_raster(src_array, dst_filename, x_pixels, y_pixels, dst_geotrans, dst_proj):
    driver = gdal.GetDriverByName('GTiff')
    outds = driver.Create(dst_filename, x_pixels, y_pixels, 1, gdal.GDT_Float32)
    if outds is None:
        print('Could not create' + dst_filename)
        sys.exit(1)
    outds.SetGeoTransform(dst_geotrans)
    outds.SetProjection(dst_proj)
    outds.GetRasterBand(1).WriteArray(src_array)
    outds.GetRasterBand(1).SetNoDataValue(-3.40282346639e+038)
    outds.FlushCache()
    outds=None

Test_folder = "E:\\Pham Tuan Dung\\Data Pre_processing\\Resample Image\\Test images\\"    
Result_folder = "E:\\Pham Tuan Dung\\Data Pre_processing\\Resample Image\\Result 26-05-01\\"    

csv_input_file = "E:\\Pham Tuan Dung\\Data Pre_processing\\Resample Image\\500m_data 26-05-01.csv" 
csv_output_file = "E:\\Pham Tuan Dung\\Data Pre_processing\\Resample Image\\Result 26-05-01.csv" 

urban_testing_image = "E:\\Pham Tuan Dung\\Data Pre_processing\\Resample Image\\Features\\Set 1 semi_random\\TIFF\\VN_urban_193_testing_points.tif"
non_urban_testing_image = "E:\\Pham Tuan Dung\\Data Pre_processing\\Resample Image\\Features\\Set 1 semi_random\\TIFF\\VN_non_urban_200_testing_points.tif"
urban_testing = open_raster(urban_testing_image)[0]
non_urban_testing = open_raster(non_urban_testing_image)[0]

data_input = pd.read_csv(csv_input_file)
data_input.columns = ["image_name", "image_dst", "threshold"]
image_name_p = list(data_input.image_name)
threshold_data = list(data_input.threshold)


POP_image = "VN.Population.2015_100m_to_500m_SUM.tif"
WATER_image = "VN.Waterbody.2009_250m_to_500m_MAJORITY.tif"

POP_thresh = threshold_data[image_name_p.index(POP_image)]
WATER_thresh = threshold_data[image_name_p.index(WATER_image)]

POP_set, XSize, YSize, input_geotrans, input_proj = open_raster(Test_folder + POP_image)
WATER_set = open_raster(Test_folder + WATER_image)[0]

img_output = np.zeros((YSize,XSize), dtype=np.float32)

DMSP_resample_type = ["NEAREST", "BILINEAR", "CUBIC"]
DMSP_resample_len=len(DMSP_resample_type)
for i in range(0,DMSP_resample_len):
    DMSP_image = "VN.DMSP_OLS.2013_DN_1km_to_500m_" + DMSP_resample_type[i] + ".tif"
    DMSP_thresh = threshold_data[image_name_p.index(DMSP_image)]
    DMSP_set = open_raster(Test_folder + DMSP_image)[0]
    ISA_resample_type = ["NEAREST", "BILINEAR", "CUBIC"]
    ISA_resample_len=len(ISA_resample_type)
    for i in range(0,ISA_resample_len):
        ISA_image = "VN.ISA.2010_1km_to_500m_" + ISA_resample_type[i] + ".tif"
        ISA_thresh = threshold_data[image_name_p.index(ISA_image)]
        ISA_set = open_raster(Test_folder + ISA_image)[0]
        NDVI_agg_type = ["MAXIMUM", "MEAN", "MEDIAN", "MINIMUM"]
        NDVI_agg_len=len(NDVI_agg_type)
        for k in range(0,NDVI_agg_len):
            NDVI_image = "VN.MOD13Q1.2015_MAX_250m_to_500m_"+ NDVI_agg_type[k] + ".tif"
            NDVI_thresh = threshold_data[image_name_p.index(NDVI_image)]
            NDVI_set = open_raster(Test_folder + NDVI_image)[0]
            urban_point= 0
            non_urban_point = 200
            for y in range(0, YSize):
                for x in range (0,XSize):
                    if POP_set[y][x] == -3.40282346639e+038 or  DMSP_set[y][x] == -3.40282346639e+038 or ISA_set[y][x] == -3.40282346639e+038 or NDVI_set[y][x] == -3.40282346639e+038 or WATER_set[y][x] == -3.40282346639e+038:
                        img_output[y][x] = -3.40282346639e+038
                    else:
                        if POP_set[y][x] < POP_thresh:
                            img_output[y][x] = 0
                        else:
                            if DMSP_set[y][x] < DMSP_thresh:
                                img_output[y][x] = 0
                            else: 
                                if ISA_set[y][x] < ISA_thresh:
                                    img_output[y][x] = 0
                                else: 
                                    if NDVI_set[y][x] > NDVI_thresh:
                                        img_output[y][x] = 0
                                    else:
                                        if WATER_set[y][x] >= WATER_thresh:
                                            img_output[y][x] = 0
                                        else:
                                            img_output[y][x] = 1
                                            if urban_testing[y][x]==1:
                                                urban_point = urban_point + 1
                                            if non_urban_testing[y][x]==1:
                                                non_urban_point = non_urban_point -1
            data_output = pd.read_csv(csv_output_file)
            data_output.columns = ["image_number","Population", "Nighttime_light", "ISA", "NDVI", "Water body", "Urban", "Non_urban", "OA"]
            image_numbers = list(data_output.image_number)
            img_no= len(image_numbers)+1
            output_image = Result_folder + "image_no_" + str(img_no) + ".tif"
            save_raster(img_output, output_image, XSize, YSize, input_geotrans, input_proj)
            print(output_image)
            oa = (non_urban_point + urban_point)/393
            with open(csv_output_file, "a") as fp:
                row_data= [img_no, POP_image,DMSP_image, ISA_image, NDVI_image, WATER_image, urban_point, non_urban_point, oa]
                writer = csv.writer(fp, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                writer.writerow(row_data)
            NDVI_set = None
        ISA_set = None
    DMSP_set = None

