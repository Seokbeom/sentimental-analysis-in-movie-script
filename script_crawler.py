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

def get_script_url(driver, movie_url):
    driver.get('http://www.imsdb.com'+movie_url)

    html = driver.page_source

    soup = bs(html, 'html.parser')
    a_tag = soup.find('table', 'script-details').find_all('a', href=True)[-1]
    
    url = a_tag['href']
    
    if not url.startswith('/scripts/'): # script url is not exist
        return ''
    else:
        return url

#ToDO: 연도 더하기
def get_movie_score(driver, movie_title):
    try:
        driver.get('https://www.imdb.com/search/title?title=%s&title_type=feature' % movie_title)
        html = driver.page_source
        soup = bs(html, 'html.parser')
        
        score_list = soup.find('div', 'lister-list').find_all('div', 'lister-item')
        
        for score_soup in score_list:
            try:
                score = score_soup.find('div', 'ratings-imdb-rating')['data-value']
                
                if score:
                    return score
            except TypeError:
                pass
            
    except AttributeError:
        driver.get('http://www.imdb.com/find?q='+movie_title+'&s=tt')
        html = driver.page_source
        soup = bs(html, 'html.parser')
        
        soup_table = soup.find('table', 'findList')
        if not soup_table:
            print(movie_title, 'You have to find score for this movie by yourself (refer- : https://www.imdb.com)')
            return 0
        movie_url_list = soup_table.find_all('tr', 'findResult')
        
        for movie_url in movie_url_list:
            url = movie_url.find('td', 'result_text').find('a', href=True)['href']
        
            driver.get('http://www.imdb.com'+url)
    
            html = driver.page_source
            
            soup = bs(html, 'html.parser')
            try:
                score = soup.find('div', 'ratingValue').find('span').text
                
                if score:
                    return score
            except:
                pass
    return 0

def get_movie_script(driver, script_url):
    
    if not path.basename(script_url).endswith('html'):
        return
    
    movie_title = script_url[9:-5]

    score = get_movie_score(driver, movie_title)
    
    # print(movie_title, score)
    
    driver.get('http://www.imsdb.com' + script_url)

    html = driver.page_source
    
    script_soup = bs(html, 'html.parser', from_encoding='utf-8')
    script_td = script_soup.find('td', 'scrtext')

    if script_td:        
        for br in script_td.find_all('br'):
            br.replace_with('\n')
        
        if len(script_td.find_all('p')) > 100:
            script_text = ''
            
            for script_line in script_td.find_all('p'):
                script_text += script_line.get_text()
        else:
            script_td.find('table').decompose()
            script_td.find('div').decompose()
            script_text = script_td.get_text()
            
            if len(script_text.split('\n')) < 100:
                return 0

        script_text = script_text.replace('\r','\n').replace("\'", "'").replace('\xa0', ' ')
        with codecs.open('./raw_script/%s_%s.txt' % (movie_title, score), 'w', 'utf-8') as f:
            f.write(script_text)
            
        return 1
    else:
        return 0
            
def work(prefix):
    print(prefix+' start')
    # selenium driver config
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    
    driver = webdriver.Chrome('chromedriver', chrome_options=options)
    driver.implicitly_wait(0.1)

    movie_tag_list = get_movie_list('http://www.imsdb.com/alphabetical/'+prefix)
    
    num_success = 0
    num_fail = 0
    for movie_tag in movie_tag_list:
        movie_url = movie_tag.find('a', href=True)['href']
        movie_script_url = get_script_url(driver, movie_url)
        
        if movie_script_url == '':
            continue
        result = get_movie_script(driver, movie_script_url)

        if result:
            num_success += 1
        else:
            print('fail: ', movie_script_url)
            num_fail += 1
    
    print('%s, all: %d success: %d fail: %d nonexsistent: %d'
          % (prefix, len(movie_tag_list), num_success, num_fail, len(movie_tag_list)-num_success-num_fail))
    driver.quit()
