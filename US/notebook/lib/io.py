def saveUSToExcel(userStories, whos, whats, whys, directory, filename):
    data = ({"UserStory": userStories ,
             "Who": whos,
             "What": whats,
             "Why": whys})
    # Create a Pandas DataFrame out of a Python dictionary
    df = pd.DataFrame.from_dict(data)
    # look at the Data
    df.head()
    
    df.to_excel(directory + filename + ".xlsx") 

# End #