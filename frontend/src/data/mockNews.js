export const mockNewsItems = [
  {
    id: 'n1',
    title: 'Fed holds rates but signals potential cut in Q4',
    source: 'Reuters',
    url: 'https://example.com/fed-q4',
    publishedAt: new Date().toISOString(),
    whatHappened: 'The Federal Reserve kept rates unchanged.',
    whyItMatters: 'Rate path impacts equity valuations and credit spreads.',
    portfolioImpact: 'Mildly supportive for duration; neutral equities.',
    impact: 'neutral', // 'up' | 'down' | 'neutral'
    tags: ['Macro', 'Rates', 'US'],
    approved: true,
  },
  {
    id: 'n2',
    title: 'CEO exits at MegaTech; interim leadership announced',
    source: 'Bloomberg',
    url: 'https://example.com/megatech-ceo',
    publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    whatHappened: 'MegaTech CEO resigns effective immediately.',
    whyItMatters: 'Leadership turnover can drive volatility and repricing.',
    portfolioImpact: 'Short‑term uncertainty; watch governance signals.',
    impact: 'down',
    tags: ['Equities', 'Technology', 'US'],
    approved: false,
  },
  {
    id: 'n3',
    title: 'Eurozone PMI surprises to upside',
    source: 'FT',
    url: 'https://example.com/ez-pmi',
    publishedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    whatHappened: 'Manufacturing PMI rose above expectations.',
    whyItMatters: 'Improving activity supports cyclical assets.',
    portfolioImpact: 'Constructive for EU equities and EUR.',
    impact: 'up',
    tags: ['Macro', 'Europe'],
    approved: true,
  },
  {
    id: 'n4',
    title: 'BankCo beats earnings; raises FY guidance',
    source: 'Company Filing',
    url: 'https://example.com/bank-earnings',
    publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    whatHappened: 'EPS beat by 8% and guidance raised.',
    whyItMatters: 'Signals resilient NII and fee income.',
    portfolioImpact: 'Positive for financials; tilt to quality.',
    impact: 'up',
    tags: ['Equities', 'Financials'],
    approved: true,
  },
  {
    id: 'n5',
    title: 'Oil spikes on supply disruption headlines',
    source: 'WSJ',
    url: 'https://example.com/oil-supply',
    publishedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    whatHappened: 'Temporary disruption tightens supply.',
    whyItMatters: "Energy prices feed into inflation and margins.",
    portfolioImpact: 'Supports energy; headwind for rate‑sensitives.',
    impact: 'up',
    tags: ['Commodities', 'Energy', 'Global'],
    approved: false,
  },
  {
    id: 'n6',
    title: 'Tech index pulls back after multi‑month rally',
    source: 'CNBC',
    url: 'https://example.com/tech-pullback',
    publishedAt: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
    whatHappened: 'Profit‑taking drives sector‑wide decline.',
    whyItMatters: 'Valuation sensitivity remains a risk.',
    portfolioImpact: 'Stay balanced; use dips selectively.',
    impact: 'down',
    tags: ['Equities', 'Technology', 'Global'],
    approved: false,
  },
  {
    id: 'n7',
    title: 'Central bank widens QE program',
    source: 'Local News',
    url: 'https://example.com/qe',
    publishedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    whatHappened: 'Asset purchase program expanded modestly.',
    whyItMatters: 'Liquidity support can buoy risk assets.',
    portfolioImpact: 'Constructive for duration and credit.',
    impact: 'up',
    tags: ['Macro', 'APAC'],
    approved: true,
  },
  {
    id: 'n8',
    title: 'Utilities underperform as yields tick higher',
    source: 'MarketWatch',
    url: 'https://example.com/utilities-yields',
    publishedAt: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
    whatHappened: 'Higher real yields weigh on defensives.',
    whyItMatters: 'Rate sensitivity key for sector allocation.',
    portfolioImpact: 'Underweight utilities; review duration hedges.',
    impact: 'down',
    tags: ['Equities', 'Rates'],
    approved: false,
  },
];

export function isToday(isoStr) {
  const d = new Date(isoStr);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

export function isWithinLastDays(isoStr, days) {
  const d = new Date(isoStr).getTime();
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  return d >= cutoff;
} 