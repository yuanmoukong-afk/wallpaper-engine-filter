"""Start/stop backup or merge a portable hidden-list export."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/companion'))

def main():
    from backup_control import ensure, stop, restore
    from backup_service import ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','stop','restore','replace','path'])
    parser.add_argument('file',type=Path,nargs='?')
    args=parser.parse_args()
    if args.action=='start':ensure();print('Backup running; Windows login startup enabled.')
    elif args.action=='stop':stop();print('Backup stopped; data retained.')
    elif args.action=='restore':restore(args.file or ROOT/'隐藏名单.json')
    elif args.action=='replace':
        if not args.file:parser.error('replace requires an explicit input file')
        restore(args.file,replace=True)
    else:print(ROOT)

if __name__=='__main__':main()
