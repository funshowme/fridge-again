/**
 * 冰箱第二春 — 內建示範資料與規則式推薦引擎（離線備案）
 * 完全對齊 backend/seed.py、backend/recommend.py 與 docs/API.md v1.1（含食安過濾與 also_in_fridge）。
 */

export function getTaipeiTodayStr() {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Taipei',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return formatter.format(new Date());
}

export function getTaipeiNowIso() {
  const now = new Date();
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Taipei',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(now);
  const map = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  const hour = map.hour === '24' ? '00' : map.hour;
  return `${map.year}-${map.month}-${map.day}T${hour}:${map.minute}:${map.second}+08:00`;
}

export function addDays(dateStr, deltaDays) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + deltaDays));
  const yy = dt.getUTCFullYear();
  const mm = String(dt.getUTCMonth() + 1).padStart(2, '0');
  const dd = String(dt.getUTCDate()).padStart(2, '0');
  return `${yy}-${mm}-${dd}`;
}

export function diffDays(targetDateStr, baseDateStr = getTaipeiTodayStr()) {
  const [ty, tm, td] = targetDateStr.split('-').map(Number);
  const [by, bm, bd] = baseDateStr.split('-').map(Number);
  const targetMs = Date.UTC(ty, tm - 1, td);
  const baseMs = Date.UTC(by, bm - 1, bd);
  return Math.round((targetMs - baseMs) / 86400000);
}

export function computeUrgency(daysLeft) {
  if (daysLeft <= 1) return 'red';
  if (daysLeft <= 3) return 'yellow';
  return 'green';
}

export function hydrateItem(raw) {
  const days_left = diffDays(raw.expires_on);
  return {
    ...raw,
    days_left,
    urgency: computeUrgency(days_left),
  };
}

const EMOJI_RULES = [
  [['香蕉', '芭蕉'], '🍌'],
  [['蛋', '雞蛋', '皮蛋', '鹹蛋'], '🥚'],
  [['飯', '白飯', '剩飯', '糙米飯'], '🍚'],
  [['豆腐', '豆干', '豆皮'], '🧈'],
  [['蔥', '青蔥', '洋蔥', '蒜'], '🧅'],
  [['奶', '鮮奶', '牛奶', '豆漿', '優格'], '🥛'],
  [['吐司', '麵包', '貝果', '饅頭'], '🍞'],
  [['起司', '乳酪', '芝士'], '🧀'],
  [['泡菜', '辣醬', '辣椒'], '🌶️'],
  [['菇', '金針菇', '香菇', '鴻喜菇', '杏鮑菇'], '🍄'],
  [['玉米'], '🌽'],
  [['火腿', '培根', '香腸', '熱狗'], '🥓'],
  [['高麗菜', '白菜', '青江菜', '菠菜', '花椰菜', '菜'], '🥬'],
  [['鮪魚', '鮭魚', '鯖魚', '魚', '蝦', '海鮮'], '🐟'],
  [['雞', '雞胸', '雞腿', '雞肉'], '🍗'],
  [['豬', '牛', '肉片', '絞肉', '肉'], '🥩'],
  [['馬鈴薯', '地瓜', '芋頭'], '🥔'],
  [['番茄', '蕃茄'], '🍅'],
  [['紅蘿蔔', '胡蘿蔔'], '🥕'],
  [['麵', '泡麵', '烏龍', '冬粉', '義大利麵'], '🍜'],
  [['餃', '水餃', '鍋貼'], '🥟'],
  [['燕麥', '麥片'], '🥣'],
  [['蘋果', '水果', '芭樂', '橘子'], '🍎'],
];

export function guessEmoji(name = '') {
  const normalized = name.trim();
  for (const [keywords, emoji] of EMOJI_RULES) {
    if (keywords.some((kw) => normalized.includes(kw))) {
      return emoji;
    }
  }
  return '🥫';
}

// 食材別名正規化字典（與 backend/recommend.py 完全一致）
const ALIAS_GROUPS = {
  雞蛋: ['雞蛋', '蛋', '水煮蛋', '溏心蛋', '雞蛋液', '鮮蛋', '土雞蛋', '荷包蛋', '滷蛋'],
  白飯: ['白飯', '剩飯', '隔夜飯', '隔夜白飯', '飯', '米飯', '白米飯', '熟飯', '糙米飯', '紫米飯'],
  牛奶: ['牛奶', '鮮奶', '鮮乳', '保久乳', '全脂牛奶', '低脂牛奶', '牛乳'],
  嫩豆腐: ['嫩豆腐', '豆腐', '板豆腐', '百頁豆腐', '雞蛋豆腐', '傳統豆腐', '盒裝豆腐', '凍豆腐'],
  舒肥雞胸肉: ['舒肥雞胸肉', '舒肥雞胸', '雞胸肉', '雞胸', '雞肉', '雞腿肉', '雞肉絲', '雞柳', '雞腿'],
  蔥: ['蔥', '青蔥', '蔥花', '蔥段', '珠蔥', '三星蔥'],
  金針菇: ['金針菇', '香菇', '鴻喜菇', '杏鮑菇', '秀珍菇', '菇', '舞菇', '雪白菇'],
  吐司: ['吐司', '白吐司', '全麥吐司', '厚片吐司', '麵包', '餐包', '貝果'],
  起司片: ['起司片', '起司', '起司絲', '乳酪', '乳酪絲', '芝士', '焗烤起司', '莫札瑞拉'],
  火腿: ['火腿', '火腿片', '培根', '熱狗', '香腸', '德式香腸', '午餐肉'],
  高麗菜: ['高麗菜', '青菜', '小白菜', '青江菜', '娃娃菜', '菠菜', '大陸妹', '空心菜', '地瓜葉'],
  番茄: ['番茄', '牛番茄', '小番茄', '聖女番茄', '蕃茄'],
  韓式泡菜: ['韓式泡菜', '泡菜', '辣泡菜', '黃金泡菜'],
  烏龍麵: ['烏龍麵', '泡麵', '王子麵', '科學麵', '麵條', '意麵', '拉麵', '冬粉', '寬粉', '關廟麵', '麵'],
  冷凍水餃: ['冷凍水餃', '水餃', '熟水餃', '煎餃', '餛飩', '雲吞', '蒸餃'],
  香蕉: ['香蕉', '熟香蕉', '芭蕉'],
  燕麥: ['燕麥', '燕麥片', '即食燕麥', '麥片'],
  醬油: ['醬油', '醬油膏', '薄鹽醬油'],
  豬肉: ['豬肉', '豬肉片', '梅花豬', '五花肉', '絞肉', '肉片'],
  牛肉: ['牛肉', '牛肉片', '牛五花', '牛絞肉'],
  海鮮: ['海鮮', '蝦', '蝦仁', '魚', '魚片', '鮭魚', '鯛魚', '蛤蜊', '透抽', '小卷', '花枝'],
  玉米: ['玉米', '玉米粒', '玉米罐頭', '玉米筍'],
  馬鈴薯: ['馬鈴薯', '洋芋', '地瓜', '番薯'],
};

const ALIAS_TO_CANONICAL = new Map();
for (const [canonical, aliases] of Object.entries(ALIAS_GROUPS)) {
  ALIAS_TO_CANONICAL.set(canonical, canonical);
  for (const alias of aliases) {
    ALIAS_TO_CANONICAL.set(alias, canonical);
  }
}

const SORTED_ALIASES = Array.from(ALIAS_TO_CANONICAL.entries()).sort(
  (a, b) => b[0].length - a[0].length
);

// 食安高風險類別：肉類、海鮮、乳製品、豆腐（days_left < 0 不可推薦）
const HIGH_RISK_CANONICALS = new Set([
  '舒肥雞胸肉',
  '豬肉',
  '牛肉',
  '火腿',
  '海鮮',
  '牛奶',
  '起司片',
  '嫩豆腐',
]);

const HIGH_RISK_KEYWORDS = [
  '雞肉', '雞胸', '雞腿', '豬', '牛', '羊', '鴨', '鵝', '肉',
  '火腿', '培根', '香腸', '熱狗',
  '魚', '蝦', '蛤', '蚵', '蟹', '海鮮', '透抽', '花枝', '小卷',
  '牛奶', '鮮奶', '鮮乳', '牛乳', '優格', '優酪乳', '起司', '乳酪', '芝士', '鮮奶油',
  '豆腐', '豆花', '豆漿',
];

export function canonicalizeIngredient(name = '') {
  const clean = String(name || '').trim();
  if (!clean) return '';
  if (ALIAS_TO_CANONICAL.has(clean)) {
    return ALIAS_TO_CANONICAL.get(clean);
  }
  for (const [alias, canonical] of SORTED_ALIASES) {
    if (alias.length >= 2 && (clean.includes(alias) || alias.includes(clean))) {
      return canonical;
    }
  }
  return clean;
}

export function ingredientsMatch(nameA, nameB) {
  const canA = canonicalizeIngredient(nameA);
  const canB = canonicalizeIngredient(nameB);
  if (!canA || !canB) return false;
  if (canA === canB) return true;
  if (canA.length >= 2 && canB.length >= 2 && (canA.includes(canB) || canB.includes(canA))) {
    return true;
  }
  return false;
}

export function isHighRiskPerishable(name = '') {
  const clean = String(name || '').trim();
  if (!clean) return false;
  const canon = canonicalizeIngredient(clean);
  if (HIGH_RISK_CANONICALS.has(canon)) return true;
  return HIGH_RISK_KEYWORDS.some((kw) => clean.includes(kw));
}

export function isExpiredUnsafe(item) {
  if (!item) return false;
  return Number(item.days_left ?? 0) < 0 && isHighRiskPerishable(item.name);
}

// 16 樣在冰箱中的種子食材（與 backend/seed.py 完全同步）
export function createSeedItems() {
  const today = getTaipeiTodayStr();
  const created = getTaipeiNowIso();

  const definitions = [
    { id: 1, name: '香蕉', emoji: '🍌', quantity: 2, unit: '根', delta: -1, owner: '阿哲', price: 25 },
    { id: 2, name: '舒肥雞胸肉', emoji: '🍗', quantity: 1, unit: '包', delta: 0, owner: '阿哲', price: 59 },
    { id: 3, name: '牛奶', emoji: '🥛', quantity: 1, unit: '瓶', delta: 0, owner: '小明', price: 65 },
    { id: 4, name: '嫩豆腐', emoji: '🧈', quantity: 1, unit: '盒', delta: 0, owner: '小美', price: 25 },
    { id: 5, name: '雞蛋', emoji: '🥚', quantity: 3, unit: '顆', delta: 1, owner: '小明', price: 30 },
    { id: 6, name: '白飯', emoji: '🍚', quantity: 2, unit: '碗', delta: 1, owner: '小美', price: 30 },
    { id: 7, name: '蔥', emoji: '🧅', quantity: 1, unit: '把', delta: 2, owner: '小明', price: 20 },
    { id: 8, name: '金針菇', emoji: '🍄', quantity: 1, unit: '包', delta: 2, owner: '小美', price: 25 },
    { id: 9, name: '吐司', emoji: '🍞', quantity: 4, unit: '片', delta: 2, owner: '阿哲', price: 35 },
    { id: 10, name: '起司片', emoji: '🧀', quantity: 3, unit: '片', delta: 3, owner: '小美', price: 40 },
    { id: 11, name: '火腿', emoji: '🥓', quantity: 4, unit: '片', delta: 3, owner: '小明', price: 45 },
    { id: 12, name: '高麗菜', emoji: '🥬', quantity: 1, unit: '顆', delta: 4, owner: '阿哲', price: 50 },
    { id: 13, name: '番茄', emoji: '🍅', quantity: 2, unit: '顆', delta: 5, owner: '小美', price: 35 },
    { id: 14, name: '韓式泡菜', emoji: '🌶️', quantity: 1, unit: '罐', delta: 6, owner: '小明', price: 85 },
    { id: 15, name: '烏龍麵', emoji: '🍜', quantity: 2, unit: '包', delta: 7, owner: '阿哲', price: 50 },
    { id: 16, name: '冷凍水餃', emoji: '🥟', quantity: 15, unit: '顆', delta: 10, owner: '小明', price: 75 },
  ];

  return definitions.map((d) =>
    hydrateItem({
      id: d.id,
      name: d.name,
      emoji: d.emoji,
      quantity: d.quantity,
      unit: d.unit,
      expires_on: addDays(today, d.delta),
      owner: d.owner,
      price: d.price,
      status: 'in_fridge',
      created_at: created,
    })
  );
}

// 19 道宿舍限定食譜（只用電鍋或微波爐，與 backend/seed.py 完全同步）
export const SEED_RECIPES = [
  {
    id: 1,
    title: '電鍋滑嫩蒸蛋',
    emoji: '🍮',
    tool: '電鍋',
    minutes: 15,
    ingredients: ['雞蛋', '蔥', '醬油'],
    optional: ['蔥', '醬油'],
    steps: [
      '雞蛋打散，加入 1.5 倍溫水與少許醬油拌勻',
      '過篩或撈掉表面氣泡，撒上蔥花',
      '電鍋外鍋放半杯水，鍋蓋夾一根筷子留縫，蒸至跳起即可',
    ],
  },
  {
    id: 2,
    title: '電鍋黃金蛋炒飯（炊飯版）',
    emoji: '🍛',
    tool: '電鍋',
    minutes: 20,
    ingredients: ['白飯', '雞蛋', '火腿', '蔥', '醬油'],
    optional: ['火腿', '蔥'],
    steps: [
      '白飯撥散放入內鍋，淋上打散的蛋液與一匙醬油拌勻',
      '鋪上切丁的火腿，外鍋加半杯水按下電鍋',
      '開關跳起後撒上蔥花翻拌，免開火也能粒粒分明',
    ],
  },
  {
    id: 3,
    title: '微波起司牛奶燉飯',
    emoji: '🧀',
    tool: '微波爐',
    minutes: 6,
    ingredients: ['白飯', '牛奶', '起司片', '火腿'],
    optional: ['火腿'],
    steps: [
      '深碗放入白飯，倒入牛奶至淹過白飯約一半高度',
      '鋪上撕碎的火腿與起司片',
      '微波爐中強火加熱 4–5 分鐘至起司融化濃稠，拌勻即可',
    ],
  },
  {
    id: 4,
    title: '電鍋韓式泡菜豆腐鍋',
    emoji: '🍲',
    tool: '電鍋',
    minutes: 20,
    ingredients: ['嫩豆腐', '韓式泡菜', '金針菇', '雞蛋', '烏龍麵', '蔥'],
    optional: ['金針菇', '雞蛋', '烏龍麵', '蔥'],
    steps: [
      '內鍋放入切塊嫩豆腐、韓式泡菜與洗淨的金針菇，加水至七分滿',
      '外鍋加一杯水蒸煮，跳起前 5 分鐘可打入雞蛋或放入烏龍麵',
      '撒上蔥花即可熱騰騰享用',
    ],
  },
  {
    id: 5,
    title: '微波法式吐司布丁',
    emoji: '🍞',
    tool: '微波爐',
    minutes: 5,
    ingredients: ['吐司', '牛奶', '雞蛋'],
    optional: [],
    steps: [
      '雞蛋與牛奶在深碗或大馬克杯中打散拌勻',
      '吐司切成一口大小方塊，浸入蛋奶液吸飽湯汁',
      '微波爐中火加熱 3 分鐘至蛋液凝固、表面蓬鬆柔軟',
    ],
  },
  {
    id: 6,
    title: '微波起司火腿蛋吐司盒',
    emoji: '🥪',
    tool: '微波爐',
    minutes: 4,
    ingredients: ['吐司', '雞蛋', '起司片', '火腿'],
    optional: ['火腿'],
    steps: [
      '吐司中間用湯匙壓出凹槽，鋪上火腿與起司片',
      '在凹槽打入一顆雞蛋，用牙籤在蛋黃戳兩個小洞防爆',
      '微波爐中火加熱 2–3 分鐘至蛋白熟透即可',
    ],
  },
  {
    id: 7,
    title: '電鍋番茄滑蛋雞胸丼',
    emoji: '🍅',
    tool: '電鍋',
    minutes: 20,
    ingredients: ['番茄', '雞蛋', '舒肥雞胸肉', '白飯', '蔥'],
    optional: ['舒肥雞胸肉', '白飯', '蔥'],
    steps: [
      '番茄切塊放入內鍋，外鍋加半杯水先蒸軟出汁',
      '倒入蛋液與手撕舒肥雞胸肉，外鍋再加 1/4 杯水蒸熟',
      '淋在熱白飯上並撒上蔥花',
    ],
  },
  {
    id: 8,
    title: '微波金針菇蒸豆腐',
    emoji: '🍄',
    tool: '微波爐',
    minutes: 6,
    ingredients: ['嫩豆腐', '金針菇', '蔥', '醬油'],
    optional: ['蔥', '醬油'],
    steps: [
      '嫩豆腐切厚片排在深盤底，上面鋪滿洗淨的金針菇',
      '淋上一匙醬油與少許開水，加蓋或覆蓋微波保鮮膜留透氣孔',
      '微波爐強火加熱 5 分鐘，出爐撒上蔥花',
    ],
  },
  {
    id: 9,
    title: '電鍋高麗菜雞胸蒸餃鍋',
    emoji: '🥟',
    tool: '電鍋',
    minutes: 20,
    ingredients: ['冷凍水餃', '高麗菜', '舒肥雞胸肉', '雞蛋'],
    optional: ['舒肥雞胸肉', '雞蛋'],
    steps: [
      '內鍋底鋪滿手撕高麗菜，擺上冷凍水餃（不需退冰）',
      '淋上半碗水並放上切片舒肥雞胸肉，外鍋加一杯水',
      '跳起後高麗菜清甜、水餃Q彈不破皮',
    ],
  },
  {
    id: 10,
    title: '微波泡菜起司烏龍麵',
    emoji: '🍜',
    tool: '微波爐',
    minutes: 7,
    ingredients: ['烏龍麵', '韓式泡菜', '起司片', '雞蛋', '蔥'],
    optional: ['起司片', '雞蛋', '蔥'],
    steps: [
      '深碗放入烏龍麵、韓式泡菜與半碗熱水，微波 4 分鐘後拌開',
      '打入雞蛋（蛋黃戳洞）並鋪上起司片，再微波 2 分鐘',
      '撒上蔥花拌勻即可享用',
    ],
  },
  {
    id: 11,
    title: '電鍋牛奶高麗菜雞肉湯麵',
    emoji: '🥣',
    tool: '電鍋',
    minutes: 20,
    ingredients: ['牛奶', '高麗菜', '舒肥雞胸肉', '烏龍麵', '金針菇'],
    optional: ['舒肥雞胸肉', '烏龍麵', '金針菇'],
    steps: [
      '內鍋放入高麗菜、金針菇、烏龍麵與半碗水，外鍋一杯水蒸煮',
      '開關跳起後倒入牛奶與切片雞胸肉，利用餘溫悶 5 分鐘',
      '湯頭濃郁不油膩，適合宵夜暖胃',
    ],
  },
  {
    id: 12,
    title: '微波起司蒸餃佐泡菜',
    emoji: '🥟',
    tool: '微波爐',
    minutes: 8,
    ingredients: ['冷凍水餃', '起司片', '韓式泡菜'],
    optional: ['韓式泡菜'],
    steps: [
      '冷凍水餃放入深盤，加半碗熱水並加蓋，微波強火 5 分鐘至熟',
      '倒掉多餘水分，鋪上泡菜與起司片再微波 1 分鐘至起司融化',
      '免開火也能做出韓式牽絲煎餃風味',
    ],
  },
  {
    id: 13,
    title: '電鍋番茄蔬菜豆腐湯餃',
    emoji: '🍅',
    tool: '電鍋',
    minutes: 25,
    ingredients: ['番茄', '嫩豆腐', '高麗菜', '金針菇', '冷凍水餃', '蔥'],
    optional: ['金針菇', '冷凍水餃', '蔥'],
    steps: [
      '番茄切塊、嫩豆腐切丁、高麗菜撥片放入內鍋，可依食量加幾顆水餃',
      '加入兩碗水，外鍋一杯水按下電鍋',
      '跳起後撒上蔥花，清爽又有飽足感',
    ],
  },
  {
    id: 14,
    title: '微波手撕雞胸蔥油拌飯',
    emoji: '🍗',
    tool: '微波爐',
    minutes: 4,
    ingredients: ['舒肥雞胸肉', '白飯', '蔥', '雞蛋', '醬油'],
    optional: ['蔥', '雞蛋', '醬油'],
    steps: [
      '白飯與手撕舒肥雞胸肉放入深碗中',
      '淋上一匙醬油並撒上蔥花，加蓋微波 2 分鐘',
      '可搭配一顆微波水波蛋拌勻享用',
    ],
  },
  {
    id: 15,
    title: '電鍋火腿起司高麗菜炊飯',
    emoji: '🍚',
    tool: '電鍋',
    minutes: 25,
    ingredients: ['白飯', '火腿', '高麗菜', '起司片'],
    optional: ['起司片'],
    steps: [
      '白飯鋪底，放上切碎的高麗菜與火腿丁，加兩匙水',
      '電鍋外鍋半杯水蒸煮，讓高麗菜甜味滲入米飯',
      '跳起後趁熱鋪上起司片悶 2 分鐘拌勻',
    ],
  },
  {
    id: 16,
    title: '微波番茄起司吐司披薩',
    emoji: '🍕',
    tool: '微波爐',
    minutes: 4,
    ingredients: ['吐司', '番茄', '起司片', '火腿', '舒肥雞胸肉'],
    optional: ['火腿', '舒肥雞胸肉'],
    steps: [
      '番茄切薄片鋪在吐司上，放上火腿丁或雞胸肉絲',
      '最上層鋪滿起司片',
      '微波爐中強火加熱 2–3 分鐘至起司融化牽絲即可',
    ],
  },
  {
    id: 17,
    title: '微波香蕉牛奶馬克杯蛋糕',
    emoji: '🍌',
    tool: '微波爐',
    minutes: 5,
    ingredients: ['香蕉', '牛奶', '雞蛋', '吐司'],
    optional: ['吐司'],
    steps: [
      '過熟香蕉在馬克杯中用叉子壓成泥（越熟越甜，不用另外加糖）',
      '打入雞蛋與牛奶攪拌均勻，可撕入半片吐司增加蛋糕體口感',
      '微波爐中強火加熱 2–3 分鐘至表面澎起熟透即可享用',
    ],
  },
  {
    id: 18,
    title: '電鍋焦糖香蕉布丁吐司',
    emoji: '🍮',
    tool: '電鍋',
    minutes: 15,
    ingredients: ['香蕉', '吐司', '牛奶', '雞蛋'],
    optional: [],
    steps: [
      '吐司切丁鋪在深碗底，擺上切片的熟香蕉',
      '雞蛋與牛奶打勻過篩後倒入碗中，讓吐司吸飽蛋奶液',
      '電鍋外鍋加半杯水蒸至跳起，香蕉果香濃郁、口感綿密',
    ],
  },
  {
    id: 19,
    title: '微波溫熱香蕉蛋奶盅',
    emoji: '🥣',
    tool: '微波爐',
    minutes: 4,
    ingredients: ['香蕉', '牛奶', '雞蛋', '燕麥'],
    optional: ['雞蛋', '燕麥'],
    steps: [
      '熟香蕉切厚片放入深碗，倒入牛奶（可依喜好加燕麥或一顆打散的雞蛋）',
      '微波爐中火分兩段加熱共 3 分鐘，中間取出攪拌一次',
      '香蕉的自然甜味融入熱牛奶，適合當宿舍早餐或宵夜',
    ],
  },
];

// 歷史統計與紀錄（與 backend/seed.py 完全同步：救回 6 樣、省下 NT$245、丟掉 2 樣、救援率 75%）
export function createSeedHistory() {
  const today = getTaipeiTodayStr();
  return {
    rescued_count: 6,
    saved_ntd: 245,
    wasted_count: 2,
    recent: [
      {
        id: 4,
        recipe_title: '微波法式吐司布丁',
        item_names: ['厚片吐司'],
        created_at: `${addDays(today, -1)}T19:30:00+08:00`,
      },
      {
        id: 3,
        recipe_title: '微波起司牛奶燉飯',
        item_names: ['鮮奶'],
        created_at: `${addDays(today, -1)}T15:30:00+08:00`,
      },
      {
        id: 2,
        recipe_title: '電鍋韓式泡菜豆腐鍋',
        item_names: ['板豆腐', '韓式泡菜'],
        created_at: `${addDays(today, -2)}T19:30:00+08:00`,
      },
      {
        id: 1,
        recipe_title: '電鍋黃金蛋炒飯（炊飯版）',
        item_names: ['雞蛋', '隔夜飯'],
        created_at: `${addDays(today, -3)}T19:30:00+08:00`,
      },
    ],
  };
}

function formatUrgencyNote(item, recipe) {
  const daysLeft = Number(item.days_left ?? 99);
  const name = item.name || '食材';
  if (daysLeft < 0) {
    return `其中${name}已過期 ${Math.abs(daysLeft)} 天（已過期，請先確認外觀氣味再使用）`;
  }
  if (daysLeft === 0) return `其中${name}今天到期`;
  if (daysLeft === 1) return `其中${name}明天到期`;
  if (daysLeft <= 3) return `其中${name}剩 ${daysLeft} 天到期`;
  return `只用${recipe.tool} ${recipe.minutes} 分鐘即可完成`;
}

/**
 * 前端規則式推薦演算法（完全對齊 backend/recommend.py 與 docs/API.md v1.1）
 * - 食安規則：days_left < 0 的肉類、海鮮、乳製品、豆腐不列入 uses 與 also_in_fridge
 * - 非高風險過期食材可推薦，但 reason 必定附加「已過期，請先確認外觀氣味再使用」
 * - 冰箱現有但未勾選的食材放入 also_in_fridge，不列入 missing
 */
export function computeRuleSuggestions(allInFridgeItems, selectedItemIds, limit = 5) {
  const selectedSet = new Set(selectedItemIds);
  const selectedItems = allInFridgeItems.filter((it) => selectedSet.has(it.id));
  const safeSelectedItems = selectedItems.filter((it) => !isExpiredUnsafe(it));

  if (safeSelectedItems.length === 0) {
    return [];
  }

  const otherFridgeItems = allInFridgeItems.filter(
    (it) => !selectedSet.has(it.id) && it.status === 'in_fridge' && !isExpiredUnsafe(it)
  );

  const scored = [];
  const usedRecipeIds = new Set();

  for (const recipe of SEED_RECIPES) {
    const recipeIngs = recipe.ingredients ?? [];
    const optionalIngs = recipe.optional ?? [];

    const matchedSelected = [];
    const uses = [];
    const uses_item_ids = [];

    for (const sItem of safeSelectedItems) {
      if (recipeIngs.some((rIng) => ingredientsMatch(sItem.name, rIng))) {
        matchedSelected.push(sItem);
        uses_item_ids.push(sItem.id);
        if (!uses.includes(sItem.name)) {
          uses.push(sItem.name);
        }
      }
    }

    if (matchedSelected.length === 0) continue;

    const also_in_fridge = [];
    const alsoIds = new Set();
    const missing = [];
    const matchedOtherExpiring = [];

    for (const rIng of recipeIngs) {
      if (matchedSelected.some((sItem) => ingredientsMatch(sItem.name, rIng))) {
        continue;
      }

      const otherMatches = otherFridgeItems.filter((oItem) =>
        ingredientsMatch(oItem.name, rIng)
      );
      if (otherMatches.length > 0) {
        for (const oItem of otherMatches) {
          if (!alsoIds.has(oItem.id)) {
            alsoIds.add(oItem.id);
            also_in_fridge.push({
              id: oItem.id,
              name: oItem.name,
              days_left: oItem.days_left,
            });
          }
          if (oItem.days_left <= 3 && !matchedOtherExpiring.includes(oItem)) {
            matchedOtherExpiring.push(oItem);
          }
        }
        continue;
      }

      const isOptional = optionalIngs.some((opt) => ingredientsMatch(opt, rIng));
      if (!isOptional) {
        missing.push(rIng);
      }
    }

    let rawScore = 27 + 30 * matchedSelected.length;
    for (const sItem of matchedSelected) {
      if (sItem.days_left <= 1) rawScore += 10;
      else if (sItem.days_left <= 3) rawScore += 5;
    }
    rawScore -= 15 * missing.length;
    rawScore += 5 * matchedOtherExpiring.length;

    const score = Math.max(0, Math.min(100, rawScore));

    const sortedMatched = [...matchedSelected].sort((a, b) => a.days_left - b.days_left);
    const mostUrgent = sortedMatched[0];
    const urgencyNote = formatUrgencyNote(mostUrgent, recipe);

    const hasExpiringSelected = matchedSelected.some((x) => x.days_left <= 3);
    let reason = hasExpiringSelected
      ? `用掉 ${matchedSelected.length} 樣快過期食材，${urgencyNote}`
      : `用掉 ${matchedSelected.length} 樣勾選食材，${urgencyNote}`;

    if (matchedOtherExpiring.length > 0) {
      const extraNames = matchedOtherExpiring
        .slice(0, 2)
        .map((it) => it.name)
        .join('、');
      reason += `（還能順便用掉冰箱裡的${extraNames}）`;
    }

    const hasExpiredUsed =
      matchedSelected.some((x) => x.days_left < 0) ||
      also_in_fridge.some((x) => x.days_left < 0);
    if (hasExpiredUsed && !reason.includes('已過期，請先確認外觀氣味再使用')) {
      reason += '（已過期，請先確認外觀氣味再使用）';
    }

    scored.push({
      sortKey: [score, matchedSelected.length, -missing.length, -(recipe.minutes || 30)],
      entry: {
        recipe,
        uses,
        uses_item_ids,
        also_in_fridge,
        missing,
        score,
        reason,
      },
    });
    usedRecipeIds.add(recipe.id);
  }

  scored.sort((a, b) => {
    for (let i = 0; i < a.sortKey.length; i += 1) {
      if (b.sortKey[i] !== a.sortKey[i]) return b.sortKey[i] - a.sortKey[i];
    }
    return 0;
  });

  const topEntries = scored.slice(0, limit).map((s) => s.entry);

  // 若少於 3 道（例如使用者新增罕見自訂食材），以百搭宿舍鍋物／炊飯補齊 3 道
  if (topEntries.length < 3 && safeSelectedItems.length > 0) {
    const fallbackTitles = new Set([
      '電鍋韓式泡菜豆腐鍋',
      '電鍋番茄蔬菜豆腐湯餃',
      '微波泡菜起司烏龍麵',
      '電鍋黃金蛋炒飯（炊飯版）',
    ]);
    const primaryItem = [...safeSelectedItems].sort((a, b) => a.days_left - b.days_left)[0];

    for (const recipe of SEED_RECIPES) {
      if (topEntries.length >= 3) break;
      if (usedRecipeIds.has(recipe.id)) continue;
      if (!fallbackTitles.has(recipe.title)) continue;

      const fbAlso = [];
      const fbAlsoIds = new Set();
      for (const rIng of recipe.ingredients ?? []) {
        for (const oItem of otherFridgeItems) {
          if (!fbAlsoIds.has(oItem.id) && ingredientsMatch(oItem.name, rIng)) {
            fbAlsoIds.add(oItem.id);
            fbAlso.push({
              id: oItem.id,
              name: oItem.name,
              days_left: oItem.days_left,
            });
          }
        }
      }

      const urgencyNote = formatUrgencyNote(primaryItem, recipe);
      let fbReason = `百搭宿舍${recipe.tool}料理，可加入${primaryItem.name}一起烹調（${urgencyNote}）`;
      const hasExpired =
        primaryItem.days_left < 0 || fbAlso.some((x) => x.days_left < 0);
      if (hasExpired && !fbReason.includes('已過期，請先確認外觀氣味再使用')) {
        fbReason += '（已過期，請先確認外觀氣味再使用）';
      }

      topEntries.push({
        recipe,
        uses: [primaryItem.name],
        uses_item_ids: [primaryItem.id],
        also_in_fridge: fbAlso,
        missing: [],
        score: Math.max(55, 65 - topEntries.length * 5),
        reason: fbReason,
      });
      usedRecipeIds.add(recipe.id);
    }
  }

  return topEntries.slice(0, limit);
}
