import os
import pprint as pp
from distutils.dir_util import copy_tree
from mpi4py import MPI

# init mpi
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
hostname = MPI.Get_processor_name()

# all processes to print Hello World
print("Hello World ! main.py {}/{}@{}".format(rank, size, hostname))
