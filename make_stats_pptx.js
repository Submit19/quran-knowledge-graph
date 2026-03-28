const pptxgen = require("pptxgenjs");
const pres = new pptxgen();

pres.layout = "LAYOUT_16x9";
pres.author = "Quran Knowledge Graph";
pres.title = "Quran Knowledge Graph — Statistical Insights";

// Color palette
const BG = "060A14";
const BG_CARD = "0F1A2E";
const GREEN = "10B981";
const GREEN_DIM = "0D9488";
const GOLD = "F59E0B";
const GOLD_DIM = "D97706";
const TEXT = "CBD5E1";
const TEXT_MUTED = "64748B";
const TEXT_BRIGHT = "F1F5F9";
const BORDER = "1E293B";

// ═══════════════════════════════════════════════════════════════
// SLIDE 1: Title
// ═══════════════════════════════════════════════════════════════
let s1 = pres.addSlide();
s1.background = { color: BG };
// Subtle top accent bar
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s1.addText("Quran Knowledge Graph", {
  x: 0.8, y: 1.2, w: 8.4, h: 1.2,
  fontSize: 42, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true, align: "center"
});
s1.addText("Statistical Insights", {
  x: 0.8, y: 2.3, w: 8.4, h: 0.7,
  fontSize: 28, fontFace: "Georgia", color: GREEN, align: "center"
});
s1.addText("6,234 verses  •  2,661 keywords  •  51,733 thematic connections", {
  x: 0.8, y: 3.6, w: 8.4, h: 0.5,
  fontSize: 14, fontFace: "Calibri", color: TEXT_MUTED, align: "center"
});
// Bottom accent
s1.addShape(pres.shapes.RECTANGLE, { x: 3.5, y: 4.3, w: 3, h: 0.02, fill: { color: GOLD_DIM, transparency: 60 } });

// ═══════════════════════════════════════════════════════════════
// SLIDE 2: The Graph at a Glance — big stat callouts
// ═══════════════════════════════════════════════════════════════
let s2 = pres.addSlide();
s2.background = { color: BG };
s2.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s2.addText("The Graph at a Glance", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});

const stats = [
  { num: "6,234", label: "Verses", sub: "across 114 surahs" },
  { num: "2,661", label: "Keywords", sub: "extracted via TF-IDF" },
  { num: "45,064", label: "MENTIONS", sub: "verse → keyword edges" },
  { num: "51,733", label: "RELATED_TO", sub: "verse ↔ verse edges" },
  { num: "93.7%", label: "Cross-Surah", sub: "connections span chapters" },
  { num: "7.27", label: "Avg Keywords", sub: "per verse" },
];
stats.forEach((s, i) => {
  const col = i % 3;
  const row = Math.floor(i / 3);
  const x = 0.6 + col * 3.1;
  const y = 1.15 + row * 2.05;
  s2.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 2.8, h: 1.8,
    fill: { color: BG_CARD },
    line: { color: BORDER, width: 0.5 },
    rectRadius: 0.08
  });
  s2.addText(s.num, {
    x, y: y + 0.2, w: 2.8, h: 0.7,
    fontSize: 32, fontFace: "Georgia", color: GREEN, bold: true, align: "center", margin: 0
  });
  s2.addText(s.label, {
    x, y: y + 0.85, w: 2.8, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: TEXT_BRIGHT, bold: true, align: "center", margin: 0
  });
  s2.addText(s.sub, {
    x, y: y + 1.2, w: 2.8, h: 0.35,
    fontSize: 11, fontFace: "Calibri", color: TEXT_MUTED, align: "center", margin: 0
  });
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 3: Most Frequent Keywords — bar chart
// ═══════════════════════════════════════════════════════════════
let s3 = pres.addSlide();
s3.background = { color: BG };
s3.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s3.addText("Most Frequent Keywords", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});
s3.addText("Top 15 keywords by number of verses mentioning them", {
  x: 0.6, y: 0.75, w: 8.8, h: 0.35,
  fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED
});

s3.addChart(pres.charts.BAR, [{
  name: "Verses",
  labels: ["disbelieve","know","send","among","righteous","may","life","everything","make","would","heaven","revelation","good","see","guide"],
  values: [298,296,279,275,274,258,252,243,225,225,220,209,204,202,198]
}], {
  x: 0.4, y: 1.2, w: 9.2, h: 4.1,
  barDir: "bar",
  chartColors: [GREEN],
  chartArea: { fill: { color: BG_CARD }, roundedCorners: true },
  plotArea: { fill: { color: BG_CARD } },
  catAxisLabelColor: TEXT,
  catAxisLabelFontSize: 10,
  valAxisLabelColor: TEXT_MUTED,
  valAxisLabelFontSize: 9,
  valGridLine: { color: BORDER, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelColor: TEXT_MUTED,
  dataLabelFontSize: 9,
  dataLabelPosition: "outEnd",
  showLegend: false,
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 4: Keyword Distribution — The Long Tail
// ═══════════════════════════════════════════════════════════════
let s4 = pres.addSlide();
s4.background = { color: BG };
s4.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s4.addText("Keyword Distribution — The Long Tail", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});

s4.addChart(pres.charts.BAR, [{
  name: "Keywords",
  labels: ["1 verse", "2–5 verses", "6–10 verses", "11–50 verses", "50+ verses"],
  values: [179, 1121, 439, 705, 217]
}], {
  x: 0.8, y: 1.1, w: 8.4, h: 3.5,
  barDir: "col",
  chartColors: [GOLD],
  chartArea: { fill: { color: BG_CARD }, roundedCorners: true },
  plotArea: { fill: { color: BG_CARD } },
  catAxisLabelColor: TEXT,
  catAxisLabelFontSize: 11,
  valAxisLabelColor: TEXT_MUTED,
  valAxisLabelFontSize: 9,
  valGridLine: { color: BORDER, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelColor: TEXT,
  dataLabelFontSize: 11,
  dataLabelPosition: "outEnd",
  showLegend: false,
});

s4.addText("42% of keywords appear in only 1–5 verses, while 8% appear in 50+ verses", {
  x: 0.8, y: 4.8, w: 8.4, h: 0.4,
  fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED, italic: true, align: "center"
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 5: Longest vs Shortest Surahs
// ═══════════════════════════════════════════════════════════════
let s5 = pres.addSlide();
s5.background = { color: BG };
s5.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s5.addText("Longest vs Shortest Surahs", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});

// Left: Longest
s5.addText("Longest", {
  x: 0.6, y: 0.9, w: 4.2, h: 0.4,
  fontSize: 14, fontFace: "Calibri", color: GREEN, bold: true, align: "center"
});
const longest = [
  ["Al-Baqarah (2)", 286], ["The Poets (26)", 227], ["The Purgatory (7)", 206],
  ["The Amramites (3)", 200], ["The Arrangers (37)", 182]
];
longest.forEach((item, i) => {
  const y = 1.4 + i * 0.75;
  const barW = (item[1] / 286) * 3.2;
  s5.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: y, w: barW, h: 0.45, fill: { color: GREEN_DIM } });
  s5.addText(item[0], { x: 0.8, y: y - 0.02, w: 3.2, h: 0.45, fontSize: 11, fontFace: "Calibri", color: TEXT_BRIGHT, margin: [0, 0, 0, 6] });
  s5.addText(String(item[1]), { x: 0.8 + barW + 0.1, y, w: 0.8, h: 0.45, fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED, bold: true, margin: 0 });
});

// Right: Shortest
s5.addText("Shortest", {
  x: 5.2, y: 0.9, w: 4.2, h: 0.4,
  fontSize: 14, fontFace: "Calibri", color: GOLD, bold: true, align: "center"
});
const shortest = [
  ["Triumph (110)", 3], ["Bounty (108)", 3], ["The Afternoon (103)", 3],
  ["Absoluteness (112)", 4], ["Quraish Tribe (106)", 4]
];
shortest.forEach((item, i) => {
  const y = 1.4 + i * 0.75;
  const barW = (item[1] / 286) * 3.2;
  s5.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: y, w: Math.max(barW, 0.15), h: 0.45, fill: { color: GOLD_DIM } });
  s5.addText(item[0], { x: 5.4, y: y - 0.02, w: 3.2, h: 0.45, fontSize: 11, fontFace: "Calibri", color: TEXT_BRIGHT, margin: [0, 0, 0, 6] });
  s5.addText(String(item[1]), { x: 5.4 + Math.max(barW, 0.15) + 0.1, y, w: 0.6, h: 0.45, fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED, bold: true, margin: 0 });
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 6: Most Central Surahs
// ═══════════════════════════════════════════════════════════════
let s6 = pres.addSlide();
s6.background = { color: BG };
s6.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s6.addText("Most Central Surahs", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});
s6.addText("Ranked by cross-surah RELATED_TO connections", {
  x: 0.6, y: 0.75, w: 8.8, h: 0.35,
  fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED
});

s6.addChart(pres.charts.BAR, [{
  name: "Cross-Surah Edges",
  labels: ["The Heifer","The Purgatory","The Amramites","The Poets","Livestock","Women","The Arrangers","The Bee","The Feast","Jonah"],
  values: [4382,3318,3244,3171,2855,2759,2673,2238,2071,1983]
}], {
  x: 0.4, y: 1.2, w: 9.2, h: 4.1,
  barDir: "bar",
  chartColors: [GREEN_DIM],
  chartArea: { fill: { color: BG_CARD }, roundedCorners: true },
  plotArea: { fill: { color: BG_CARD } },
  catAxisLabelColor: TEXT,
  catAxisLabelFontSize: 10,
  valAxisLabelColor: TEXT_MUTED,
  valAxisLabelFontSize: 9,
  valGridLine: { color: BORDER, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelColor: TEXT_MUTED,
  dataLabelFontSize: 9,
  dataLabelPosition: "outEnd",
  showLegend: false,
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 7: Connection Density — Edges per Verse
// ═══════════════════════════════════════════════════════════════
let s7 = pres.addSlide();
s7.background = { color: BG };
s7.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s7.addText("Connection Density — Edges per Verse", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});

// Most dense (left)
s7.addText("Most Dense", {
  x: 0.4, y: 0.9, w: 4.6, h: 0.4,
  fontSize: 14, fontFace: "Calibri", color: GREEN, bold: true, align: "center"
});
s7.addChart(pres.charts.BAR, [{
  name: "Edges/Verse",
  labels: ["Mutual Blaming","The Key","Proof","Kneeling","Luqmaan"],
  values: [24.89, 20.29, 20.13, 19.62, 19.09]
}], {
  x: 0.2, y: 1.3, w: 4.6, h: 3.8,
  barDir: "bar",
  chartColors: [GREEN],
  chartArea: { fill: { color: BG_CARD }, roundedCorners: true },
  plotArea: { fill: { color: BG_CARD } },
  catAxisLabelColor: TEXT,
  catAxisLabelFontSize: 10,
  valAxisLabelColor: TEXT_MUTED,
  valAxisLabelFontSize: 9,
  valGridLine: { color: BORDER, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelColor: TEXT,
  dataLabelFontSize: 10,
  dataLabelPosition: "outEnd",
  showLegend: false,
});

// Least dense (right)
s7.addText("Least Dense", {
  x: 5.2, y: 0.9, w: 4.6, h: 0.4,
  fontSize: 14, fontFace: "Calibri", color: GOLD, bold: true, align: "center"
});
s7.addChart(pres.charts.BAR, [{
  name: "Edges/Verse",
  labels: ["Most Gracious","Quraish Tribe","The Afternoon","The Backbiter","People"],
  values: [8.13, 9.50, 10.67, 11.11, 12.00]
}], {
  x: 5.2, y: 1.3, w: 4.6, h: 3.8,
  barDir: "bar",
  chartColors: [GOLD_DIM],
  chartArea: { fill: { color: BG_CARD }, roundedCorners: true },
  plotArea: { fill: { color: BG_CARD } },
  catAxisLabelColor: TEXT,
  catAxisLabelFontSize: 10,
  valAxisLabelColor: TEXT_MUTED,
  valAxisLabelFontSize: 9,
  valGridLine: { color: BORDER, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelColor: TEXT,
  dataLabelFontSize: 10,
  dataLabelPosition: "outEnd",
  showLegend: false,
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 8: Strongest Verse Pairs — table
// ═══════════════════════════════════════════════════════════════
let s8 = pres.addSlide();
s8.background = { color: BG };
s8.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s8.addText("Strongest Verse Pairs", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});
s8.addText("Highest RELATED_TO scores — verses sharing the most rare keywords", {
  x: 0.6, y: 0.75, w: 8.8, h: 0.35,
  fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED
});

const headerOpts = { fill: { color: GREEN_DIM }, color: "FFFFFF", bold: true, fontSize: 11, fontFace: "Calibri", align: "center" };
const cellOpts = { fill: { color: BG_CARD }, color: TEXT, fontSize: 10, fontFace: "Calibri" };
const cellOptsC = { fill: { color: BG_CARD }, color: TEXT, fontSize: 10, fontFace: "Calibri", align: "center" };
const scoreOpts = { fill: { color: BG_CARD }, color: GOLD, fontSize: 11, fontFace: "Calibri", bold: true, align: "center" };

const tableRows = [
  [{ text: "Verse 1", options: headerOpts }, { text: "Verse 2", options: headerOpts }, { text: "Theme", options: headerOpts }, { text: "Score", options: headerOpts }],
  [{ text: "4:43", options: cellOptsC }, { text: "5:6", options: cellOptsC }, { text: "Ablution rules", options: cellOpts }, { text: "3.82", options: scoreOpts }],
  [{ text: "2:136", options: cellOptsC }, { text: "3:84", options: cellOptsC }, { text: "Prophets accepted", options: cellOpts }, { text: "3.52", options: scoreOpts }],
  [{ text: "16:115", options: cellOptsC }, { text: "2:173", options: cellOptsC }, { text: "Forbidden foods", options: cellOpts }, { text: "3.28", options: scoreOpts }],
  [{ text: "4:11", options: cellOptsC }, { text: "4:12", options: cellOptsC }, { text: "Inheritance law", options: cellOpts }, { text: "3.27", options: scoreOpts }],
  [{ text: "16:115", options: cellOptsC }, { text: "6:145", options: cellOptsC }, { text: "Forbidden foods", options: cellOpts }, { text: "3.26", options: scoreOpts }],
  [{ text: "27:3", options: cellOptsC }, { text: "31:4", options: cellOptsC }, { text: "Prayer & charity", options: cellOpts }, { text: "3.15", options: scoreOpts }],
  [{ text: "27:10", options: cellOptsC }, { text: "28:31", options: cellOptsC }, { text: "Moses and fire", options: cellOpts }, { text: "3.04", options: scoreOpts }],
  [{ text: "2:173", options: cellOptsC }, { text: "6:145", options: cellOptsC }, { text: "Forbidden foods", options: cellOpts }, { text: "2.98", options: scoreOpts }],
  [{ text: "20:71", options: cellOptsC }, { text: "26:49", options: cellOptsC }, { text: "Pharaoh threatens", options: cellOpts }, { text: "2.90", options: scoreOpts }],
  [{ text: "2:35", options: cellOptsC }, { text: "7:19", options: cellOptsC }, { text: "Adam in paradise", options: cellOpts }, { text: "2.83", options: scoreOpts }],
];

s8.addTable(tableRows, {
  x: 0.6, y: 1.2, w: 8.8,
  colW: [1.2, 1.2, 4.4, 1.2],
  border: { pt: 0.5, color: BORDER },
  rowH: [0.38, 0.36, 0.36, 0.36, 0.36, 0.36, 0.36, 0.36, 0.36, 0.36, 0.36],
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 9: Connection Score Distribution
// ═══════════════════════════════════════════════════════════════
let s9 = pres.addSlide();
s9.background = { color: BG };
s9.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s9.addText("Connection Score Distribution", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});

s9.addChart(pres.charts.BAR, [{
  name: "Edges",
  labels: ["< 0.5", "0.5 – 1.0", "1.0 – 1.5", "1.5 – 2.0", "2.0+"],
  values: [1846, 41221, 7426, 1046, 194]
}], {
  x: 0.8, y: 1.1, w: 8.4, h: 3.5,
  barDir: "col",
  chartColors: [GREEN_DIM],
  chartArea: { fill: { color: BG_CARD }, roundedCorners: true },
  plotArea: { fill: { color: BG_CARD } },
  catAxisLabelColor: TEXT,
  catAxisLabelFontSize: 11,
  valAxisLabelColor: TEXT_MUTED,
  valAxisLabelFontSize: 9,
  valGridLine: { color: BORDER, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelColor: TEXT,
  dataLabelFontSize: 10,
  dataLabelPosition: "outEnd",
  showLegend: false,
});

s9.addText("Mean score: 0.81  •  79.7% of connections fall in the 0.5–1.0 range", {
  x: 0.8, y: 4.8, w: 8.4, h: 0.4,
  fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED, italic: true, align: "center"
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 10: Topological Insights
// ═══════════════════════════════════════════════════════════════
let s10 = pres.addSlide();
s10.background = { color: BG };
s10.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s10.addText("Topological Insights", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});

const insights = [
  { text: "93.7% cross-surah connections", detail: "The Quran's themes are deeply woven across chapters, not siloed within them" },
  { text: "Surah 12 (Joseph) is uniquely isolated", detail: "111 verses but only 12.26 edges/verse — its continuous narrative makes it thematically distinct from the rest" },
  { text: "Surah 55 (Most Gracious) is least dense", detail: "8.13 edges/verse — its repetitive refrain structure creates internal similarity but less external connection" },
  { text: "Surah 64 (Mutual Blaming) is most connected", detail: "24.89 edges/verse — its universal themes of belief, judgment, and obedience resonate across the entire Quran" },
  { text: "Near-complete keyword coverage", detail: "Only 33 verses (0.5%) have no extracted keywords out of 6,234 total" },
  { text: "Forbidden food passages cluster tightly", detail: "3 of the top 10 strongest verse pairs are about dietary prohibitions (2:173, 6:145, 16:115)" },
];

insights.forEach((item, i) => {
  const y = 1.05 + i * 0.72;
  // Green accent bar
  s10.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: y + 0.05, w: 0.06, h: 0.5, fill: { color: GREEN } });
  s10.addText(item.text, {
    x: 0.85, y: y, w: 8.5, h: 0.32,
    fontSize: 13, fontFace: "Calibri", color: TEXT_BRIGHT, bold: true, margin: 0
  });
  s10.addText(item.detail, {
    x: 0.85, y: y + 0.3, w: 8.5, h: 0.32,
    fontSize: 11, fontFace: "Calibri", color: TEXT_MUTED, margin: 0
  });
});

// ═══════════════════════════════════════════════════════════════
// SLIDE 11: Intra vs Inter-Surah — pie chart
// ═══════════════════════════════════════════════════════════════
let s11 = pres.addSlide();
s11.background = { color: BG };
s11.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: GREEN } });
s11.addText("Intra vs Inter-Surah Connections", {
  x: 0.6, y: 0.25, w: 8.8, h: 0.6,
  fontSize: 28, fontFace: "Georgia", color: TEXT_BRIGHT, bold: true
});

s11.addChart(pres.charts.DOUGHNUT, [{
  name: "Connections",
  labels: ["Inter-surah (93.7%)", "Intra-surah (6.3%)"],
  values: [48485, 3248]
}], {
  x: 1.5, y: 0.9, w: 4.5, h: 4.2,
  chartColors: [GREEN, GOLD_DIM],
  showPercent: true,
  dataLabelColor: TEXT_BRIGHT,
  dataLabelFontSize: 13,
  showLegend: true,
  legendPos: "b",
  legendColor: TEXT,
  legendFontSize: 11,
});

// Right side: callout
s11.addShape(pres.shapes.RECTANGLE, {
  x: 6.4, y: 1.6, w: 3.2, h: 2.4,
  fill: { color: BG_CARD },
  line: { color: BORDER, width: 0.5 },
});
s11.addText("48,485", {
  x: 6.4, y: 1.8, w: 3.2, h: 0.6,
  fontSize: 30, fontFace: "Georgia", color: GREEN, bold: true, align: "center", margin: 0
});
s11.addText("cross-surah edges", {
  x: 6.4, y: 2.35, w: 3.2, h: 0.35,
  fontSize: 13, fontFace: "Calibri", color: TEXT, align: "center", margin: 0
});
s11.addText("vs only 3,248 within\nthe same surah", {
  x: 6.4, y: 2.8, w: 3.2, h: 0.6,
  fontSize: 11, fontFace: "Calibri", color: TEXT_MUTED, align: "center", margin: 0
});

s11.addText("The Quran is a deeply interconnected web, not 114 isolated chapters", {
  x: 0.8, y: 5.0, w: 8.4, h: 0.35,
  fontSize: 13, fontFace: "Georgia", color: TEXT_MUTED, italic: true, align: "center"
});

// ═══════════════════════════════════════════════════════════════
// SAVE
// ═══════════════════════════════════════════════════════════════
pres.writeFile({ fileName: "C:/Users/alika/Agent Teams/quran-graph/quran_graph_stats.pptx" })
  .then(() => console.log("Saved: quran_graph_stats.pptx"))
  .catch(err => console.error("Error:", err));
