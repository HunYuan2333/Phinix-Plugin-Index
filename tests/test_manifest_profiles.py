import copy
import unittest
import bot
import manifest_profiles as profiles
import source_updates as updates
from test_source_updates import configured,next_candidate

def dual(manifest):
    first=copy.deepcopy(manifest);second=copy.deepcopy(manifest)
    for value,game,tfm in [(first,'1.6','net472'),(second,'1.7','net10.0')]:
        value['targetFramework']=tfm
        value['compatibility']['rimWorldVersions']=[game]
        value['compatibility']['abstractionsRange']='>=3.0.0 <4.0.0'
    return dict(schemaVersion=2,variants=[first,second])

class ManifestProfileTests(unittest.TestCase):
    def test_envelope_identity_version_and_language_prefix(self):
        m=configured()[0]['package']['manifest'];envelope=dual(m)
        self.assertEqual(profiles.product_version(envelope),m['version'])
        self.assertEqual(profiles.resource_prefix(envelope),'1.6/')
        self.assertEqual(profiles.scope(envelope),profiles.scope(dict(schemaVersion=2,variants=list(reversed(envelope['variants'])))))

    def test_duplicate_runtime_wrong_tfm_identity_and_bool_schema_rejected(self):
        m=dual(configured()[0]['package']['manifest'])
        for change in [lambda v:v['variants'][1]['compatibility'].update(rimWorldVersions=['1.6']),
                       lambda v:v['variants'][1].update(targetFramework='net472'),
                       lambda v:v['variants'][1].update(packageId='different'),
                       lambda v:v['variants'][1].update(schemaVersion=True)]:
            bad=copy.deepcopy(m);change(bad)
            with self.assertRaises(ValueError):profiles.variants(bad)

    def test_first_expansion_requires_readmission_then_patch_updates_allowed(self):
        base,_,_,policy=configured();candidate=next_candidate(base)
        candidate['package']['manifest']=dual(candidate['package']['manifest'])
        with self.assertRaises(bot.Rejected):updates.permitted(policy,base,candidate)
        base['package']['manifest']=dual(base['package']['manifest'])
        updates.permitted(policy,base,candidate)
        candidate['package']['manifest']['variants'][1]['compatibility']['abstractionsRange']='>=3.1.0 <4.0.0'
        with self.assertRaises(bot.Rejected):updates.permitted(policy,base,candidate)
