# -*- coding: utf-8 -*-
"""Expediarmus.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QVz68r8d-wOnPP1zjfPgizATv1uup4uC

# 1. Imports
"""## Libraries"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import csv
import keras
import tensorflow
import pickle
import seaborn as sns

from sklearn import *
from sklearn import datasets
from sklearn import preprocessing

from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn.feature_selection import RFE

from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LassoCV

from sklearn.svm import SVR
from sklearn.svm import SVC
from sklearn.svm import LinearSVC

from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_validate
from sklearn.model_selection import GridSearchCV

from sklearn.multiclass import OneVsRestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import GradientBoostingClassifier

from sklearn.metrics import accuracy_score
from sklearn.metrics import make_scorer
from sklearn.datasets import dump_svmlight_file
import _io
import tempfile

"""## Get data from Kaggle
Directly downloads the data from the competition
"""

!pip install -U -q kaggle
!mkdir -p ~/.kaggle

"""Get your API code from Kaggle:
> 1. "My Account > Generate new API Token"
> 2. Download the .json file
> 3. Upload the file in the next cell
"""

from google.colab import files
files.upload()

!cp kaggle.json ~/.kaggle/

!kaggle competitions list

!kaggle competitions download -c vu-dmt-2assignment
!ls

"""# 2. Reading stuff

## Local files import
"""

tren = pd.read_csv('training_set_VU_DM.csv.zip', compression='zip')
test = pd.read_csv('test_set_VU_DM.csv.zip', compression='zip')

"""## Treating the data

### Correlation check
Generates image to see which features are correlated
"""

correlation = tren.corr()

plt.figure(figsize=(50, 50))
sns.heatmap(correlation, vmax = 1, annot = True, cmap='viridis')
plt.savefig('correlation_la_foto_del_antes.png')

#trento = tren.groupby(["srch_id"]).describe() #Esto tarda la vida

"""### Add up
Multiplies "compX_rate", "compX_rate_percent_diff" and "price_usd"
"""

trento = None
trento = tren

price = trento.columns.get_loc('price_usd') #15
init = trento.columns.get_loc('comp1_rate') #27
end = trento.columns.get_loc('comp8_rate_percent_diff') #50

while init <= end:
  trento.iloc[:,init] = trento.iloc[:,init] * trento.iloc[:,init + 2] * (trento.iloc[:,price]/100)
  trento = trento.drop(trento.columns[init + 2], axis = 1)
  
  init = init + 2
  end = end - 1

"""### Cleaning

Drops features with NaN values concentration greater than 75%...
"""

trento = trento.drop(trento.loc[:, trento.isnull().mean() > .75].columns, axis = 1)

"""... and check correlation again."""

correlation = trento.corr()
plt.figure(figsize=(50, 50))
sns.heatmap(correlation, vmax = 1, annot = True, cmap='viridis')
plt.savefig('correlation_post.png')

"""### Down-sampling bookings
Non-booked samples are 34 times more present than the booked ones.
"""

# Shuffle Dataset
chufchuf = trento.sample(frac = 1, random_state = 4)

# Select the undersampled
booking_1 = tren[tren['booking_bool'] == 1]

#Randomly select 200.000 observations from the non-booked (majority class)
booking_0 = chufchuf.loc[chufchuf['booking_bool'] == 0].sample(n = 200000, random_state = 42)

# Concatenate both dataframes again
trenfrom = pd.concat([booking_0, booking_1])

sns.countplot(x='prop_country_id',data=trenfrom, palette='hls')
plt.show();

"""### Creating the scores (y term)"""

tren['score'] = 0
tren.loc[tren.click_bool == 1, 'score'] = 1
tren.loc[tren.booking_bool == 1, 'score'] = 5

tren[['score', 'booking_bool', 'click_bool']]

"""# 4. Models"""

X_train, X_test, y_train, y_test = train_test_split(tren, tren['score'], test_size=0.1, random_state=np.random)

def get_ensemble_models():
    rf = RandomForestClassifier(n_estimators=51,min_samples_leaf=5,min_samples_split=3)
    bagg = BaggingClassifier(n_estimators=51,random_state=42)
    extra = ExtraTreesClassifier(n_estimators=51,random_state=42)
    ada = AdaBoostClassifier(n_estimators=51,random_state=42)
    grad = GradientBoostingClassifier(n_estimators=51,random_state=42)
    classifier_list = [rf,bagg,extra,ada,grad]
    classifier_name_list = ['Random Forests','Bagging','Extra Trees','AdaBoost','Gradient Boost']
    return classifier_list,classifier_name_list
    

    
classifier_list, classifier_name_list = get_ensemble_models()

for classifier,classifier_name in zip(classifier_list,classifier_name_list):
    classifier.fit(X_train,y_train)
    print_evaluation_metrics(classifier,classifier_name,X_test,y_test)

"""### Ada Boost"""

AdaBoostClassifier(n_estimators=51,random_state=42).fit(X_train, y_train)
print_evaluation_metrics(classifier,classifier_name,X_test,y_test)

"""### SVM Rank"""

#Generate the SVM file
train_data_file = tempfile.mktemp(suffix='.dat')
dump_svmlight_file(tren, tren['score'],train_data_file)

!tar -xvzf  svm_rank.tar.gz 
!pip install svmlight

def print_evaluation_metrics(trained_model,trained_model_name,X_test,y_test):
    print('--------- Model : ', trained_model_name, ' ---------------\n')
    predicted_values = trained_model.predict(X_test)
    print(metrics.classification_report(y_test,predicted_values))
    print("Accuracy Score : ",metrics.accuracy_score(y_test,predicted_values))
    print("---------------------------------------\n")

def train_model(model, prediction_function, X_train, y_train, X_test, y_test):
    model.fit(X_train, y_train)
    
    y_train_pred = prediction_function(model, X_train)
    print('train precision: ' + str(precision_score(y_train, y_train_pred)))
    print('train recall: ' + str(recall_score(y_train, y_train_pred)))
    print('train accuracy: ' + str(accuracy_score(y_train, y_train_pred)))
    y_test_pred = prediction_function(model, X_test)
    print('test precision: ' + str(precision_score(y_test, y_test_pred)))
    print('test recall: ' + str(recall_score(y_test, y_test_pred)))
    print('test accuracy: ' + str(accuracy_score(y_test, y_test_pred)))
    
    return model

