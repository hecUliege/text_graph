import torch
import torch.nn as nn

class BERT_Arch(nn.Module):
    
    def __init__(self, bert, numClassOutput, isFreezeBert=True):
        """
        @param    bert: a BertModel object
        
        @param    freeze_bert (bool): Set `False` to fine-tune the BERT model
        """
        super(BERT_Arch, self).__init__()

        self.bert = bert 

        # dropout layer
        self.dropout = nn.Dropout(0.1)

        # relu activation function
        self.relu =  nn.ReLU()

        # self.bert = BertModel.from_pretrained(BERT_MODEL_NAME, return_dict=True)
        # self.classifier = nn.Linear(self.bert.config.hidden_size, n_classes)
        # self.bert = BertForSequenceClassification.from_pretrained(BERT_MODEL_NAME, num_labels=YOUR_NUM_OF_CLASSES)

        # dense layer 1
        self.fc1 = nn.Linear(768,512) # bert-base 768  ; bert-large 1024

        # dense layer 2 (Output layer)
        self.fc2 = nn.Linear(512,numClassOutput)

        #softmax activation function
        self.softmax = nn.LogSoftmax(dim=1)
        
        if isFreezeBert:
            # freeze all the parameters
            for param in bert.parameters():
                param.requires_grad = False

    #define the forward pass
    def forward(self, sent_id, mask):

        #pass the inputs to the model  
        _, cls_hs = self.bert(sent_id, attention_mask=mask, return_dict=False)
#         print('test',cls_hs)
        x = self.fc1(cls_hs)
#         print(x)
        x = self.relu(x)

        x = self.dropout(x)

        # output layer
        x = self.fc2(x)

        # apply softmax activation
        x = self.softmax(x)

        return x