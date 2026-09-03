'use client';

import { useEffect, useMemo, useState } from 'react';
import { Bookmark, ExternalLink, Search, SlidersHorizontal, X } from 'lucide-react';

type Paper = {
  id: number;
  doi: string;
  journal: string;
  title: string;
  abstract: string;
  first_author: string;
  published_date: string;
  url: string;
  score: number;
  reason: string;
};

type Topic = 'all' | 'cartilage' | 'regeneration' | 'regulation';
type TimeRange = 'all' | '7' | '30' | '90' | '365';

const topicLabels: Record<Topic, string> = {
  all: '全部主题',
  cartilage: '软骨发育 / 再生',
  regeneration: '组织再生',
  regulation: '基因调控',
};

const topicTerms: Record<Exclude<Topic, 'all'>, string[]> = {
  cartilage: [
    'cartilage', 'chondrogen', 'chondrocyte', 'chondral', 'osteochondral',
    'endochondral', 'growth plate', 'perichondrium', 'sox9', 'col2a1',
    'aggrecan', 'gdf5', 'prg4',
  ],
  regeneration: [
    'regenerat', 'blastema', 'wound', 'fibroblast', 'appendage', 'limb',
    'axolotl', 'zebrafish', 'repair',
  ],
  regulation: [
    'enhancer', 'cis-regulat', 'chromatin', 'multiome', 'atac', 'scrna',
    'single-cell', 'single cell', 'hi-c', 'micro-c', '3d genome', 'crispr',
  ],
};

function matchesTopic(paper: Paper, topic: Topic) {
  if (topic === 'all') return true;
  const haystack = `${paper.title} ${paper.abstract} ${paper.reason}`.toLowerCase();
  return topicTerms[topic].some((term) => haystack.includes(term));
}

function compactAbstract(value: string) {
  if (!value) return '暂无摘要，点击标题可前往出版商页面查看全文信息。';
  return value.length > 360 ? `${value.slice(0, 357).trim()}…` : value;
}

export default function Home() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [query, setQuery] = useState('');
  const [journal, setJournal] = useState('all');
  const [topic, setTopic] = useState<Topic>('all');
  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [bookmarksOnly, setBookmarksOnly] = useState(false);
  const [saved, setSaved] = useState<string[]>([]);
  const [visibleCount, setVisibleCount] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
    void fetch(`${basePath}/papers.json`)
      .then((response) => {
        if (!response.ok) throw new Error('文献数据载入失败');
        return response.json() as Promise<Paper[]>;
      })
      .then((data: Paper[]) => setPapers(data))
      .catch(() => setPapers([]))
      .finally(() => setLoading(false));

    queueMicrotask(() => {
      try {
        setSaved(JSON.parse(localStorage.getItem('paper-radar-bookmarks') || '[]'));
      } catch {
        setSaved([]);
      }
    });
  }, []);

  const journals = useMemo(
    () => [...new Set(papers.map((paper) => paper.journal))].sort(),
    [papers],
  );

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const cutoff = new Date();
    if (timeRange !== 'all') cutoff.setDate(cutoff.getDate() - Number(timeRange));
    const cutoffDate = cutoff.toISOString().slice(0, 10);
    return papers
      .filter((paper) => journal === 'all' || paper.journal === journal)
      .filter((paper) => matchesTopic(paper, topic))
      .filter((paper) => timeRange === 'all' || paper.published_date >= cutoffDate)
      .filter((paper) => !bookmarksOnly || saved.includes(paper.doi))
      .filter((paper) => {
        if (!needle) return true;
        return `${paper.title} ${paper.abstract} ${paper.first_author} ${paper.doi}`
          .toLowerCase()
          .includes(needle);
      })
      .sort((a, b) => b.score - a.score || b.published_date.localeCompare(a.published_date));
  }, [papers, query, journal, topic, timeRange, bookmarksOnly, saved]);

  const topRelevant = papers.filter((paper) => paper.score >= 55).length;
  const latestDate = papers.reduce(
    (latest, paper) => (paper.published_date > latest ? paper.published_date : latest),
    '',
  );

  function toggleSaved(doi: string) {
    setSaved((current) => {
      const next = current.includes(doi)
        ? current.filter((item) => item !== doi)
        : [...current, doi];
      localStorage.setItem('paper-radar-bookmarks', JSON.stringify(next));
      return next;
    });
  }

  function clearFilters() {
    setQuery('');
    setJournal('all');
    setTopic('all');
    setTimeRange('all');
    setBookmarksOnly(false);
  }

  return (
    <main>
      <header className="hero">
        <nav className="nav-shell" aria-label="主导航">
          <a className="brand" href="#top" aria-label="文献雷达首页">
            <span className="brand-mark">R</span>
            <span>文献雷达</span>
          </a>
          <button
            className={`saved-button ${bookmarksOnly ? 'active' : ''}`}
            onClick={() => setBookmarksOnly((value) => !value)}
          >
            <Bookmark size={16} fill={bookmarksOnly ? 'currentColor' : 'none'} />
            我的收藏 <span>{saved.length}</span>
          </button>
        </nav>

        <div className="hero-content" id="top">
          <p className="eyebrow">REGENERATIVE BIOLOGY LITERATURE RADAR</p>
          <h1>文献推送</h1>
          <p className="hero-copy">
            聚合再生生物学、软骨发育与基因调控领域的重要期刊，按照你的研究画像自动排序。
          </p>

          <div className="search-box">
            <Search size={20} aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索标题、摘要、作者或 DOI…"
              aria-label="搜索文献"
            />
            {query && (
              <button className="icon-button" onClick={() => setQuery('')} aria-label="清空搜索">
                <X size={17} />
              </button>
            )}
          </div>

          <div className="stats" aria-label="文献库统计">
            <span><strong>{papers.length}</strong> 篇文献</span>
            <span><strong>{journals.length}</strong> 本期刊</span>
            <span><strong>{topRelevant}</strong> 篇高度相关</span>
            {latestDate && <span>更新至 <strong>{latestDate}</strong></span>}
          </div>
        </div>
      </header>

      <section className="library" aria-label="文献列表">
        <div className="filter-row">
          <div className="filter-title"><SlidersHorizontal size={16} /> 筛选</div>
          <div className="topic-tabs" aria-label="主题筛选">
            {(Object.keys(topicLabels) as Topic[]).map((item) => (
              <button
                key={item}
                className={topic === item ? 'active' : ''}
                onClick={() => setTopic(item)}
              >
                {topicLabels[item]}
              </button>
            ))}
          </div>
          <div className="select-controls">
            <select value={timeRange} onChange={(event) => setTimeRange(event.target.value as TimeRange)} aria-label="发表时间筛选">
              <option value="all">全部时间</option>
              <option value="7">近 7 天</option>
              <option value="30">近 30 天</option>
              <option value="90">近 90 天</option>
              <option value="365">近 1 年</option>
            </select>
            <select value={journal} onChange={(event) => setJournal(event.target.value)} aria-label="期刊筛选">
              <option value="all">全部期刊</option>
              {journals.map((item) => <option key={item}>{item}</option>)}
            </select>
          </div>
        </div>

        <div className="result-heading">
          <div>
            <p className="section-kicker">CURATED FOR YOUR RESEARCH</p>
            <h2>{bookmarksOnly ? '我的收藏' : topicLabels[topic]}</h2>
          </div>
          <p>找到 {filtered.length} 篇 · 按相关度排序</p>
        </div>

        {loading ? (
          <div className="empty-state">正在载入文献库…</div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <h3>没有找到匹配的文献</h3>
            <p>可以换一个关键词，或清除当前筛选条件。</p>
            <button onClick={clearFilters}>清除筛选</button>
          </div>
        ) : (
          <div className="paper-list">
            {filtered.slice(0, visibleCount).map((paper) => {
              const isSaved = saved.includes(paper.doi);
              return (
                <article className={`paper-card ${paper.score >= 55 ? 'high-score' : ''}`} key={paper.id}>
                  <div className="paper-main">
                    <div className="paper-labels">
                      <span className="journal">{paper.journal}</span>
                      {paper.score >= 55 && <span className="recommended">重点推荐</span>}
                    </div>
                    <h3>
                      <a href={paper.url} target="_blank" rel="noreferrer">
                        {paper.title} <ExternalLink size={15} aria-hidden="true" />
                      </a>
                    </h3>
                    <p className="abstract">{compactAbstract(paper.abstract)}</p>
                    <div className="paper-meta">
                      <span>{paper.first_author || '作者信息待补充'}</span>
                      <span>{paper.published_date || '日期待补充'}</span>
                      <span>{paper.doi}</span>
                    </div>
                    {paper.reason && <p className="reason">相关线索：{paper.reason.replace(/^关键词：/, '')}</p>}
                  </div>
                  <aside className="paper-actions">
                    <div className="score-ring" aria-label={`相关度 ${paper.score} 分`}>
                      <strong>{paper.score}</strong>
                      <span>相关度</span>
                    </div>
                    <button
                      className={`bookmark-button ${isSaved ? 'active' : ''}`}
                      onClick={() => toggleSaved(paper.doi)}
                      aria-label={isSaved ? '取消收藏' : '收藏文献'}
                    >
                      <Bookmark size={18} fill={isSaved ? 'currentColor' : 'none'} />
                      {isSaved ? '已收藏' : '收藏'}
                    </button>
                  </aside>
                </article>
              );
            })}
          </div>
        )}

        {visibleCount < filtered.length && (
          <button className="load-more" onClick={() => setVisibleCount((count) => count + 30)}>
            再显示 30 篇
          </button>
        )}
      </section>

      <footer>
        <div><strong>文献雷达</strong><span>为闲暇阅读留一条更短的路径。</span></div>
        <p>文献元数据来自 Crossref / PubMed · 收藏仅保存在当前浏览器</p>
      </footer>
    </main>
  );
}
