#!/usr/bin/env python
import argparse, sys
from dstream.ds_api import death_star
from pub_dbi        import pubdb_conn_info
from pub_util       import pub_logger

myparser = argparse.ArgumentParser(description='Refilling a run table (practically re-creating it...)')

myparser.add_argument('--name', dest='name', action='store',
                      default='TestRun', type=str,
                      help='Name of a run table to create/alter')

myparser.add_argument('--nruns', dest='nruns', action='store',
                      default=0, type=int,
                      help='Number of runs to fill')

myparser.add_argument('--nsubruns',dest='nsubruns',action='store',
                      default=0, type=int,
                      help='Number of sub-runs to fill')

args = myparser.parse_args()

logger = pub_logger.get_logger('death_star')
k=death_star( pubdb_conn_info.admin_info(),
              logger )

if not k.connect():
    sys.exit(1)

k.refill_death_star(args.name,args.nruns,args.nsubruns)

