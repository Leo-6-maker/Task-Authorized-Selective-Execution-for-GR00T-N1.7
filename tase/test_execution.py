"""TEST lifecycle guard around the unchanged checked-prefix executor."""
from .execution_gate import candidate,execute_checked
from .test_authorization import require


class TestBoundary:
    def __init__(self, system):
        require(system in ['B0','G'], 'unknown TEST system')
        self.system=system
        self.stopped=False

    def execute(self, prefix, monitor, execute):
        require(not self.stopped, 'TEST episode stopped; no new prediction or execution')
        def checked(value):
            # Validate the same16-step raw candidate and never recode the gripper here.
            import numpy as np
            candidate({key:np.asarray(arr)[None] for key,arr in value.items()})
            score=monitor(value)
            if score.get('decision')=='ACCEPT' and self.system=='G':
                require(type(score.get('checked_controls')) is int and 1<=score['checked_controls']<=8,
                        'invalid checked TEST prediction prefix')
            return score
        decision,result=execute_checked(prefix,checked,execute)
        if decision['decision']!='ACCEPT':
            self.stopped=True
        return decision,result
