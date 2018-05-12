# -*- coding: utf-8 -*-
import codecs
import nltk
from nltk.corpus import stopwords, sentiwordnet as swn
import numpy as np
import scipy.signal as sps
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import math

#nltk.download('sentiwordnet')
#nltk.download('punkt')
stops = set(stopwords.words('english'))

def get_sentiment_score(word):
    syn_set = list(swn.senti_synsets(word))
    
    if len(syn_set) == 0:
        return [0, 0]

    pos_score = 0
    neg_score = 0
    
    for syn in syn_set:
        pos_score += syn.pos_score()
        neg_score += syn.neg_score()
    
    pos_score /= len(syn_set)
    neg_score /= len(syn_set)
    
    return [pos_score, neg_score]

def get_window_sentiment_score(scripts):
    pos_score = 0
    neg_score = 0
    cnt = 0
    for script in scripts:
        token_list = nltk.word_tokenize(script)
        for token in token_list:
            token_senti_score = get_sentiment_score(token)
            
            # sentiment score가 0, 0인 경우 계산에 제외함
            if token_senti_score[0] == 0 and token_senti_score[1] == 0:
                cnt -= 1
            else:
                pos_score += token_senti_score[0]
                neg_score += token_senti_score[1]
        cnt += len(token_list)
    
    pos_score /= cnt
    neg_score /= cnt
    
    return [pos_score, neg_score]

def savitzky_golay_filter(filepath, image=False):
    title = filepath.split('_')[0]
    
    with codecs.open('./score/'+filepath, 'r') as f:
        data = f.read()
    data= data.split('\n')
    
    score_arr = []
    for score in data:
        try:
            pos, neg = score.split(' ')
            score_arr.append([pos, neg])
        except ValueError:
             pass
    np_score_arr = np.array(score_arr).astype(np.float32).transpose()
    
    pos_filter = sps.savgol_filter(np_score_arr[0], 33, 5)
    neg_filter = sps.savgol_filter(np_score_arr[1], 33, 5)

    #save smooth graph image
    if image:
        ymax = math.ceil(np.max(np_score_arr)/0.01)*0.01
        
        plt.figure(figsize=(550/80,700/80))
        plt.suptitle('Data Smoothing ('+title+')', fontsize=16)
    
        #positive sentiment score graph
        plt.subplot(2, 1, 1)
        plt.plot(np_score_arr[0], '-k', color='red', label='raw')
        plt.plot(pos_filter, "-k", label='filtered')
        
        plt.title('positive sentiment score')
        plt.xlabel('window')
        plt.ylabel('sentiment score')
        plt.legend()
    
        ax1 = plt.axis()
        plt.axis([ax1[0], ax1[1], 0, ymax])

        #negative sentiment score graph
        plt.subplot(2, 1, 2)
        plt.plot(np_score_arr[1], '-k', color='red', label='raw')
        plt.plot(neg_filter, '-k', label='filtered')
        
        plt.title('negative sentiment score')
        plt.xlabel('window')
        plt.ylabel('sentiment score')
        plt.legend()
        
        ax2 = plt.axis()
        plt.axis([ax2[0], ax2[1], 0, ymax])
    
        plt.savefig('./graph/%s.png' % filepath.split('.txt')[0], dpi=80)
        plt.gcf().clear()

    #Min-Max Scaling
    scaler = MinMaxScaler(feature_range=(0,1))
    norm_senti_score = scaler.fit_transform(np.array([pos_filter, neg_filter]).reshape(pos_filter.shape[0]*2, 1)).reshape(pos_filter.shape[0], 2)
    
    #save normalized data
    with codecs.open('./norm/%s.txt' % filepath.split('.txt')[0], 'w') as f:
        for score in norm_senti_score :
            f.write('%f %f\n' % (score[0], score[1]))

def work(script_filepath):
    print(script_filepath)
    
    # 불필요한 문자, 공백 제거
    with codecs.open('./raw_script/'+script_filepath, 'r', 'utf-8', errors='ignore') as f:
        script = f.read()
    
    script_list = script.split('\n')
    
    idx = 0
    while idx < len(script_list):
        script_list[idx] = script_list[idx].strip()
        if script_list[idx] == '':
            script_list.pop(idx)
        else:
            script_list[idx]= ' '.join(list(filter(lambda w: not w.lower() in stops, script_list[idx].split())))
            
            idx += 1
    
    # get sentimental score
    # 20 line을 1 window로 만든다.
    # ToDo: N line to 1 window 에 적절한 N 구하기
    # ToDo: 품사에 맞는 감정점수 가져오기
    # ToDo: remove characters name
    
    N = 20
    
    num_windows = int(len(script_list)/N)
    
    with codecs.open('./score/'+script_filepath, 'w', 'utf-8') as f:
        for idx in range(num_windows):
            window_senti = get_window_sentiment_score(script_list[20*idx:20*(idx+1)])
            f.write('%f %f\n' % (window_senti[0], window_senti[1]))

    # normalize(savitzky-golay-filtering with min-max-norm)
    savitzky_golay_filter(script_filepath, image=True)
    