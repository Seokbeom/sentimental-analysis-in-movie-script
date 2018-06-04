# -*- coding: utf-8 -*-
from keras.models import Sequential
from keras.layers import Dense, LSTM
from keras.callbacks import EarlyStopping

from hyperopt import Trials, STATUS_OK, tpe
from hyperas import optim
from hyperas.distributions import choice, uniform, conditional

import numpy as np

import codecs
import os
import shutil
import random

def classify_data():
    static = [0]*11
    training_cnt = 0
    test_cnt = 0
    
    file_list = os.listdir('./norm')
    random.shuffle(file_list)
    for filename in file_list:
        if filename:
            score = filename.split('_')[1][:-4]
            round_score = round(float(score))
            static[round_score] += 1
            
            if round_score >= 7 and training_cnt < 300:
                shutil.copyfile('./norm/'+filename, './training/'+filename)
                training_cnt += 1
            elif test_cnt < 50:
                shutil.copyfile('./norm/'+filename, './test/'+filename)
                test_cnt += 1
            else:
                shutil.copyfile('./norm/'+filename, './deploy/'+filename)

def make_data():
    x_train = []
    y_train = []
    x_test = []
    y_test = []

    def split(x):
        if x:
            return x.split(' ')

    # Training
    training_file_list = os.listdir('./training')
    for filename in training_file_list:
        with codecs.open('./training/'+filename, 'r') as f:
            scores = f.read()
        scores = scores.split('\n')[:-1]
        scores = list(map(split, scores))
        
        for idx in range(len(scores)-50):
            x_train.append(scores[idx:idx+50])
            y_train.append(scores[idx+50])
    # Test
    test_file_list = os.listdir('./test')
    for filename in test_file_list:
        with codecs.open('./test/'+filename, 'r') as f:
            scores = f.read()
        scores = scores.split('\n')[:-1]
        scores = list(map(split, scores))
        
        for idx in range(len(scores)-50):
            x_test.append(scores[idx:idx+50])
            y_test.append(scores[idx+50])
    
    x_train = np.array(x_train).reshape((len(x_train), 50, 2)).astype(np.float)
    y_train = np.array(y_train).reshape((len(y_train), 2)).astype(np.float)
    x_test = np.array(x_test).reshape((len(x_test), 50, 2)).astype(np.float)
    y_test = np.array(y_test).reshape((len(y_test), 2)).astype(np.float)
    
    return x_train, y_train, x_test, y_test
    
def create_lstm_model(x_train, y_train, x_test, y_test) :
    num_layer = conditional({{choice(['one', 'two'])}})
    lstm_units = {{choice([16, 32, 64, 128, 256])}}
    print('lstm',lstm_units)
    if num_layer == 'two':
        lstm2_units = {{choice([16, 32, 64, 128])}}
        if lstm2_units > lstm_units:
            lstm2_units = lstm_units
        print('lstm2',lstm2_units)
        
    dropout_rate = {{uniform(0, 1)}}
    recurrent_dropout_rate = {{uniform(0, 1)}}
    print('dropout',dropout_rate)
    print('recurrent_dropout',recurrent_dropout_rate)
    epochs = int({{uniform(1, 25)}})
    batch_size = {{choice([256, 512, 1024])}}
    optimizer = {{choice(['sgd','adam', 'rmsprop'])}}
    print('batch size', batch_size, optimizer)
    
    model = Sequential()
    model.add(LSTM(
            units = lstm_units,
            input_shape = (50, 2),
            dropout = dropout_rate,
            recurrent_dropout = recurrent_dropout_rate,
            return_sequences = (num_layer == 'two'))
    )

    if num_layer == 'two':
        model.add(LSTM(
            units = lstm2_units,
            input_shape = (50, lstm_units),
            dropout = dropout_rate,
            recurrent_dropout = recurrent_dropout_rate,
            return_sequences = False)
        )

    model.add(Dense(units = 2))

    model.compile(loss = 'mse',
                  optimizer = optimizer,
                  metrics=['mse'])
    early_stopping_monitor = EarlyStopping(patience=5, verbose=0)
    model.fit(x_train, y_train,
              epochs = epochs,
              batch_size = batch_size,
              validation_data=(x_test, y_test),
              callbacks = [early_stopping_monitor],
              verbose = 2)

    score, mse = model.evaluate(x_test, y_test, verbose = 2)
    print(score)
    if np.isnan(score):
        print('loss is nan')
        score = 100.0

    return {'loss': score, 'status': STATUS_OK, 'model': model}

def random_search():
    best_run, best_model = optim.minimize(model = create_lstm_model,
                                          data = make_data,
                                          algo = tpe.suggest,
                                          max_evals = 10,
                                          trials = Trials())

    X_train, Y_train, X_test, Y_test = make_data()
    print("Evalutation of best performing model:")
    print(best_model.evaluate(X_test, Y_test))
    print("Best performing model chosen hyper-parameters:")
    print(best_run)
    best_model.save('lstm_model.h5')
    
    return best_model