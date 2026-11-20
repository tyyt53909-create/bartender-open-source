"""Cross-document and authorization-boundary regressions found in external review."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from validate_plan import validate_catalog, validate_package, digest
from render_docs import render_all

class PlanRegressionTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'coordination/tasks.json').read_text())
        self.tasks={t['id']:t for t in self.data['tasks']}
    def rehash(self):
        for t in self.data['tasks']:
            t['task_spec_sha256']=digest({k:t[k] for k in self.data['task_spec_fields'] if k in t})
    def errors(self):self.rehash();return validate_catalog(self.data,ROOT)
    def test_current_catalog_valid(self):self.assertEqual(self.errors(),[])
    def test_missing_m0_is_detected_even_after_spec_rehash(self):
        self.tasks['APP-12']['execution_gates']=[]
        self.assertTrue(any('M0 baseline gate missing' in x for x in self.errors()))
    def test_validation_cannot_gain_production_write_scope(self):
        self.tasks['APP-22']['scope_paths'].append('Apps/MenuBarApp/UI/Settings/Permissions/')
        self.assertTrue(any('validation owns production source' in x for x in self.errors()))
    def test_permissions_ui_dependency_cannot_disappear(self):
        self.tasks['APP-22']['depends_on'].remove('APP-18')
        self.assertTrue(any('permissions/UI implementation missing' in x for x in self.errors()))
    def test_resource_list_cannot_override_expression(self):
        self.tasks['APP-18']['validation_compute_classes']=['macos_gui_exclusive']
        self.assertTrue(any('summary differs from expression' in x for x in self.errors()))
    def test_gate_reference_cycle_is_detected(self):
        self.data['gate_definitions']['at_least_one_runner_ready']={'kind':'gate_ref','gate_id':'automation_runtime_ready'}
        self.assertTrue(any('dependency cycle' in x for x in self.errors()))
    def test_m3_cannot_omit_original_authors(self):
        self.data['gate_policies']['M3_PRODUCT_GATE_PASSED']['required_subject_tasks'].remove('APP-18')
        self.assertTrue(any('subject-author binding policy missing' in x for x in self.errors()))
    def test_current_generated_documents_match(self):
        for path,content in render_all(ROOT).items():
            with self.subTest(path=path):self.assertEqual((ROOT/path).read_text(),content)
    def test_changed_task_propagates_to_all_required_views(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);(r/'coordination/document-templates').mkdir(parents=True)
            for name in ['roles.json','models.json','hosts.json']:
                (r/'coordination'/name).write_bytes((ROOT/'coordination'/name).read_bytes())
            for p in (ROOT/'coordination/document-templates').glob('*.md'):
                (r/'coordination/document-templates'/p.name).write_bytes(p.read_bytes())
            self.tasks['APP-12']['wave']='W3';(r/'coordination/tasks.json').write_text(json.dumps(self.data))
            changed=render_all(r);current=render_all(ROOT)
            for name in ['project-plan','task-book','coordination-board']:
                self.assertNotEqual(changed['docs/'+name+'.md'],current['docs/'+name+'.md'])
    def test_existing_scope_typo_is_detected(self):
        self.tasks['OPS-02']['scope_paths']=['coordination/models/']
        self.rehash();errors=validate_package(ROOT,self.data,check_docs=False)
        self.assertTrue(any('cannot write required existing source coordination/hosts.json' in x for x in errors))

if __name__=='__main__':unittest.main()
