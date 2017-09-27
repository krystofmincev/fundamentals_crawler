#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 16:55:26 2017

@author: mincev
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  9 00:34:00 2017

@author: mincev
"""
import pickle 
import csv
import json 
import gzip
import os
import requests
import re
import webbrowser as wb
from time import sleep 
from bs4 import BeautifulSoup
from urllib.request import urlopen

class helper(object):
    """
    supports:
        saving and loading python data structures
        getting a url (output bs_object) and identifing hyperlinks
        downloading and opening files
    """
    global REPEAT, TIMEOUT, SLEEP
    REPEAT = 5
    TIMEOUT = 5
    SLEEP = 0.5
    
    def save_obj(filename, obj):
        """
        input:
            filename (str) = name of file excluding .pkl
            obj = data structure to save
        output:
            -
        """
        assert type(filename) is str
        
        overide = False
        while os.path.isfile('obj/' + filename + '.pkl') is True and overide is False:
            print("File already exists:\n")
            input_overide = input("Do you want to overide the file? (y/n)\n")
            if input_overide.lower() == 'y': 
                overide = True 
            else: 
                filename = input("Choose a different filename:\n")
        
        assert filename[-4:] is not ".pkl"
        with open('obj/' + filename + '.pkl', 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)    

    def load_obj(filename):#
        """
        input:
            filename (str) = name of file excluding .pkl
            obj = data structure to save
        output:
            python obj
        """
        assert type(filename) is str
        assert filename[-4:] is not ".pkl"
        
        with open('obj/' + filename + '.pkl', 'rb') as f:
            return pickle.load(f)
        
    def save2csv(filename, obj):
        """
        Saves 'obj' to csv 'filename' in obj folder.
        Input:
            filename (str) = name of file exculiding .csv
            obj (list of lists) = eg: xml links from EDGAR Crawler 
        Output:
            saved (bool) = True if succsfully saved obj
        """
        assert type(filename) is str 
        assert type(obj) and type(obj[0]) is list 
        
        write_to = "w"
        if os.path.isfile('obj/' + filename + '.csv'):
            write_to = "a"
        
        try:
            with open('obj/' + filename + '.csv', write_to) as file:
                writer = csv.writer(file)
                writer.writerows(obj)
            return True
        except:
            print("Failed to save obj")
            return False
    
    def json_dump(filename, obj):
        """
        Saves 'obj' to txt 'filename' in obj folder.
        Input:
            filename (str) = name of file exculiding .csv
            obj (list of lists) = eg: xml links from EDGAR Crawler 
        Output:
            saved (bool) = True if succsfully saved obj
        """
        assert type(filename) is str 
        assert type(obj) and type(obj[0]) is list
        
        with open('obj/' + filename + '.txt','w') as file:
            json.dump(obj, file)
    
    def retrive_bs_obj(url, use_header = False, use_mobile_header = False):
        """
        Get Beautifuk Soup ibj using requests.get
        Input:
            url (str) = site url to access 
            use_header (bool) = if True requests uses either a pc of mobile header 
            use_mobile_header = if True mobile header is used
        Output:
            bs_obj 
        """
        assert type(url) is str
        
        print("Loading site data for:\n" + url +"\n")
        if use_header: #set header to pc browser or mobile
            if use_mobile_header:
                user_agent = "User-Agent:Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) " + \
                             "AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D257 " + \
                             "Safari/9537.53"
            else:
                user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)" + \
                             "AppleWebKit 537.36 (KHTML, like Gecko) Chrome"
          
            headers = {"User-Agent":user_agent,
                       "Accept":"text/html,application/xhtml+xml,application/xml;" + \
                             "q=0.9,image/webp,*/*;q=0.8"}
        
        session = requests.Session()
        try:
            if use_header:
                archive = session.get(url, headers=headers).content
            else:
                archive = session.get(url).content
        except:
            try:
                archive = urlopen(url)
            except:
                print("Unable to retrive data for:\n" + url)
                return None
        
        print("Finished loading data\n")
        return BeautifulSoup(archive)
    
    def get_href(bs_obj, regular_expression = "form\.[0-9]+\.idx"):
        """
        Get href links corresponding to regular expression
        Input:
            bs_obj = Beautiful Soup object from eg retrive_bs_obj function
            regular_expression (str) = regular expression for identifying valid href
        Output:
            links (str list) = list of hrefs
        """
        assert type(regular_expression) is str
        
        print("Extracting idx hyperlinks")
        archive_links = bs_obj.find_all("a", \
                                        {"href": re.compile(regular_expression)})
        
        #store links
        links = []
        try:
            print("Found " + str(len(archive_links)) + " links.")
            for link in archive_links:
                links.append(link["href"])
        except:
            print("No href links found")
            pass
        
        print("--------------------\n")
        return links
      
    def download_url(url):
        """
        Input:
            url (str) = 
        Output:
            (bool) = TRUE if downloaded 
        """
        assert type(url) is str 
        
        print("Downloding data from:\n"  + url)
        for i in range(REPEAT):
            if wb.open(url, autoraise=False): 
                return True
            sleep(SLEEP)
            
        print("Unable to Download")
        print("-----------------------\n")
        return False
    
    def load_idx(filename, file_path = "/home/mincev//Downloads/", \
                 remove_download = True):
        """
        Adds csv data as a list to a dictionary if available 
        Input:
            filename (str) = filename (.idx or.idx.gz file)
            file_path (str) = directory where file stored 
            remove_download = if TRUE file removed after excecution
        Output:
            (ndarray) = file as numpy array
        """
        assert type(filename) and type(file_path) is str
        assert filename[-4:] == ".idx" or filename[-7:] == ".idx.gz"
        assert type(remove_download) is bool
        
        counter = 0
        file = file_path + filename
        while not counter == TIMEOUT and not os.path.exists(file):
            sleep(1)
            counter += 1

        if counter == TIMEOUT: #if could not find file
            print("Could not find file: {0}".format(filename))
            print("-------------------------\n")
            return None
        
        if filename[-3:] == ".gz": #if .gz file use gzip library to open
            comp_file = gzip.open(file, 'r')
            data = comp_file.readlines()
            data = [row.decode("utf-8") for row in data] #requires decoding
            comp_file.close()
        else:
            with open(file) as comp_file:
                data = comp_file.readlines()
        
        if remove_download:
            os.remove(file)
        
        return data