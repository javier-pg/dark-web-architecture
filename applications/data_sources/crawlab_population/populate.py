from crawlab import save_item
import pickle

# read pickles which are list of dictionaries
def read_pickle(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data

data = read_pickle('repositories.pkl')

for item in data:
    print(item)
    save_item(item)
