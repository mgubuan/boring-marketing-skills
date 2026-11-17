import copy
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).parents[1] / 'scripts/validate_packet.py'
spec = importlib.util.spec_from_file_location('validate_packet', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PacketTest(unittest.TestCase):
    def setUp(self):
        self.row = dict(id='synthetic', company='Example', domain='example.invalid',
            status='qualified_for_draft', relationship='non_client', duplicate='clear',
            excluded=False, ai_team='no_evidence_found', ai_team_sources=[],
            draft_state='pending_review', research_complete=True,
            sources=['https://example.invalid/contact'], fit_hypothesis='Synthetic fit',
            contact=dict(route='email', value='example@example.invalid', verification='official_source'),
            checked_at='2026-11-17')
    def test_complete(self): self.assertEqual(module.validate(self.row), [])
    def test_blocks_each_gate(self):
        for field, value in [('relationship','unknown'), ('relationship','client'),
            ('duplicate','duplicate'), ('duplicate','unchecked'), ('excluded',True),
            ('ai_team','unknown'), ('ai_team','confirmed_team'), ('ai_team','competing_provider'),
            ('draft_state','rejected'), ('research_complete',False), ('sources',[]),
            ('fit_hypothesis',''), ('checked_at','bad'), ('excluded','false')]:
            with self.subTest(field=field, value=value):
                row=copy.deepcopy(self.row);row[field]=value
                self.assertTrue(module.validate(row))
    def test_contact_holds(self):
        for contact in (None, {}, {'route':'form'}, dict(route='email',value='x',verification='guessed')):
            row=copy.deepcopy(self.row);row['contact']=contact
            self.assertTrue(module.validate(row))
    def test_evidenced_disqualification(self):
        self.row.update(status='disqualified', ai_team='confirmed_team', ai_team_sources=['https://example.invalid/team'])
        self.assertEqual(module.validate(self.row), [])
    def test_unknown_research_can_hold(self):
        self.row.update(status='hold', relationship='unknown',ai_team='unknown',research_complete=False)
        self.assertEqual(module.validate(self.row), [])
    def test_non_object(self): self.assertTrue(module.validate('not a record'))

if __name__ == '__main__': unittest.main()
