# -*- coding: utf-8 -*-
from selenium import webdriver
import requests
from bs4 import BeautifulSoup as bs
import codecs
from os import path

def get_movie_list(url):
    res = requests.get(url)
    
    soup = bs(res.text, 'html.parser')
    soup_td = soup.find_all('td')
    movie_tag_list = soup_td[5].find_all('p')
    
    return movie_tag_list

def get_script_url(movie_url):
    res = requests.get('http://www.imsdb.com'+movie_url)
    
    soup = bs(res.text, 'html.parser')
    a_tag = soup.find('table', 'script-details').find_all('a', href=True)[-1]
    
    return a_tag['href']

def get_movie_score(driver, movie_title):
    res = requests.get('http://www.imdb.com/find?q='+movie_title+'&s=all')
    
    soup = bs(res.text, 'html.parser')
    movie_url = soup.find('table', 'findList').find('td', 'result_text').find('a', href=True)['href']
    
    driver.get('http://www.imdb.com'+movie_url)
    
    html = driver.page_source
    
    soup = bs(html, 'html.parser')
    score = soup.find('div', 'ratingValue').find('span').text
    
    return score

def get_movie_script(driver, script_url):
    
    if not path.basename(script_url).endswith('html'):
        return

    movie_title = script_url[9:-5]
    
    score = get_movie_score(driver, movie_title)
    
    print(movie_title, score)
    
    driver.get('http://www.imsdb.com' + script_url)

    html = driver.page_source
    
    script_soup = bs(html, 'html.parser', from_encoding='utf-8')
    script_td = script_soup.find_all('td', 'scrtext')
    if script_td:
        script_td[0].find('table').decompose()
        script_td[0].find('div').decompose()
        script_text = script_td[0].get_text()
        script_text = script_text.replace('\r','\n')
        
        with codecs.open('./raw_script/%s_%s.txt' % (script_url[9:-5], score), 'w', 'utf-8') as f:
            f.write(script_text)
            
def work(prefix):
    # selenium driver config
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver.Chrome('chromedriver', chrome_options=options)
    driver.implicitly_wait(0.4)

    movie_tag_list = get_movie_list('http://www.imsdb.com/alphabetical/'+prefix)
    
    for movie_tag in movie_tag_list:
        movie_url = movie_tag.find('a', href=True)['href']
        movie_script_url = get_script_url(movie_url)
        get_movie_script(driver, movie_script_url)
        
    driver.quit()
