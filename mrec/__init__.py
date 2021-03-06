import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.io import mmread
try:
    import cPickle as pickle
except ImportError:
    import pickle

from sparse import fast_sparse_matrix, loadtxt, loadz
from base_recommender import BaseRecommender

def load_fast_sparse_matrix(input_format,filepath):
    """
    Load a fast_sparse_matrix from an input file of the specified format,
    by delegating to the appropriate static method.

    Parameters
    ----------
    input_format : str
        Specifies the file format:
        - tsv
        - csv
        - mm  (MatrixMarket)
        - fsm (mrec.sparse.fast_sparse_matrix)
    filepath : str
        The file to load.
    """
    if input_format == 'tsv':
        return fast_sparse_matrix.loadtxt(filepath)
    elif input_format == 'csv':
        return fast_sparse_matrix.loadtxt(filepath,delimiter=',')
    elif input_format == 'mm':
        return fast_sparse_matrix.loadmm(filepath)
    elif input_format == 'fsm':
        return fast_sparse_matrix.load(filepath)
    raise ValueError('unknown input format: {0}'.format(input_format))

def load_sparse_matrix(input_format,filepath):
    """
    Load a scipy.sparse.csr_matrix from an input file of the specified format.

    Parameters
    ----------
    input_format : str
        Specifies the file format:
        - tsv
        - csv
        - mm  (MatrixMarket)
        - npz (scipy.sparse.csr_matrix serialized with mrec.sparse.savez())
        - fsm (mrec.sparse.fast_sparse_matrix)
    filepath : str
        The file to load.
    """
    if input_format == 'tsv':
        return loadtxt(filepath).tocsr()
    elif input_format == 'csv':
        return loadtxt(filepath,delimiter=',').tocsr()
    elif input_format == 'mm':
        return mmread(filepath).tocsr()
    elif input_format == 'npz':
        return loadz(filepath)
    elif input_format == 'fsm':
        return fast_sparse_matrix.load(filepath).X
    raise ValueError('unknown input format: {0}'.format(input_format))

def save_recommender(model,filepath):
    """
    Save a recommender model to file.  If the model holds similarity matrix
    then numpy.savez is used to save it to disk efficiently, otherwise the
    model is simply pickled.

    Parameters
    ----------
    filepath : str
        The filepath to write to.
    """
    if hasattr(model,'similarity_matrix'):
        # pickle the model without its similarity matrix
        tmp = model.similarity_matrix
        model.similarity_matrix = None
        m = pickle.dumps(model)
        # use numpy to save the similarity matrix efficiently
        model.similarity_matrix = tmp
        if isinstance(model.similarity_matrix,np.ndarray):
            np.savez(filepath,mat=model.similarity_matrix,model=m)
        elif isinstance(model.similarity_matrix,csr_matrix):
            d = model.similarity_matrix.tocoo(copy=False)
            np.savez(filepath,row=d.row,col=d.col,data=d.data,shape=d.shape,model=m)
        else:
            pickle.dump(model,open(filepath,'w'))
    else:
        pickle.dump(model,open(filepath,'w'))

def load_recommender(filepath):
    """
    Load a recommender model from file after it has been saved by
    save_recommender().

    Parameters
    ----------
    filepath : str
        The filepath to read from.
    """
    r = np.load(filepath)
    if isinstance(r,BaseRecommender):
        model = r
    else:
        model = np.loads(str(r['model']))
        if 'mat' in r.files:
            model.similarity_matrix = r['mat']
        elif 'row' in r.files:
            model.similarity_matrix = coo_matrix((r['data'],(r['row'],r['col'])),shape=r['shape']).tocsr()
        else:
            raise IOError('ERROR: unexpected serialization format.'
            'Was this file created with save_recommender()?')
    return model

def read_recommender_description(filepath):
    """
    Read a recommender model description from file after it has
    been saved by save_recommender(), without loading all the
    associated data into memory.

    Parameters
    ----------
    filepath : str
        The filepath to read from.
    """
    r = np.load(filepath,mmap_mode='r')
    if isinstance(r,BaseRecommender):
        model = r
    else:
        model = np.loads(str(r['model']))
    return str(model)
