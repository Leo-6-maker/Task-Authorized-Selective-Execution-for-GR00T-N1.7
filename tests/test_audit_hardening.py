"""SYNTHETIC CPU regression cases, including all four R002 mutations."""
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
import numpy as np
from audit_fixture import auditor, build, seal, write, REPO
from tase.retention import cleanup_resources, traced_control_step


class AuditHardeningTests(unittest.TestCase):
    def test_strict_delivery_rejects_unavailable_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'manifest.json'
            write(p,{'artifacts':[{'visibility':'private','storage':'runtime',
                'artifact_id':'synthetic-missing','bytes':1,'sha256':'0'*64}]})
            command=[sys.executable,str(REPO/'scripts/verify_delivery.py'),'--manifest',str(p)]
            result=subprocess.run(command,capture_output=True)
            self.assertEqual(result.returncode,0)
            self.assertIn(b'NOT_VERIFIED',result.stdout)
            strict=subprocess.run(command+['--require-private'],capture_output=True)
            self.assertNotEqual(strict.returncode,0)

    def test_valid_control(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);build(root)
            self.assertEqual(auditor.audit(root)['model_forwards'],1)

    def test_single_corruptions_rejected_after_rehash(self):
        mutations=['missing_wrist','empty_observation','empty_parity','missing_parity_key',
            'nonboolean_parity','empty_manifest','omitted_manifest_entry','duplicate_manifest',
            'wrong_dtype','wrong_shape','action_tampering','step_count','duplicate_decision',
            'missing_horizon','identity','language','receipt','server_count','manifest_escape']
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root=Path(temp);folder=build(root)
                if mutation in ['missing_wrist','empty_observation','wrong_dtype','wrong_shape']:
                    with np.load(folder/'observation-000.npz') as data:obs=dict(data)
                    if mutation=='missing_wrist':del obs['video.wrist_image']
                    if mutation=='empty_observation':obs={}
                    if mutation=='wrong_dtype':obs['state.x']=obs['state.x'].astype(np.float64)
                    if mutation=='wrong_shape':obs['state.x']=np.zeros((1,2,1),dtype=np.float32)
                    np.savez(folder/'observation-000.npz',**obs)
                if 'parity' in mutation:
                    p=folder/'reset_parity.json';d=json.loads(p.read_text());m=d['latest_native_observation_equal']
                    if mutation=='empty_parity':m.clear()
                    if mutation=='missing_parity_key':del m['video.wrist_image']
                    if mutation=='nonboolean_parity':m['video.wrist_image']=1
                    write(p,d)
                if mutation=='action_tampering':
                    with np.load(folder/'action-000.npz') as d:actions=dict(d)
                    actions['action.x'][0,0,0]=1;np.savez(folder/'action-000.npz',**actions)
                if mutation in ['step_count','identity','language']:
                    p=folder/'result.json';d=json.loads(p.read_text())
                    d[{'step_count':'inner_steps','identity':'repo_sha','language':'native_language'}[mutation]]=2 if mutation=='step_count' else 'invalid'
                    write(p,d)
                if mutation=='duplicate_decision':
                    p=folder/'decisions.jsonl';p.write_text(p.read_text()*2)
                if mutation=='missing_horizon':(folder/'horizon.json').unlink()
                if mutation=='receipt':write(root/'runs/synthetic-dev.exit.json',dict(exit_code=1,child_pid=1,child_returncode=1))
                if mutation=='server_count':
                    p=root/'runs/server-03/inference.jsonl';d=json.loads(p.read_text());d['request']=2;write(p,d)
                seal(root,folder)
                if mutation in ['empty_manifest','omitted_manifest_entry','duplicate_manifest','manifest_escape']:
                    p=folder/'artifact_manifest.json';d=json.loads(p.read_text())
                    if mutation=='empty_manifest':d=[]
                    if mutation=='omitted_manifest_entry':d.pop()
                    if mutation=='duplicate_manifest':d.append(d[0])
                    if mutation=='manifest_escape':d[0]['artifact_id']='../../escape'
                    write(p,d)
                with self.assertRaises((ValueError,KeyError,FileNotFoundError)):
                    auditor.audit(root)

    def test_partial_trace_and_cleanup_faults_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);states=[];actions=[]
            result=dict(inner_steps=0,status='RUNTIME_ERROR',exit_code=1)
            traced_control_step(lambda a:None,np.zeros(7),lambda:np.ones(2),folder,states,actions,result)
            def broken(action):raise RuntimeError('SYNTHETIC execution failure')
            with self.assertRaises(RuntimeError):
                traced_control_step(broken,np.ones(7),lambda:np.ones(2),folder,states,actions,result)
            def close():raise RuntimeError('SYNTHETIC cleanup failure')
            cleanup_resources(folder,result,[('client',close),('video',close)])
            write(folder/'result.json',result)
            with np.load(folder/'control_trace.npz') as trace:self.assertEqual(len(trace['states']),1)
            self.assertEqual(result['inner_steps'],1)
            self.assertEqual(result['status'],'RUNTIME_ERROR')
            self.assertEqual(result['cleanup_errors'],2)
            self.assertTrue((folder/'control_step_errors.jsonl').is_file())

    def test_cleanup_failure_changes_success_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            result=dict(status='SUCCESS',exit_code=0)
            def close():raise RuntimeError('SYNTHETIC cleanup')
            cleanup_resources(Path(temp),result,[('client',close)])
            self.assertEqual(result['exit_code'],1)
            self.assertEqual(result['status'],'CLEANUP_ERROR')
