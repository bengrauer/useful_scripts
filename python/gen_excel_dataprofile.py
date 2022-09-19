#!/usr/bin/env python
# coding: utf-8


# Author: Ben Grauer 
# Created a python script that does some basic exploratory analysis / dov and exports to excel for easy viewing
# Designed for quick exploratory analysis of the data sets from Kaggle


####################
# Log
####################
# 02/00/2017 - Script Created 
# 04/00/2017 - Added more summary stats, included additional tabs
# 05/00/2017 - Re-did stats to include variance, pivoted the data to allow sorting in excel. Added function pullSummaryStats_df 
# 05/00/2017 - Froze some column headers.  Sample head(75) + tail(75)
# 06/00/2017 - created ordered summary stats for quick sorting - also in progress step of re-factoring the code
# 07/10/2017 - Fixed the orderd summary stats
# 12/15/2017 - Adjusted for directory of csv
# 11/01/2019 - REWRITE
# 03/01/2020 - REWRITE
# 03/15/2020 - Added Nan count + percentage.  Added distribution percentage even for high # of dov. cap at 500


# imports
import platform, sys, os, subprocess, glob, errno


import numpy as np
import pandas as pd

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

import pylab
from pylab import figure, axes, pie, title, show


def check_is_file(fileOrDirectory):
    if os.path.isfile(fileOrDirectory):
        print('processing - single file determined')
        return True
    else:
        return False
    
def check_is_directory(fileOrDirectory):
    if os.path.isdir(fileOrDirectory):
        print('processing - directory determined')
        return True
    else:
        return False

def directory_exists(inputDirectory):
    return os.path.exists(inputDirectory)


def append_analysis_directory(inputDirectory):
    
    analysisDirectory = os.path.join(inputDirectory, "analysis")
    
    if not os.path.exists(inputDirectory):
        try:
            os.mkdir(inputDirectory)
            print("Directory created: " + str(inputDirectory))
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
    else:
        print('directory check - already exists: ' + str(inputDirectory))
        
    # return the analysis directory
    return analysisDirectory

def load_file(fileName):
    return pd.read_csv(fileName)

def generate_summary_stats(df):

    #pd.options.display.float_format = '{:.2f}'.format
 
    # create a new dataframe with metrics

    #totalMetric = {}
    runningDf = pd.DataFrame()

    for column in df:    

        # initialize
        colMetric = {}
        colMetric['dtype'] = ''
        colMetric['count'] = ''
        colMetric['totalNull'] = ''
        colMetric['totalNullPerc'] = ''
        colMetric['mean'] = ''
        colMetric['median'] = ''
        colMetric['std'] = ''
        colMetric['var'] = ''
        colMetric['range'] = ''
        colMetric['0%'] = ''
        colMetric['25%'] = ''
        colMetric['50%'] = ''
        colMetric['75%'] = ''
        colMetric['100%'] = ''

        # Assign variables
        colMetric['dtype'] = str(df[column].dtype)
        colMetric['count'] = len(df[column]) 

        # TODO: # of na's 
        totalNull = len(df[column]) - df[column].count()
        colMetric['totalNull'] = totalNull


        if totalNull > 0:
            totalNullPerc = str(round(( (len(df) - df[column].count()) / len(df[column]))*100, 0))
        else:
            totalNullPerc = '0'    
        colMetric['totalNullPerc'] = totalNullPerc


        # This was the original stats area.  Possibly take from the existing data set, or move around / re-factor
        # if the columns is a numerical data type - give the summary stat
        if np.issubdtype(df[column].dtype, np.number):

            # count
            colMetric['count'] = df[column].count()        

            # mean
            colMetric['mean'] = df[column].mean()

            # median
            colMetric['median'] = df[column].median()
            
            # Std
            colMetric['std'] = df[column].std()
            
            # Var
            colMetric['var'] = df[column].var()
            
            # Range
            colMetric['range'] = df[column].max() - df[column].min()

            # min / 0%
            colMetric['0%'] = df[column].quantile([0.0][0])

            # 25%
            colMetric['25%'] = df[column].quantile([0.25][0])
            # 50%
            colMetric['50%'] = df[column].quantile([0.50][0])

            # 75%
            colMetric['75%'] = df[column].quantile([0.75][0])

            # max / 100%
            colMetric['100%'] = df[column].quantile([1.0][0])


        #totalMetric[column] = [colMetric]
        # set a temp dataframe from the column metrics gathered in dictionary
        tempDf = pd.DataFrame.from_dict(colMetric, orient='index', columns=[column])

        # concat the columns of the dataframe
        runningDf = pd.concat([runningDf, tempDf], axis=1).reindex(tempDf.index)

    # outside column loop
    return runningDf


# Function to take a workbook, sheetname, and iterate through to populate columns
# TODO: Refine and break out by number:  array([dtype('int64'), dtype('float64'), dtype('O')], dtype=object)
#      df.dtypes
def excel_add_df(inputWorkBook, inputWorkSheet, inputSheetName, inputDataFrame, 
                 inputStartRow=0,inputStartCol=0, inputUseIndex=False):
    
    bold = inputWorkBook.add_format({'bold': True})
    font14bold = inputWorkBook.add_format({'font_size':14, 'bold': True})
    
    # local variables
    rowNum = inputStartRow
    colNum = inputStartCol
    
    # add the input header about the sheet
    inputWorkSheet.write(rowNum, inputStartCol, inputSheetName, font14bold)
    rowNum = rowNum + 1
    
    # add an index
    if inputUseIndex==True:
        inputWorkSheet.write_column(inputStartRow+3, colNum, inputDataFrame.index, bold)
        colNum = colNum + 1
    
    for column in inputDataFrame:
        rowNum = inputStartRow + 2  # for the column headers. so 2 down
        inputWorkSheet.write(rowNum, colNum, inputDataFrame[column].name, bold)
        
        rowNum = inputStartRow + 3
        inputWorkSheet.write_column(rowNum, colNum, inputDataFrame[column])
    
        # add a column
        colNum = colNum + 1


# ADD THE CERTAIN SUMMARY SHEET
def excel_addsheet_summary_and_dov(workbook, df, summaryDf):
    # Add the DOV Work sheet - quite a bit of code
    worksheet = workbook.add_worksheet('DOV')

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    italic = workbook.add_format({'italic': True})
    underline = workbook.add_format({'underline': True})
    formatHigh = workbook.add_format({'font_color': 'red'})
    formatLow = workbook.add_format({'font_color': 'blue'})

    offSetDataType = 1
    offsetCount = 2
    offSetNumNaN = 3
    offSetNaNPerc = 4

    offsetMean = 5
    offsetMedian = 6
    offsetStd = 7
    offsetVar = 8
    offsetRange = 9
    offset0Prct = 10
    offset25Prct = 11
    offset50Prct = 12
    offset75Prct = 13
    offset100Prct = 14

    offsetContOrDesc = 16
    offsetNotes = 17

    offsetRowDataHeader = 19

    offsetRowFreezeRow = 19

    # star the column Iteration at 2
    colIteration = 1
    rowIteration = 0  # to start
    rowDataHeader = offsetRowDataHeader  # bumpt out to 5 to start, so we have 4 for summary data

    # set the row descriptions
    worksheet.write(rowIteration, 0, 'Col Name', bold)
    worksheet.write(offSetDataType, 0, 'Data Type', bold)
    worksheet.write(offsetCount, 0, 'count', bold)
    worksheet.write(offSetNumNaN, 0, 'NaN', bold)
    worksheet.write(offSetNaNPerc, 0, 'NaN %', bold)
    worksheet.write(offsetMean, 0, 'mean', bold)
    worksheet.write(offsetMedian, 0, 'median', bold)
    worksheet.write(offsetStd, 0, 'std', bold)
    worksheet.write(offsetVar, 0, 'var', bold)
    worksheet.write(offsetRange, 0, 'range', bold)
    worksheet.write(offset0Prct, 0, '0%', bold)
    worksheet.write(offset25Prct, 0, '25%', bold)
    worksheet.write(offset50Prct, 0, '50%', bold)
    worksheet.write(offset75Prct, 0, '75%', bold)
    worksheet.write(offset100Prct, 0, '100%', bold)

    worksheet.write(offsetContOrDesc, 0, 'Var Type')
    worksheet.write(offsetNotes, 0, 'Notes')

    # columns = ['count','NaN','NaNPerc','mean','median','std','var','range','0%','25%','50%','75%','100%']
    # dfOrdStat = pd.DataFrame(index=(['']), columns = columns )

    for column in df:

        # grab this from the detail dataFrame 
        worksheet.write(rowIteration, colIteration, df[column].name, bold)  # header
        worksheet.write(offSetDataType, colIteration, str(df[column].dtypes))  # data type

        # use the summary DF here
        # summaryDf.loc['totalNull']['card5']
        worksheet.write(offsetCount, colIteration, summaryDf.loc['count'][column])
        worksheet.write(offSetNumNaN, colIteration, summaryDf.loc['totalNull'][column])
        worksheet.write(offSetNaNPerc, colIteration, summaryDf.loc['totalNullPerc'][column])

        if np.issubdtype(df[column].dtype, np.number):
            # mean
            worksheet.write(offsetMean, colIteration, summaryDf.loc['mean'][column])
            # median
            worksheet.write(offsetMedian, colIteration, summaryDf.loc['median'][column])
            # Std
            worksheet.write(offsetStd, colIteration, summaryDf.loc['std'][column])
            # Var
            worksheet.write(offsetVar, colIteration, summaryDf.loc['var'][column])
            # Range    
            worksheet.write(offsetRange, colIteration, summaryDf.loc['range'][column])
            # min
            worksheet.write(offset0Prct, colIteration, summaryDf.loc['0%'][column])
            # 25%
            worksheet.write(offset25Prct, colIteration, summaryDf.loc['25%'][column])
            # 50%
            worksheet.write(offset50Prct, colIteration, summaryDf.loc['50%'][column])
            # 75%
            worksheet.write(offset75Prct, colIteration, summaryDf.loc['75%'][column])
            # max
            worksheet.write(offset100Prct, colIteration, summaryDf.loc['100%'][column])

        # header for the DOV
        worksheet.write(rowDataHeader - 1, colIteration, 'DOV', underline)
        worksheet.write(rowDataHeader - 1, colIteration + 1, 'DistPrc', underline)

        # shorten these down for real-estate in excel
        const_dataTypeContinuous = 'continous'  # 'cont'
        const_dataTypeCategorical = 'categrical'
        const_dataTypeDiscrete = 'discrete'

        # init 
        varType = const_dataTypeContinuous
        worksheet.write(offsetContOrDesc, colIteration,
                        const_dataTypeContinuous)  # auto set continous - discrete determined below

        # TODO: could refine slightly. 
        # if numerical and > x then continous
        # if categorical and > x then print top 200 x
        if df[column].nunique() > 500:

            # MOVED DOWN BELOW
            # worksheet.write(rowDataHeader, colIteration, '> 500 unq', italic)

            # maybe pass this in as an optional paramter
            # worksheet.write_column(rowDataHeader+1, colIteration, df[column].head(100)) # shorten this to 100
            # colIteration = colIteration + 1

            # If we have a number
            if np.issubdtype(df[column].dtype, np.number):
                varType = const_dataTypeContinuous
                # worksheet.write(rowIteration+offsetContOrDesc, colIteration, 'continuous') # data type
            else:
                varType = const_dataTypeCategorical
                # worksheet.write(rowIteration+offsetContOrDesc, colIteration, 'categorical') # data type
        else:

            # here just saying if less than 25, then categorical vs continous - to move the dial
            if df[column].nunique() < 100:
                if np.issubdtype(df[column].dtype, np.number):
                    varType = const_dataTypeDiscrete
                    # worksheet.write(rowIteration+offsetContOrDesc, colIteration, 'discrete') # data type
                else:
                    varType = const_dataTypeCategorical
                    # worksheet.write(rowIteration+offsetContOrDesc, colIteration, 'categorical') # data type
            else:
                varType = const_dataTypeCategorical
                # worksheet.write(rowIteration+offsetContOrDesc, colIteration, 'categorical') # data type

        # Write the final data type
        worksheet.write(rowIteration + offsetContOrDesc, colIteration, varType)

        # if > 500 then write that at the start 
        # if df[column].nunique() > 500:

        # worksheet.write(rowDataHeader, colIteration, '> 500 unq', italic)
        # worksheet.write_column(rowDataHeader+1, colIteration, df[column].head(100)) # shorten this to 100
        # colIteration = colIteration + 1        

        # grab the distribution percentage
        disbDF = pd.DataFrame(df.groupby([column]).size() * 100 / len(df))
        disbDF.rename(columns={0: 'distprc'}, inplace=True)
        disbDF = disbDF.sort_values(['distprc'], ascending=False)

        # rename index and reset
        disbDF = disbDF.rename_axis('dov').reset_index().copy()

        if df[column].nunique() > 500:

            worksheet.write(rowDataHeader, colIteration, '> 500 unq', italic)
            worksheet.write_column(rowDataHeader + 1, colIteration,
                                   disbDF.loc[:, 'dov'].head(100))  # shorten this to 100
            colIteration = colIteration + 1

            worksheet.write(rowDataHeader, colIteration, '> 500 unq')
            worksheet.write_column(rowDataHeader + 1, colIteration, disbDF.loc[:, 'distprc'].head(100))
            colIteration = colIteration + 1

        else:

            # TODO: change the index name to "DOV" for better readability
            worksheet.write_column(rowDataHeader, colIteration, disbDF.loc[:, 'dov'])
            colIteration = colIteration + 1

            worksheet.write(rowDataHeader, colIteration, 'DistPrc')
            worksheet.write_column(rowDataHeader, colIteration, disbDF.loc[:, 'distprc'])
            colIteration = colIteration + 1

        # PULL THIS OUT INTO ANOTHER NOTEBOOK
        # Notes - here give a section for the note.
        # if all nulls, remove
        # if two parts of the distribution are above 10% - ok, if two are about 15% even better
        # if more than 90%, 95%, or 97% of all data is in a single category.

    worksheet.freeze_panes(offsetRowDataHeader, 1)  # # Freeze the first row and column

    print('excel sheet completed - DOV')

# Summary Stats
def excel_addsheet_summaryOrdered(workbook, summaryDf):
    
    worksheet = workbook.add_worksheet('OrderSummaryStats')
    excel_add_df(inputWorkBook=workbook, inputWorkSheet=worksheet, inputSheetName='OrderSummaryStats', 
                 inputDataFrame=summaryDf.transpose(),inputStartRow=0,inputStartCol=0,inputUseIndex=True)

    print('excel sheet completed - Summary Stats Ordered')


# Write out the correlation matrix work-sheet (not summary Df)
def excel_addsheet_correlation(workbook, df):
    
    worksheet = workbook.add_worksheet('Correlation')
    dfCorr = df.corr().round(2)
    excel_add_df(inputWorkBook=workbook, inputWorkSheet=worksheet, inputSheetName='Correlation', 
                 inputDataFrame=dfCorr,inputStartRow=0,inputStartCol=0,inputUseIndex=True)

    # May neeed to add number formatting here - before the conditional formatting
    
    # add conditional highlighting
    # length of columns
    formatHigh = workbook.add_format({'font_color': 'red'})
    formatLow = workbook.add_format({'font_color': 'blue'})
    
    lenColsDfCorr = len(dfCorr.columns) + 1
    lenRowsDfCorr = len(dfCorr.index) + 4 # for header
    cellStart = xl_rowcol_to_cell(3, 2)  # C2
    cellEnd = xl_rowcol_to_cell(len(dfCorr.index) + 2, len(dfCorr.columns) )  # C2
    worksheet.conditional_format(cellStart + ':' + cellEnd, {'type':'cell',
                                            'criteria': '>=',
                                            'value':    0.60,
                                            'format':   formatHigh})

    worksheet.conditional_format('B3:K12', {'type':     'cell',
                                            'criteria': '<',
                                            'value':    -0.60,
                                            'format':   formatLow})

    print('excel sheet completed - Correlation')

    
# Write out the co-variance matrix work-sheet    
def excel_addsheet_covariance(workbook, df):
    
    worksheet = workbook.add_worksheet('Co-Variance')
    excel_add_df(inputWorkBook=workbook, inputWorkSheet=worksheet, inputSheetName='Co-Variance', 
                 inputDataFrame=df.cov().round(2),inputStartRow=0,inputStartCol=0,inputUseIndex=True)

    print('excel sheet completed - Covariance')

# Write out the 200 Samples - 100 head / 100 tail
def excel_addsheet_samples(workbook, df):    
    worksheet = workbook.add_worksheet('150samples')
    excel_add_df(inputWorkBook=workbook, inputWorkSheet=worksheet, inputSheetName='150samples (Top 75)', 
                 inputDataFrame=df.head(75),inputStartRow=0,inputStartCol=0,inputUseIndex=True)

    excel_add_df(inputWorkBook=workbook, inputWorkSheet=worksheet, inputSheetName='150samples (Tail 75)', 
                 inputDataFrame=df.tail(75),inputStartRow=80,inputStartCol=0,inputUseIndex=True)

    print('excel sheet completed - 150 Head / Tail Samples')



def generate_excel_workbook(inputFileName, outputFileName):

    # read in the file
    df = load_file(inputFileName)
    #print('file loaded')
    
    workbook = xlsxwriter.Workbook(outputFileName, {'nan_inf_to_errors': True})
    
    summaryDf = generate_summary_stats(df)

    # Write the summary / DOV
    excel_addsheet_summary_and_dov(workbook, df, summaryDf)
    excel_addsheet_summaryOrdered(workbook, summaryDf)
    excel_addsheet_correlation(workbook, df)
    excel_addsheet_covariance(workbook, df)
    excel_addsheet_samples(workbook, df)
    #excel_add
    # close wb

    workbook.close()    
    print('excel workbook generated: ' + outputFileName)



# ### Main Analysis Routine
def run_analysis_routine(fileOrDirectory, predictorVariable):
    
    # Determine if we are using a file or directory
    if check_is_file(fileOrDirectory):
        isFileToAnalyze = True
        isPathToAnalyze = False
        fileToEvaluate = fileOrDirectory
    elif check_is_directory(fileOrDirectory):
        isPathToAnalyze = True
        isFileToAnalyze = False
        directoryToEvaluate = fileOrDirectory
    else:
        isFileToAnalyze = False
        isPathToAnalyze = False
        print('Error - Invalid file or path passed in.  ' + fileOrDirectory)
        return 0
    
    # (future use) Determine if we are using a predictor variable or not
    if predictorVariable:
        print('predictor variable detected')
    
    if isPathToAnalyze:
        
        outputDirectory = append_analysis_directory(directoryToEvaluate)

        # Check output directory
        for fileName in os.listdir(fileOrDirectory):

            # If file is .csv
            if len(fileName) > 3:
                if fileName[-4:] == '.csv':

                    # grab the base file name
                    print('input file: ' + directoryToEvaluate + fileName)

                    # Set output file
                    outputFileName = os.path.join(outputDirectory, ('analysis_' + str(fileName)[:-4] + '_v2.xlsx'))
                    print('file to generate: ' + outputFileName)

                    # Generate Excel
                    generate_excel_workbook(directoryToEvaluate + fileName, outputFileName)        
        
    elif isFileToAnalyze:
        
        fileName = os.path.basename(fileOrDirectory)
        
        inputDirectory = os.path.dirname(fileOrDirectory)
        
        outputDirectory = append_analysis_directory(inputDirectory)
        
        outputFileName = os.path.join(outputDirectory, ('analysis_' + str(fileName)[:-4] + '_v2.xlsx'))
        print('file to generate: ' + outputFileName)
        
        generate_excel_workbook(fileOrDirectory, outputFileName)    


    
# example of directory
# python gen_excel_dataprofile.py "//media/data/project/data/dd_watertable/"

# example of single file
# python gen_excel_dataprofile.py "//media/data/project/data/dd_watertable/training_data.csv"        
        
# main method
if __name__ == '__main__':

    # argument # 1 - either "file" or "directory" as input parameter path (or full file name)
    if len(sys.argv) > 1:
        print('arg 1: ' + str(sys.argv[1]))
        fileOrDirectory = sys.argv[1]
        
    
    # argument #2 - predictor variable
    if len(sys.argv) > 2:
        print('arg 2: ' + str(sys.argv[2]))
        predictorVariable = sys.argv[2]
        
    # run the main analysis 
    run_analysis_routine(fileOrDirectory, None)
    




