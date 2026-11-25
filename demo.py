"""Generate a self-contained, offline browser view of actual algorithm outputs."""
import json
from pathlib import Path
from experiment import trace
from methods import METHODS

def build():
    scenarios = []
    for name,x,k in [('Six games',[28,14,20,17,12,16],5),('Equal scores',[18]*9,5),
                     ('One expensive update',[9,8,7,6,5,4,3,2,1,10],9)]:
        answers = [f(x,k) for f in METHODS]
        assert all(a==answers[0] for a in answers)
        modes=[]
        for keep in [False,True]:
            indices=[]
            metrics=list(trace(x,k,keep,indices))
            modes.append([dict(c=c,p=p,queue=q,maximum=v) for (c,p,_,v),q in zip(metrics,indices)])
        scenarios.append(dict(name=name,x=x,k=k,answers=answers[0],modes=modes))
    html = Path(__file__).with_name('viewer.template').read_text(encoding='utf-8')
    dest=Path(__file__).with_name('viewer.html')
    dest.write_text(html.replace('TRACE_DATA',json.dumps(scenarios)),encoding='utf-8')
    print('Open viewer.html to inspect the verified Python traces.')


if __name__=='__main__':
    build()
