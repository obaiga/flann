#Copyright 2008-2009  Marius Muja (mariusm@cs.ubc.ca). All rights reserved.
#Copyright 2008-2009  David G. Lowe (lowe@cs.ubc.ca). All rights reserved.
#
#THE BSD LICENSE
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions
#are met:
#
#1. Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#2. Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#from ctypes import *  # TODO: * imports are bad and should be removed
import ctypes as C
from ctypes import c_char_p, c_int, c_float, c_uint, c_long, c_void_p, Structure, POINTER
#from ctypes.util import find_library
from numpy import float32, float64, uint8, int32
from numpy.ctypeslib import ndpointer
from os.path import join, exists, realpath, dirname, normpath
import sys

STRING = c_char_p

__DEBUG_CLIB__ = '--debug' in sys.argv or '--debug-clib' in sys.argv


class CustomStructure(Structure):
    """
        This class extends the functionality of the ctype's structure
        class by adding custom default values to the fields and a way of translating
        field types.
    """
    _defaults_ = {}
    _translation_ = {}

    def __init__(self):
        Structure.__init__(self)
        self.__field_names = [f for (f, t) in self._fields_]
        self.update(self._defaults_)

    def update(self, dict):
        for k, v in dict.items():
            if k in self.__field_names:
                setattr(self, k, self.__translate(k, v))

    def __getitem__(self, k):
        if k in self.__field_names:
            return self.__translate_back(k, getattr(self, k))

    def __setitem__(self, k, v):
        if k in self.__field_names:
            setattr(self, k, self.__translate(k, v))
        else:
            raise KeyError("No such member: " + k)

    def keys(self):
        return self.__field_names

    def __translate(self, k, v):
        if k in self._translation_:
            if v in self._translation_[k]:
                return self._translation_[k][v]
        return v

    def __translate_back(self, k, v):
        if k in self._translation_:
            for tk, tv in self._translation_[k].items():
                if tv == v:
                    return tk
        return v


class FLANNParameters(CustomStructure):
    _fields_ = [
        ('algorithm', c_int),
        ('checks', c_int),
        ('eps', c_float),
        ('sorted', c_int),
        ('max_neighbors', c_int),
        ('cores', c_int),
        ('trees', c_int),
        ('leaf_max_size', c_int),
        ('branching', c_int),
        ('iterations', c_int),
        ('centers_init', c_int),
        ('cb_index', c_float),
        ('target_precision', c_float),
        ('build_weight', c_float),
        ('memory_weight', c_float),
        ('sample_fraction', c_float),
        ('table_number_', c_uint),
        ('key_size_', c_uint),
        ('multi_probe_level_', c_uint),
        ('log_level', c_int),
        ('random_seed', c_long),
    ]
    _defaults_ = {
        'algorithm': 'kdtree',
        'checks': 32,
        'eps': 0.0,
        'sorted': 1,
        'max_neighbors': -1,
        'cores': 0,
        'trees': 1,
        'leaf_max_size': 4,
        'branching': 32,
        'iterations': 5,
        'centers_init': 'random',
        'cb_index': 0.5,
        'target_precision': 0.9,
        'build_weight': 0.01,
        'memory_weight': 0.0,
        'sample_fraction': 0.1,
        'table_number_': 12,
        'key_size_': 20,
        'multi_probe_level_': 2,
        'log_level': "warning",
        'random_seed': -1
    }
    _translation_ = {
        "algorithm": {"linear": 0, "kdtree": 1, "kmeans": 2, "composite": 3,
                      "kdtree_single": 4, "hierarchical": 5, "lsh": 6, "saved":
                      254, "autotuned": 255, "default": 1},
        "centers_init": {"random": 0, "gonzales": 1, "kmeanspp": 2, "default": 0},
        "log_level": {"none": 0, "fatal": 1, "error": 2, "warning": 3, "info": 4, "default": 2}
    }


default_flags = ['C_CONTIGUOUS', 'ALIGNED']
allowed_types = [ float32, float64, uint8, int32]

FLANN_INDEX = c_void_p


def get_lib_fname_list(libname):
    'returns possible library names given the platform'
    if sys.platform == 'win32':
        libnames = ['lib' + libname + '.dll', libname + '.dll']
    elif sys.platform == 'darwin':
        libnames = ['lib' + libname + '.dylib']
    elif sys.platform == 'linux2':
        libnames = ['lib' + libname + '.so']
    else:
        raise Exception('Unknown operating system: %s' % sys.platform)
    return libnames


def get_lib_dpath_list(root_dir):
    'returns possible lib locations'
    get_lib_dpath_list = [root_dir,
                          join(root_dir, 'lib'),
                          join(root_dir, 'build'),
                          join(root_dir, 'build', 'lib')]
    return get_lib_dpath_list


def find_lib_fpath(libname, root_dir, recurse_down=True):
    lib_fname_list = get_lib_fname_list(libname)
    tried_list = []
    count = 0
    while root_dir is not None:
        for lib_fname in lib_fname_list:
            for lib_dpath in get_lib_dpath_list(root_dir):
                lib_fpath = normpath(join(lib_dpath, lib_fname))
                lib_fpath = lib_fpath.replace('HOTSPO~1', 'hotspotter')
                #print('testing: %r' % lib_fpath)
                tried_list.append(lib_fpath)
                if exists(lib_fpath):
                    if __DEBUG_CLIB__:
                        print('using: %r' % lib_fpath)
                    return lib_fpath
        _new_root = dirname(root_dir)
        count += 1
        if count > 5:
            if '--quiet' not in sys.argv:
                print('not checking after 5 directories')
            root_dir = None
            break
        if _new_root == root_dir:
            root_dir = None
            break
        else:
            root_dir = _new_root
        if not recurse_down:
            break
    failed_paths = '\n * '.join(tried_list)
    raise ImportError('Cannot find dynamic library. Tried: %s' %
                      failed_paths)


def load_library2(libname, root_dir):
    lib_fpath = find_lib_fpath(libname, root_dir)
    try:
        clib = C.cdll[lib_fpath]
    except Exception as ex:
        print('Caught exception: %r' % ex)
        raise ImportError('Cannot load dynamic library. Did you compile FLANN?')
    return clib


def load_flann_library():
    try:
        root_dir = realpath(dirname(__file__))
    except NameError as ex:
        if '--quiet' not in sys.argv:
            print(ex)
        raise
    # root_dir = realpath(dirname(os.getcwd()))
    flannlib = load_library2('flann', root_dir)
    return flannlib


flannlib = load_flann_library()
if flannlib is None:
    raise ImportError('Cannot load dynamic library. Did you compile FLANN?')


class FlannLibInterface:
    pass
FLANN_INTERFACE = FlannLibInterface()


flannlib.flann_log_verbosity.restype = None
flannlib.flann_log_verbosity.argtypes = [
    c_int  # level
]

flannlib.flann_set_distance_type.restype = None
flannlib.flann_set_distance_type.argtypes = [
    c_int,
    c_int,
]

type_mappings = ( ('float',  'float32'),
                  ('double', 'float64'),
                  ('byte',   'uint8'),
                  ('int',    'int32') )


def define_functions(str):
    for type in type_mappings:
        eval(compile(str % {'C': type[0], 'numpy': type[1]}, "<string>", "exec"))

FLANN_INTERFACE.build_index = {}
define_functions(r"""
flannlib.flann_build_index_%(C)s.restype = FLANN_INDEX
flannlib.flann_build_index_%(C)s.argtypes = [
        ndpointer(%(numpy)s, ndim = 2, flags='aligned, c_contiguous'), # dataset
        c_int, # rows
        c_int, # cols
        POINTER(c_float), # speedup
        POINTER(FLANNParameters)  # flann_params
]
FLANN_INTERFACE.build_index[%(numpy)s] = flannlib.flann_build_index_%(C)s
""")

FLANN_INTERFACE.add_points = {}
define_functions(r"""
flannlib.flann_add_points_%(C)s.restype = None
flannlib.flann_add_points_%(C)s.argtypes = [
        FLANN_INDEX, # index_id
        ndpointer(%(numpy)s, ndim = 2, flags='aligned, c_contiguous'), # dataset
        c_int, # rows
        c_int, # cols
        c_int, # rebuild_threshhold
]
FLANN_INTERFACE.add_points[%(numpy)s] = flannlib.flann_add_points_%(C)s
""")


FLANN_INTERFACE.save_index = {}
define_functions(r"""
flannlib.flann_save_index_%(C)s.restype = None
flannlib.flann_save_index_%(C)s.argtypes = [
        FLANN_INDEX, # index_id
        c_char_p #filename
]
FLANN_INTERFACE.save_index[%(numpy)s] = flannlib.flann_save_index_%(C)s
""")

FLANN_INTERFACE.load_index = {}
define_functions(r"""
flannlib.flann_load_index_%(C)s.restype = FLANN_INDEX
flannlib.flann_load_index_%(C)s.argtypes = [
        c_char_p, #filename
        ndpointer(%(numpy)s, ndim = 2, flags='aligned, c_contiguous'), # dataset
        c_int, # rows
        c_int, # cols
]
FLANN_INTERFACE.load_index[%(numpy)s] = flannlib.flann_load_index_%(C)s
""")

FLANN_INTERFACE.find_nearest_neighbors = {}
define_functions(r"""
flannlib.flann_find_nearest_neighbors_%(C)s.restype = c_int
flannlib.flann_find_nearest_neighbors_%(C)s.argtypes = [
        ndpointer(%(numpy)s, ndim = 2, flags='aligned, c_contiguous'), # dataset
        c_int, # rows
        c_int, # cols
        ndpointer(%(numpy)s, ndim = 2, flags='aligned, c_contiguous'), # testset
        c_int,  # tcount
        ndpointer(int32, ndim = 2, flags='aligned, c_contiguous, writeable'), # result
        ndpointer(float32, ndim = 2, flags='aligned, c_contiguous, writeable'), # dists
        c_int, # nn
        POINTER(FLANNParameters)  # flann_params
]
FLANN_INTERFACE.find_nearest_neighbors[%(numpy)s] = flannlib.flann_find_nearest_neighbors_%(C)s
""")

# fix definition for the 'double' case

flannlib.flann_find_nearest_neighbors_double.restype = c_int
flannlib.flann_find_nearest_neighbors_double.argtypes = [
    ndpointer(float64, ndim=2, flags='aligned, c_contiguous'),  # dataset
    c_int,  # rows
    c_int,  # cols
    ndpointer(float64, ndim=2, flags='aligned, c_contiguous'),  # testset
    c_int,  # tcount
    ndpointer(int32, ndim=2, flags='aligned, c_contiguous, writeable'),  # result
    ndpointer(float64, ndim=2, flags='aligned, c_contiguous, writeable'),  # dists
    c_int,  # nn
    POINTER(FLANNParameters)  # flann_params
]
FLANN_INTERFACE.find_nearest_neighbors[float64] = flannlib.flann_find_nearest_neighbors_double


FLANN_INTERFACE.find_nearest_neighbors_index = {}
define_functions(r"""
flannlib.flann_find_nearest_neighbors_index_%(C)s.restype = c_int
flannlib.flann_find_nearest_neighbors_index_%(C)s.argtypes = [
        FLANN_INDEX, # index_id
        ndpointer(%(numpy)s, ndim = 2, flags='aligned, c_contiguous'), # testset
        c_int,  # tcount
        ndpointer(int32, ndim = 2, flags='aligned, c_contiguous, writeable'), # result
        ndpointer(float32, ndim = 2, flags='aligned, c_contiguous, writeable'), # dists
        c_int, # nn
        POINTER(FLANNParameters) # flann_params
]
FLANN_INTERFACE.find_nearest_neighbors_index[%(numpy)s] = flannlib.flann_find_nearest_neighbors_index_%(C)s
""")

flannlib.flann_find_nearest_neighbors_index_double.restype = c_int
flannlib.flann_find_nearest_neighbors_index_double.argtypes = [
    FLANN_INDEX,  # index_id
    ndpointer(float64, ndim=2, flags='aligned, c_contiguous'),  # testset
    c_int,  # tcount
    ndpointer(int32, ndim=2, flags='aligned, c_contiguous, writeable'),  # result
    ndpointer(float64, ndim=2, flags='aligned, c_contiguous, writeable'),  # dists
    c_int,  # nn
    POINTER(FLANNParameters)  # flann_params
]
FLANN_INTERFACE.find_nearest_neighbors_index[float64] = flannlib.flann_find_nearest_neighbors_index_double

FLANN_INTERFACE.radius_search = {}
define_functions(r"""
flannlib.flann_radius_search_%(C)s.restype = c_int
flannlib.flann_radius_search_%(C)s.argtypes = [
        FLANN_INDEX, # index_id
        ndpointer(%(numpy)s, ndim = 1, flags='aligned, c_contiguous'), # query
        ndpointer(int32, ndim = 1, flags='aligned, c_contiguous, writeable'), # indices
        ndpointer(float32, ndim = 1, flags='aligned, c_contiguous, writeable'), # dists
        c_int, # max_nn
        c_float, # radius
        POINTER(FLANNParameters) # flann_params
]
FLANN_INTERFACE.radius_search[%(numpy)s] = flannlib.flann_radius_search_%(C)s
""")

flannlib.flann_radius_search_double.restype = c_int
flannlib.flann_radius_search_double.argtypes = [
    FLANN_INDEX,  # index_id
    ndpointer(float64, ndim=1, flags='aligned, c_contiguous'),  # query
    ndpointer(int32, ndim=1, flags='aligned, c_contiguous, writeable'),  # indices
    ndpointer(float64, ndim=1, flags='aligned, c_contiguous, writeable'),  # dists
    c_int,    # max_nn
    c_float,  # radius
    POINTER(FLANNParameters)  # flann_params
]
FLANN_INTERFACE.radius_search[float64] = flannlib.flann_radius_search_double


FLANN_INTERFACE.compute_cluster_centers = {}
define_functions(r"""
flannlib.flann_compute_cluster_centers_%(C)s.restype = c_int
flannlib.flann_compute_cluster_centers_%(C)s.argtypes = [
        ndpointer(%(numpy)s, ndim = 2, flags='aligned, c_contiguous'), # dataset
        c_int,  # rows
        c_int,  # cols
        c_int,  # clusters
        ndpointer(float32, flags='aligned, c_contiguous, writeable'), # result
        POINTER(FLANNParameters)  # flann_params
]
FLANN_INTERFACE.compute_cluster_centers[%(numpy)s] = flannlib.flann_compute_cluster_centers_%(C)s
""")
# double is an exception
flannlib.flann_compute_cluster_centers_double.restype = c_int
flannlib.flann_compute_cluster_centers_double.argtypes = [
    ndpointer(float64, ndim=2, flags='aligned, c_contiguous'),  # dataset
    c_int,  # rows
    c_int,  # cols
    c_int,  # clusters
    ndpointer(float64, flags='aligned, c_contiguous, writeable'),  # result
    POINTER(FLANNParameters)  # flann_params
]
FLANN_INTERFACE.compute_cluster_centers[float64] = flannlib.flann_compute_cluster_centers_double


FLANN_INTERFACE.free_index = {}
define_functions(r"""
flannlib.flann_free_index_%(C)s.restype = None
flannlib.flann_free_index_%(C)s.argtypes = [
        FLANN_INDEX,  # index_id
        POINTER(FLANNParameters) # flann_params
]
FLANN_INTERFACE.free_index[%(numpy)s] = flannlib.flann_free_index_%(C)s
""")
