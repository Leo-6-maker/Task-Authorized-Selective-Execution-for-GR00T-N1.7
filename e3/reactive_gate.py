"""A0: strictly past observed bilateral contact, native chunk boundaries only."""
import copy
from tase.gate_features import contact_view
from .discovery import require,digest

class ReactiveGate:
    def __init__(self,spec,k=3):
        spec=copy.deepcopy(spec).validate()
        require(type(k) is int and k==3,'E3 A0 fixes k=3')
        self.names=tuple(spec.objects);self.target=spec.target;self.k=k
        self.counts={n:0 for n in self.names};self.step=0;self.failed=False
        self.spec_sha=digest(vars(spec))

    def observe(self,view):
        try:
            require(not self.failed,'reactive history permanently invalid')
            require(type(view) is dict and set(view)=={'step','left_contacts','right_contacts'},'A0 accepts contact-only actual history')
            value=contact_view(view,self.names)
            require(value['step']==self.step+1,'actual contacts missing/duplicate/reordered')
            self.counts={n:self.counts[n]+1 if value['left_contacts'][n] and value['right_contacts'][n] else 0 for n in self.names}
            self.step=value['step']
        except Exception:
            self.failed=True
            raise

    def decide(self,completed):
        require(not self.failed,'reactive history permanently invalid')
        require(type(completed) is int and completed==self.step and 0<=completed<720 and completed%8==0,'A0 only at next native8 boundary after complete actual history')
        triggers=[{'object':n,'actual_bilateral_count':self.counts[n]} for n in self.names if n!=self.target and self.counts[n]>=3]
        return {'decision':'REJECT' if triggers else 'ACCEPT','system':'A0','k':3,'triggers':triggers,'completed_controls':completed,'checked_controls':0,'future_shadow_calls':0,'scope':'PAST_ACTUAL_CONTACT_ONLY_NATIVE_CHUNK_BOUNDARY'}
