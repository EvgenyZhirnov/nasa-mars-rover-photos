import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'deploy'))
import deploy as delivery


class DeliveryTests(unittest.TestCase):
    def test_rejects_archive_that_can_replace_another_service_image(self):
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as file:
            payload = json.dumps([{'RepoTags': ['postgres:latest']}]).encode()
            with tarfile.open(file.name, 'w:gz') as archive:
                info = tarfile.TarInfo('manifest.json')
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            with self.assertRaises(ValueError):
                delivery.validate_manifest(file.name, 'nasarover-release:' + 'a' * 40)

    def test_failed_release_restores_previous_image_and_preserves_state(self):
        old, new = 'a' * 40, 'b' * 40
        with tempfile.TemporaryDirectory() as root:
            location = Path(root) / 'preview'
            location.mkdir()
            state = {'revision': old, 'image': 'nasarover-release:' + old}
            (location / 'state.json').write_text(json.dumps(state))
            metadata = [{'Config': {'Labels': {'org.opencontainers.image.revision': new}}}]
            with patch.object(delivery, 'ROOT', Path(root)), \
                 patch.object(delivery, 'validate_manifest'), \
                 patch.object(delivery.subprocess, 'check_output', return_value=json.dumps(metadata)), \
                 patch.object(delivery.subprocess, 'run') as run, \
                 patch.object(delivery, 'check', side_effect=[RuntimeError('bad release'), None]) as check:
                with self.assertRaises(RuntimeError):
                    delivery.deploy('preview', new, io.BytesIO(b'image'))
                self.assertEqual(run.call_args.kwargs['env']['APP_IMAGE'], state['image'])
                self.assertEqual(check.call_args.args[1], old)
            self.assertEqual(json.loads((location / 'state.json').read_text()), state)

    def test_target_and_revision_cannot_be_shell_commands_or_paths(self):
        for target, revision in [('other', 'a' * 40), ('preview', '../main'), ('production', 'a' * 40 + ';id')]:
            with self.assertRaises(ValueError):
                delivery.deploy(target, revision, io.BytesIO())
