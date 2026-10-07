# 하네스 산출물

## 폴더 구조

```txt
claude skill/
├── docs/                         기준 문서 (사람이 읽음)
├── harness/
│   ├── r2-purpose.md ~ r8-*.md   라운드별 설계 문서
│   ├── rules.json                판정 규칙 SSOT
│   └── figma.json                공용 Figma 파일 키
└── runs/
    └── <화면-id>/                대상 화면 1개당 폴더 1개
        ├── state.json
        ├── gates.json
        ├── s1-brief.md
        ├── s2-references.md
        ├── s3-keyscreens.snapshot.json
        ├── s4-screen.snapshot.json
        └── s5-verdict.json
```

## 단계별 파일

| 단계 | 파일 | 내용 |
|---|---|---|
| S1 | `s1-brief.md` | 화면 목적, 관련 유저스토리, 데이터 필드, 권한별 차이, 상태값 |
| S2 | `s2-references.md` | uibowl 화면 5~8개, 각각의 UX·UI 포인트, 반영할 것 |
| S3 | `s3-keyscreens.snapshot.json` | Figma `02 Screens` › `Key Screens`의 키스크린 2~3개 노드 속성 |
| S4 | `s4-screen.snapshot.json` | Figma `03 Tokens & Components`의 변수 + `02 Screens` › `Screens`의 화면 노드 속성 |
| S5 | `s5-verdict.json` | 위반 목록, 위반 수 |
| 게이트 | `gates.json` | G1~G3 각각 승인/반려, 시각, 반려 사유 |

## 화면 id

영문 소문자와 하이픈만 쓴다.

| 화면 (PRD 16장) | 화면 id |
|---|---|
| 홈 | `home` |
| 무료 학습자료 | `free-content` |
| 유료 멤버 자료실 | `member-library` |
| 스킬 라이브러리 | `skill-library` |
| 미션 상세 | `mission-detail` |
| 제출 화면 | `submission` |
| 내 학습 | `my-learning` |
| 내 자산 | `my-assets` |
| 자산 상세 | `asset-detail` |
| 운영자 검수 화면 | `admin-review` |

## 규칙 SSOT

- `harness/rules.json` 1개. 판정 스크립트는 이 파일만 본다.
- `docs/design.md` 규칙과 `docs/story-service.md`의 A·B를 셀 수 있는 값으로 담는다. (값은 R5에서 채운다)
- `docs/design.md`는 설명 문서로 둔다. `design.md`가 바뀌면 `rules.json`도 같이 고친다.

## 재개

- 가능. `runs/<화면-id>/state.json`에 현재 단계, 단계별 재시도 횟수(최대 3), 게이트 상태를 기록한다.
- 다시 실행하면 마지막으로 끝나지 않은 단계부터 이어서 한다.

## Figma 파일

- 모든 화면이 파일 1개를 함께 쓴다. 파일 키는 `harness/figma.json`에 저장한다.
- `01 References`: 화면 id 이름의 섹션에 S2 레퍼런스를 둔다.
- `02 Screens`: 영역 Section `Key Screens`와 `Screens` 안에 화면 id 이름의 섹션을 하나씩 만든다.
- `03 Tokens & Components`: 모든 화면이 공유한다.
