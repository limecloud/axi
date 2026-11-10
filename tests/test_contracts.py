"""覆盖会误导执行与恢复的合同负例，以及参考提供方的事务行为。"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from contracts import validate_document, validate_package  # noqa: E402

module = importlib.util.spec_from_file_location("review_provider", ROOT / "examples/review/provider.py")
provider_module = importlib.util.module_from_spec(module)
module.loader.exec_module(provider_module)
Provider = provider_module.Provider
EXAMPLES = ROOT / "content/examples/0.2.1"


def fixture(name):
    return json.loads((EXAMPLES / f"{name}.json").read_text())


class ContractTests(unittest.TestCase):
    def test_all_examples_and_references(self):
        self.assertEqual(validate_package(EXAMPLES), 9)

    def test_unknown_core_field_rejected(self):
        value = fixture("succeeded")
        value["statuz"] = "succeeded"
        with self.assertRaises(ValidationError):
            validate_document(value)

    def test_unknown_spec_version_rejected(self):
        value = fixture("succeeded")
        value["spec_version"] = "latest"
        with self.assertRaises(ValidationError):
            validate_document(value)

    def test_unknown_requires_recovery(self):
        for field in ("operation", "error"):
            value = fixture("unknown")
            value.pop(field)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_document(value)
        value = fixture("unknown")
        value["error"]["resolution"]["kind"] = "none"
        with self.assertRaises(ValidationError):
            validate_document(value)

    def test_write_cannot_remove_idempotency(self):
        value = fixture("review-action")
        value["idempotency"] = {"mode": "not_applicable"}
        with self.assertRaises(ValidationError):
            validate_document(value)

    def test_key_must_be_required_input(self):
        value = fixture("review-action")
        value["input_schema"]["required"].remove("operation_key")
        with self.assertRaises(ValueError):
            validate_document(value)

    def test_consistent_snapshot_requires_revision(self):
        value = fixture("page")
        value["snapshot"]["mode"] = "consistent"
        with self.assertRaises(ValidationError):
            validate_document(value)

    def test_empty_page_with_cursor_is_valid(self):
        validate_document(fixture("page"))

    def test_batch_rejects_duplicate_ids_false_success_and_scope_leak(self):
        original = fixture("batch")
        mutations = [
            lambda v: v["results"][1].update(item_id="one"),
            lambda v: v.update(status="succeeded"),
            lambda v: v["results"][1]["result"]["context"].update(scope_id="other"),
        ]
        for mutation in mutations:
            value = deepcopy(original)
            mutation(value)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_document(value)

    def test_namespaced_optional_extensions(self):
        value = fixture("succeeded")
        value["extensions"] = {"org.example/review": {"note": "data"}}
        validate_document(value)
        value["extensions"] = {"coreOverride": {}}
        with self.assertRaises(ValidationError):
            validate_document(value)

    def test_catalog_drift_and_path_escape_rejected(self):
        for target in ("../outside.json", "https://invalid.test/action.json", "review-action.json"):
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                for source in EXAMPLES.glob("*.json"):
                    (directory / source.name).write_text(source.read_text())
                catalog = fixture("catalog")
                catalog["capabilities"][0]["contract_ref"] = target
                catalog["capabilities"][0]["effect"] = "read"
                (directory / "catalog.json").write_text(json.dumps(catalog))
                with self.subTest(target=target), self.assertRaises(ValueError):
                    validate_package(directory)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "review.sqlite"
        self.provider = Provider(self.db)
        self.provider.initialize()
        self.value = fixture("review-input")

    def tearDown(self):
        self.provider.close()
        self.temp.cleanup()

    def count_operations(self):
        return self.provider.connection.execute("SELECT count(*) FROM operations").fetchone()[0]

    def test_success_quality_scope_and_digest_vector(self):
        result = self.provider.decide(self.value)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["context"]["revision"], 8)
        self.assertEqual(result["data"]["verification"]["content_quality"], "not_evaluated")
        self.assertEqual(result["operation"]["input_digest"], fixture("succeeded")["operation"]["input_digest"])

    def test_drop_response_recovers_persisted_original_after_restart(self):
        unknown = self.provider.decide(self.value, drop_response=True)
        self.assertEqual(unknown["status"], "unknown")
        self.provider.close()
        self.provider = Provider(self.db)
        recovered = self.provider.recover(self.value["operation_key"])
        self.assertEqual(recovered["operation"], unknown["operation"])
        self.assertEqual(recovered["status"], "succeeded")
        self.assertEqual(self.count_operations(), 1)

    def test_same_key_returns_same_receipt_before_cas(self):
        first = self.provider.decide(self.value)
        self.assertEqual(self.provider.decide(dict(reversed(list(self.value.items())))), first)
        self.assertEqual(self.provider.get()["context"]["revision"], 8)

    def test_same_key_different_input_rejected(self):
        first = self.provider.decide(self.value)
        changed = {**self.value, "decision": "request_changes", "comment": "补充条款"}
        self.assertEqual(self.provider.decide(changed)["error"]["code"], "idempotency_conflict")
        self.assertEqual(self.provider.recover(self.value["operation_key"]), first)

    def test_new_key_stale_revision_cannot_repeat_effect(self):
        self.provider.decide(self.value)
        result = self.provider.decide({**self.value, "operation_key": "review_contract_002"})
        self.assertEqual(result["error"]["code"], "revision_conflict")
        self.assertEqual(self.count_operations(), 1)

    def test_invalid_input_and_scope_never_write(self):
        for changed in ({"extra": True}, {"scope_id": "other"}, {"decision": "request_changes", "comment": "  "}):
            result = self.provider.decide({**self.value, **changed})
            self.assertEqual(result["error"]["code"], "invalid_input")
        self.assertEqual(self.count_operations(), 0)
        self.assertEqual(self.provider.get()["context"]["revision"], 7)

    def test_revocation_blocks_read_write_and_recovery(self):
        self.provider.decide(self.value)
        self.provider.can_read = False
        for result in (self.provider.get(), self.provider.decide(self.value), self.provider.recover(self.value["operation_key"])):
            self.assertEqual(result["error"]["code"], "forbidden")
            self.assertNotIn("operation", result)
            self.assertNotIn("data", result)

    def test_write_permission_does_not_follow_read_permission(self):
        self.provider.can_decide = False
        self.assertEqual(self.provider.get()["status"], "succeeded")
        self.assertEqual(self.provider.decide(self.value)["error"]["code"], "forbidden")

    def test_request_changes_persists_comment_and_recovers_it(self):
        value = {**self.value, "decision": "request_changes", "comment": "请补充交付日期"}
        result = self.provider.decide(value)
        self.assertEqual(result["data"]["document"]["comment"], value["comment"])
        self.assertEqual(self.provider.get()["data"]["comment"], value["comment"])
        self.assertEqual(self.provider.recover(value["operation_key"]), result)

    def test_expiry_does_not_allow_reexecution(self):
        self.provider.decide(self.value)
        created = self.provider.connection.execute("SELECT created FROM operations").fetchone()[0]
        self.provider.now = lambda: created + provider_module.RETENTION
        self.assertEqual(self.provider.recover(self.value["operation_key"])["error"]["code"], "operation_expired")
        self.assertEqual(self.provider.decide(self.value)["error"]["code"], "operation_expired")
        self.assertEqual(self.count_operations(), 1)

    def test_concurrent_same_key_has_one_effect(self):
        def submit(_):
            provider = Provider(self.db)
            try:
                return provider.decide(self.value)
            finally:
                provider.close()
        with ThreadPoolExecutor(max_workers=4) as pool:
            receipts = list(pool.map(submit, range(4)))
        self.assertTrue(all(receipt == receipts[0] for receipt in receipts))
        self.assertEqual(self.count_operations(), 1)
        self.assertEqual(self.provider.get()["context"]["revision"], 8)

    def test_transaction_failure_rolls_back_domain_change(self):
        self.provider.connection.execute("""CREATE TRIGGER reject_operation BEFORE INSERT ON operations
                                           BEGIN SELECT RAISE(ABORT, 'simulated persistence failure'); END""")
        with self.assertRaises(provider_module.sqlite3.IntegrityError):
            self.provider.decide(self.value)
        self.assertEqual(self.provider.get()["context"]["revision"], 7)
        self.assertEqual(self.count_operations(), 0)


class CLITests(unittest.TestCase):
    def test_quickstart_subprocesses_and_machine_output(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix = [sys.executable, str(ROOT / "examples/review/provider.py"), "--db", str(Path(temp) / "review.sqlite")]
            def run(arguments, code):
                result = subprocess.run([*prefix, *arguments], capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(result.stderr, "")
                value = json.loads(result.stdout)
                validate_document(value)
                return value
            self.assertEqual(run(["init"], 0)["context"]["revision"], 7)
            unknown = run(["decide", "--input", str(EXAMPLES / "review-input.json"), "--drop-response"], 3)
            self.assertEqual(unknown["status"], "unknown")
            recovered = run(["recover", "--key", "review_contract_001"], 0)
            self.assertEqual(recovered["operation"], unknown["operation"])
            self.assertEqual(run(["get"], 0)["context"]["revision"], 8)
            self.assertEqual(run(["decide", "--input", str(EXAMPLES / "review-input.json")], 0), recovered)


if __name__ == "__main__":
    unittest.main()
