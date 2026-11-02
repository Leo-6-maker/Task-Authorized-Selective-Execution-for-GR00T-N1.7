"""Data-only second-location copier with bounded, offset-preserving transport.

Private config: transport_argv (strict SSH prefix), workspace, operator_directory,
local_backup_root. No host names, credentials, model or TEST operations here.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

from .contract import require
from .custody import verify_archive
from .processes import write


class Copier:
    def __init__(self, config, receipts):
        self.config = config
        self.receipts = Path(receipts)
        self.receipts.mkdir(mode=0o700)
        self.serial = 0
        self.transport = config['transport_argv']
        self.nested = config.get('nested_transport_argv', [])
        require(isinstance(self.transport, list) and self.transport and
                all(isinstance(s, str) for s in self.transport), 'explicit private SSH argv required')
        require('StrictHostKeyChecking=yes' in self.transport and
                'BatchMode=yes' in self.transport and
                not any('StrictHostKeyChecking=no' in s for s in self.transport),
                'strict noninteractive verified SSH required')
        if self.nested:
            require(self.nested[0] == 'ssh' and 'StrictHostKeyChecking=yes' in self.nested and
                    'BatchMode=yes' in self.nested and
                    not any('StrictHostKeyChecking=no' in s for s in self.nested),
                    'strict verified nested SSH required')

    def remote(self, code, destination=None):
        # Stream the program on stdin. Large complete evidence proofs must never
        # become one argv item (Linux MAX_ARG_STRLEN is often only128KiB).
        self.serial += 1
        label = 'transport-'+str(self.serial).zfill(5)
        remote_command = 'python3 -'
        if self.nested:
            remote_command = shlex.join(self.nested + [remote_command])
        command = self.transport + [remote_command]
        with (self.receipts/(label+'.stderr.private.txt')).open('x') as err:
            try:
                result = subprocess.run(command, input=code.encode(), stdout=destination or subprocess.PIPE,
                                        stderr=err, timeout=100)
            except subprocess.TimeoutExpired:
                write(self.receipts/(label+'.exit.json'), dict(actual_exit=None, timeout=True))
                raise
            except OSError as error:
                write(self.receipts/(label+'.exit.json'),
                      dict(actual_exit=None, child_created=False,
                           spawn_error=type(error).__name__, errno=error.errno))
                raise
        write(self.receipts/(label+'.exit.json'), dict(actual_exit=result.returncode))
        require(result.returncode == 0, 'read-only copy transport failed; partial bytes retained')
        return result.stdout

    def query(self):
        op = self.config['operator_directory']
        code = 'from pathlib import Path;import json\nop=Path('+repr(op)+')\n'
        code += "requests=[json.loads(p.read_text()) for p in sorted(op.glob('*.backup-request.json'))]\n"
        code += "f=op/'operator-terminal.json';print(json.dumps(dict(requests=requests,terminal=json.loads(f.read_text()) if f.exists() else None)))\n"
        return json.loads(self.remote(code))

    def copy(self, receipt):
        stage = receipt['stage']
        require(stage and all(c.isalnum() or c in '-_' for c in stage), 'unsafe archive stage')
        dest = Path(self.config['local_backup_root'])/stage
        dest.mkdir(mode=0o700, parents=True, exist_ok=True)
        require(not dest.is_symlink(), 'redirected backup stage refused')
        marker = dest/'primary-receipt.json'
        if marker.exists():
            require(json.loads(marker.read_text()) == receipt, 'source archive receipt conflict')
        else:
            write(marker, receipt)
        final, partial = dest/'evidence.tar.gz', dest/'evidence.tar.gz.pending'
        require(not final.is_symlink() and not partial.is_symlink(), 'redirected backup copy refused')
        remote_path = str(Path(self.config['workspace'])/'evidence_exports'/stage/'evidence.tar.gz')
        if not final.exists():
            with partial.open('ab') as out:
                failures = 0
                while out.tell() < receipt['bytes']:
                    offset = out.tell()
                    count = min(4*1024**2, receipt['bytes']-offset)
                    code = ('from pathlib import Path;import sys\nf=Path('+repr(remote_path)+
                            ").open('rb');f.seek("+str(offset)+
                            ');sys.stdout.buffer.write(f.read('+str(count)+'))')
                    try:
                        self.remote(code, out)
                        out.flush()
                        require(out.tell() == offset+count, 'short transfer; retain actual offset')
                        failures = 0
                    except (ValueError, subprocess.TimeoutExpired):
                        failures += 1
                        if failures >= 3:
                            raise
                        time.sleep([30, 120][failures-1])
        source = final if final.exists() else partial
        verify_archive(source, receipt)
        if not final.exists():
            partial.rename(final)
        proof = dict(status='TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_SHA256_VERIFIED',
                     stage=stage, original_files=receipt['original_files'],
                     primary_archive_sha256=receipt['sha256'], secondary_archive_sha256=receipt['sha256'],
                     archive_bytes=receipt['bytes'], actual_copied_artifacts=receipt['artifacts'],
                     verification_by='EXECUTOR_NOT_INDEPENDENT_SCIENTIFIC_REVIEWER')
        proof_path = dest/'second-copy-proof.json'
        if proof_path.exists():
            require(json.loads(proof_path.read_text()) == proof, 'existing second-copy proof conflict')
        else:
            write(proof_path, proof)
        # Primary recomputes whole hash after transfer, then exclusively records proof.
        code = 'from pathlib import Path;import json,hashlib\nproof='+repr(proof)+'\n'
        code += 'd=Path('+repr(str(Path(remote_path).parent))+')\n'
        code += "f=d/'evidence.tar.gz'\n"
        code += "with f.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()\n"
        code += "assert actual==proof['primary_archive_sha256'] and f.stat().st_size==proof['archive_bytes']\n"
        code += "p=d/'second-copy-proof.json'\nif p.exists():assert json.loads(p.read_text())==proof\nelse:p.open('x').write(json.dumps(proof,indent=2)+'\\n')\n"
        self.remote(code)
        return proof


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-config', type=Path, required=True)
    p.add_argument('--receipts', type=Path, required=True)
    a = p.parse_args()
    agent = Copier(json.loads(a.private_config.read_text()), a.receipts)
    handled = set()
    failures = 0
    while True:
        try:
            state = agent.query()
            failures = 0
        except (ValueError, subprocess.TimeoutExpired):
            failures += 1
            if failures >= 3:
                raise
            time.sleep([30, 120][failures-1])
            continue
        for request in state['requests']:
            stage = request['receipt']['stage']
            if stage not in handled:
                try:
                    agent.copy(request['receipt'])
                except BaseException as error:
                    record = dict(type=type(error).__name__, message=str(error),
                                  stage=stage, new_IDs_must_stop=True)
                    write(agent.receipts/'COPY_ERROR.json', record)
                    # No fake proof on error. Tell the operator to stop waiting,
                    # retaining exact originals, partial transfer and failures.
                    code = 'from pathlib import Path;import json\n'
                    code += 'p=Path('+repr(str(Path(agent.config['operator_directory'])/
                                               'BACKUP_INTEGRITY_ERROR.json'))+')\n'
                    code += 'if not p.exists():p.open("x").write('+repr(json.dumps(record))+')\n'
                    try:
                        agent.remote(code)
                    except Exception:
                        pass  # Bounded operator deadline remains the final stop.
                    raise
                handled.add(stage)
        if state['terminal'] is not None:
            write(agent.receipts/'remote-terminal-observed.json', state['terminal'])
            return
        time.sleep(20)


if __name__ == '__main__':
    main()
