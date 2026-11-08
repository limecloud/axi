"""本地审批参考提供方；模拟身份，不作为生产认证或网络服务。"""

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from contracts import validate_business, validate_document  # noqa: E402


ACTION_PATH = ROOT / "content/examples/0.2.0/review-action.json"
ACTION = json.loads(ACTION_PATH.read_text())
RETENTION = ACTION["idempotency"]["retention_seconds"]


def input_digest(value):
    # 本例输入只有字符串与整数：UTF-8、键排序、无空格，不声称实现通用 JCS。
    fixed = {key: item for key, item in value.items() if key != "operation_key"}
    encoded = json.dumps(fixed, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


class Provider:
    def __init__(self, path, *, can_read=True, can_decide=True, now=time.time):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, isolation_level=None)
        self.can_read = can_read
        self.can_decide = can_decide
        self.now = now
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                scope_id TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL,
                state TEXT NOT NULL, comment TEXT NOT NULL, PRIMARY KEY(scope_id, id)
            );
            CREATE TABLE IF NOT EXISTS operations (
                scope_id TEXT NOT NULL, action TEXT NOT NULL, key TEXT NOT NULL,
                digest TEXT NOT NULL, receipt TEXT NOT NULL, created REAL NOT NULL,
                PRIMARY KEY(scope_id, action, key)
            );
        """)

    def close(self):
        self.connection.close()

    def initialize(self):
        self.connection.execute("INSERT OR IGNORE INTO documents VALUES (?, ?, ?, ?, ?)",
                                ("scope_demo", "doc_contract_001", 7, "pending", ""))
        return self.get()

    @staticmethod
    def result(action, status, *, data=None, error=None, operation=None, revision=None, resource=True):
        context = {"scope_id": "scope_demo"}
        if resource:
            context["resource_id"] = "doc_contract_001"
        if revision is not None:
            context["revision"] = revision
        result = {"spec_version": "0.2.0", "kind": "result", "action": action,
                  "contract_revision": "1", "status": status, "context": context}
        if data is not None:
            result["data"] = data
        if error is not None:
            result["error"] = error
        if operation is not None:
            result["operation"] = operation
        validate_document(result)
        return result

    def blocked(self, action, code, message, kind="none", next_action=None):
        resolution = {"kind": kind}
        if next_action:
            resolution["action"] = next_action
        return self.result(action, "blocked", error={"code": code, "message": message, "resolution": resolution}, resource=False)

    def get(self):
        if not self.can_read:
            return self.blocked("documents.get", "forbidden", "当前身份无读取权限")
        row = self.connection.execute("SELECT revision, state, comment FROM documents WHERE scope_id=? AND id=?",
                                      ("scope_demo", "doc_contract_001")).fetchone()
        if not row:
            return self.blocked("documents.get", "not_found", "示例文档不存在，请先 init")
        return self.result("documents.get", "succeeded", revision=row[0], data={"review_state": row[1], "comment": row[2]})

    def decide(self, value, *, drop_response=False):
        from jsonschema import ValidationError
        try:
            validate_business(value, ACTION["input_schema"], ACTION_PATH)
        except ValidationError:
            return self.blocked("documents.decide", "invalid_input", "审批输入不符合合同", "correct_input")
        if not self.can_read or not self.can_decide:
            return self.blocked("documents.decide", "forbidden", "当前身份无审批权限")
        digest = input_digest(value)
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            if not self.can_read or not self.can_decide:
                result = self.blocked("documents.decide", "forbidden", "当前身份无审批权限")
            else:
                result = self._decide_in_transaction(value, digest)
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise
        if drop_response and result["status"] == "succeeded":
            return self.result("documents.decide", "unknown", operation=result["operation"],
                               error={"code": "result_unknown", "message": "提交应答未到达；请核对原操作",
                                      "resolution": {"kind": "recover", "action": "operations.get"}})
        return result

    def _decide_in_transaction(self, value, digest):
        key = value["operation_key"]
        old = self.connection.execute("SELECT digest, receipt, created FROM operations WHERE scope_id=? AND action=? AND key=?",
                                      ("scope_demo", "documents.decide", key)).fetchone()
        if old:
            if self.now() - old[2] >= RETENTION:
                return self.blocked("documents.decide", "operation_expired", "原操作超过保证恢复期，需人工核对", "request_decision")
            if old[0] != digest:
                return self.blocked("documents.decide", "idempotency_conflict", "同键输入与原操作不同", "correct_input")
            return json.loads(old[1])
        row = self.connection.execute("SELECT revision FROM documents WHERE scope_id=? AND id=?",
                                      (value["scope_id"], value["document_id"])).fetchone()
        if not row:
            return self.blocked("documents.decide", "not_found", "当前范围内没有该文档")
        if row[0] != value["expected_revision"]:
            return self.blocked("documents.decide", "revision_conflict", "文档修订已改变，需核对差异", "read", "documents.get")
        revision = row[0] + 1
        state = "approved" if value["decision"] == "approve" else "changes_requested"
        comment = value.get("comment", "")
        operation = {"id": "op_" + uuid.uuid4().hex, "key": key, "input_digest": digest, "recover_action": "operations.get"}
        result = self.result("documents.decide", "succeeded", revision=revision, operation=operation,
                             data={"document": {"id": value["document_id"], "revision": revision, "review_state": state, "comment": comment},
                                   "verification": {"decision_recorded": True, "content_quality": "not_evaluated"}})
        self.connection.execute("UPDATE documents SET revision=?, state=?, comment=? WHERE scope_id=? AND id=?",
                                (revision, state, comment, value["scope_id"], value["document_id"]))
        self.connection.execute("INSERT INTO operations VALUES (?, ?, ?, ?, ?, ?)",
                                ("scope_demo", "documents.decide", key, digest, json.dumps(result, ensure_ascii=False), self.now()))
        return result

    def recover(self, key):
        if not self.can_read:
            return self.blocked("operations.get", "forbidden", "当前身份无读取权限")
        row = self.connection.execute("SELECT receipt, created FROM operations WHERE scope_id=? AND action=? AND key=?",
                                      ("scope_demo", "documents.decide", key)).fetchone()
        if not row:
            return self.blocked("operations.get", "not_found", "当前范围未找到原操作；不得由此推断外部副作用未发生")
        if self.now() - row[1] >= RETENTION:
            return self.blocked("operations.get", "operation_expired", "原操作超过保证恢复期，需人工核对", "request_decision")
        # 恢复返回原动作回执，避免把审批成功误称为新执行了一次。
        return json.loads(row[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    commands.add_parser("get")
    decide = commands.add_parser("decide")
    decide.add_argument("--input", type=Path, required=True)
    decide.add_argument("--drop-response", action="store_true")
    recover = commands.add_parser("recover")
    recover.add_argument("--key", required=True)
    args = parser.parse_args()
    provider = Provider(args.db)
    try:
        if args.command == "init":
            result = provider.initialize()
        elif args.command == "get":
            result = provider.get()
        elif args.command == "decide":
            result = provider.decide(json.loads(args.input.read_text()), drop_response=args.drop_response)
        else:
            result = provider.recover(args.key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return {"succeeded": 0, "blocked": 2, "unknown": 3}.get(result["status"], 1)
    finally:
        provider.close()


if __name__ == "__main__":
    sys.exit(main())
