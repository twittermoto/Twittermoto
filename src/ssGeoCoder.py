# -*- coding: utf-8 -*-
"""
Created on Sat Jun 22 13:53:57 2019

@author: Arsalan
"""
# IMPORTANT NOTE:
# While using FTS3 and FTS4 extensions of sqlite3 you need to download latest
# sqlite3.dll from https://www.sqlite.org/download.html and paste the dll file
# in the following folder: C:\Users\<Username>\Anaconda3\DLLs

import sqlite3
import os.path
import time
from fuzzywuzzy import process
from geopy import Nominatim
from geopy.extra.rate_limiter import RateLimiter

class GeoCoder():
    
#-------------------------------ATTRIBUTES-------------------------------------    
    # STATIC ATTRIBUTES/VARIABLES
    DIR = './Data'
    
    # CLASS INSTANTIATION
    def __init__(self,dbfilename = 'cities500',sourcefilename = 'cities500'):
        self.dbfilename = dbfilename # filename of database to be created/queried
        self.sourcefilename = sourcefilename # filename of the text file containing data source
        # txt file containing data
        self.FILE = '/{}.txt'.format(self.sourcefilename)
        # path to txt file containing data
        self.file = '{}{}'.format(GeoCoder.DIR, self.FILE)
        # creating instance of Nominatim
        self.geolocator  = Nominatim(user_agent="my-application")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1) 
        
# ------------------------------- METHODS -------------------------------------
    
    # METHOD TO CREATE NEW FTS4 TABLE IN DATABASE
    def create_table(self):
        self.c.execute('''DROP TABLE IF EXISTS {}'''.format(self.dbfilename))
        self.c.execute('''CREATE VIRTUAL TABLE cities500 USING fts4(geonameid, name, asciiname, alternatenames, latitude, longitude, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date)''')

    # METHOD TO ENTER DATA ROW IN DATABASE TABLE
    def data_entry(self,lineList):
        geonameid ,	name , asciiname , alternatenames ,latitude , longitude , feature_class , feature_code , country_code , cc2 , admin1_code , admin2_code , admin3_code , admin4_code , population , elevation , dem , timezone , modification_date \
         = lineList
        try:
            population = int(population)
        except:
            population  = 'NaN'
        try:
            elevation = float(elevation)
        except:
            elevation = 'NaN'
        try:
            dem = int(dem)
        except:
            dem = 'NaN'
        self.c.execute(" INSERT INTO cities500 (geonameid ,	name , asciiname , alternatenames ,latitude , longitude , feature_class , feature_code , country_code , cc2 , admin1_code , admin2_code , admin3_code , admin4_code , population , elevation , dem , timezone , modification_date) \
                  VALUES( ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ?) "  , \
                  (int(geonameid) ,	name , asciiname , alternatenames , float(latitude) , float(longitude) , feature_class , feature_code , country_code , cc2 , admin1_code , admin2_code , admin3_code , admin4_code , population , elevation , dem , timezone , modification_date) )
    
    # METHOD TO CREATE NEW DATABASE AND POPULATE THE ROWS
    def create_database(self):
        start = time.time()
        if os.path.isfile('{}.db'.format(self.dbfilename)):
            print('DataBase Already Exist!')
        else:
            self.open_connection()
            print('Creating DataBase ....')
            self.create_table()
            with open(self.file, encoding="utf8") as f:
                for line in f:
                    lineList = line.split('\t')
                    self.data_entry(lineList)
            self.conn.commit()        
            print('.... Finished')
            self.close_connection()
            end = time.time()
            print('DataBase created in {:.4f} seconds'.format(end - start))            
        
    # METHOD TO READ LAT LONG FROM DATABASE
    def get_Lat_Long(self,findName):
        start = time.time()
        self.c.execute("SELECT name,latitude,longitude,population FROM cities500 WHERE name MATCH ? ORDER BY population" , [findName])
        try:
            for row in self.c.fetchall():
                result = row
                print(row)
            end = time.time()
            print('Search time was {:.6f} seconds'.format(end - start))    
            return result # returns the last result from fetchall()
        except:
            print('WARNING! No Location Found.')
            result = []
    
    # METHOD TO READ LAT LONG FROM DATABASE USING FUZZY SEARCH        
    def get_fuzzy_Lat_Long(self,findName):
        start = time.time()
        nameList = self.c.execute("SELECT name FROM cities500") # alternateNames can also be used instead of name here
        Ratios = process.extract(findName,nameList)
        foundName = Ratios[0][0][0]
        result = self.get_Lat_Long(foundName)
        end = time.time()
        print('Search time was {:.6f} seconds'.format(end - start)) 
        return result         
    
    # METHOD TO CONVERT LOCATION TO LAT LONG USING NOMINATIM
    def get_Lat_Long_Nominatim(self,findName):
        start = time.time()
        geo = self.geocode(findName)
        if geo is None:
            result = None
        else:
            result = (findName,geo.latitude,geo.longitude,-1) # -1 implies there is no population data using Nominatim
        end = time.time()
        print('Search time was {:.6f} seconds'.format(end - start)) 
        return result         
    
    # METHOD TO CONVERT LOCATION TO LAT LONG USING FTS4, FUZZY SEARCH, AND NOMINATIM
    def get_Lat_Long_Hybrid(self,findName):
        result = self.get_Lat_Long(findName) 
        if result is None:
            print('Using Nominatim to find location...')
            result = self.get_Lat_Long_Nominatim(findName)
            if result is None:
                print('Using Fuzzy Search to find location...')
                result = self.get_fuzzy_Lat_Long(findName)                    
        return result         
    
    # METHOD TO CLOSE CONNECTION TO DATABASE
    def close_connection(self):
        self.c.close()
        self.conn.close()
        print('Connection to {}.db Closed!'.format(self.dbfilename))
    
    # METHOD TO OPEN CONNECTION TO DATABASE    
    def open_connection(self):    
        self.conn = sqlite3.connect('{}.db'.format(self.dbfilename))
        self.c = self.conn.cursor()
        print('Connection to {}.db Opened!'.format(self.dbfilename))        

    