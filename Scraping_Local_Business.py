#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Load libraries
import requests
import json
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import re
import time 
import pandas as pd 
import openpyxl
import certifi
import urllib3


# In[2]:


api_key = 'xxx'


# In[3]:


class Google_Maps_Client(object):
    lat = None
    lng = None
    lookup_type ='json'
    location_query = None
    api_key = None
    
    def __init__(self, api_key = None, address_or_zipcode = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if api_key == None:
            raise Exception("API key is required")
        self.api_key = api_key
        self.location_query = address_or_zipcode
        if self.location_query != None:   
            self.extract_lat_lng()
    
    def extract_lat_lng(self, location = None):
        loc_query = self.location_query
        if location != None:
            loc_query = location
        endpoint = f'https://maps.googleapis.com/maps/api/geocode/{self.lookup_type}'
        params = {'address' : loc_query,
                  'key' : self.api_key
                 }
        url_params = urlencode(params)
        url = f'{endpoint}?{url_params}'
        r = requests.get(url)
        if r.status_code not in range(200,299):
            return {}
        latlng = {}
        try:
            latlng = r.json()['results'][0]['geometry']['location']
        except:
            pass
        lat, lng = latlng.get('lat'), latlng.get('lng')
        self.lat = lat
        self.lng = lng
        return lat,lng
    
    def search(self, keyword = "commercial real estate developers", radius = 50000, location = None):
        lat,lng = self.lat, self.lng
        if location != None:
            lat,lng = self.extract_lat_lng(location = location)
        endpoint = f'https://maps.googleapis.com/maps/api/place/nearbysearch/{self.lookup_type}'
        params = {'key': self.api_key,
                'location': f'{lat},{lng}',
                'radius': radius,
                'keyword': keyword,
                'inputtype': 'textquery', 
                'fields': 'name,formatted_address,business_status,place_id'
                 }
        params_encoded = urlencode(params)
        places_url = f'{endpoint}?{params_encoded}'
        results = requests.get(places_url)
        page_1 = results.json()['results']
       
        next_page = []
        page_count = 1
        time.sleep(5)
        if results.json()['next_page_token'] != None:
            pagetoken = results.json()['next_page_token']
            while page_count < 2:
                page_count +=1
                params['pagetoken'] = results.json()['next_page_token']
                params_encoded = urlencode(params)
                places_url_2= f'{endpoint}?{params_encoded}'
                time.sleep(10)
                r_2 = requests.get(places_url_2)
                next_page += r_2.json()['results']
                pagetoken = r_2.json()['next_page_token']
        final_results = page_1+ next_page
        return final_results
    
    #Extracting place details including website for each listed prospect from above search
    def details(self, place_id = None, fields=["name", "formatted_address", "type", "website"]): 
        details_endpoint = f'https://maps.googleapis.com/maps/api/place/details/json'
        detail_params = {'key': api_key,
                     'place_id': place_id,
                     'fields': ",".join(fields)
                        }
        params_encoded3 = urlencode(detail_params)
        detail_url = f'{details_endpoint}?{params_encoded3}'
        r = requests.get(detail_url)
        if r.status_code not in range (200,299):
            return {}
        return r.json()


# In[4]:


client = Google_Maps_Client(api_key=api_key, address_or_zipcode = # "YOUR ADDREESS")
search_results = client.search(# "YOUR SEARCH QUERY)

#collect place details using the place_id tokens from the client.search() results
place_detail_dict = []

for item in search_results:
    my_place_id = item['place_id'].format()
    place_detail = client.details(place_id = my_place_id)
    if place_detail != place_detail_dict:
        place_detail_dict.append(place_detail)
place_detail_dict

#extract website information for each business, as listed in place_details_dict
company_website =[]
for url in company_list:
    try:
        company_website.append(url.get('website'))
    except AttributeError as err:
        print(str(err))
        continue
company_website


# In[ ]:


#set urlib.request parameters and collect all linkedin URLS using website information collected from place details

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

http = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=2.0, read=4.0),
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
    )


linkedin_list =[]
for url in company_website:
    if url == None:
        linkedin_list.append("Website not available")
    else:
        try:
            request = http.request('GET', url, headers = headers, redirect=1)

        except urllib3.exceptions.MaxRetryError as e: 
                linkedin_list.append((str(e)))  # print error detail (this may not be a timeout after all!)
        else:
                source_content = request.data
                soup = BeautifulSoup(source_content, 'html.parser')
                link = soup.find('a', href=re.compile("linkedin"))
                if link != None: 
                    linkedin_list.append((link.get('href')))
                else:
                    linkedin_list.append('No Linkedin on website')
                    
#update all dict items in company_list to include all linkedin URLs
n = 0

while n in range(1,len(linkedin_list)):
    for item in company_list:
        item.update({"linkedin": linkedin_list[n]})
        n +=1
company_list

# Convert list as a pd.dataframe and rearrange columns to read website and linkedin info easily.
local_business= pd.DataFrame(company_list) 
local_business=local_business[local_business.columns[[1,3,4,0,2]]] #rearranging column order

