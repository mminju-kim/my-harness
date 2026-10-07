# Figma 작업 규칙 (판정 스크립트가 읽을 수 있게)

`judge.py`는 Figma 화면을 직접 보지 못하고 `export-snapshot.js`가 꺼낸 값만 본다. 아래 이름과 속성을 지켜야 판정이 맞게 동작한다.

## 파일 구조

- 파일 키: `harness/figma.json`의 `fileKey`
- 페이지 3개: `01 References` / `02 Screens` / `03 Tokens & Components`
- `02 Screens`는 영역 Section 두 개로 나눈다: `Key Screens` (S3), `Screens` (S4)
- 화면별 작업은 화면 id 이름의 **Section** 안에서만 한다.
  - `01 References` › `<id>`
  - `02 Screens` › `Key Screens` › `<id>`
  - `02 Screens` › `Screens` › `<id>`

## 프레임

- 크기: 390×844
- 이름: `<화면-id> / <역할>` (S3 시안은 `<화면-id> / <역할> / A`, `B`, `C`)
- 역할: `guest`, `free`, `paid`, `seller`, `admin` 중 하나. 역할마다 보이는 것이 다르면 프레임을 나눈다.

## 컴포넌트 이름

- `docs/design.md`의 컴포넌트 이름을 그대로 쓴다: `button-primary`, `button-outline`, `button-pill-soft`, `text-input`, `nav-pill`, `badge-popular`, `badge-overlay`, `app-icon-squircle`, `segmented-control`, `segmented-control-active`, `faq-row` 등
- 판정에 쓰는 컴포넌트 (이름과 속성을 정확히 맞춘다):

| 컴포넌트 | 속성 (Component property) | 값 | 판정 |
|---|---|---|---|
| `visibility-control` | `default` | `private` / `member_only` / `sale_requested` | A1 |
| `visibility-option` | `value` | `private` / `member_only` / `sale_requested` | A2 |
| `review-checklist` | 안에 `checklist-item` 8개 | — | B1, B2 |
| `checklist-item` | `id`, `checked` | `C1`~`C8`, `true`/`false` | B1, B2 |
| `approve-button` | `enabled` | `true`/`false` | B2 |
| `text-input` | `state` | `rest` / `focused` | D7 |

- `C1`~`C8`의 뜻은 `harness/rules.json`의 `B1.items`에 있다.

## 값

- 색, 모서리, 그림자, 글꼴, 간격의 허용 값은 `harness/rules.json`이 기준이다.
- 텍스트 스타일 이름은 `docs/design.md`의 typography 토큰 이름과 같게 한다 (`display`, `heading-1`~`heading-4`, `title`, `body-lg`, `body`, `body-sm`, `link`, `label`, `caption`).
- 더미 연락처는 `@example.com` 이메일과 `010-0000-0000`만 쓴다.
- 이미지는 `createImageAsync`를 쓸 수 없다. 레퍼런스는 텍스트 카드(제목 + 링크 + 포인트)로 남긴다.
