"""Retained R017 external reset/predicted-actual checks, parameterized only.
No actions, scene construction, model inference or native imports.
"""
import json
from pathlib import Path
import numpy as np
from .contract import require
from e3.ledger import ROOTS

def check_block(R, REPO, block):
    """Read-only actual reset/physical-window checks; no protocol retuning."""
    cfg=json.loads((REPO/'configs/e3_run_config.proposed.json').read_text())
    def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
    def close_array(a,b,tolerance):
        x=np.asarray(a);y=np.asarray(b)
        return x.shape==y.shape and np.isfinite(x).all() and np.isfinite(y).all() and np.allclose(x,y,rtol=0,atol=tolerance)
    comparisons=[]
    for cell in block:
        f=R/'runs'/ROOTS[cell['epoch']]/cell['run_id'];result=json.loads((f/'result.json').read_text())
        require(result['settling_steps']==10 and result['egl_binding_check']=='MATCH' and
                result['egl_process_gpu_indices']==[1], 'actual reset/settling/EGL contract differs')
        parity=json.loads((f/'reset_parity.json').read_text())
        require(parity['state_unchanged'] is True and
                all(parity['latest_native_observation_equal'].values()),'native reset parity failed')
        ack=json.loads((f/'policy_reset.json').read_text())
        require(ack['seed']==cell['policy_seed'] and ack['scenario_id']==cell['scenario_id'],
                'actual policy reset seed/scenario differs')
        native_start=json.loads((R/'runs'/(cell['run_id']+'.exit.started.json')).read_text())
        p=Path('/proc')/str(native_start['child_pid'])
        if p.exists():
            fields=(p/'stat').read_text().rsplit(')',1)[1].split()
            require(fields[0] in ['Z','X'],'native episode process still alive')
        if cell['system']=='A0':
            require(not list(f.glob('prediction-*')) and not (f/'shadow_setup.json').exists(),
                    'A0 invoked future Shadow')
        if cell['system']!='G':continue
        b=next(c for c in block if c['condition']==cell['condition'] and c['system']=='B0')
        bf=R/'runs'/ROOTS[b['epoch']]/b['run_id']
        frames={x['step']:x for x in lines(bf/'physical_frames.jsonl')}
        own={x['step']:x for x in lines(f/'physical_frames.jsonl')}
        windows=0;compared=0
        for d in lines(f/'gate_decisions.jsonl'):
            pred=json.loads((f/f'prediction-{d["index"]:03d}.json').read_text());windows+=1
            for pf in pred['frames']:
                step=pf['step']
                # Actual B0 is comparable through the same checked candidate;
                # accepted controls are independently available in G itself.
                actual=own.get(step) if d['decision']=='ACCEPT' else frames.get(step)
                require(actual is not None,'predicted physical frame has no paired actual evidence')
                for key,tolerance in [('eef_pos',cfg['position_tolerance_m']),
                                      ('eef_quat',cfg['orientation_tolerance_rad']),
                                      ('gripper',cfg['gripper_tolerance_m'])]:
                    require(close_array(pf[key],actual[key],tolerance),
                            'prediction/main physical '+key+' mismatch')
                require(set(pf['objects'])==set(actual['objects']), 'prediction object set differs')
                for name in pf['objects']:
                    for key,tolerance in [('pos',cfg['position_tolerance_m']),
                                          ('quat',cfg['orientation_tolerance_rad'])]:
                        require(close_array(pf['objects'][name][key],actual['objects'][name][key],tolerance),
                                'prediction/main object pose mismatch')
                for key in ['left_contacts','right_contacts','official_success','control_input']:
                    require(pf[key]==actual[key],'prediction/main contact/control/success mismatch')
                compared+=1
        comparisons.append(dict(run_id=cell['run_id'],prediction_windows=windows,physical_frames_compared=compared))
    return dict(status='REAL_RESET_SETTLING_EGL_AND_PREDICTED_ACTUAL_FRAMES_CHECKED',comparisons=comparisons)

