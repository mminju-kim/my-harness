// Figma 스냅샷 내보내기 (use_figma의 code로 넘긴다).
// 맨 위 세 값만 바꿔서 쓴다. 반환값(JSON 문자열)을 runs/<id>/의 스냅샷 파일에 그대로 저장한다.
//   S3: AREA_NAME = "Key Screens", STAGE = "s3" → s3-keyscreens.snapshot.json
//   S4: AREA_NAME = "Screens",     STAGE = "s4" → s4-screen.snapshot.json
//
// 규칙
// - "02 Screens" 페이지 › AREA_NAME 영역 Section › SCREEN_ID Section 아래의 Frame만 읽는다.
// - Frame 이름은 "<화면-id> / <역할>" 또는 "<화면-id> / <역할> / <시안>" (역할: guest, free, paid, seller, admin)
// - 숨긴 노드(visible = false)는 건너뛴다.
const AREA_NAME = "Screens";
const SCREEN_ID = "my-assets";
const STAGE = "s4";
const PAGE_NAME = "02 Screens";

const round = (x) => Math.round(x * 100) / 100;
const hex = (c) => "#" + [c.r, c.g, c.b].map((x) => Math.round(x * 255).toString(16).padStart(2, "0")).join("");

function paintList(paints) {
  if (!paints || paints === figma.mixed) return [];
  return paints
    .filter((p) => p.visible !== false)
    .map((p) => (p.type === "SOLID" ? { type: "SOLID", color: hex(p.color), opacity: round(p.opacity ?? 1) } : { type: p.type }));
}

async function componentName(node) {
  if (node.type !== "INSTANCE") return null;
  const main = await node.getMainComponentAsync();
  if (!main) return null;
  return main.parent && main.parent.type === "COMPONENT_SET" ? main.parent.name : main.name;
}

function componentProps(node) {
  const props = {};
  for (const [key, prop] of Object.entries(node.componentProperties || {})) props[key.split("#")[0]] = prop.value;
  return props;
}

async function checklistItems(node) {
  const items = [];
  for (const child of node.findAll((n) => n.type === "INSTANCE" && n.visible !== false)) {
    if ((await componentName(child)) !== "checklist-item") continue;
    const p = componentProps(child);
    items.push({ id: p.id, checked: p.checked === true || p.checked === "true" });
  }
  return items;
}

async function textInfo(node) {
  const segments = node.getStyledTextSegments(["fontName", "fontWeight", "letterSpacing"]);
  let textStyle = null;
  if (node.textStyleId && node.textStyleId !== figma.mixed) {
    const style = await figma.getStyleByIdAsync(node.textStyleId);
    textStyle = style ? style.name : null;
  }
  return {
    characters: node.characters,
    fontFamilies: [...new Set(segments.map((s) => s.fontName.family))],
    fontWeights: [...new Set(segments.map((s) => s.fontWeight))],
    letterSpacings: [...new Set(segments.map((s) => round(s.letterSpacing.value)))],
    textStyle,
  };
}

async function walk(node, out) {
  if (node.visible === false) return;
  const rec = { id: node.id, name: node.name, type: node.type, width: round(node.width), height: round(node.height) };
  const component = await componentName(node);
  if (component) {
    rec.component = component;
    rec.props = componentProps(node);
    if (component === "review-checklist") rec.props.items = await checklistItems(node);
  }
  if ("fills" in node) rec.fills = paintList(node.fills);
  if ("strokes" in node) {
    rec.strokes = paintList(node.strokes);
    rec.strokeWeight = node.strokeWeight === figma.mixed
      ? Math.max(node.strokeTopWeight, node.strokeRightWeight, node.strokeBottomWeight, node.strokeLeftWeight)
      : node.strokeWeight;
  }
  if ("topLeftRadius" in node) {
    rec.radii = [node.topLeftRadius, node.topRightRadius, node.bottomRightRadius, node.bottomLeftRadius].map(round);
  }
  if ("effects" in node) rec.effects = node.effects.filter((e) => e.visible !== false).map((e) => ({ type: e.type }));
  if ("layoutMode" in node && node.layoutMode !== "NONE") {
    Object.assign(rec, {
      paddingTop: node.paddingTop, paddingRight: node.paddingRight,
      paddingBottom: node.paddingBottom, paddingLeft: node.paddingLeft,
    });
    if (node.primaryAxisAlignItems !== "SPACE_BETWEEN") rec.itemSpacing = node.itemSpacing;
    if (node.layoutWrap === "WRAP") rec.counterAxisSpacing = node.counterAxisSpacing;
  }
  if (node.type === "TEXT") Object.assign(rec, await textInfo(node));
  out.push(rec);
  if ("children" in node) for (const child of node.children) await walk(child, out);
}

const page = figma.root.children.find((p) => p.name === PAGE_NAME);
if (!page) throw new Error(`페이지 없음: ${PAGE_NAME}`);
await figma.setCurrentPageAsync(page);
const area = page.children.find((n) => n.type === "SECTION" && n.name === AREA_NAME);
if (!area) throw new Error(`영역 섹션 없음: ${PAGE_NAME} › ${AREA_NAME}`);
const section = area.children.find((n) => n.type === "SECTION" && n.name === SCREEN_ID);
if (!section) throw new Error(`섹션 없음: ${PAGE_NAME} › ${AREA_NAME} › ${SCREEN_ID}`);

const frames = [];
for (const f of section.children.filter((n) => n.type === "FRAME" && n.visible !== false)) {
  const role = (f.name.split("/")[1] || "").trim() || null;
  const nodes = [];
  await walk(f, nodes);
  frames.push({ id: f.id, name: f.name, role, width: round(f.width), height: round(f.height), nodes });
}

return JSON.stringify({ screen_id: SCREEN_ID, stage: STAGE, page: PAGE_NAME, area: AREA_NAME, frames }, null, 2);
