import spacy
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer(language='english')

nlp = spacy.load('en_core_web_trf')

def preProcessing(data):
    labels = []
    for i in data:
        tmp = nlp(i.lower().replace('so that', '').strip())
        sen = ""
        for j in tmp:
            sen = sen + " " + j.lemma_
        labels.append(removeSignAtEndSent(sen))

    return labels

# End # 

def preProcessing2(data):
    labels = []
    for i in data:
        tmp = nlp(i.lower().replace('so that', '').replace('i want to', '').replace('i want', '').replace('i need', '').replace('i would like to', '').replace('i\'d like to', '').replace('i can', '').strip())
        sen = ""
        for j in tmp:
            sen = sen + " " + j.lemma_
        labels.append(removeSignAtEndSent(sen))

    return labels

# Apply Lemma and stemming
def preProcessing3(data):
    labels = []
    for i in data:
        tmp = i.lower().replace('so that', '').replace('i want to', '').replace('i want', '').replace('i need', '').replace('i would like to', '').replace('i\'d like to', '').replace('i can', '').strip()
        stemms = [stemmer.stem(token) for token in tmp.split()]
        tmp = nlp(' '.join(stemms))
        sen = ""
        for j in tmp:
            sen = sen + " " + j.lemma_
        labels.append(sen)

    return labels

def preProcessing4(data):
    labels = []
    for i in data:
        tmp = i.lower().replace('so that', '')
        stemms = [stemmer.stem(token) for token in tmp.split()]
        tmp = nlp(' '.join(stemms))
        sen = ""
        for j in tmp:
            sen = sen + " " + j.lemma_
        labels.append(sen.lower().strip())

    return labels


def preProcessing5(data):
    labels = []
    for i in data:
        tmp = i.lower().replace('so that', '').replace('i want to', '').replace('i want', '').replace('i need', '').replace('i would like to', '').replace('i\'d like to', '').replace('i can', '').strip()
        labels.append(tmp)

    return labels

def preProcessing6(data):
    labels = []
    for i in data:
        tmp = i.lower().replace('so that', '')
        # stemms = [stemmer.stem(token) for token in tmp.split()]
        tmp = nlp(tmp)
        sen = ""
        for j in tmp:
            sen = sen + " " + j.lemma_
        labels.append(sen.lower().strip())

    return labels
# Remove sign , . ; at the end of sentence
def removeSignAtEndSent(sent):
    
    sent = sent.strip()
    if len(sent) > 0:
        if sent[-1] == '.' or sent[-1] == ',' or sent[-1] == ';' : # Get the last character of String       
            return sent[:-1].strip() # Remove '.' ',' at the end of String
    return sent

# End # 

def separateUS(us):
    who = what = why = ""
    isWho = True
    isWhat = isWhy = False
    for j in nlp(us.lower()):
        if j.tag_ == 'PRP' and isWhy == False:
            isWhat = True
            isWho = False
            what = what + ' ' + j.lemma_
        elif j.tag_ == 'IN' and j.text == 'so':
            isWhy = True
            isWhat = False
        else:
            if isWho == True:
                who = who + ' ' + j.lemma_
            elif isWhat == True:
                what = what + ' ' + j.lemma_
            elif isWhy == True:
#                 print(isWhy, i)
                if (j.lemma_ == 'so' and j.tag_ == 'IN') or (j.lemma_ == 'that' and j.tag_ == 'IN'):
#                     print('so', j.lemma_, i)
                    continue
                else: 
#                     print(why)
                    why = why + ' ' + j.lemma_
    return who, what, why

# End # 

# separate User Story without applying Lemma and it also return US
def separateUSNoLemma(us):
    who = what = why = ""
    isWho = True
    isWhat = isWhy = False
    for j in nlp(us.lower()):
        if j.tag_ == 'PRP' and isWhy == False:
            isWhat = True
            isWho = False
            what = what + ' ' + j.text
        elif j.tag_ == 'IN' and j.text == 'so':
            isWhy = True
            isWhat = False
        else:
            if isWho == True:
                who = who + ' ' + j.text
            elif isWhat == True:
                what = what + ' ' + j.text
            elif isWhy == True:
#                 print(isWhy, i)
                if (j.text == 'so' and j.tag_ == 'IN') or (j.text == 'that' and j.tag_ == 'IN'):
#                     print('so', j.lemma_, i)
                    continue
                else: 
#                     print(why)
                    why = why + ' ' + j.text
    return who, what, why, us

def removeWho(us):
    what = ''
    isWhat = False
    for j in nlp(us.lower()):
        if j.tag_ == 'PRP':
            isWhat = True
            what = what + ' ' + j.lemma_
        elif j.tag_ == 'IN' and j.text == 'so':
            isWhat = False
        else:
            if isWhat == True:
                what = what + ' ' + j.lemma_
            
    return removeSignAtEndSent(what)

# End # 