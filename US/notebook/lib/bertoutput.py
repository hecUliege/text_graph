import torch

def mean_pooling(output, attention_mask):
    token_embeddings = output['last_hidden_state']
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def mean_sqrt_len_pooling(output, attention_mask):
    token_embeddings = output['last_hidden_state']
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.sqrt(torch.clamp(input_mask_expanded.sum(1), min=1e-9))

def max_pooling(output, attention_mask):
    token_embeddings = output['last_hidden_state']
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    token_embeddings[input_mask_expanded == 0] = -1e9  # Set padding tokens to large negative value
    max_over_time = torch.max(token_embeddings, 1)[0]
#     return torch.cat(max_over_time, 1)
    return max_over_time

# Concatenate last 4 layers
def concatenateLast4Layers(output, attention_mask):
    o_mean = [mean_pooling(output.hidden_states[-x], attention_mask) for x in range(1,5)]
  #we want a tensor and not a list
    o_mean = torch.stack(o_mean, dim=1)
  #we want only one tensor per sequence
    return torch.mean(o_mean,dim=1)

def getCLSfromLastLayer(output):
    return output[0][:, 0, :]

def getCLSfromSecondLastLayer(output):
#     return return output[0][:, 1, :]
    return output.hidden_states[-2][:, 0]

def getPoolingOutput(output):
    return output['pooler_output']

# Concatenate last 4 cls's feature
def concatenateLast4CLS(output):
  #We only use the cls token (i.e. first token of the sequence)
  #id 101
    o_cls = [output.hidden_states[-x][:, 0] for x in range(1,5)]
  #we want a tensor and not a list
    o_cls = torch.stack(o_cls, dim=1)
  #we want only one tensor per sequence
    return torch.mean(o_cls, dim=1)