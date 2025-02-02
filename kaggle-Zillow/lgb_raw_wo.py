###XGB Finale - No Outliers
from sklearn import model_selection, preprocessing, ensemble
#import xgboost as xgb
import pandas as pd
import numpy as np
import datetime as dt
import gc
from sklearn.metrics import mean_absolute_error
from sklearn.externals import joblib
import lightgbm as lgb
	
train = joblib.load("../input/trainstat.pkl")

cols = [a for a in [y for y in [x for x in [a for a in train.columns if 'X' not in a] if 'countenc0' not in x] if 'meanshftenc0' not in y] if 'yrmonth' not in a]

cols = cols +['X4_Mon_logerror3std',
'X3_Mon_logerror6skew',
'X3_Mon_logerror3mean',
'X4_Mon_logerror3skew',
'X3_Mon_logerror3std',
'X1_Mon_logerror6skew',
'X1_Mon_logerror3std',
'X1_Mon_logerror3skew',
'X3_Mon_logerror3skew',
'X2_Mon_logerror3skew',
'X4_Mon_logerror6skew',
'X4_Mon_logerror6std',
'X4_Mon_logerror3mean',
'X1_Mon_logerror6mean']

x = train.yrmonth
train = train[cols]
y = joblib.load("../input/y.pkl")
#################################################
# Val Split
#################################################
#x = pd.read_csv('../input/train_2016_v2.csv')
#x["transactiondate"] = pd.to_datetime(x["transactiondate"])
#x["yrmonth"] = x["transactiondate"].apply(lambda x: x.strftime('%Y%m')).astype(int)  

y_logit = x
valindex = y_logit > pd.Period('2017-05')
trainindex = y_logit <= pd.Period('2017-05')
valid = train[valindex]
#train = train[trainindex]
yval = y[valindex]
#y = y[trainindex]
#################################################

lbound = -0.4#np.mean(y) - 3 * np.std(y)
ubound = 0.419#np.mean(y) + 3 * np.std(y)

test = joblib.load("../input/teststat.pkl")
test = test[cols]

#test = valid # remove

oobtest = np.zeros((test.shape[0],1))
oobval = np.zeros((train.shape[0],1))
valerr = []
cnt = 0
val_scores = []
cv_r2 = []
nfold = 5
nbag =1
gc.collect()
for i in [5]:
    for seed in [2017]:
        kf = model_selection.KFold(n_splits=nfold, shuffle=False, random_state=seed)
        for dev_index, val_index in kf.split(y): # explain for regression convert y to bins and use that for split
            dev_X, val_X = train.iloc[dev_index,:], train.iloc[val_index,:]
            dev_y, val_y = y[dev_index], y[val_index]
            #dev_X = dev_X[(dev_y > lbound) & (dev_y < ubound)]
            #dev_y = dev_y[(dev_y > lbound) & (dev_y < ubound)]
            #val_X2 = val_X[(val_y > lbound) & (val_y < ubound)]
            #val_y2 = val_y[(val_y > lbound) & (val_y < ubound)]
            print(dev_X.shape)  
            params = {
                'learning_rate': 0.03,
                'boosting' : 'gbdt',
                'num_leaves': 10,
                'num_iterations': 1000,
#                'threads': 2,
                'min_sum_hessian_in_leaf': 0.1,
                'max_depth' : 4,    
                'feature_fraction': .5,
                'min_data_in_leaf' : 4,
                'poission_max_delta_step' :0.7,
                'bagging_fraction' : 0.8,
                'min_gain_to_split' : 0,
                'scale_pos_weight' : 1.0,
                'lambda_l2' : 0.1,
                'lambda_l1' : 0.1,
                'huber_delta' :1.0,
                'bagging_freq' :1,
                'objective' : 'regression_l1',
                'seed': 2017,
                'categorical_feature' :0,
                'xgboost_dart_mode' : False,
                'drop_rate':0.1,
                'skip_drop':0.5,
                'max_drop':50,
                'top_rate':0.1,
                'other_rate':0.1,
                'max_bin':255,
                'min_data_in_bin':50,
                'bin_construct_sample_cnt':1000000,
                'two_round':False,
                'uniform_drop':False,
                'verbose':0
            }

            xgtrain = lgb.Dataset(dev_X, label=dev_y)
            xgval = lgb.Dataset(val_X, label=val_y)

            watchlist = [xgval] 
            model = lgb.train(params, xgtrain, 1000, watchlist) 
            preds = model.predict(val_X).reshape(-1,1)
            oobval[val_index,:] += preds
            cv_r2.append(mean_absolute_error(val_y, preds))    
            print(cv_r2, np.mean(cv_r2),"---", np.std(cv_r2))
            val_scores.append(mean_absolute_error(model.predict(valid), yval))
            print(val_scores, np.mean(val_scores),"---", np.std(val_scores))            
            predtst = model.predict(test).reshape(-1,1)
            oobtest += predtst
pred = oobtest / (nfold * nbag)
oobpred = oobval / nbag
joblib.dump(oobpred,'../input/train_lgb_raw_stat_withoutliers.pkl')
joblib.dump(pred,'../input/test_lgb_raw_stat_withoutliers.pkl')

