"""Read-only E3 CPU manifest/ledger/statistical entry. Never launches native code."""
import argparse,json
from pathlib import Path
from .manifest import verify
from .ledger import audit,ROOTS
from .statistics import summarize

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['verify-manifest','audit']);p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--workspace',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();cells=json.loads((a.repo/'configs/e3_cells.proposed.json').read_text())['cells'];source=json.loads((a.repo/'configs/e3_sources.proposed.json').read_text());value=verify(cells,source)
    if a.operation=='audit':
        if a.workspace is None:p.error('audit requires explicit workspace')
        from .audit import original
        audits=[audit(a.workspace/'runs'/ROOTS[epoch],[c for c in cells if c['epoch']==epoch],lambda f,r:original(a.workspace,a.repo,f,r)) for epoch in ROOTS];value=dict(epochs=audits,statistics=summarize([row for x in audits for row in x['rows']],cells))
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

if __name__=='__main__':main()
