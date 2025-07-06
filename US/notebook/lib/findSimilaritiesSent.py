def findMaxVec(sent, labels_embeddings):
    similarities = cosine_similarity(model.encode(sent), labels_embeddings)
    max_vector = max(similarities[0])
    # return array because similarites is 2D array
    max_index = np.argwhere(similarities == max_vector)
    return max_vector, max_index

# End #