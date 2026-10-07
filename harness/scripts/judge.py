#!/usr/bin/env python3
"""허들링 하네스 판정 스크립트.

- 규칙은 harness/rules.json만 본다. 파이썬 표준 라이브러리만 쓴다.
- 같은 입력이면 항상 같은 결과를 낸다 (시각 등 바뀌는 값을 기록하지 않는다).

사용법:
  python3 harness/scripts/judge.py m1 runs/my-assets
  python3 harness/scripts/judge.py m2 runs/my-assets
  python3 harness/scripts/judge.py m3 runs/my-assets
  python3 harness/scripts/judge.py s5 runs/my-assets

결과는 runs/<id>/s5-verdict.json의 M1 / M2 / M3 / S5 키에 기록한다.
종료 코드: 0 통과, 1 위반 있음, 2 입력 오류.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES = ROOT / "harness" / "rules.json"
VERDICT_FILE = "s5-verdict.json"
STAGES = {
    "m1": ("M1", "s1-brief.md"),
    "m2": ("M2", "s2-references.md"),
    "m3": ("M3", "s3-keyscreens.snapshot.json"),
    "s5": ("S5", "s4-screen.snapshot.json"),
}
S5_RULES = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "A1", "A2", "B1", "B2", "B3"]


def violation(rule_id, detail, frame=None, node=None):
    out = {"id": rule_id, "detail": detail}
    if frame is not None:
        out["frame"] = frame
    if node is not None:
        out["node"] = node
    return out


# ---------- 문서 판정 (M1, M2) ----------

def parse_sections(text, prefix):
    """prefix로 시작하는 제목 아래 본문을 (제목, 본문) 목록으로 나눈다."""
    sections, name, body = [], None, []
    for line in text.splitlines():
        if line.startswith(prefix):
            if name is not None:
                sections.append((name, "\n".join(body)))
            name, body = line[len(prefix):].strip(), []
        elif name is not None:
            body.append(line)
    if name is not None:
        sections.append((name, "\n".join(body)))
    return sections


def judge_m1(text, rules):
    r = rules["M1"]
    sections = dict(parse_sections(text, "## "))
    out = []
    for name in r["sections"]:
        if not sections.get(name, "").strip():
            out.append(violation("M1", f"섹션이 없거나 비어 있음: {name}"))
    if not re.search(r["story_ref_pattern"], sections.get(r["story_section"], "")):
        out.append(violation("M1", "유저스토리 섹션에 유효한 번호(US-1~US-5)가 없음"))
    return out


def judge_m2(text, rules):
    r = rules["M2"]
    refs = parse_sections(text, "### ")
    out = []
    if not r["min"] <= len(refs) <= r["max"]:
        out.append(violation("M2", f"레퍼런스 {len(refs)}개 (허용 {r['min']}~{r['max']}개)"))
    for name, body in refs:
        fields = {}
        for line in body.splitlines():
            m = re.match(r"^\s*-\s*([^:]+):\s*(.*)$", line)
            if m:
                fields[m.group(1).strip()] = m.group(2).strip()
        for field in r["fields"]:
            if not fields.get(field):
                out.append(violation("M2", f"필드가 없거나 비어 있음: {field}", node=name))
    return out


# ---------- 스냅샷 판정 (M3, S5) ----------

def frame_size_violations(rule_id, frames, rules):
    w, h = rules["frame"]["width"], rules["frame"]["height"]
    return [
        violation(rule_id, f"프레임 크기 {f.get('width')}×{f.get('height')} (허용 {w}×{h})", frame=f.get("name"))
        for f in frames
        if (f.get("width"), f.get("height")) != (w, h)
    ]


def judge_m3(snap, rules):
    r = rules["M3"]
    frames = snap.get("frames", [])
    out = []
    if not r["min"] <= len(frames) <= r["max"]:
        out.append(violation("M3", f"키스크린 {len(frames)}개 (허용 {r['min']}~{r['max']}개)"))
    out += frame_size_violations("M3", frames, rules)
    return out


def applies(rule, screen_id):
    screens = rule.get("screens", "all")
    return screens == "all" or screen_id in screens


def solid_paints(node):
    for key in ("fills", "strokes"):
        for p in node.get(key) or []:
            if p.get("type") == "SOLID" and p.get("visible", True):
                yield key, p


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def check_d1(frame, node, rules):
    r = rules["D1"]
    allowed = {c.lower() for c in r["colors"]}
    exceptions = r["exceptions"].get(node.get("component"), [])
    bad = []
    for key, p in solid_paints(node):
        color, opacity = p["color"].lower(), round(p.get("opacity", 1), 2)
        if any(color == e["color"].lower() and opacity == e["opacity"] for e in exceptions):
            continue
        if color in allowed and opacity == r["opacity"]:
            continue
        bad.append(f"{key} {color} opacity {opacity}")
    return [violation("D1", "허용되지 않은 색: " + ", ".join(bad), frame, node.get("name"))] if bad else []


def uses_accent(node, accent):
    return any(p["color"].lower() == accent for _, p in solid_paints(node))


def check_d2_frame(frame, rules):
    r = rules["D2"]
    accent = r["accent"].lower()
    nodes = [n for n in frame.get("nodes", []) if uses_accent(n, accent)]
    out = []
    if len(nodes) > r["max_per_frame"]:
        out.append(violation("D2", f"파란색 사용 {len(nodes)}개 (허용 {r['max_per_frame']}개 이하)", frame.get("name")))
    for n in nodes:
        if n.get("component") in r["forbidden_components"]:
            out.append(violation("D2", f"{n.get('component')}에 파란색 사용", frame.get("name"), n.get("name")))
    return out


def check_d3(frame, node, rules):
    r = rules["D3"]
    radii = node.get("radii")
    if not radii:
        return []
    if node.get("component") == r["squircle_component"]:
        expected = r["squircle_ratio"] * min(node.get("width", 0), node.get("height", 0))
        bad = [x for x in radii if abs(x - expected) > r["squircle_tolerance"]]
        detail = f"스쿼클 모서리 {sorted(set(bad))} (기대 {round(expected, 2)})"
    else:
        bad = [x for x in radii if x not in r["radii"]]
        detail = f"허용되지 않은 모서리 {sorted(set(bad))}"
    return [violation("D3", detail, frame, node.get("name"))] if bad else []


def check_d4(frame, node, rules):
    r = rules["D4"]
    shadows = [e for e in node.get("effects") or [] if e.get("type") in r["shadow_types"] and e.get("visible", True)]
    if shadows and node.get("component") not in r["allowed_components"]:
        return [violation("D4", "그림자 사용: " + ", ".join(e["type"] for e in shadows), frame, node.get("name"))]
    return []


def check_d5(frame, node, rules):
    if node.get("type") != "TEXT":
        return []
    r = rules["D5"]
    reasons = []
    families = as_list(node.get("fontFamilies"))
    weights = as_list(node.get("fontWeights"))
    spacings = as_list(node.get("letterSpacings"))
    if any(f not in r["families"] for f in families):
        reasons.append(f"글꼴 {families}")
    if any(w not in r["weights"] for w in weights):
        reasons.append(f"굵기 {weights}")
    if any(s != r["letter_spacing"] for s in spacings):
        reasons.append(f"자간 {spacings}")
    style = node.get("textStyle") or ""
    if any(style.startswith(p) for p in r["heading_style_prefixes"]) and any(w != r["heading_weight"] for w in weights):
        reasons.append(f"제목 스타일 {style}의 굵기 {weights}")
    return [violation("D5", "; ".join(reasons), frame, node.get("name"))] if reasons else []


def check_d6(frame, node, rules):
    r = rules["D6"]
    bad = [f"{k} {node[k]}" for k in r["keys"] if k in node and node[k] not in r["spacing"]]
    return [violation("D6", "허용되지 않은 간격: " + ", ".join(bad), frame, node.get("name"))] if bad else []


def check_d7(frame, node, rules):
    r = rules["D7"]
    if node.get("component") not in r["components"]:
        return []
    state = (node.get("props") or {}).get("state")
    has_stroke = any(key == "strokes" for key, _ in solid_paints(node)) and (node.get("strokeWeight") or 0) > 0
    if state in r["rest_states"] and has_stroke:
        return [violation("D7", "평소 상태 입력칸에 테두리", frame, node.get("name"))]
    return []


def check_a1(screen_id, frame, rules):
    r = rules["A1"]
    if not applies(r, screen_id):
        return []
    return [
        violation("A1", f"공개 범위 기본값이 '{(n.get('props') or {}).get('default')}' (기대 '{r['default']}')", frame.get("name"), n.get("name"))
        for n in frame.get("nodes", [])
        if n.get("component") == r["component"] and (n.get("props") or {}).get("default") != r["default"]
    ]


def check_a2(screen_id, frame, rules):
    r = rules["A2"]
    if not applies(r, screen_id) or frame.get("role") in r["allowed_roles"]:
        return []
    return [
        violation("A2", f"'{frame.get('role')}' 화면에 판매 신청 선택지가 보임", frame.get("name"), n.get("name"))
        for n in frame.get("nodes", [])
        if n.get("component") == r["component"] and (n.get("props") or {}).get("value") == r["value"]
    ]


def checklist_ids(node):
    return {i.get("id") for i in (node.get("props") or {}).get("items", [])}


def check_b1(screen_id, frames, rules):
    r = rules["B1"]
    if not applies(r, screen_id):
        return []
    required = set(r["items"])
    checklists = [(f, n) for f in frames for n in f.get("nodes", []) if n.get("component") == r["component"]]
    if not checklists:
        return [violation("B1", "판매 기준 체크리스트가 화면에 없음")]
    out = []
    for f, n in checklists:
        missing = sorted(required - checklist_ids(n))
        if missing:
            out.append(violation("B1", f"체크리스트 항목 누락: {missing}", f.get("name"), n.get("name")))
    return out


def check_b2(screen_id, frame, rules):
    r = rules["B2"]
    if not applies(r, screen_id):
        return []
    required = len(rules["B1"]["items"])
    nodes = frame.get("nodes", [])
    checked = [
        sum(1 for i in (n.get("props") or {}).get("items", []) if i.get("checked"))
        for n in nodes
        if n.get("component") == r["checklist"]
    ]
    complete = bool(checked) and all(c >= required for c in checked)
    return [
        violation("B2", f"체크리스트 {min(checked) if checked else 0}/{required}인데 승인 버튼이 활성", frame.get("name"), n.get("name"))
        for n in nodes
        if n.get("component") == r["button"] and (n.get("props") or {}).get("enabled") and not complete
    ]


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PHONE_RE = re.compile(r"(?<!\d)01[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)")


def check_b3(screen_id, frame, node, rules):
    r = rules["B3"]
    if not applies(r, screen_id) or node.get("type") != "TEXT":
        return []
    text = node.get("characters") or ""
    out = []
    for m in EMAIL_RE.finditer(text):
        if m.group(1).lower() not in r["allowed_email_domains"]:
            out.append(violation("B3", f"실제 이메일 형식: {m.group(0)}", frame, node.get("name")))
    for m in PHONE_RE.finditer(text):
        normalized = re.sub(r"[. ]", "-", m.group(0))
        if normalized not in r["allowed_phones"]:
            out.append(violation("B3", f"실제 전화번호 형식: {m.group(0)}", frame, node.get("name")))
    return out


def judge_s5(snap, rules):
    screen_id = snap.get("screen_id")
    frames = snap.get("frames", [])
    out = frame_size_violations("D8", frames, rules)
    for f in frames:
        name = f.get("name")
        for n in f.get("nodes", []):
            for check in (check_d1, check_d3, check_d4, check_d5, check_d6, check_d7):
                out += check(name, n, rules)
            out += check_b3(screen_id, name, n, rules)
        out += check_d2_frame(f, rules)
        out += check_a1(screen_id, f, rules)
        out += check_a2(screen_id, f, rules)
        out += check_b2(screen_id, f, rules)
    out += check_b1(screen_id, frames, rules)
    order = {rid: i for i, rid in enumerate(S5_RULES)}
    return sorted(out, key=lambda v: order[v["id"]])


JUDGES = {"M1": judge_m1, "M2": judge_m2, "M3": judge_m3, "S5": judge_s5}


def run(key, path, rules):
    """판정 키(M1/M2/M3/S5)와 입력 파일로 위반 목록을 돌려준다."""
    text = Path(path).read_text(encoding="utf-8")
    data = text if key in ("M1", "M2") else json.loads(text)
    return JUDGES[key](data, rules)


def summarize(violations):
    counts = {}
    for v in violations:
        counts[v["id"]] = counts.get(v["id"], 0) + 1
    return {"pass": not violations, "violation_count": len(violations), "by_id": counts, "violations": violations}


def main():
    parser = argparse.ArgumentParser(description="허들링 하네스 판정")
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("run_dir", help="runs/<화면-id>")
    parser.add_argument("--rules", default=str(DEFAULT_RULES))
    parser.add_argument("--input", help="입력 파일 (기본: 단계별 정해진 파일)")
    parser.add_argument("--no-write", action="store_true", help="s5-verdict.json에 기록하지 않음")
    args = parser.parse_args()

    key, default_input = STAGES[args.stage]
    run_dir = Path(args.run_dir)
    input_path = Path(args.input) if args.input else run_dir / default_input
    try:
        rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
        result = summarize(run(key, input_path, rules))
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}", "input": str(input_path)}, ensure_ascii=False))
        sys.exit(2)

    if not args.no_write:
        verdict_path = run_dir / VERDICT_FILE
        verdict = json.loads(verdict_path.read_text(encoding="utf-8")) if verdict_path.exists() else {}
        verdict[key] = result
        verdict_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({key: result}, ensure_ascii=False, indent=2))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
