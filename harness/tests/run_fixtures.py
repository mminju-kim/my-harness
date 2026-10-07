#!/usr/bin/env python3
"""judge.py 검증 (harness/r8-verification.md 1번).

샘플을 harness/tests/fixtures/에 다시 만들고, judge.py로 판정해 기대값과 비교한다.
- clean/: 위반 0건이어야 한다
- violations/<id>.*: 그 id만 정확히 1건 걸려야 한다

사용법: python3 harness/tests/run_fixtures.py
종료 코드: 0 전부 일치, 1 하나라도 불일치
"""
import copy
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import judge  # noqa: E402

FIXTURES = HERE / "fixtures"
RULES = json.loads((HERE.parent / "rules.json").read_text(encoding="utf-8"))

# ---------- 깨끗한 샘플 ----------

BRIEF = """# 내 자산 (my-assets) 화면 브리프

## 목적
멤버가 만든 자산 목록을 보고 새 자산을 등록한다.

## 유저스토리
- US-4: 판매 승인 회원이 내 자산을 판매 신청하고 검수 상태를 확인한다.

## 데이터 필드
- Asset.title, Asset.visibility, Asset.review_status

## 권한
- paid: 비공개 / 멤버 공개
- seller: 비공개 / 멤버 공개 / 판매 신청

## 상태값
- 임시저장 / 검수 대기 / 수정 요청 / 승인됨 / 반려
"""


def reference(n):
    return (
        f"### R{n} 예시 앱 {n}\n"
        f"- ui_url: https://uibowl.io/example/{n}\n"
        "- UX 포인트: 상태별 필터를 상단에 고정\n"
        "- UI 포인트: 카드 우측 상단에 상태 배지\n"
        "- 반영할 것: 검수 상태 배지를 카드에 표시\n"
    )


REFERENCES = "# 내 자산 레퍼런스\n\n" + "\n".join(reference(n) for n in range(1, 6))


def solid(color, opacity=1):
    return {"type": "SOLID", "color": color, "opacity": opacity}


def text(name, characters, weight=400, style="body"):
    return {
        "name": name, "type": "TEXT", "characters": characters,
        "fontFamilies": ["Pretendard"], "fontWeights": [weight], "letterSpacings": [0],
        "textStyle": style, "fills": [solid("#141414")],
    }


def frame(name, role, nodes):
    root = {"name": name, "type": "FRAME", "width": 390, "height": 844, "fills": [solid("#ffffff")], "radii": [0, 0, 0, 0]}
    return {"name": name, "role": role, "width": 390, "height": 844, "nodes": [root] + nodes}


def my_assets_nodes(role):
    options = ["private", "member_only"] + (["sale_requested"] if role == "seller" else [])
    return [
        {"name": "nav", "type": "INSTANCE", "component": "nav-pill", "fills": [solid("#f3f3f3")],
         "radii": [9999] * 4, "paddingLeft": 16, "paddingRight": 16, "itemSpacing": 8},
        text("title", "내 자산", 700, "heading-1"),
        text("lead", "내가 만든 프롬프트와 스킬을 모아 둬요", 300, "body-lg"),
        {"name": "card", "type": "FRAME", "fills": [solid("#ffffff")], "strokes": [solid("#f0f0f0")],
         "strokeWeight": 1, "radii": [24] * 4, "paddingTop": 24, "paddingBottom": 24, "itemSpacing": 12},
        {"name": "icon", "type": "INSTANCE", "component": "app-icon-squircle", "width": 48, "height": 48,
         "radii": [14.4] * 4, "fills": [solid("#f3f3f3")]},
        {"name": "tag", "type": "INSTANCE", "component": "badge-overlay", "fills": [solid("#737373", 0.56)], "radii": [9999] * 4},
        {"name": "popular", "type": "INSTANCE", "component": "badge-popular", "fills": [solid("#0066ff")], "radii": [9999] * 4},
        {"name": "tabs-active", "type": "INSTANCE", "component": "segmented-control-active",
         "fills": [solid("#ffffff")], "radii": [9999] * 4, "effects": [{"type": "DROP_SHADOW"}]},
        {"name": "search", "type": "INSTANCE", "component": "text-input", "props": {"state": "rest"},
         "fills": [solid("#f0f0f0")], "strokes": [], "radii": [16] * 4, "paddingTop": 12, "paddingLeft": 16},
        {"name": "visibility", "type": "INSTANCE", "component": "visibility-control", "props": {"default": "private"},
         "fills": [solid("#f3f3f3")], "radii": [9999] * 4},
    ] + [
        {"name": f"option-{o}", "type": "INSTANCE", "component": "visibility-option", "props": {"value": o},
         "fills": [solid("#ffffff")], "radii": [9999] * 4}
        for o in options
    ] + [
        text("owner", "작성자 kim@example.com · 010-0000-0000", 400, "caption"),
        {"name": "cta", "type": "INSTANCE", "component": "button-primary", "fills": [solid("#141414")],
         "radii": [9999] * 4, "paddingLeft": 16, "paddingRight": 16},
        text("cta-label", "새 자산 등록", 600, "link") | {"fills": [solid("#ffffff")]},
    ]


def checklist(checked):
    items = [{"id": cid, "checked": i < checked} for i, cid in enumerate(RULES["B1"]["items"])]
    return {"name": "checklist", "type": "INSTANCE", "component": "review-checklist", "props": {"items": items},
            "fills": [solid("#f3f3f3")], "radii": [24] * 4}


def admin_review_nodes():
    return [
        text("title", "검수 대기", 700, "heading-1"),
        checklist(3),
        {"name": "approve", "type": "INSTANCE", "component": "approve-button", "props": {"enabled": False},
         "fills": [solid("#141414")], "radii": [9999] * 4},
        {"name": "reject", "type": "INSTANCE", "component": "button-outline", "fills": [solid("#ffffff")],
         "strokes": [solid("#e0e0e0")], "strokeWeight": 1, "radii": [9999] * 4},
    ]


KEYSCREENS = {"screen_id": "my-assets", "stage": "s3", "frames": [
    frame("my-assets / paid / A", "paid", my_assets_nodes("paid")),
    frame("my-assets / paid / B", "paid", my_assets_nodes("paid")),
]}
MY_ASSETS = {"screen_id": "my-assets", "stage": "s4", "frames": [
    frame("my-assets / paid", "paid", my_assets_nodes("paid")),
    frame("my-assets / seller", "seller", my_assets_nodes("seller")),
]}
ADMIN_REVIEW = {"screen_id": "admin-review", "stage": "s4", "frames": [
    frame("admin-review / admin", "admin", admin_review_nodes()),
]}

# ---------- 위반 샘플: 기본 샘플을 한 군데만 바꾼다 ----------


def node(snap, name, frame_index=0):
    return next(n for n in snap["frames"][frame_index]["nodes"] if n["name"] == name)


def mutate(base, change):
    snap = copy.deepcopy(base)
    change(snap)
    return snap


def accent_badges(s):
    for i in range(2):
        s["frames"][0]["nodes"].append({"name": f"extra-popular-{i}", "type": "INSTANCE", "component": "badge-popular",
                                        "fills": [solid("#0066ff")], "radii": [9999] * 4})


def drop_checklist_item(s):
    items = node(s, "checklist")["props"]["items"]
    items[:] = [i for i in items if i["id"] != "C7"]


VIOLATIONS = {
    "M1": ("s1-brief.md", BRIEF.split("## 상태값")[0]),
    "M2": ("s2-references.md", "# 내 자산 레퍼런스\n\n" + "\n".join(reference(n) for n in range(1, 5))),
    "M3": ("s3-keyscreens.snapshot.json",
           mutate(KEYSCREENS, lambda s: s["frames"][1].update(width=375, height=812))),
    "D1": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: node(s, "card")["fills"].__setitem__(0, solid("#ff0000")))),
    "D2": ("s4-screen.snapshot.json", mutate(MY_ASSETS, accent_badges)),
    "D3": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: node(s, "card").update(radii=[12] * 4))),
    "D4": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: node(s, "card").update(effects=[{"type": "DROP_SHADOW"}]))),
    "D5": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: node(s, "lead").update(letterSpacings=[-0.5]))),
    "D6": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: node(s, "card").update(paddingTop=10))),
    "D7": ("s4-screen.snapshot.json",
           mutate(MY_ASSETS, lambda s: node(s, "search").update(strokes=[solid("#e0e0e0")], strokeWeight=1))),
    "D8": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: s["frames"][0].update(height=900))),
    "A1": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: node(s, "visibility")["props"].update(default="member_only"))),
    "A2": ("s4-screen.snapshot.json", mutate(MY_ASSETS, lambda s: s["frames"][0]["nodes"].append(
        {"name": "option-sale_requested", "type": "INSTANCE", "component": "visibility-option",
         "props": {"value": "sale_requested"}, "fills": [solid("#ffffff")], "radii": [9999] * 4}))),
    "B1": ("s4-screen.snapshot.json", mutate(ADMIN_REVIEW, drop_checklist_item)),
    "B2": ("s4-screen.snapshot.json", mutate(ADMIN_REVIEW, lambda s: node(s, "approve")["props"].update(enabled=True))),
    "B3": ("s4-screen.snapshot.json",
           mutate(MY_ASSETS, lambda s: node(s, "owner").update(characters="작성자 minsu@gmail.com"))),
}

CLEAN = {
    "s1-brief.md": BRIEF,
    "s2-references.md": REFERENCES,
    "s3-keyscreens.snapshot.json": KEYSCREENS,
    "s4-screen.snapshot.json": MY_ASSETS,
    "s4-screen.admin-review.snapshot.json": ADMIN_REVIEW,
}
JUDGE_KEY = {"s1": "M1", "s2": "M2", "s3": "M3", "s4": "S5"}


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2) + "\n"
    path.write_text(body, encoding="utf-8")


def judge_ids(path):
    key = JUDGE_KEY[re.search(r"(?:^|\.)(s[1-4])-", path.name).group(1)]
    return [v["id"] for v in judge.run(key, path, RULES)]


def main():
    shutil.rmtree(FIXTURES, ignore_errors=True)
    cases = []
    for filename, content in CLEAN.items():
        path = FIXTURES / "clean" / filename
        write(path, content)
        cases.append((f"clean/{filename}", path, []))
    for rule_id, (filename, content) in VIOLATIONS.items():
        suffix = filename.split(".", 1)[1]
        path = FIXTURES / "violations" / f"{rule_id}.{filename.split('.')[0]}.{suffix}"
        write(path, content)
        cases.append((f"violations/{path.name}", path, [rule_id]))

    failed = 0
    for label, path, expected in cases:
        got = judge_ids(path)
        ok = got == expected
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:55s} 기대 {expected}  결과 {got}")
    print(f"\n{len(cases) - failed}/{len(cases)} 일치")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
