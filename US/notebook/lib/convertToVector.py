from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer

def convertClassToNum(y):
    Encoder = LabelEncoder()
    return Encoder.fit_transform(y)

def convertSentToTFVec(fullX, train_x, test_x, maxFeatures=5000):
    Tfidf_vect = TfidfVectorizer(max_features=maxFeatures)
    Tfidf_vect.fit(fullX)
    return Tfidf_vect.transform(train_x), Tfidf_vect.transform(test_x)