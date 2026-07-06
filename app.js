const fallbackUpcomingMatches = [
  {
    id: "m1",
    league: "Premier League",
    kickoff: "今晚 22:00",
    home: "Arsenal",
    away: "Chelsea",
    homeElo: 1885,
    awayElo: 1780,
    odds: { home: 1.82, draw: 3.75, away: 4.4, over25: 1.86, btts: 1.74 },
  },
  {
    id: "m2",
    league: "La Liga",
    kickoff: "明日 03:00",
    home: "Sevilla",
    away: "Valencia",
    homeElo: 1692,
    awayElo: 1708,
    odds: { home: 2.48, draw: 3.25, away: 2.88, over25: 2.06, btts: 1.93 },
  },
  {
    id: "m3",
    league: "Serie A",
    kickoff: "明日 01:30",
    home: "Roma",
    away: "Lazio",
    homeElo: 1765,
    awayElo: 1748,
    odds: { home: 2.23, draw: 3.3, away: 3.25, over25: 1.95, btts: 1.82 },
  },
  {
    id: "m4",
    league: "J League",
    kickoff: "週三 18:00",
    home: "Yokohama F. Marinos",
    away: "Kawasaki Frontale",
    homeElo: 1620,
    awayElo: 1658,
    odds: { home: 2.72, draw: 3.55, away: 2.42, over25: 1.68, btts: 1.58 },
  },
  {
    id: "m5",
    league: "MLS",
    kickoff: "週四 08:30",
    home: "Austin FC",
    away: "Seattle Sounders",
    homeElo: 1515,
    awayElo: 1598,
    odds: { home: 2.95, draw: 3.42, away: 2.36, over25: 1.78, btts: 1.65 },
  },
  {
    id: "m6",
    league: "K League",
    kickoff: "週四 19:00",
    home: "Ulsan HD",
    away: "Jeonbuk",
    homeElo: 1668,
    awayElo: 1602,
    odds: { home: 2.02, draw: 3.18, away: 3.86, over25: 2.12, btts: 1.97 },
  },
];

const fallbackSettledMatches = [
  ["2026-06-01", "Arsenal", "Tottenham", 1872, 1790, { home: 1.95, draw: 3.55, away: 3.8 }, "home"],
  ["2026-06-02", "Chelsea", "Everton", 1772, 1640, { home: 1.7, draw: 3.85, away: 4.9 }, "draw"],
  ["2026-06-03", "Milan", "Roma", 1810, 1760, { home: 2.05, draw: 3.25, away: 3.75 }, "home"],
  ["2026-06-04", "Lazio", "Napoli", 1740, 1832, { home: 3.05, draw: 3.35, away: 2.32 }, "away"],
  ["2026-06-05", "Valencia", "Sevilla", 1708, 1692, { home: 2.34, draw: 3.18, away: 3.15 }, "home"],
  ["2026-06-06", "Dortmund", "Leipzig", 1844, 1822, { home: 2.18, draw: 3.62, away: 3.05 }, "away"],
  ["2026-06-07", "Ulsan HD", "Pohang", 1660, 1580, { home: 1.88, draw: 3.4, away: 4.1 }, "home"],
  ["2026-06-08", "Seattle", "Austin", 1598, 1515, { home: 1.82, draw: 3.6, away: 4.2 }, "home"],
  ["2026-06-09", "Kawasaki", "Yokohama", 1658, 1620, { home: 2.1, draw: 3.5, away: 3.28 }, "draw"],
  ["2026-06-10", "Jeonbuk", "Daegu", 1602, 1540, { home: 1.98, draw: 3.2, away: 3.95 }, "home"],
  ["2026-06-11", "Roma", "Inter", 1765, 1876, { home: 3.1, draw: 3.3, away: 2.28 }, "away"],
  ["2026-06-12", "Sevilla", "Betis", 1692, 1712, { home: 2.55, draw: 3.15, away: 2.82 }, "draw"],
].map(([date, home, away, homeElo, awayElo, odds, result], index) => ({
  id: `h${index}`,
  date,
  home,
  away,
  homeElo,
  awayElo,
  odds,
  result,
}));

const generatedData = window.PREDICTOR_DATA || null;
const upcomingMatches = generatedData
  ? generatedData.predictions.map((item) => ({ ...item, precomputed: item.prediction }))
  : fallbackUpcomingMatches;
const settledMatches = generatedData ? generatedData.backtest : fallbackSettledMatches;

const fmt = new Intl.NumberFormat("zh-TW", { style: "percent", maximumFractionDigits: 1 });
const num = new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 2 });
let activeQualityFilter = "all";
let activeSportFilter = "all";
let activeBacktestFilter = "all";
let backtestSortMode = "latest";
let backtestPage = 1;
const backtestPageSize = 10;

const sportLabels = {
  all: "全部",
  soccer: "足球",
  basketball: "籃球",
  baseball: "棒球",
  esports: "電競",
  football: "美足",
  hockey: "冰球",
  cricket: "足球",
  tennis: "網球",
  mma: "格鬥",
  boxing: "拳擊",
  rugby: "橄欖球",
  mixed: "其他",
};

const teamZh = {
  Afghanistan: "阿富汗",
  Argentina: "阿根廷",
  Australia: "澳洲",
  Austria: "奧地利",
  Belgium: "比利時",
  Brazil: "巴西",
  Canada: "加拿大",
  Chile: "智利",
  China: "中國",
  Colombia: "哥倫比亞",
  Croatia: "克羅埃西亞",
  Denmark: "丹麥",
  Ecuador: "厄瓜多",
  Egypt: "埃及",
  England: "英格蘭",
  France: "法國",
  Germany: "德國",
  Ghana: "迦納",
  India: "印度",
  Iran: "伊朗",
  Ireland: "愛爾蘭",
  Italy: "義大利",
  Japan: "日本",
  Mexico: "墨西哥",
  Morocco: "摩洛哥",
  Netherlands: "荷蘭",
  "New Zealand": "紐西蘭",
  Nigeria: "奈及利亞",
  Norway: "挪威",
  Pakistan: "巴基斯坦",
  Paraguay: "巴拉圭",
  Poland: "波蘭",
  Portugal: "葡萄牙",
  Qatar: "卡達",
  Scotland: "蘇格蘭",
  Senegal: "塞內加爾",
  Serbia: "塞爾維亞",
  Spain: "西班牙",
  "South Africa": "南非",
  "Sri Lanka": "斯里蘭卡",
  Sweden: "瑞典",
  Switzerland: "瑞士",
  Tunisia: "突尼西亞",
  Turkey: "土耳其",
  Ukraine: "烏克蘭",
  Uruguay: "烏拉圭",
  USA: "美國",
  "United States": "美國",
  Wales: "威爾斯",
  "West Indies": "西印度群島",
  Arsenal: "兵工廠",
  Chelsea: "切爾西",
  "Man City": "曼城",
  "Manchester City": "曼城",
  Liverpool: "利物浦",
  "Real Madrid": "皇家馬德里",
  Barcelona: "巴塞隆納",
  Inter: "國際米蘭",
  Milan: "AC 米蘭",
  "Bayern Munich": "拜仁慕尼黑",
  Dortmund: "多特蒙德",
  "Paris SG": "巴黎聖日耳曼",
  Marseille: "馬賽",
  "New York Yankees": "紐約洋基",
  "Boston Red Sox": "波士頓紅襪",
  "Los Angeles Dodgers": "洛杉磯道奇",
  "San Francisco Giants": "舊金山巨人",
  "New York Mets": "紐約大都會",
  "Philadelphia Phillies": "費城費城人",
  "T1": "T1",
  "Gen.G": "Gen.G",
};

const leagueZh = {
  "One Day Internationals": "單日國際賽",
  "International Twenty20": "國際 Twenty20",
  "T20 Blast": "T20 Blast",
  "Test Matches": "國際測試賽",
  "FIFA World Cup": "世界盃",
  "FIFA World Cup Winner": "世界盃冠軍",
  "EPL": "英超",
  "Premier League": "英超",
  "La Liga": "西甲",
  "Serie A": "義甲",
  "Bundesliga": "德甲",
  "Ligue 1": "法甲",
  "MLB": "美國職棒 MLB",
  "WNBA": "美國女子職籃 WNBA",
  "NBA Summer League": "NBA 夏季聯賽",
  "CFL": "加拿大美式足球 CFL",
  "NCAAF": "美國大學美足 NCAAF",
  "NFL": "NFL 美式足球",
  "NFL Preseason": "NFL 季前賽",
  "AFL": "澳式足球 AFL",
  "MMA": "綜合格鬥 MMA",
  "Boxing": "拳擊",
  "ATP Wimbledon": "溫布頓 ATP",
  "WTA Wimbledon": "溫布頓 WTA",
};

function zhTeam(name) {
  return teamZh[name] || name;
}

function zhLeague(name) {
  return leagueZh[name] || name || "";
}

function formatKickoff(value) {
  if (!value || !/^\d{4}-\d{2}-\d{2}T/.test(value)) return value || "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-TW", {
    timeZone: "Asia/Taipei",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function isFutureMatch(match) {
  const value = match.kickoff || "";
  if (!/^\d{4}-\d{2}-\d{2}T/.test(value)) return true;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return true;
  return date.getTime() > Date.now();
}

function sportOf(match) {
  if (match.sport) return match.sport;
  return (match.league || "").toLowerCase().includes("mlb") ? "baseball" : "soccer";
}

function marketLabel(match, market) {
  if (!market) return "";
  if (market.key === "home") return `${zhTeam(match.home)} 勝`;
  if (market.key === "away") return `${zhTeam(match.away)} 勝`;
  if (market.key === "draw") return "和局";
  if (market.key === "over25") return "大 2.5";
  if (market.key === "btts") return "雙方進球";
  return market.label;
}

function sportLeagueLabel(match) {
  return `${sportLabels[sportOf(match)] || sportOf(match)} · ${zhLeague(match.league)}`;
}

function resultSportOf(item) {
  const key = item.sport_key || "";
  if (key.startsWith("soccer_")) return "soccer";
  if (key.startsWith("baseball_")) return "baseball";
  if (key.startsWith("tennis_")) return "tennis";
  if (key.startsWith("esports_")) return "esports";
  if (key.startsWith("cricket_")) return "soccer";
  return item.sport || "soccer";
}

function settledSportLabel(item) {
  return `${sportLabels[resultSportOf(item)] || resultSportOf(item)} · ${zhLeague(item.sport_title || item.league)}`;
}

function valueText(match, p) {
  if (!p.best || p.best.ev < 0.04) return "無明顯價值";
  return `${marketLabel(match, p.best)}`;
}

function signedPct(value) {
  const number = Number(value || 0);
  const sign = number > 0 ? "+" : "";
  return `${sign}${pct(number)}`;
}

function factorRows(p) {
  const factors = p.factors;
  if (!factors) return '<p class="muted-line">尚未輸入傷兵/狀態資料。</p>';
  const rows = [factors.home, factors.away].map((factor) => `
    <div class="factor-row">
      <b>${zhTeam(factor.team)}</b>
      <span>傷兵 ${signedPct(factor.injuryImpact)}</span>
      <span>狀態 ${signedPct(factor.formImpact)}</span>
      <span>休息 ${factor.restDays ?? "?"} 天</span>
      <span>旅途 ${signedPct(factor.travelImpact)}</span>
      ${factor.notes ? `<small>${factor.notes}</small>` : ""}
      ${factor.source ? `<small>來源：${factor.source}${factor.updatedAt ? ` · ${factor.updatedAt}` : ""}</small>` : ""}
    </div>
  `);
  const adj = p.factorAdjustment;
  const edge = adj?.applied ? `<p class="muted-line">因素調整 edge：${signedPct(adj.edge)}，已反映到勝率。</p>` : '<p class="muted-line">目前因素分數接近，未調整勝率。</p>';
  return `${edge}<div class="factor-list">${rows.join("")}</div>`;
}

function poisson(k, lambda) {
  let factorial = 1;
  for (let i = 2; i <= k; i += 1) factorial *= i;
  return (Math.E ** -lambda * lambda ** k) / factorial;
}

function normalize(raw) {
  const total = raw.home + raw.draw + raw.away;
  return {
    home: raw.home / total,
    draw: raw.draw / total,
    away: raw.away / total,
  };
}

function predict(match) {
  if (match.precomputed) return match.precomputed;
  if (match.prediction) return match.prediction;

  const homeAdv = 70;
  const diff = match.homeElo + homeAdv - match.awayElo;
  const homeBase = 1 / (1 + 10 ** (-diff / 400));
  const draw = Math.max(0.18, 0.29 - Math.abs(diff) / 1600);
  const probs = normalize({
    home: homeBase * (1 - draw),
    draw,
    away: (1 - homeBase) * (1 - draw),
  });

  const homeGoals = Math.max(0.55, 1.34 + diff / 360);
  const awayGoals = Math.max(0.45, 1.12 - diff / 520);
  const scoreGrid = [];
  let over25 = 0;
  let btts = 0;

  for (let h = 0; h <= 4; h += 1) {
    for (let a = 0; a <= 4; a += 1) {
      const prob = poisson(h, homeGoals) * poisson(a, awayGoals);
      if (h + a > 2.5) over25 += prob;
      if (h > 0 && a > 0) btts += prob;
      scoreGrid.push({ score: `${h}-${a}`, prob });
    }
  }

  scoreGrid.sort((a, b) => b.prob - a.prob);

  const markets = [
    { key: "home", label: `${match.home} 勝`, prob: probs.home, odds: match.odds.home },
    { key: "draw", label: "和局", prob: probs.draw, odds: match.odds.draw },
    { key: "away", label: `${match.away} 勝`, prob: probs.away, odds: match.odds.away },
  ];

  if (match.odds.over25) {
    markets.push({ key: "over25", label: "大 2.5", prob: over25, odds: match.odds.over25 });
  }
  if (match.odds.btts) {
    markets.push({ key: "btts", label: "雙方進球", prob: btts, odds: match.odds.btts });
  }

  const best = markets
    .map((market) => ({ ...market, ev: market.prob * market.odds - 1 }))
    .sort((a, b) => b.ev - a.ev)[0];

  const topSide = markets.slice(0, 3).sort((a, b) => b.prob - a.prob)[0];
  const confidence = topSide.prob;
  const tier = confidence >= 0.58 ? "high" : confidence >= 0.48 ? "medium" : "low";

  return {
    probs,
    homeGoals,
    awayGoals,
    over25,
    btts,
    scoreGrid,
    best,
    topSide,
    confidence,
    tier,
    isValue: best.ev >= 0.08,
  };
}

function pct(value) {
  return fmt.format(value || 0);
}

function renderSportFilters() {
  const holder = document.querySelector("#sportFilters");
  const preferred = ["soccer", "basketball", "baseball", "esports"];
  const available = new Set(upcomingMatches.filter(isFutureMatch).map((match) => sportOf(match)));
  const sports = ["all", ...preferred, ...[...available].filter((sport) => !preferred.includes(sport))];
  holder.innerHTML = sports
    .map((sport) => `<button class="sport-chip ${sport === activeSportFilter ? "active" : ""}" data-sport="${sport}">${sportLabels[sport] || sport}</button>`)
    .join("");
}

function renderBacktestFilters() {
  const holder = document.querySelector("#backtestFilters");
  const settled = generatedData?.settledResults || [];
  const available = new Set([
    ...settledMatches.map((match) => sportOf(match)),
    ...settled.map((item) => resultSportOf(item)),
  ]);
  const preferred = ["all", "soccer", "basketball", "baseball", "esports", "tennis"];
  const filters = [...preferred, ...[...available].filter((sport) => !preferred.includes(sport))];
  holder.innerHTML = filters
    .map((sport) => `<button class="sport-chip ${sport === activeBacktestFilter ? "active" : ""}" data-backtest-sport="${sport}">${sportLabels[sport] || sport}</button>`)
    .join("");
}

function renderPredictions() {
  const grid = document.querySelector("#matchGrid");
  const cards = upcomingMatches
    .filter(isFutureMatch)
    .map((match) => ({ match, p: predict(match) }))
    .filter(({ match, p }) => {
      if (activeSportFilter !== "all" && sportOf(match) !== activeSportFilter) return false;
      if (activeQualityFilter === "value") return p.isValue;
      if (activeQualityFilter === "high") return p.tier === "high";
      return true;
    });

  grid.innerHTML = cards
    .map(({ match, p }) => `
      <article class="match-card">
        <div class="match-head">
          <div>
            <div class="league">${sportLeagueLabel(match)}</div>
            <div class="teams">${zhTeam(match.home)}<br />${zhTeam(match.away)}</div>
          </div>
          <div class="kickoff">${formatKickoff(match.kickoff)}</div>
        </div>
        <div class="badges">
          <span class="badge ${p.tier}">${p.tier === "high" ? "高信心" : p.tier === "medium" ? "中信心" : "觀察"}</span>
          ${p.isValue ? '<span class="badge value">價值單</span>' : ""}
        </div>
        <div class="prob-row ${p.probs.draw === undefined ? "two-way" : ""}">
          <div class="prob-box"><strong>${pct(p.probs.home)}</strong><span>主勝</span></div>
          ${p.probs.draw === undefined ? "" : '<div class="prob-box"><strong>' + pct(p.probs.draw) + '</strong><span>和局</span></div>'}
          <div class="prob-box"><strong>${pct(p.probs.away)}</strong><span>客勝</span></div>
        </div>
        <div class="pick-line">
          <div>
            <span class="league">勝率最高</span><br />
            <b>${marketLabel(match, p.topSide)}</b> <span class="league">${pct(p.topSide.prob)}</span>
            <br />
            <span class="league">價值方向：${valueText(match, p)}</span>
          </div>
          <button class="details-btn" data-match="${match.id}">細節</button>
        </div>
      </article>
    `)
    .join("");

  if (!cards.length) {
    const label = sportLabels[activeSportFilter] || activeSportFilter;
    grid.innerHTML = `<article class="match-card">目前沒有${activeSportFilter === "all" ? "" : label}符合條件的比賽。</article>`;
  }
}

function renderBacktest() {
  const rows = settledMatches.map((match, index) => {
    const p = predict(match);
    const pick = p.topSide;
    const won = pick.key === match.result;
    return { match, p, pick, won, index };
  });

  const filteredRows = activeBacktestFilter === "all" ? rows : rows.filter((row) => sportOf(row.match) === activeBacktestFilter);
  const settledResults = (generatedData?.settledResults || []).filter((item) => activeBacktestFilter === "all" || resultSportOf(item) === activeBacktestFilter);
  const snapshotBacktest = (generatedData?.snapshotBacktest || []).filter((item) => activeBacktestFilter === "all" || (item.sport || "soccer") === activeBacktestFilter);
  const m = activeBacktestFilter === "all" ? generatedData?.metrics : null;
  let statItems;
  if (m) {
    statItems = [
      ["測試場次", `${m.matches} 場`],
      ["總命中率", pct(m.accuracy)],
      ["高信心", m.highConfidence?.accuracy ? `${pct(m.highConfidence.accuracy)} (${m.highConfidence.matches})` : "無"],
      ["Log Loss", m.logLoss],
      ["平注 ROI", pct(m.roi)],
      ["價值單 ROI", m.valueRoi === null ? "無" : pct(m.valueRoi)],
      ["真實快照回測", `${generatedData?.snapshotBacktest?.length || 0} 筆`],
      ["已完賽結果", `${generatedData?.settledResults?.length || 0} 筆`],
    ];
  } else {
    const total = filteredRows.length;
    const wins = filteredRows.filter((row) => row.won).length;
    const high = filteredRows.filter((row) => row.p.tier === "high");
    const highWins = high.filter((row) => row.won).length;
    const valueRows = filteredRows.filter((row) => row.p.best.ev >= 0.08);
    const profit = filteredRows.reduce((sum, row) => sum + (row.won ? row.pick.odds - 1 : -1), 0);
    statItems = [
      ["回測場次", `${total} 場`],
      ["總命中率", total ? pct(wins / total) : "無"],
      ["高信心", high.length ? `${pct(highWins / high.length)} (${highWins}/${high.length})` : "無"],
      ["價值單數", `${valueRows.length} 場`],
      ["平注 ROI", total ? pct(profit / total) : "無"],
      ["真實快照回測", `${snapshotBacktest.length} 筆`],
      ["已完賽結果", `${settledResults.length} 筆`],
    ];
  }

  document.querySelector("#backtestStats").innerHTML = statItems
    .map(([label, value]) => `<div class="stat-card"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");

  const resultRows = settledResults.map((item, index) => ({
    kind: "result",
    index: rows.length + index,
    match: {
      date: (item.commence_time || "").slice(0, 10),
      league: item.sport_title,
      home: item.home,
      away: item.away,
      score: `${item.home_score}-${item.away_score}`,
      result: item.result,
      sport: resultSportOf(item),
    },
    item,
  }));
  const snapshotRows = snapshotBacktest.map((item, index) => ({
    kind: "snapshot",
    index: rows.length + resultRows.length + index,
    match: {
      date: (item.kickoff || "").slice(0, 10),
      league: item.league,
      home: item.home,
      away: item.away,
      score: item.score,
      result: item.result,
      sport: item.sport,
    },
    item,
  }));
  const combinedRows = [
    ...filteredRows.map((row) => ({ ...row, kind: "backtest" })),
    ...snapshotRows,
    ...resultRows,
  ];
  const sortedRows = combinedRows.sort((a, b) => {
    if (backtestSortMode === "oldest") return new Date(a.match.date) - new Date(b.match.date);
    if (backtestSortMode === "restore") return b.index - a.index;
    return new Date(b.match.date) - new Date(a.match.date);
  });
  const totalPages = Math.max(1, Math.ceil(sortedRows.length / backtestPageSize));
  backtestPage = Math.min(Math.max(1, backtestPage), totalPages);
  const visibleRows = sortedRows.slice((backtestPage - 1) * backtestPageSize, backtestPage * backtestPageSize);
  const sortIcon = document.querySelector("#dateSortIcon");
  if (sortIcon) {
    sortIcon.textContent = backtestSortMode === "oldest" ? "↑" : backtestSortMode === "restore" ? "↕" : "↓";
  }

  document.querySelector("#historyRows").innerHTML = visibleRows
    .map(({ match, p, pick, won, kind, item }) => kind === "snapshot" ? `
      <tr>
        <td>${match.date}</td>
        <td><span class="league">${sportLeagueLabel(match)} · 快照</span><br />${zhTeam(match.home)} vs ${zhTeam(match.away)}</td>
        <td>${marketLabel(match, { key: item.pick_key, label: item.pick_label })}</td>
        <td>${item.pick_prob ? pct(Number(item.pick_prob)) : "—"}</td>
        <td class="${item.won === "true" ? "win" : "loss"}">${item.won === "true" ? "命中" : "未中"} (${match.result}${match.score ? ` ${match.score}` : ""})</td>
      </tr>
    ` : kind === "result" ? `
      <tr>
        <td>${match.date}</td>
        <td><span class="league">${settledSportLabel(item)}</span><br />${zhTeam(match.home)} vs ${zhTeam(match.away)}</td>
        <td>已完賽結果</td>
        <td>—</td>
        <td>${match.result} ${match.score ? `(${match.score})` : ""}</td>
      </tr>
    ` : `
      <tr>
        <td>${match.date}</td>
        <td><span class="league">${sportLeagueLabel(match)}</span><br />${zhTeam(match.home)} vs ${zhTeam(match.away)}</td>
        <td>${marketLabel(match, pick)}</td>
        <td>${pct(p.confidence)}</td>
        <td class="${won ? "win" : "loss"}">${won ? "命中" : "未中"} (${match.result}${match.score ? ` ${match.score}` : ""})</td>
      </tr>
    `)
    .join("");

  document.querySelector("#backtestPager").innerHTML = `
    <button type="button" data-page="prev" ${backtestPage <= 1 ? "disabled" : ""}>上一頁</button>
    <span>第 ${backtestPage} / ${totalPages} 頁 · 共 ${sortedRows.length} 筆</span>
    <button type="button" data-page="next" ${backtestPage >= totalPages ? "disabled" : ""}>下一頁</button>
  `;
}

function openDetails(matchId) {
  const match = upcomingMatches.find((item) => item.id === matchId);
  if (!match) return;
  const p = predict(match);
  const expectedHome = p.expectedHomeGoals ?? p.homeGoals;
  const expectedAway = p.expectedAwayGoals ?? p.awayGoals;
  const isSoccer = sportOf(match) === "soccer";
  const topSideLabel = marketLabel(match, p.topSide);
  const soccerDetails = isSoccer
    ? `
      <p><b>預期進球：</b>${zhTeam(match.home)} ${num.format(expectedHome)}，${zhTeam(match.away)} ${num.format(expectedAway)}</p>
      <p><b>大小分：</b>大 2.5 ${pct(p.over25)}，BTTS ${pct(p.btts)}</p>
      <p><b>最可能比分：</b>${p.scoreGrid[0].score} (${pct(p.scoreGrid[0].prob)})</p>
    `
    : `
      <p><b>模型勝率：</b>${zhTeam(match.home)} ${pct(p.probs.home)}，${zhTeam(match.away)} ${pct(p.probs.away)}</p>
      <p><b>最高勝率：</b>${topSideLabel} (${pct(p.topSide.prob)})</p>
    `;
  const drawer = document.querySelector("#drawer");
  drawer.classList.add("open");
  drawer.innerHTML = `
    <div class="drawer-head">
      <div>
        <p class="eyebrow">${zhLeague(match.league)}</p>
        <h3>${zhTeam(match.home)} vs ${zhTeam(match.away)}</h3>
      </div>
      <button class="details-btn" id="closeDrawer">關閉</button>
    </div>
    <div class="drawer-body">
      <p><b>勝率最高：</b>${marketLabel(match, p.topSide)}，${pct(p.topSide.prob)}</p>
      <p><b>價值方向：</b>${valueText(match, p)}${p.best ? `，最佳 EV ${pct(p.best.ev)}` : ""}</p>
      ${soccerDetails}
      <div class="factor-box">
        <b>客觀因素</b>
        ${factorRows(p)}
      </div>
      ${isSoccer ? `<div class="score-grid">
        ${p.scoreGrid.slice(0, 10).map((item) => `<div class="score-cell"><b>${item.score}</b>${pct(item.prob)}</div>`).join("")}
      </div>` : ""}
    </div>
  `;
  document.querySelector("#closeDrawer").addEventListener("click", () => drawer.classList.remove("open"));
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.view}`).classList.add("active");
  });
});

document.querySelectorAll(".seg").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".seg").forEach((seg) => seg.classList.remove("active"));
    button.classList.add("active");
    activeQualityFilter = button.dataset.filter;
    renderPredictions();
  });
});

document.querySelector("#sportFilters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-sport]");
  if (!button) return;
  activeSportFilter = button.dataset.sport;
  document.querySelectorAll(".sport-chip").forEach((chip) => chip.classList.remove("active"));
  button.classList.add("active");
  renderPredictions();
});

document.querySelector("#backtestFilters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-backtest-sport]");
  if (!button) return;
  activeBacktestFilter = button.dataset.backtestSport;
  backtestPage = 1;
  document.querySelectorAll("[data-backtest-sport]").forEach((chip) => chip.classList.remove("active"));
  button.classList.add("active");
  renderBacktest();
});

document.querySelector("#dateSortBtn").addEventListener("click", () => {
  backtestSortMode = backtestSortMode === "latest" ? "oldest" : backtestSortMode === "oldest" ? "restore" : "latest";
  backtestPage = 1;
  renderBacktest();
});

document.querySelector("#backtestPager").addEventListener("click", (event) => {
  const button = event.target.closest("[data-page]");
  if (!button || button.disabled) return;
  backtestPage += button.dataset.page === "next" ? 1 : -1;
  renderBacktest();
});

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-match]");
  if (button) openDetails(button.dataset.match);
});

renderSportFilters();
renderBacktestFilters();
renderPredictions();
renderBacktest();
