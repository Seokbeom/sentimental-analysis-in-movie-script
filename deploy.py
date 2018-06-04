# -*- coding: utf-8 -*-
from keras.models import load_model
from sklearn.metrics import mean_squared_error
from scipy.spatial.distance import cosine
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np
import codecs 
import os

def rmse(actual, predict):
    return sqrt(mean_squared_error(actual, predict))

def make_deploy_data(filename):
    x_deploy = []
    y_deploy = []
    
    def split(x):
        if x:
            return x.split(' ')

    # Deploy
    with codecs.open('./deploy/'+filename, 'r') as f:
        scores = f.read()
    scores = scores.split('\n')[:-1]
    scores = list(map(split, scores))

    for idx in range(len(scores)-50):
        x_deploy.append(scores[idx:idx+50])
        y_deploy.append(scores[idx+50])

    x_deploy = np.array(x_deploy).reshape((len(x_deploy), 50, 2)).astype(np.float)
    y_deploy = np.array(y_deploy).reshape((len(y_deploy), 2)).astype(np.float)
    
    return x_deploy, y_deploy

def evaluation(title, actual, predict, image=True):
    actual_pos, actual_neg = np.hsplit(actual, 2)
    predict_pos, predict_neg = np.hsplit(predict, 2)
    rmse_avg = rmse(actual.reshape(actual.shape[0]*2,1), predict.reshape(predict.shape[0]*2,1))
    cosine_avg = cosine(actual.reshape(actual.shape[0]*2,1), predict.reshape(predict.shape[0]*2,1))
    cosine_avg = 1 - cosine_avg

    if image:
        plt.figure(figsize=(550/80,700/80))
        plt.suptitle('%s_%.3f_%d%%' % (title.split('.txt')[0], rmse_avg, int(cosine_avg*100)), fontsize=16)
    
        #positive sentiment score graph
        plt.subplot(2, 1, 1)
        plt.plot(actual_pos, '-k', label='actual')
        plt.plot(predict_pos, "-k", color='red', label='predict')
        
        plt.title('positive sentiment score')
        plt.xlabel('window')
        plt.ylabel('sentiment score')
        plt.legend()
    
        ax1 = plt.axis()
        plt.axis([ax1[0], ax1[1], 0, 1])

        #negative sentiment score graph
        plt.subplot(2, 1, 2)
        plt.plot(actual_neg, '-k', label='actual')
        plt.plot(predict_neg, '-k', color='red', label='predict')
        
        plt.title('negative sentiment score')
        plt.xlabel('window')
        plt.ylabel('sentiment score')
        plt.legend()
        
        ax2 = plt.axis()
        plt.axis([ax2[0], ax2[1], 0, 1])
    
        plt.savefig('./deploy_graph/%s.png' % title.split('.txt')[0], dpi=80)
        plt.gcf().clear()
    
    return rmse_avg, cosine_avg

def deploy(import_model = '', image = True):
    if import_model:
        model = import_model
    else:
        model = load_model('lstm_model.h5')
    
    rmse_avg = 0
    cosine_avg = 0
    deploy_file_list = os.listdir('./deploy')
    for filename in deploy_file_list :
        x_deploy, y_deploy = make_deploy_data(filename)
        predictions = model.predict(x_deploy, batch_size=1, verbose=2)
        
        result = evaluation(filename, predictions, y_deploy, image=image)
        print(filename, result[0], result[1])
        
        rmse_avg += result[0]
        cosine_avg += result[1]
        
    rmse_avg /= len(deploy_file_list)
    cosine_avg /= len(deploy_file_list)
    
    print('Avg rmse:', rmse_avg, 'Avg Cos:', cosine_avg)