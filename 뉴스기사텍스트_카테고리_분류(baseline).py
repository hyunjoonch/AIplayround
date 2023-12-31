# -*- coding: utf-8 -*-
"""뉴스기사텍스트_카테고리_분류(Baseline).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PDr2SEOHkuMVva2q95qGp3HjB1SRVREg
"""

pip install konlpy --quiet

"""## Text Classification"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import tensorflow as tf
import re
import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Conv1D
from tensorflow.keras.layers import MaxPooling1D
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Embedding
from tensorflow.keras.utils import to_categorical

"""## 뉴스기사 텍스트 카테고리 분류"""

from google.colab import drive
drive.mount('/content/drive', force_remount=True)

DATA_DIR = "/content/drive/MyDrive/ai/뉴스기사텍스트 카테고리분류"

tf.random.set_seed(7)

def preprocess(text, okt, remove_stopwords=True, stop_words=[]):
    text = re.sub("[^가-힣ㄱ-ㅎㅏ-ㅣ\\s]", "", text)
    text_words = okt.morphs(text, stem=True)
    if remove_stopwords:
        text_words = [token for token in text_words if not token in stop_words]
    return ' '.join(text_words)

from konlpy.tag import Okt

okt=Okt()

stop_words=set(['이다','되다','이제','이에','지난','우리','은','는','이','가','을','를','께','에','하다','있다','것','들','째','의','와','있','되','데','등','한'
,'따르다','으로', '에서', '로', '과', '도', '일', '적', '수', '인', '년','돼다', '전', '하고', '않다', '없다', '말', '받다', '까지'])

from tqdm import tqdm
tqdm.pandas()

train_clean_path = os.path.join(DATA_DIR, 'train_clean.csv')
if os.path.exists(train_clean_path):
    train_clean = pd.read_csv(train_clean_path)
else:
    train = pd.read_csv(os.path.join(DATA_DIR, 'train.csv'))
    train_clean = pd.DataFrame({'text': [], 'category': []})
    train_clean['text'] = train.text.progress_apply(lambda text: preprocess(text, okt, stop_words=stop_words))
    train_clean['category'] = train.category
    train_clean.to_csv(train_clean_path, index=False)
train_clean.head()

label_encoder = LabelEncoder()
train_clean['label'] = label_encoder.fit_transform(train_clean.category)
train_clean.label

num_labels = len(np.unique(train_clean.label))
num_labels

train, valid = train_test_split(train_clean, test_size=0.2, stratify=train_clean.label, random_state=47)

VOCAB_SIZE = 5000
vectorizer = tf.keras.layers.TextVectorization(max_tokens=VOCAB_SIZE)
vectorizer.adapt(train.text.values)

vocab = np.array(vectorizer.get_vocabulary())
vocab[:20]

model = tf.keras.Sequential([
    vectorizer,
    tf.keras.layers.Embedding(
        input_dim=len(vectorizer.get_vocabulary()),
        output_dim=64,
        # Use masking to handle the variable sequence lengths
        mask_zero=True),
    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64, return_sequences=True)),
    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(32)),
    tf.keras.layers.Flatten(input_shape=(56,56)),
    tf.keras.layers.Dense(64),
    tf.keras.layers.Dense(128),
    tf.keras.layers.Dense(256),
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.Dense(num_labels, activation='softmax')
])

model.compile(optimizer='adam',
    loss="sparse_categorical_crossentropy",
    metrics=['accuracy']
)

early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=7, restore_best_weights=True)

model.fit(train.text.values, train.label, validation_data=(valid.text.values, valid.label),
          epochs=100, batch_size=64, callbacks=[early_stop])

test_clean_path = os.path.join(DATA_DIR, 'test_clean.csv')
if os.path.exists(test_clean_path):
    test_clean = pd.read_csv(test_clean_path)
else:
    test = pd.read_csv(os.path.join(DATA_DIR, 'test.csv'))
    test_clean = pd.DataFrame({'ID': [], 'text': []})
    test_clean['ID'] = test.ID
    test_clean['text'] = test.text.progress_apply(lambda text: preprocess(text, okt, stop_words=stop_words))
    test_clean.to_csv(test_clean_path, index=False)
test_clean.head()

y_pred = label_encoder.inverse_transform(
    [np.argmax(cls) for cls in model.predict(test_clean.text.values)])
y_pred

pd.DataFrame({'text': test_clean.text, 'category': y_pred})

submission = pd.DataFrame({'ID': test_clean.ID, 'category': y_pred})
submission.head(10)

submission.to_csv(os.path.join(DATA_DIR, 'submission.csv'), index=False)

