"""AXI 草案的离线结构、引用及跨字段检查；不替代业务授权。"""

import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SCHEMA_PATH = CONTENT / "schemas/0.2.1/axi.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())


def retrieve_local(uri):
    parsed = urlsplit(uri)
    if parsed.scheme != "file" or parsed.netloc:
        raise NoSuchResource(ref=uri)
    path = Path(unquote(parsed.path)).resolve()
    if not path.is_relative_to(CONTENT) or not path.is_file():
        raise NoSuchResource(ref=uri)
    return Resource.from_contents(json.loads(path.read_text()))


REGISTRY = Registry(retrieve=retrieve_local).with_resources([
    (SCHEMA_PATH.as_uri(), Resource.from_contents(SCHEMA)),
    (SCHEMA["$id"], Resource.from_contents(SCHEMA)),
])
VALIDATOR = Draft202012Validator(SCHEMA, registry=REGISTRY)


def validate_document(document):
    VALIDATOR.validate(document)
    kind = document["kind"]
    if kind == "catalog":
        names = [entry["name"] for entry in document["capabilities"]]
        if len(names) != len(set(names)):
            raise ValueError("目录存在重复动作名")
    if kind == "action":
        for field in ("input_schema", "output_schema"):
            Draft202012Validator.check_schema(document[field])
        schema = document["input_schema"]
        properties = schema.get("properties", {})
        for name in document["required_context"]:
            if name not in properties or name not in schema.get("required", []):
                raise ValueError(f"必要上下文不在必填输入中：{name}")
        idem = document["idempotency"]
        if idem["mode"] == "required":
            key = idem["key_field"]
            if key not in properties or key not in schema.get("required", []):
                raise ValueError("幂等键不在必填输入中")
    if kind == "batch":
        items = document["results"]
        ids = [item["item_id"] for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("批量 item_id 不唯一")
        succeeded = all(item["result"]["status"] == "succeeded" for item in items)
        if (document["status"] == "succeeded") != succeeded:
            raise ValueError("批量整体状态与逐项状态不一致")
        if any(item["result"]["context"]["scope_id"] != document["context"]["scope_id"] for item in items):
            raise ValueError("批量不得混入其他范围")


def validate_business(value, schema, source_path):
    Draft202012Validator.check_schema(schema)
    based = {**schema, "$id": source_path.resolve().as_uri()}
    Draft202012Validator(based, registry=REGISTRY).validate(value)


def validate_package(directory):
    directory = directory.resolve()
    documents = {}
    for path in sorted(directory.glob("*.json")):
        value = json.loads(path.read_text())
        if "kind" in value:
            validate_document(value)
            documents[path] = value
    actions = {doc["name"]: (path, doc) for path, doc in documents.items() if doc["kind"] == "action"}
    # 先核对目录完整性，再解析业务输出；引用错误不应被后续读取掩盖。
    for path, document in documents.items():
        if document["kind"] == "catalog":
            for entry in document["capabilities"]:
                reference = urlsplit(entry["contract_ref"])
                if reference.scheme or reference.netloc or reference.query or reference.fragment:
                    raise ValueError("示例合同只接受包内相对引用")
                target = (path.parent / unquote(reference.path)).resolve()
                if not target.is_relative_to(directory) or target not in documents:
                    raise ValueError("合同引用越界或不存在")
                contract = documents[target]
                if contract["kind"] != "action":
                    raise ValueError("目录引用的不是动作合同")
                for field in ("name", "contract_revision", "effect", "required_context", "purpose"):
                    if entry[field] != contract[field]:
                        raise ValueError(f"目录和合同不同步：{field}")
    for path, document in documents.items():
        if document["kind"] == "action" and document["idempotency"]["mode"] == "required":
            recovery = actions.get(document["idempotency"]["recovery_action"])
            if not recovery or recovery[1]["effect"] != "read":
                raise ValueError("恢复动作不存在或不是只读")
        results = [document] if document["kind"] == "result" else [item["result"] for item in document["results"]] if document["kind"] == "batch" else []
        for result in results:
            if result["action"] not in actions:
                raise ValueError("示例结果引用未知动作")
            source, action = actions[result["action"]]
            if result["contract_revision"] != action["contract_revision"]:
                raise ValueError("结果合同修订不一致")
            validate_business(result, action["output_schema"], source)
            if action["effect"] in ("draft", "submit", "irreversible") and result["status"] != "blocked" and "operation" not in result:
                raise ValueError("写入结果缺少原操作引用")
            if "operation" in result:
                recovery = result["operation"]["recover_action"]
                if recovery not in actions or actions[recovery][1]["effect"] != "read":
                    raise ValueError("回执恢复动作不可解析")
    source, action = actions["documents.decide"]
    validate_business(json.loads((directory / "review-input.json").read_text()), action["input_schema"], source)
    return len(documents)
