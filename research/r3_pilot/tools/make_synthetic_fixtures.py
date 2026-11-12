"""Explicitly labelled artificial parser fixtures; no human records."""
from pathlib import Path
import sys,copy
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tests'));from fixture_factory import *
lock=A.load(P/'BUILD_LOCK.json');folder=P/'fixtures';folder.mkdir(exist_ok=True);base=lock['technical_identities'][0];paths=[]
paths.append(write_fixture(folder/'SYNTHETIC_VALID_TECHNICAL.json',record(base)))
partial=record(base,completed=5);partial['participant']['pseudonymous_id']='TEST-SYN0002';partial['session']['session_id']='S-1111111111111111';paths.append(write_fixture(folder/'SYNTHETIC_PARTIAL_TECHNICAL.json',partial))
d=record(base);d['experiment']['application_build_id']='0'*64;paths.append(write_fixture(folder/'SYNTHETIC_INCOMPATIBLE.json',d));bad=folder/'SYNTHETIC_CORRUPT.json';bad.write_text('{not valid JSON\n');paths.append(bad);catalog(paths,folder/'SYNTHETIC_CATALOG.json');print('Generated4SYNTHETICsoftware fixtures; no human observations.')
