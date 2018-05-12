# -*- coding: utf-8 -*-
"""
Created on Sun May  6 13:26:15 2018

@author: KIM
"""
from concurrent.futures import ThreadPoolExecutor
from string import ascii_uppercase
import time
import os
import script_crawler as sc
import preprocessing

"""
1. IMSDB에서 영화 목록 가져오기
2-1. IMSDB에서 영화 스크립트 가져오기
2-2. IMDB에서 영화 평점 가져오기
3. 스크립트 전처리
4=1. 스크립트 감정점수 치환
4-2. Smooting (savitzky-golay filtering)
4-3. Min Max norm
5. 모델 구성(random search or bayesian optimization)
6. 학습
7. 테스트
"""

"""
Get movie script
"""

start_time = time.time()

# [A-Z, 0]
prefix_list = list(ascii_uppercase)
prefix_list.append('0')

os.makedirs('raw_script', exist_ok=True)

#with ThreadPoolExecutor(max_workers=4) as executor:
#    for prefix in prefix_list:
        #executor.submit(sc.work, prefix)
        
for prefix in prefix_list:
    sc.work(prefix)

get_script_time = time.time()
print('end -', get_script_time-start_time, 'sec')

"""
Preprocessing
"""

start_time = time.time()
os.makedirs('score', exist_ok=True)
filepath_list = os.listdir('raw_script')
for filepath in filepath_list:
    preprocessing.work(filepath)

"""
with ThreadPoolExecutor(max_workers=4) as executor:
    for filepath in filepath_list:
        executor.submit(preprocessing.work,filepath)

end_time = time.time()
print(end_time-start_time,'sec')
"""