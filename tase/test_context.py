"""TEST-only prediction envelope checks; the contact Gate and oracle are unchanged."""
import json
from .e2_context import E2Context
from .test_authorization import require


def validate_prediction_envelope(prediction, snapshot_hash, completed):
    """Only transport/termination identity; no oracle/fault answer is consulted."""
    count=prediction.get('steps')
    require(prediction.get('status')=='PASS' and type(count) is int and
            count==len(prediction.get('frames',[])) and 1<=count<=min(8,720-completed),
            'invalid TEST prediction count/status/cap')
    require(prediction.get('source_snapshot_hash')==prediction.get('restored_snapshot_hash')==snapshot_hash,
            'TEST prediction snapshot identity differs')
    require(type(prediction.get('terminated')) is bool and type(prediction.get('truncated')) is bool,
            'invalid TEST prediction terminal flags')
    require(count==min(8,720-completed) or prediction['terminated'], 'short TEST prediction is not terminal')
    require([f['step'] for f in prediction['frames']]==list(range(completed+1,completed+count+1)),
            'TEST prediction frame sequence differs')


class TestContext(E2Context):
    def check(self,index,prefix):
        decision=super().check(index,prefix)
        if self.cell['system']=='G':
            prediction=json.loads((self.folder/f'prediction-{index:03d}.json').read_text())
            guards=[json.loads(s) for s in (self.folder/'noninterference.jsonl').read_text().splitlines()]
            validate_prediction_envelope(prediction,guards[-1]['before_hash'],len(self.frames))
        return decision
