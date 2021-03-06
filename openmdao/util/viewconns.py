
import os
import sys
import json
from itertools import chain

from six import iteritems

from openmdao.core.problem import Problem
from openmdao.devtools.webview import webview

def view_connections(root, outfile='connections.html', show_browser=True):
    """
    Generates a self-contained html file containing a detailed connection
    viewer.  Optionally pops up a web browser to view the file.

    Args
    ----
    root : system or Problem
        The root for the desired tree.

    outfile : str, optional
        The name of the output html file.  Defaults to 'connections.html'.

    show_browser : bool, optional
        If True, pop up a browser to view the generated html file.
        Defaults to True.
    """
    # since people will be used to passing the Problem as the first arg to
    # the N2 diagram funct, allow them to pass a Problem here as well.
    if isinstance(root, Problem):
        system = root.root
    else:
        system = root

    connections = system._probdata.connections
    to_prom = system._sysdata.to_prom_name
    src2tgts = {}
    units = {n: m.get('units','') for n,m in chain(iteritems(system._unknowns_dict),
                                                   iteritems(system._params_dict))}

    sizes = {}
    for t, (s, idxs) in iteritems(connections):
        if idxs is not None:
            sizes[t] = len(idxs)
        else:
            sizes[t] = system._params_dict[t]['size']
        if s not in src2tgts:
            src2tgts[s] = [t]
        else:
            src2tgts[s].append(t)

    src_systems = set()
    tgt_systems = set()
    for s in src2tgts:
        parts = s.split('.')
        for i in range(len(parts)):
            src_systems.add('.'.join(parts[:i]))

    for t in connections:
        parts = t.split('.')
        for i in range(len(parts)):
            tgt_systems.add('.'.join(parts[:i]))

    # reverse sort so that "NO CONNECTION" shows up at the bottom
    src2tgts['NO CONNECTION'] = sorted([t for t in to_prom
                                    if t not in system._unknowns_dict and
                                       t not in connections], reverse=True)

    src_systems = [{'name':n} for n in sorted(src_systems)]
    src_systems.insert(1, {'name': "NO CONNECTION"})
    tgt_systems = [{'name':n} for n in sorted(tgt_systems)]
    tgt_systems.insert(1, {'name': "NO CONNECTION"})

    data = {
        'src2tgts': [(s,ts) for s,ts in sorted(iteritems(src2tgts), reverse=True)],
        'proms': to_prom,
        'units': units,
        'sizes': sizes,
        'src_systems': src_systems,
        'tgt_systems': tgt_systems,
        'noconn_srcs': sorted((n for n in system._unknowns_dict
                               if n not in src2tgts), reverse=True),
    }

    viewer = 'connect_table.html'

    code_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(code_dir, viewer), "r") as f:
        template = f.read()

    graphjson = json.dumps(data)

    with open(outfile, 'w') as f:
        s = template.replace("<connection_data>", graphjson)
        f.write(s)

    if show_browser:
        webview(outfile)
