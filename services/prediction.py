import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import nltk
nltk.download('punkt')  
nltk.download('stopwords')
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords



def predict(text, model):
    tfidf = pickle.load(open("tfidf.pickle", "rb"))
    ps = PorterStemmer()
    
    def preprocess_text_pred(list_text):
        for text in list_text:
            text = text.lower()
            text = nltk.word_tokenize(text)

            res=[]

            for i in text:
                if i.isalnum():
                    if i not in stopwords.words('english'):
                        res.append(ps.stem(i))
            
        return " ".join(res)


    def upperspec_count(x):
        count=0
        s='[@_!#$%^&*()<>?/\|}{~:]£'
        for i in x:
            if i.isupper() or i in s:
                count+=1
        return count
    email_pp = preprocess_text_pred([text])
    email_trans = tfidf.transform([email_pp]).toarray()
    upspec = upperspec_count(text)
    new_arr = np.append(email_trans[0], upspec)
    new_arr = new_arr.reshape(1, -1)

    pred = model.predict(new_arr)

    return pred[0]