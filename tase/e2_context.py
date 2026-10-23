"""E2 evidence and contact-only Gate around the unchanged native executor."""
import copy
import json
import pickle
import time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from .evidence import append_json, write_json, sha256
from .event_oracle import EventOracle
from .task_spec import TaskSpec
from .m2_native import sample
from .m2_context import jsonable
from .snapshot import capture, digest
from .shadow import Shadow
from .gate_features import contact_view, score_contacts


class E2Context:
    def __init__(self, raw, wrapped, client, folder, cell, cfg):
        self.raw=raw; self.wrapped=wrapped; self.client=client; self.folder=folder
        self.cell=cell; self.cfg=cfg; self.shadow=None; self.frames=[]
        self.spec=TaskSpec.from_native(raw, cell['task'])
        first=sample(raw,self.spec,0)
        self.oracle=EventOracle(self.spec,{n:o['pos'] for n,o in first['objects'].items()},
            cfg['oracle_lift_m'], cfg['oracle_sustain_control_steps'], cfg['oracle_relative_motion_tolerance_m'])
        self.contact_history={name:0 for name in self.spec.objects}
        self.policy_language='pick up the '+cell['policy_target'].replace('_',' ')+' and place it in the basket'
        if cell['policy_target']+'_1' not in self.spec.objects:
            raise ValueError('predeclared policy target not in actual scene')
        from libero.libero import benchmark
        suite=benchmark.get_benchmark_dict()['libero_object']()
        if self.policy_language.replace(' ','_') not in suite.get_task_names():
            raise ValueError('policy instruction is not an official Object instruction')
        write_json(folder/'task_spec.json',asdict(self.spec))
        write_json(folder/'e2_identity.json',{'cell':cell,'actual_policy_language':self.policy_language,
            'true_task_target':self.spec.target,'epoch':'E2','protocol_id':'TASE-002-v1.0',
            'baseline_positions':{n:o['pos'].tolist() for n,o in first['objects'].items()},
            'oracle_parameters':{k:cfg[k] for k in ['oracle_lift_m','oracle_sustain_control_steps','oracle_relative_motion_tolerance_m']}})

    def frame(self, action):
        value=sample(self.raw,self.spec,len(self.frames)+1)
        view=contact_view(value,self.spec.objects)
        for name in self.spec.objects:
            self.contact_history[name]=self.contact_history[name]+1 if view['left_contacts'][name] and view['right_contacts'][name] else 0
        value['oracle']=self.oracle.consume(value)
        value['control_input']=np.array(action,copy=True)
        self.frames.append(value)
        append_json(self.folder/'physical_frames.jsonl',jsonable(value))

    def capture(self):
        return capture(self.raw,self.wrapped,self.oracle,{'policy_control_steps':len(self.frames)})

    def check(self,index,prefix):
        begin=time.perf_counter();tick=begin; snapshot=self.capture(); snapshot_hash=digest(snapshot)
        path=self.folder/f'snapshot-{index:03d}.pkl'
        with path.open('xb') as f:pickle.dump(snapshot,f,protocol=5)
        append_json(self.folder/'snapshots.jsonl',{'decision':index,'completed_controls':len(self.frames),
            'snapshot_hash':snapshot_hash,'file_sha256':sha256(path),'contact_history':dict(self.contact_history),
            'classification':'ORIGINAL_E2_PRE_ACTION_SNAPSHOT','capture_seconds':time.perf_counter()-tick})
        if self.cell['system']=='B0':
            return {'decision':'ACCEPT','system':'B0','checked_controls':0,'reason':'NATIVE_BASELINE'}
        snapshot_seconds=time.perf_counter()-begin;tick=time.perf_counter()
        rng_before=self.client.call_endpoint('rng_digest',requires_input=False)
        rng_before_seconds=time.perf_counter()-tick
        setup_seconds=0.;prediction_seconds=0.;decision_seconds=0.;decision=None
        try:
            if self.shadow is None:
                tick=time.perf_counter()
                self.shadow=Shadow(self.cell['task'],self.cell['init_index'],vars(self.wrapped.contract),self.cell['environment_seed'])
                write_json(self.folder/'shadow_setup.json',self.shadow.setup)
                setup_seconds=time.perf_counter()-tick
            tick=time.perf_counter(); prediction=self.shadow.predict(snapshot,prefix)
            prediction_seconds=time.perf_counter()-tick
            with (self.folder/f'prediction-{index:03d}.pkl').open('xb') as f:pickle.dump(prediction,f,protocol=5)
            write_json(self.folder/f'prediction-{index:03d}.json',jsonable(prediction))
            if prediction['status']!='PASS' or not 1<=prediction['steps']<=8:
                raise ValueError('shadow error or invalid prefix length')
            if prediction['source_snapshot_hash']!=snapshot_hash or prediction['restored_snapshot_hash']!=snapshot_hash:
                raise ValueError('shadow roundtrip differs')
            expected=min(8,720-len(self.frames))
            if prediction['steps']!=expected and not prediction['terminated']:
                raise ValueError('shadow prefix ended without success')
            # Explicit projection: no oracle output, fault/condition/instruction or body pose reaches scorer.
            views=[contact_view(f,self.spec.objects) for f in prediction['frames']]
            tick=time.perf_counter()
            decision=score_contacts(views,list(self.spec.objects),self.spec.target,
                                    self.contact_history,len(self.frames),self.cfg['gate_k'])
            decision_seconds=time.perf_counter()-tick
            decision.update(prediction_seconds=prediction_seconds,decision_seconds=decision_seconds)
            append_json(self.folder/'gate_contact_views.jsonl',{'index':index,'views':views,
                'actual_contact_history':dict(self.contact_history),'trusted_target':self.spec.target})
            return decision
        finally:
            tick=time.perf_counter()
            after=digest(self.capture())
            rng_after=self.client.call_endpoint('rng_digest',requires_input=False)
            guard={'index':index,'before_hash':snapshot_hash,'after_hash':after,
                   'main_state_unchanged':snapshot_hash==after,'policy_rng_before':rng_before,
                   'policy_rng_after':rng_after,'policy_rng_unchanged':rng_before==rng_after,
                   'model_calls_from_shadow':0}
            append_json(self.folder/'noninterference.jsonl',guard)
            timing={'index':index,'snapshot_and_record_seconds':snapshot_seconds,
                'rng_before_seconds':rng_before_seconds,'worker_setup_and_record_seconds':setup_seconds,
                'prediction_seconds':prediction_seconds,'decision_seconds':decision_seconds,
                'final_guard_and_record_seconds':time.perf_counter()-tick,
                'total_monitor_before_execution_seconds':time.perf_counter()-begin,
                'scope':'INCLUDES_SNAPSHOT_WORKER_SETUP_PREDICTION_EVIDENCE_AND_GUARDS_EXCLUDES_THIS_TIMING_ROW_AND_MAIN_EXECUTION'}
            append_json(self.folder/'monitor_timing.jsonl',timing)
            if decision is not None:
                decision.update(total_monitor_before_execution_seconds=time.perf_counter()-begin,
                                worker_setup_seconds=setup_seconds)
            if after!=snapshot_hash or rng_before!=rng_after:
                raise RuntimeError('shadow modified main state or policy RNG')

    def close(self):
        if self.shadow is not None:self.shadow.close()
