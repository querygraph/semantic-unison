"""Original metadata-only controls; no image/device or process operations."""
import copy,os,unittest
from unittest.mock import Mock,patch
from pathlib import Path
from final_volume_owner import cases,owned_attachment,sync_argv,persist_completed_command


class VolumeContract(unittest.TestCase):
    image=Path('/private/tmp/u-volume-original/fixture.dmg')
    mount=Path('/private/tmp/u-volume-original/mount')
    def info(self):
        return dict(images=[{'image-path':str(self.image),'owner-uid':os.getuid(),'system-entities':[
            {'mount-point':str(self.mount),'volume-kind':'hfs','dev-entry':'/dev/disk42s1'}]}])

    def test_all_twelve_cases_both_directions_and_modes(self):
        rows=cases()
        self.assertEqual(len(rows),12)
        self.assertEqual(len({tuple(r.values()) for r in rows}),12)
        self.assertEqual(sum(r['direction']=='apfs-to-hfs' for r in rows),6)
        self.assertEqual(sum(r['mode']=='generic-off' for r in rows),4)

    def test_only_exact_owned_image_mount_can_select_device(self):
        out=owned_attachment(self.info(),self.image,self.mount)
        self.assertEqual(out['dev-entry'],'/dev/disk42s1')
        for mutate in (
            lambda r:r['images'].clear(),
            lambda r:r['images'].append(copy.deepcopy(r['images'][0])),
            lambda r:r['images'][0].update({'image-path':'/private/tmp/foreign.dmg'}),
            lambda r:r['images'][0]['system-entities'][0].update({'mount-point':'/Volumes/Photo'}),
            lambda r:r['images'][0]['system-entities'][0].update({'volume-kind':'apfs'}),
            lambda r:r['images'][0]['system-entities'][0].update({'dev-entry':'/dev/disk42'}),
            lambda r:r['images'][0]['system-entities'].append(copy.deepcopy(r['images'][0]['system-entities'][0]))):
            info=self.info();mutate(info)
            with self.assertRaises(ValueError):owned_attachment(info,self.image,self.mount)

    def test_actual_image_info_schema_uses_hfs_content_hint(self):
        info=self.info();point=info['images'][0]['system-entities'][0]
        point.pop('volume-kind');point['content-hint']='48465300-0000-11AA-AA11-00306543ECAC'
        self.assertEqual(owned_attachment(info,self.image,self.mount)['dev-entry'],'/dev/disk42s1')
        point['content-hint']='APFS'
        with self.assertRaises(ValueError):owned_attachment(info,self.image,self.mount)
        point['volume-kind']='hfs';info['images'][0]['owner-uid']=os.getuid()+1
        with self.assertRaises(ValueError):owned_attachment(info,self.image,self.mount)

    def test_local_commands_reuse_qualified_endpoint_flags(self):
        for mode in ('generic-auto','generic-off','dng-auto'):
            argv=sync_argv('/private/tmp/unison','/private/tmp/a/source','/private/tmp/a/target',mode)
            self.assertNotIn('-semanticmaxthreads',argv)
            self.assertEqual(argv[argv.index('-semanticcpubudget')+1],'2')
            self.assertEqual(argv[argv.index('-maxthreads')+1],'2')
            self.assertEqual(argv[argv.index('-adobevalidate')+1],'off')
            self.assertEqual('-semanticdng' in argv,mode=='dng-auto')

    def test_failed_raw_command_is_saved_before_functional_rejection(self):
        store=Mock();out=dict(returncode=1)
        def reject(value,code):
            store.write.assert_called_once_with('failed-seed.json',out)
            self.assertIs(value,out);raise ValueError('original nonzero command')
        with patch('final_volume_owner.closed',side_effect=reject):
            with self.assertRaisesRegex(ValueError,'original nonzero'):persist_completed_command(store,'failed-seed',out)

    def test_native_debug_stderr_is_included_only_for_cli_observation(self):
        out=dict(stdout='ordinary stdout',stderr='Local receiver clone preserved 1966080 logical bytes')
        with patch('final_volume_owner.closed'):
            self.assertEqual(persist_completed_command(Mock(),'plist',out)[1],'ordinary stdout')
            self.assertIn('Local receiver clone preserved',persist_completed_command(Mock(),'update',out,combined=True)[1])


if __name__=='__main__':unittest.main()
