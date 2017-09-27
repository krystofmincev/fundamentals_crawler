#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 15:25:02 2017

@author: mincev
USEFUL LINKS:
    http://www.euclidean.com/deep-learning-investing-part-2-preprocessing-data/
    http://sraf.nd.edu/data/
    http://sraf.nd.edu/textual-analysis/resources/#LM_10X_Summaries
    
TO DO:
    Write financial statement txt extractrer - extract qualitative data from report
"""
import string
from helper import helper

class EDGAR_Crawler(object):
    """
    A class designed for scraping SECs EDGAR to retrive fundamental financial data \n
    Supports: obtaining links to txt fillings, and links to xml filings  
    """
    global URL_START
    URL_START = "https://www.sec.gov/Archives/edgar/"
    year = 2011
    quarter = "QTR3"
    
    def get_idx_links(self, year = 1995, quarter = "QTR1"):
        """
        Obtain links from URL_START for downloading company fillings ('form')
        for a given 'year' and 'quarter'
        NOTE: data starts at QTR4 1994
        Input: 
            year (int) = year for which forms are desired (in which filled)
            quarter (str) = fiancial quarter from QTR1 - QTR4
        Output:
            links (str list) = list of idx links for quarter and year 
        """
        assert type(year) is int
        assert year >= 1994 
        assert quarter in ["QTR1", "QTR2", "QTR3", "QTR4"]
        if year == 1994: assert quarter == "QTR4"

        url = URL_START + "daily-index/" + str(year) + "/" + quarter + "/"
        bs_obj = helper.retrive_bs_obj(url)
        links = helper.get_href(bs_obj, "form\.[0-9]+\.idx")
        return links
    
    def idx_links_scraper(self, link, year, quarter, form = "10-K"):
        """
        Obtain 'form' supplementary variables from idx files for a given year and quarter - same \n
        year and quarter as was used to get the link
        NOTE: File_Name eg(data/1347185/0001193125-14-264930.txt) gives sec link to txt 'form'
        Input: 
            link (str) = idx file obtained from SEC - one output element from get_idx_links 
            year (int) = year for which forms are desired (in which filled)
            quarter (str) = fiancial quarter from QTR1 - QTR4
            form (list) = company filed document eg: 10-K, or 8-K, or 10-D
        Output:
            form_list (str list) = list of [Form_Type, Company_Name, CIK, Date_Filed, File_Name]
        """
        assert type(link) is str 
        assert link[-4:] == '.idx' or link[-7:] == ".idx.gz"
        assert type(year) is int and type(quarter) is str
        
        url = URL_START + str(year) + "/" + quarter + "/" + link
        if not helper.download_url(url): #if download fails return None
            return None
        
        try:
            idx_object = helper.load_idx(link)
            assert idx_object is not None 
        except:
            return None
        
        form_list = []
        for idx_line in idx_object:
            if form in idx_line[:len(form)]: #check for correct form
                form_list.append(idx_line.split())
                
        return form_list
    
    def get_ciks(self):
        """
        Function to get CIK compnay identifier. As well as the cik, the name, and 
        sec number are retrieved.
        Input:
            -
        Output:
            data (str list) = list of [Name, CIK, SEC] (list of lists)
        """
        print("Downloading CIKs (Company Identifier Numbers) from: \n\
              https://www.sec.gov/divisions/corpfin/organization/..\n\
              This might take a while so please be patient....\n")
        
        url_start = "https://www.sec.gov/divisions/corpfin/organization/cfia-{0}.htm"
        data = []
        for letter in string.ascii_lowercase:
            url = url_start.format(letter)
            bs_obj = helper.retrive_bs_obj(url, use_header = True, 
                                           use_mobile_header = True)
            try: 
                assert bs_obj is not None
                rows = bs_obj.find("table",{"id":"cos"}).find_all('tr',{"valign":"top"})
                for row in rows:
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele])  
                print("Succesfully found ciks for letter: " + letter)
                print("-------------------------------")
            except:
                print("Unable to find cik for letter: " + letter)
                print("-------------------------------")
                continue
        
        return data
                
    def get_xml_links(self, cik = 320193):
        """
        Obtains xml links to 10-K forms for a given cik - to be used with \n
        finstr (R library)
        Input:
            cik (int) = cik - firm numeric identifier eg: default for apple
        Output:
            xml_links (list str) = xml_links to 10-k files used with R code finstr
        
        """
        assert type(cik) is int 
        
        print("Retrieving xml links for " + str(cik) + " ciks" +
              "\nThis may take a while so please be patient...\n")
        url = URL_START + 'data/' + str(cik)
        bs_obj = helper.retrive_bs_obj(url, use_header = True, use_mobile_header = True)
        
        if bs_obj is None: 
            return None 
        
        regular_expression = "\/Archives\/edgar\/data\/" + str(cik) +"\/[0-9]+"
        intermediate_links = helper.get_href(bs_obj, regular_expression)
        number_of_int_links = str(len(intermediate_links))
        print(number_of_int_links + " intermediate links found\n")
        
        xml_links = []
        xml_set = set() #prevent duplication of links
        url_start = "https://www.sec.gov"
        regular_expression = "[a-z]+\-[0-9]{8}.xml"
        for i, intermediate_link in enumerate(intermediate_links):
            print("Link " + str(i) + " out of " + number_of_int_links)
            url = url_start + intermediate_link
            bs_obj = helper.retrive_bs_obj(url, use_header = True, \
                                           use_mobile_header = True)
            if bs_obj is not None: #if data found 
                xml_link = helper.get_href(bs_obj, regular_expression)
                if len(xml_link) is 1: #link found so add to xml_links 
                    if xml_link[0] not in xml_set: 
                        xml_set.add(xml_link[0])
                        xml_link.append(str(cik)) #add identifier
                        xml_links.append(xml_link)
        
        return xml_links
         
if __name__ == "__main__":
    #get all ciks
    crawler = EDGAR_Crawler()
    ciks = crawler.get_ciks()#[Name, CIK, SEC]
    
    #test case get APPLE XMLs
    apple_links = crawler.get_xml_links()
    assert len(apple_links) > 0
    helper.json_dump("apple_links", apple_links)
    
    #get all xml links
    cik_xml_dic = {}
    ciks_with_docs = [] #keep track of ciks that have f.statements
    for cik in ciks:
        cik_id = int(cik[1])
        xml_links = crawler.get_xml_links(cik_id)
        if len(xml_links) is not 0: #if financial statements found for cik
            cik_xml_dic[cik_id] = xml_links
            ciks_with_docs.append(cik)
    
    #save cik_xml_dic
    print("Saving data...")
    helper.json_dump("cik_xml_dic", cik_xml_dic)
    print("\nData saved in obj folder")   
