"""Independent E3 stop latch around exact frozen native candidate handling."""
import numpy as np
from tase.execution_gate import candidate,execute_checked
from .discovery import require

class Boundary:
    def __init__(self,arm):
        require(arm in ['B0','A0','G'],'unknown E3 arm');self.arm=arm;self.stopped=False

    def execute(self,prefix,monitor,execute):
        require(not self.stopped,'E3 episode stopped; no retry/new action')
        def check(value):
            candidate({k:np.asarray(v)[None] for k,v in value.items()})
            score=monitor(value)
            if score.get('decision')=='ACCEPT' and self.arm=='G':
                require(type(score.get('checked_controls')) is int and 1<=score['checked_controls']<=8,'G checked prefix missing')
            return score
        try:decision,result=execute_checked(prefix,check,execute)
        except BaseException:
            self.stopped=True
            raise
        if decision['decision']!='ACCEPT':self.stopped=True
        return decision,result
