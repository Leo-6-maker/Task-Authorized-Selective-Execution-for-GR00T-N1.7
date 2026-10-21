"""CPU tests of installer scope guards, independent of any GPU runtime."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare_runtime',
    Path(__file__).resolve().parents[1] / 'scripts/prepare_runtime.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallSafetyTests(unittest.TestCase):
    def test_parent_and_equal_root_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            for value in [root, root.parent, root / '..' / 'other']:
                with self.assertRaises(ValueError):
                    module.contained(root, value)

    def test_unrecognized_upstream_script_is_not_executed(self):
        with self.assertRaises(ValueError):
            module.cpu_setup('rm -rf "$HOME/.libero"\n')


if __name__ == '__main__':
    unittest.main()
