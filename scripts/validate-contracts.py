"""校验本仓库的版本化合同与独立示例，不发起网络请求。"""

import json
from datetime import datetime, timezone
import re

from jsonschema import Draft202012Validator
import yaml

from contracts import ROOT, SCHEMA, validate_package


def main():
    Draft202012Validator.check_schema(SCHEMA)
    count = validate_package(ROOT / "content/examples/0.2.0")
    skill = (ROOT / "examples/review/skills/document-review/SKILL.md").read_text()
    metadata = yaml.safe_load(skill.split("---", 2)[1])
    assert metadata["name"] == "document-review" and metadata["description"]
    catalog = json.loads((ROOT / "content/examples/0.2.0/catalog.json").read_text())
    actions = {entry["name"] for entry in catalog["capabilities"]}
    mentioned = set(re.findall(r"`([a-z]+\.[a-z_]+)`", skill))
    assert mentioned == actions, "方法引用与示例能力目录不一致"
    evidence = ROOT / ".dev"
    evidence.mkdir(exist_ok=True)
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "spec_version": "0.2.0",
        "status": "passed",
        "documents_validated": count,
        "skill_references": sorted(mentioned),
        "scope": "本仓库 Schema、业务输入样例、目录引用与回执一致性；不证明生产提供方行为",
    }
    (evidence / "contract-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
