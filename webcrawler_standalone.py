#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 26 17:12:07 2019

@author: Daphne Cheung
"""

from datetime import datetime
import time
import requests
import xlsxwriter
import urllib
import urllib.request
import urllib.parse
from urllib.parse import urlparse
import urllib.error
import re


def check_for_redirects(url):
    try:
        r = requests.get(url, allow_redirects=False, timeout=0.5)
        if 300 <= r.status_code < 400:
            return r.status_code
        else:
            return '[no redirect]'
    except requests.exceptions.Timeout:
        return '[timeout]'
    except requests.exceptions.ConnectionError:
        return '[connection error]'

def site_crawler(domainList, starter, original, all_URLs={}):
    
    starter = urllib.parse.quote(starter, safe="/:?=&")
    o = urlparse(starter)
    currDomain = o.hostname
    scheme = o.scheme
    path = o.path
    
    if (scheme != "https" and scheme != "http"):
        return all_URLs
    
    if (re.search("\.(js|css|doc|pdf|jpg|jpeg|avi|mov|mp[0-9]|xls|ppt|wav|svg|flv|png|gif|ico)", path, re.IGNORECASE)):
        return all_URLs
    
    if starter in all_URLs.keys():
        return all_URLs
    
    if (type(domainList)!=list or not domainList):
        print ("Incorrect format or empty domain list provided.")
        return 0
    
    domains = "(";
    for domain in domainList:
        domains += "https?:\/\/" + domain.replace(".","\.") + "|"
    domains = domains[:-1]
    domains += ")"

    pattern = r'href="((' + domains + '[^"?&#]+)|\/[^"?&#]+)'
    pattern_canonical = r'rel="canonical" href="([^"]+)"'
    pattern_hreflang = r'rel="alternate" href="(https?:\/\/[^"]+)" hreflang="([^"]+)"'
    
    regex = re.compile(pattern, re.IGNORECASE)
    regex_canonical = re.compile(pattern_canonical, re.IGNORECASE)
    regex_hreflang = re.compile(pattern_hreflang, re.IGNORECASE)
    
    canonical = "Not found"
    hreflang = "Not found"
    lang = "Not found"
    pageName = "~deletekey~"
    
    try:
        print("now connecting to: " + starter)
        worksheet.write('D' + str(len(all_URLs) + 2), check_for_redirects(starter))
        with urllib.request.urlopen(starter) as response:
            html = response.read().decode('utf-8')
            
        for curr_page in regex_canonical.finditer(html):
            canonical = curr_page.group(1)
        
        for curr_page in regex_hreflang.finditer(html):
            hreflang = curr_page.group(1)
            lang = curr_page.group(2)
        
        if (canonical != "Not found" and "fr" in lang):
            lang = "en"
        elif (hreflang != "Not found" and "en" in lang):
            lang = "fr"
 
        
        all_URLs[starter] = (canonical, hreflang, lang)
        worksheet.write('C' + str(len(all_URLs) + 1), starter)
        worksheet.write('E' + str(len(all_URLs) + 1), canonical)
        worksheet.write('F' + str(len(all_URLs) + 1), hreflang)
        worksheet.write('G' + str(len(all_URLs) + 1), lang)
        worksheet.write('H' + str(len(all_URLs) + 1), pageName)
        print ("all_URLs length: " + str(len(all_URLs)))
        
        # Make sure we want to scrape this page (in current domain)
        c = urlparse(canonical)
        canDomain = c.hostname
        if (canDomain not in domainList):
            return all_URLs
        
        for m in regex.finditer(html):   
            new_link = m.group(1)
            
            if ("http" not in new_link):
                new_link = currDomain + new_link
                if ("http" not in new_link):
                    new_link = "https://" + new_link
            
            if (new_link not in all_URLs.keys()):
                worksheet.write('A' + str(len(all_URLs) + 1), original)
                worksheet.write('B' + str(len(all_URLs) + 2), m.group(1))
                site_crawler(domainList, new_link, starter, all_URLs)
        
        return all_URLs
        
    except urllib.error.HTTPError as err:
        all_URLs[starter] = (err.code, err.code, err.code)
        worksheet.write('A' + str(len(all_URLs) + 1), original)
        worksheet.write('C' + str(len(all_URLs) + 1), starter)
        worksheet.write('E' + str(len(all_URLs) + 1), str(err.code))
        worksheet.write('F' + str(len(all_URLs) + 1), str(err.code))
        worksheet.write('G' + str(len(all_URLs) + 1), lang)
        worksheet.write('H' + str(len(all_URLs) + 1), pageName)
        print (starter + ": " + str(err.code))
        

if __name__ == "__main__":
    
    start_time = time.time()
    
    # Timestamps
    timestamp = datetime.now().isoformat()
    dtstamp = timestamp.replace(":","-").replace(".","-")
    
    # Excel worksheet
    workbook = xlsxwriter.Workbook('webcrawltest_' + dtstamp + '.xlsx')
    worksheet = workbook.add_worksheet()
    worksheet.write('A1', 'Parent URL')
    worksheet.write('B1', 'Relevant Path')
    worksheet.write('D1', 'HTTP Status Code')
    worksheet.write('C1', 'Absolute Path')
    worksheet.write('E1', 'Canonical Link')
    worksheet.write('F1', 'Hreflang Link')
    worksheet.write('G1', 'Language')
    worksheet.write('H1', 'Page Name')    
    
    # Set the parameters
    starter = input("Please enter the site URL you wish to crawl: ")
    if (starter[0:5]!="http"):
        starter = "https://" + starter
    domainList = input("Enter all the domains that make up the site separated by a comma: ")
    domainList = domainList.split(',')
    #campaignPages = []
    
    # Start crawling
    try:
        site_crawler(domainList, starter, starter)
        
        #for link in campaignPages:
        #    site_crawler(domainList, link, prefix)
        
    finally:
        workbook.close()
        
    print("--- %.2fs seconds ---" % (time.time() - start_time))
    workbook.close()