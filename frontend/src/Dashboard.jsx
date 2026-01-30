import { useState, useEffect, useRef } from "react"
import axios from "axios"
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Legend
} from "recharts"

const API = "http://127.0.0.1:8000"

// ── Color system ────────────────────────────────────────────────
const C = {
  bg:       "#070B14",
  surface:  "#0D1526",
  card:     "#111C35",
  border:   "#1A2744",
  accent:   "#2563EB",
  accentLo: "#1D3A8A",
  green:    "#00C896",
  greenLo:  "#003D2D",
  red:      "#F04438",
  redLo:    "#3D1010",
  amber:    "#F59E0B",
  amberLo:  "#3D2800",
  muted:    "#4A5A7A",
  sub:      "#8A9BBD",
  text:     "#D4E0F7",
  white:    "#FFFFFF",
}

const PIE_COLORS = ["#2563EB","#00C896","#F59E0B","#A855F7","#F04438","#06B6D4"]

// ── Tiny helpers ────────────────────────────────────────────────
const Badge = ({ label, color, bg }) => (
  <span style={{
    fontSize: 11, fontWeight: 700, padding: "3px 9px",
    borderRadius: 20, letterSpacing: "0.05em",
    color: color, background: bg, textTransform: "uppercase"
  }}>{label}</span>
)

const actionStyle = (action) => {
  if (action === "BUY")  return { color: C.green, bg: C.greenLo }
  if (action === "SELL") return { color: C.red,   bg: C.redLo   }
  return                        { color: C.amber, bg: C.amberLo }
}

const ConfBar = ({ value, max = 100 }) => (
  <div style={{
    width: 80, height: 6, background: C.border,
    borderRadius: 3, overflow: "hidden"
  }}>
    <div style={{
      height: "100%",
      width: `${(value / max) * 100}%`,
      background: value > 70 ? C.green : value > 40 ? C.amber : C.red,
      borderRadius: 3, transition: "width 0.6s ease"
    }}/>
  </div>
)

const StatCard = ({ label, value, sub, color }) => (
  <div style={{
    background: C.card, border: `1px solid ${C.border}`,
    borderRadius: 12, padding: "16px 20px"
  }}>
    <div style={{ fontSize: 12, color: C.muted, marginBottom: 6,
      textTransform: "uppercase", letterSpacing: "0.07em" }}>
      {label}
    </div>
    <div style={{ fontSize: 22, fontWeight: 700,
      color: color || C.text, letterSpacing: "-0.02em" }}>
      {value}
    </div>
    {sub && <div style={{ fontSize: 12, color: C.sub, marginTop: 4 }}>{sub}</div>}
  </div>
)

const Spinner = () => (
  <div style={{
    width: 18, height: 18, border: `2px solid ${C.border}`,
    borderTopColor: C.accent, borderRadius: "50%",
    animation: "spin 0.8s linear infinite", display: "inline-block"
  }}/>
)

// ── Main Dashboard ──────────────────────────────────────────────
export default function Dashboard() {
  const [budget,      setBudget]      = useState(5000)
  const [risk,        setRisk]        = useState("moderate")
  const [loading,     setLoading]     = useState(false)
  const [result,      setResult]      = useState(null)
  const [error,       setError]       = useState(null)
  const [watchlist,   setWatchlist]   = useState(null)
  const [wlLoading,   setWlLoading]   = useState(false)
  const [history,     setHistory]     = useState(null)
  const [mood,        setMood]        = useState(null)
  const [behavior,    setBehavior]    = useState(null)
  const [sipAmt,      setSipAmt]      = useState(2000)
  const [sipStatus,   setSipStatus]   = useState(null)
  const [executeReal, setExecuteReal] = useState(false)
  const [funds,       setFunds]       = useState(null)
  const [advice,      setAdvice]      = useState(null)
  const [advLoading,  setAdvLoading]  = useState(false)
  const [activeTab,   setActiveTab]   = useState("overview")
  const [agentStatus, setAgentStatus] = useState("IDLE")
  const [expandedRow, setExpandedRow] = useState(null)
  const [scenarios,    setScenarios]    = useState(null)
  const [performance,  setPerformance]  = useState(null)
  const [rebalance,    setRebalance]    = useState(null)

  // Agent status cycling while loading
  useEffect(() => {
    if (!loading) { setAgentStatus("IDLE"); return }
    const steps = ["SCANNING","ANALYZING","SCORING","ALLOCATING","GENERATING"]
    let i = 0
    const t = setInterval(() => {
      setAgentStatus(steps[i % steps.length])
      i++
    }, 2200)
    return () => clearInterval(t)
  }, [loading])

  const runAgent = async () => {
    if (executeReal) {
      const ok = window.confirm(
        `LIVE TRADING\n\nPlaces REAL orders on NSE.\nAmount: ₹${Number(budget).toLocaleString()}\n\nConfirm?`)
      if (!ok) return
    }
    setLoading(true); setError(null); setResult(null)
    try {
      const res = await axios.post(`${API}/invest`, {
        budget: parseFloat(budget), risk_level: risk,
        user_id: "demo_user",
        mode: executeReal ? "live" : "paper",
        execute: executeReal
      })
      setResult(res.data)
      setActiveTab("overview")
    } catch(e) { setError(e.response?.data?.detail || e.message) }
    setLoading(false)
  }

  const loadWatchlist = async () => {
    setWlLoading(true)
    try {
      const res = await axios.get(`${API}/watchlist`)
      setWatchlist(res.data.prices)
    } catch(e) { setError("Watchlist: " + e.message) }
    setWlLoading(false)
  }

  const loadMood = async () => {
    try {
      const [m, b] = await Promise.all([
        axios.get(`${API}/market-mood`),
        axios.get(`${API}/behavior/demo_user`)
      ])
      setMood(m.data); setBehavior(b.data)
    } catch(e) { setError("Market Pulse: " + e.message) }
  }

  const loadHistory = async () => {
    try {
      const res = await axios.get(`${API}/history/demo_user`)
      setHistory(res.data.trades)
    } catch(e) { setError("History: " + e.message) }
  }

  const loadFunds = async () => {
    try {
      const res = await axios.get(`${API}/funds`)
      setFunds(res.data)
    } catch(e) { setError("Funds: " + e.message) }
  }

  const loadAdvice = async () => {
    setAdvLoading(true)
    try {
      const res = await axios.get(`${API}/advice-all`)
      setAdvice(res.data.advice)
    } catch(e) { setError("Advice: " + e.message) }
    setAdvLoading(false)
  }

  const setupSip = async () => {
    try {
      const res = await axios.post(`${API}/sip/setup`, {
        user_id: "demo_user",
        monthly_amt: parseFloat(sipAmt),
        risk_level: risk
      })
      setSipStatus(res.data)
    } catch(e) { setError("SIP: " + e.message) }
  }

  const loadInsights = async () => {
  try {
    const [s, p, r] = await Promise.all([
      axios.get(`${API}/scenarios/demo_user`),
      axios.get(`${API}/performance/demo_user`),
      axios.get(`${API}/rebalance-check/demo_user`)
    ])
    setScenarios(s.data)
    setPerformance(p.data)
    setRebalance(r.data)
  } catch(e) { setError("Insights: " + e.message) }
}

  const pieData = result?.allocation?.holdings?.map(h => ({
    name: h.symbol, value: h.spent
  })) || []

  const barData = result?.top_stocks?.slice(0,6).map(s => ({
    name: s.symbol,
    score: Math.round(s.final_score || 0),
    rsi: Math.round(s.rsi || 0)
  })) || []

  const moodColor = mood ? (
    mood.color === "green"  ? C.green :
    mood.color === "red"    ? C.red   :
    mood.color === "yellow" ? C.amber : C.accent
  ) : C.muted

  return (
    <div style={{
      minHeight: "100vh", background: C.bg,
      color: C.text, fontFamily: "'DM Mono', 'Fira Code', monospace",
      fontSize: 13
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes slideIn { from{opacity:0;transform:translateX(-12px)} to{opacity:1;transform:translateX(0)} }
        .row-hover:hover { background: #111C35 !important; cursor: pointer; }
        .btn-primary:hover { background: #1D4ED8 !important; }
        .btn-ghost:hover { background: #111C35 !important; }
        .tab-btn:hover { color: #D4E0F7 !important; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1A2744; border-radius: 2px; }
      `}</style>

      {/* ── Top nav ───────────────────────────────────── */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 28px",
        borderBottom: `1px solid ${C.border}`,
        background: C.surface,
        position: "sticky", top: 0, zIndex: 100
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: C.accent,
            display: "flex", alignItems: "center",
            justifyContent: "center",
            fontSize: 16, fontWeight: 700,
            fontFamily: "'Space Grotesk', sans-serif",
            color: "#fff"
          }}>S</div>
          <span style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: 700, fontSize: 16, color: C.white
          }}>Stock Agent AI</span>
          <span style={{ color: C.muted, fontSize: 11 }}>v2.0</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {/* Agent status */}
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "5px 12px",
            background: loading ? "#0D2744" : C.card,
            border: `1px solid ${loading ? C.accent : C.border}`,
            borderRadius: 20, fontSize: 11
          }}>
            {loading
              ? <><Spinner /><span style={{ color: C.accent }}>{agentStatus}</span></>
              : <>
                  <div style={{
                    width: 6, height: 6, borderRadius: "50%",
                    background: C.green,
                    animation: "pulse 2s ease infinite"
                  }}/>
                  <span style={{ color: C.green }}>AGENT READY</span>
                </>
            }
          </div>

          {/* Mode badge */}
          <div style={{
            padding: "5px 12px",
            background: executeReal ? C.redLo : C.greenLo,
            border: `1px solid ${executeReal ? C.red : C.green}`,
            borderRadius: 20, fontSize: 11, fontWeight: 700,
            color: executeReal ? C.red : C.green
          }}>
            {executeReal ? "● LIVE" : "● PAPER"}
          </div>
        </div>
      </div>

      <div style={{ padding: "24px 28px", maxWidth: 1400, margin: "0 auto" }}>

        {/* ── Control bar ──────────────────────────────── */}
        <div style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 14, padding: "20px 24px",
          marginBottom: 24,
          animation: "fadeIn 0.4s ease"
        }}>
          <div style={{
            display: "flex", gap: 16, flexWrap: "wrap",
            alignItems: "flex-end"
          }}>
            {/* Budget */}
            <div>
              <div style={{
                fontSize: 11, color: C.muted, marginBottom: 6,
                textTransform: "uppercase", letterSpacing: "0.07em"
              }}>Budget</div>
              <div style={{
                display: "flex", alignItems: "center",
                background: C.card, border: `1px solid ${C.border}`,
                borderRadius: 8, overflow: "hidden"
              }}>
                <span style={{
                  padding: "10px 12px", color: C.sub, fontSize: 13
                }}>₹</span>
                <input
                  type="number" value={budget}
                  onChange={e => setBudget(e.target.value)}
                  style={{
                    background: "transparent", border: "none",
                    color: C.text, fontSize: 15, fontWeight: 600,
                    padding: "10px 12px 10px 0",
                    outline: "none", width: 120,
                    fontFamily: "'Space Grotesk', sans-serif"
                  }}
                />
              </div>
            </div>

            {/* Risk */}
            <div>
              <div style={{
                fontSize: 11, color: C.muted, marginBottom: 6,
                textTransform: "uppercase", letterSpacing: "0.07em"
              }}>Risk</div>
              <select value={risk} onChange={e => setRisk(e.target.value)}
                style={{
                  background: C.card, border: `1px solid ${C.border}`,
                  color: C.text, fontSize: 13, padding: "10px 14px",
                  borderRadius: 8, outline: "none",
                  fontFamily: "'DM Mono', monospace", cursor: "pointer"
                }}>
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>

            {/* Buttons */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button onClick={runAgent} disabled={loading}
                className="btn-primary"
                style={{
                  padding: "10px 22px",
                  background: loading ? C.border :
                              executeReal ? C.red : C.accent,
                  color: C.white, border: "none",
                  borderRadius: 8, fontSize: 13, fontWeight: 600,
                  cursor: loading ? "not-allowed" : "pointer",
                  fontFamily: "'Space Grotesk', sans-serif",
                  display: "flex", alignItems: "center", gap: 8,
                  transition: "background 0.2s"
                }}>
                {loading && <Spinner />}
                {loading ? agentStatus + "..." :
                 executeReal ? `EXECUTE LIVE ₹${Number(budget).toLocaleString()}` :
                 `▶  Analyze ₹${Number(budget).toLocaleString()}`}
              </button>
              <button onClick={loadInsights} style={{
                padding: "10px 16px", background: "transparent",
                border: `1px solid ${C.border}`,
                color: C.sub, borderRadius: 8,
                fontSize: 12, cursor: "pointer"
              }}>
                  Insights
              </button>

              {[
                { label: "Prices",   fn: loadWatchlist, loading: wlLoading },
                { label: "Pulse",    fn: loadMood },
                { label: "Signals",  fn: loadAdvice, loading: advLoading },
                { label: "Funds",    fn: loadFunds },
                { label: "History",  fn: loadHistory },
              ].map(b => (
                <button key={b.label} onClick={b.fn}
                  disabled={b.loading}
                  className="btn-ghost"
                  style={{
                    padding: "10px 16px",
                    background: "transparent",
                    border: `1px solid ${C.border}`,
                    color: C.sub, borderRadius: 8,
                    fontSize: 12, cursor: "pointer",
                    transition: "all 0.15s"
                  }}>
                  {b.loading ? "..." : b.label}
                </button>
              ))}

              {/* Live toggle */}
              <div style={{
                display: "flex", alignItems: "center",
                gap: 8, marginLeft: 4
              }}>
                <div onClick={() => setExecuteReal(!executeReal)}
                  style={{
                    width: 44, height: 24,
                    background: executeReal ? C.red : C.border,
                    borderRadius: 12, position: "relative",
                    cursor: "pointer", transition: "background 0.2s"
                  }}>
                  <div style={{
                    position: "absolute", top: 3,
                    left: executeReal ? 22 : 2,
                    width: 18, height: 18,
                    background: C.white, borderRadius: "50%",
                    transition: "left 0.2s"
                  }}/>
                </div>
                <span style={{
                  fontSize: 11, color: executeReal ? C.red : C.muted,
                  fontWeight: 600
                }}>
                  {executeReal ? "LIVE" : "PAPER"}
                </span>
              </div>
            </div>
          </div>

          {/* Funds */}
          {funds?.status === "success" && (
            <div style={{
              marginTop: 12, padding: "8px 14px",
              background: C.card,
              border: `1px solid ${C.border}`,
              borderRadius: 8, fontSize: 12,
              display: "flex", gap: 24, color: C.sub
            }}>
              <span>Available: <b style={{ color: C.green }}>
                ₹{funds.available_margin?.toLocaleString()}</b></span>
              <span>Used: <b style={{ color: C.text }}>
                ₹{funds.used_margin?.toLocaleString()}</b></span>
            </div>
          )}

          {executeReal && (
            <div style={{
              marginTop: 12, padding: "8px 14px",
              background: C.redLo,
              border: `1px solid ${C.red}`,
              borderRadius: 8, fontSize: 12, color: C.red
            }}>
              ⚠ LIVE MODE — real NSE orders will be placed
            </div>
          )}
        </div>

        {/* ── Error ──────────────────────────────────── */}
        {error && (
          <div style={{
            background: C.redLo, border: `1px solid ${C.red}`,
            borderRadius: 8, padding: "10px 16px",
            color: C.red, fontSize: 13, marginBottom: 20
          }}>
            {error}
            <span onClick={() => setError(null)}
              style={{ float: "right", cursor: "pointer" }}>✕</span>
          </div>
        )}

        {/* ── Market Pulse ────────────────────────────── */}
        {mood && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px,1fr))",
            gap: 12, marginBottom: 24,
            animation: "slideIn 0.4s ease"
          }}>
            <div style={{
              background: C.card,
              border: `1px solid ${moodColor}33`,
              borderRadius: 12, padding: "16px 20px",
              borderLeft: `3px solid ${moodColor}`
            }}>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 6,
                textTransform: "uppercase", letterSpacing: "0.07em" }}>
                Market Regime
              </div>
              <div style={{ fontSize: 22, fontWeight: 700,
                color: moodColor, fontFamily: "'Space Grotesk', sans-serif" }}>
                {mood.mood}
              </div>
              <div style={{ fontSize: 11, color: C.sub, marginTop: 4 }}>
                {mood.advice}
              </div>
            </div>

            <StatCard
              label="Nifty 50"
              value={mood.nifty?.toLocaleString("en-IN")}
              sub={`${mood.nifty_change >= 0 ? "▲" : "▼"} ${Math.abs(mood.nifty_change)}% week`}
              color={mood.nifty_change >= 0 ? C.green : C.red}
            />

            <div style={{
              background: C.card, border: `1px solid ${C.border}`,
              borderRadius: 12, padding: "16px 20px"
            }}>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 6,
                textTransform: "uppercase", letterSpacing: "0.07em" }}>
                India VIX
              </div>
              <div style={{
                fontSize: 22, fontWeight: 700,
                color: mood.high_fear ? C.red : C.green,
                fontFamily: "'Space Grotesk', sans-serif"
              }}>
                {mood.india_vix}
              </div>
              <div style={{
                marginTop: 8, height: 4, background: C.border,
                borderRadius: 2
              }}>
                <div style={{
                  height: "100%",
                  width: `${Math.min((mood.india_vix / 40) * 100, 100)}%`,
                  background: mood.high_fear ? C.red : C.green,
                  borderRadius: 2
                }}/>
              </div>
              <div style={{
                display: "flex", justifyContent: "space-between",
                fontSize: 10, color: C.muted, marginTop: 3
              }}>
                <span>Greed</span><span>Fear</span>
              </div>
            </div>

            {behavior && (
              <div style={{
                background: C.card, border: `1px solid ${C.border}`,
                borderRadius: 12, padding: "16px 20px"
              }}>
                <div style={{ fontSize: 11, color: C.muted, marginBottom: 6,
                  textTransform: "uppercase", letterSpacing: "0.07em" }}>
                  Your Profile
                </div>
                <div style={{ fontSize: 15, fontWeight: 600,
                  color: C.amber,
                  fontFamily: "'Space Grotesk', sans-serif" }}>
                  {behavior.risk_pattern?.toUpperCase()} INVESTOR
                </div>
                <div style={{ fontSize: 11, color: C.sub, marginTop: 4 }}>
                  {behavior.total_trades} trades · avg ₹{behavior.avg_budget?.toLocaleString()}
                </div>
                {behavior.insights?.[0] && (
                  <div style={{
                    marginTop: 8, fontSize: 11, color: C.amber,
                    borderTop: `1px solid ${C.border}`, paddingTop: 6
                  }}>
                    {behavior.insights[0]}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Live Prices ──────────────────────────────── */}
        {watchlist && (
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 14, padding: "20px 24px",
            marginBottom: 24, animation: "fadeIn 0.4s ease"
          }}>
            <div style={{
              display: "flex", justifyContent: "space-between",
              alignItems: "center", marginBottom: 16
            }}>
              <h3 style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontWeight: 600, fontSize: 14, color: C.white
              }}>Live NSE Prices</h3>
              <span style={{ fontSize: 11, color: C.muted }}>
                {watchlist.length} stocks
              </span>
            </div>

            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(140px,1fr))",
              gap: 8
            }}>
              {watchlist.map(s => (
                <div key={s.symbol} style={{
                  background: C.card, border: `1px solid ${C.border}`,
                  borderRadius: 8, padding: "10px 12px",
                  transition: "border-color 0.2s",
                  cursor: "default"
                }}>
                  <div style={{
                    fontSize: 11, color: C.accent,
                    fontWeight: 600, marginBottom: 4,
                    letterSpacing: "0.05em"
                  }}>{s.symbol}</div>
                  <div style={{
                    fontSize: 15, fontWeight: 700,
                    color: C.white,
                    fontFamily: "'Space Grotesk', sans-serif"
                  }}>
                    ₹{s.price?.toLocaleString("en-IN")}
                  </div>
                  <div style={{
                    fontSize: 11, marginTop: 3,
                    color: s.change_pct >= 0 ? C.green : C.red
                  }}>
                    {s.change_pct >= 0 ? "▲" : "▼"} {Math.abs(s.change_pct)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── BUY/HOLD/SELL Advisor ────────────────────── */}
        {advice && (
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 14, padding: "20px 24px",
            marginBottom: 24, animation: "fadeIn 0.5s ease"
          }}>
            <div style={{
              display: "flex", justifyContent: "space-between",
              alignItems: "center", marginBottom: 16
            }}>
              <h3 style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontWeight: 600, fontSize: 14, color: C.white
              }}>AI Signals — Buy / Hold / Sell</h3>
              <span style={{ fontSize: 11, color: C.muted }}>
                {advice.length} stocks analyzed
              </span>
            </div>

            {/* Table header */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1.2fr 0.8fr 0.8fr 0.8fr 0.7fr 1fr 1.5fr",
              padding: "6px 12px", marginBottom: 4,
              fontSize: 10, color: C.muted, textTransform: "uppercase",
              letterSpacing: "0.07em"
            }}>
              <span>Stock</span>
              <span>Price</span>
              <span>Action</span>
              <span>Confidence</span>
              <span>RSI</span>
              <span>From High</span>
              <span>Signal</span>
            </div>

            {advice.map((a, i) => {
              const { color, bg } = actionStyle(a.action)
              const isExpanded    = expandedRow === i
              return (
                <div key={i} style={{ marginBottom: 2 }}>
                  <div
                    className="row-hover"
                    onClick={() => setExpandedRow(isExpanded ? null : i)}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1.2fr 0.8fr 0.8fr 0.8fr 0.7fr 1fr 1.5fr",
                      padding: "10px 12px",
                      background: isExpanded ? C.card : "transparent",
                      borderRadius: 8, alignItems: "center",
                      transition: "background 0.15s"
                    }}>
                    <span style={{
                      fontWeight: 600, color: C.white, fontSize: 13
                    }}>{a.symbol}</span>

                    <span style={{ color: C.text }}>
                      ₹{a.current_price?.toLocaleString("en-IN")}
                    </span>

                    <span>
                      <Badge label={a.action || "HOLD"} color={color} bg={bg}/>
                    </span>

                    <div style={{
                      display: "flex", flexDirection: "column", gap: 3
                    }}>
                      <ConfBar value={a.confidence || 50}/>
                      <span style={{ fontSize: 10, color: C.sub }}>
                        {a.confidence || 50}%
                      </span>
                    </div>

                    <span style={{
                      color: (a.rsi || 50) < 40 ? C.green :
                             (a.rsi || 50) > 70 ? C.red   : C.sub
                    }}>
                      {a.rsi?.toFixed(1)}
                    </span>

                    <span style={{
                      color: (a.pct_from_high || 0) < -20 ? C.green :
                             (a.pct_from_high || 0) > -5  ? C.red   : C.sub
                    }}>
                      {a.pct_from_high}%
                    </span>

                    <span style={{
                      fontSize: 11, color: C.sub,
                      overflow: "hidden", textOverflow: "ellipsis",
                      whiteSpace: "nowrap"
                    }}>
                      {a.reason?.slice(0, 45)}...
                    </span>
                  </div>

                  {isExpanded && (
                    <div style={{
                      background: C.card,
                      border: `1px solid ${C.border}`,
                      borderRadius: 8, padding: "12px 16px",
                      marginTop: 2, fontSize: 12,
                      animation: "fadeIn 0.2s ease"
                    }}>
                      <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(3, 1fr)",
                        gap: 16
                      }}>
                        <div>
                          <div style={{
                            fontSize: 10, color: C.muted,
                            textTransform: "uppercase", marginBottom: 4
                          }}>Full Signal</div>
                          <div style={{ color: C.text }}>{a.reason}</div>
                        </div>
                        <div>
                          <div style={{
                            fontSize: 10, color: C.muted,
                            textTransform: "uppercase", marginBottom: 4
                          }}>Technicals</div>
                          <div style={{ color: C.sub }}>
                            MACD: {a.macd_bull ? "Bullish" : "Bearish"}<br/>
                            MA200: {a.above_ma200 ? "Above (uptrend)" : "Below (downtrend)"}
                          </div>
                        </div>
                        <div>
                          <div style={{
                            fontSize: 10, color: C.muted,
                            textTransform: "uppercase", marginBottom: 4
                          }}>Range</div>
                          <div style={{ color: C.sub }}>
                            52W Low: +{a.pct_from_low}%<br/>
                            52W High: {a.pct_from_high}%
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* ── Results tabs ──────────────────────────────── */}
        {result && (
          <div style={{ animation: "fadeIn 0.5s ease" }}>

            {/* Tab bar */}
            <div style={{
              display: "flex", gap: 4, marginBottom: 20,
              borderBottom: `1px solid ${C.border}`, paddingBottom: 0
            }}>
              {["overview","allocation","report","orders"].map(tab => (
                <button key={tab}
                  className="tab-btn"
                  onClick={() => setActiveTab(tab)}
                  style={{
                    padding: "8px 18px",
                    background: "transparent", border: "none",
                    fontSize: 12, cursor: "pointer",
                    color: activeTab === tab ? C.white : C.muted,
                    borderBottom: activeTab === tab
                      ? `2px solid ${C.accent}` : "2px solid transparent",
                    fontFamily: "'DM Mono', monospace",
                    transition: "color 0.15s",
                    textTransform: "uppercase",
                    letterSpacing: "0.07em"
                  }}>
                  {tab}
                </button>
              ))}
            </div>

            {/* OVERVIEW tab */}
            {activeTab === "overview" && (
              <>
                {/* Stat row */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(160px,1fr))",
                  gap: 12, marginBottom: 24
                }}>
                  <StatCard
                    label="Total Budget"
                    value={`₹${result.allocation?.budget?.toLocaleString("en-IN")}`}
                    color={C.text}
                  />
                  <StatCard
                    label="Invested"
                    value={`₹${result.allocation?.total_spent?.toLocaleString("en-IN")}`}
                    color={C.green}
                    sub={`${Math.round((result.allocation?.total_spent / result.allocation?.budget) * 100)}% deployed`}
                  />
                  <StatCard
                    label="Cash Reserve"
                    value={`₹${result.allocation?.reserve?.toLocaleString("en-IN")}`}
                    color={C.amber}
                    sub="10% safety buffer"
                  />
                  <StatCard
                    label="Positions"
                    value={result.allocation?.holdings?.length}
                    color={C.accent}
                    sub="diversified picks"
                  />
                </div>

                {/* Charts */}
                <div style={{
                  display: "grid", gridTemplateColumns: "1fr 1fr",
                  gap: 16, marginBottom: 24
                }}>
                  <div style={{
                    background: C.surface, border: `1px solid ${C.border}`,
                    borderRadius: 14, padding: 20
                  }}>
                    <h3 style={{
                      fontFamily: "'Space Grotesk', sans-serif",
                      fontWeight: 600, fontSize: 14,
                      color: C.white, marginBottom: 16
                    }}>Allocation Breakdown</h3>
                    {pieData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={220}>
                        <PieChart>
                          <Pie data={pieData} cx="50%" cy="50%"
                            outerRadius={85} innerRadius={40}
                            dataKey="value" paddingAngle={3}
                            label={({name, percent}) =>
                              `${name} ${(percent*100).toFixed(0)}%`}
                            labelLine={false}>
                            {pieData.map((_, i) => (
                              <Cell key={i}
                                fill={PIE_COLORS[i % PIE_COLORS.length]}/>
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={v => `₹${v?.toLocaleString("en-IN")}`}
                            contentStyle={{
                              background: C.card,
                              border: `1px solid ${C.border}`,
                              borderRadius: 8, fontSize: 12
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div style={{
                        height: 220, display: "flex",
                        alignItems: "center", justifyContent: "center",
                        color: C.muted, fontSize: 12
                      }}>No allocation data</div>
                    )}
                  </div>

                  <div style={{
                    background: C.surface, border: `1px solid ${C.border}`,
                    borderRadius: 14, padding: 20
                  }}>
                    <h3 style={{
                      fontFamily: "'Space Grotesk', sans-serif",
                      fontWeight: 600, fontSize: 14,
                      color: C.white, marginBottom: 16
                    }}>AI Score vs RSI</h3>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={barData} barGap={2}>
                        <XAxis dataKey="name"
                          tick={{ fill: C.muted, fontSize: 11 }}
                          axisLine={false} tickLine={false}/>
                        <YAxis
                          tick={{ fill: C.muted, fontSize: 11 }}
                          axisLine={false} tickLine={false}/>
                        <Tooltip contentStyle={{
                          background: C.card,
                          border: `1px solid ${C.border}`,
                          borderRadius: 8, fontSize: 12
                        }}/>
                        <Legend wrapperStyle={{ fontSize: 11 }}/>
                        <Bar dataKey="score" fill={C.accent}
                          radius={[4,4,0,0]} name="AI Score"/>
                        <Bar dataKey="rsi" fill={C.green}
                          radius={[4,4,0,0]} name="RSI"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            )}

            {/* ALLOCATION tab */}
            {activeTab === "allocation" && (
              <div style={{
                background: C.surface, border: `1px solid ${C.border}`,
                borderRadius: 14, padding: 20, marginBottom: 24
              }}>
                <h3 style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 600, fontSize: 14,
                  color: C.white, marginBottom: 16
                }}>Portfolio Allocation Plan</h3>

                {/* Table header */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 0.7fr 1fr 1fr 0.7fr 0.7fr",
                  padding: "6px 12px", marginBottom: 4,
                  fontSize: 10, color: C.muted,
                  textTransform: "uppercase", letterSpacing: "0.07em",
                  borderBottom: `1px solid ${C.border}`
                }}>
                  {["Symbol","Shares","Price","Invested","Weight","Score"].map(h => (
                    <span key={h}>{h}</span>
                  ))}
                </div>

                {result.allocation?.holdings?.map((h, i) => (
                  <div key={i} style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 0.7fr 1fr 1fr 0.7fr 0.7fr",
                    padding: "12px 12px",
                    borderBottom: `1px solid ${C.border}`,
                    alignItems: "center"
                  }}>
                    <div>
                      <div style={{
                        fontWeight: 700, color: C.accent, fontSize: 13
                      }}>{h.symbol}</div>
                      <div style={{ fontSize: 11, color: C.muted }}>
                        {h.reason?.slice(0, 40)}...
                      </div>
                    </div>
                    <span style={{ color: C.text }}>{h.shares}</span>
                    <span style={{ color: C.sub }}>
                      ₹{h.price?.toLocaleString("en-IN")}
                    </span>
                    <span style={{ color: C.green, fontWeight: 600 }}>
                      ₹{h.spent?.toLocaleString("en-IN")}
                    </span>
                    <div>
                      <div style={{
                        height: 4, background: C.border,
                        borderRadius: 2, marginBottom: 3
                      }}>
                        <div style={{
                          height: "100%",
                          width: `${h.pct}%`,
                          background: PIE_COLORS[i % PIE_COLORS.length],
                          borderRadius: 2
                        }}/>
                      </div>
                      <span style={{ fontSize: 10, color: C.muted }}>
                        {h.pct}%
                      </span>
                    </div>
                    <div style={{
                      display: "inline-flex", alignItems: "center",
                      justifyContent: "center",
                      width: 36, height: 36,
                      background: h.score > 70 ? C.greenLo :
                                  h.score > 40 ? C.amberLo : C.redLo,
                      borderRadius: "50%",
                      fontSize: 12, fontWeight: 700,
                      color: h.score > 70 ? C.green :
                             h.score > 40 ? C.amber  : C.red,
                      fontFamily: "'Space Grotesk', sans-serif"
                    }}>
                      {Math.round(h.score)}
                    </div>
                  </div>
                ))}

                <div style={{
                  display: "flex", justifyContent: "space-between",
                  padding: "12px 12px 0",
                  fontSize: 12, color: C.sub
                }}>
                  <span>Leftover cash: <b style={{ color: C.text }}>
                    ₹{result.allocation?.leftover_cash?.toLocaleString("en-IN")}
                  </b></span>
                  <span>Reserve: <b style={{ color: C.amber }}>
                    ₹{result.allocation?.reserve?.toLocaleString("en-IN")}
                  </b></span>
                </div>
              </div>
            )}

            {/* REPORT tab */}
            {activeTab === "report" && (
              <div style={{
                background: C.surface, border: `1px solid ${C.border}`,
                borderRadius: 14, padding: 24, marginBottom: 24
              }}>
                <div style={{
                  display: "flex", justifyContent: "space-between",
                  alignItems: "center", marginBottom: 20
                }}>
                  <h3 style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    fontWeight: 600, fontSize: 14, color: C.white
                  }}>AI Investment Report</h3>
                  <Badge label="GPT-4o-mini" color={C.accent} bg={C.accentLo}/>
                </div>
                <div style={{
                  fontSize: 13, lineHeight: 1.9,
                  color: C.sub, whiteSpace: "pre-wrap",
                  borderLeft: `3px solid ${C.accent}`,
                  paddingLeft: 20
                }}>
                  {result.explanation}
                </div>
              </div>
            )}

            {/* ORDERS tab */}
            {activeTab === "orders" && result.order_results?.length > 0 && (
              <div style={{
                background: C.surface, border: `1px solid ${C.border}`,
                borderRadius: 14, padding: 20, marginBottom: 24
              }}>
                <h3 style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 600, fontSize: 14,
                  color: result.mode === "live" ? C.red : C.white,
                  marginBottom: 16
                }}>
                  {result.mode === "live" ? "Live Orders" : "Paper Orders"}
                </h3>
                {result.order_results.map((o, i) => {
                  const statusColor =
                    o.status === "EXECUTED"       ? C.green :
                    o.status === "PAPER_EXECUTED" ? C.accent :
                    o.status === "SKIPPED"        ? C.muted  : C.red
                  return (
                    <div key={i} style={{
                      display: "flex",
                      justifyContent: "space-between",
                      padding: "10px 12px",
                      borderBottom: `1px solid ${C.border}`,
                      alignItems: "center", fontSize: 13
                    }}>
                      <span style={{ fontWeight: 600, color: C.accent }}>
                        {o.symbol}
                      </span>
                      <Badge label={o.status}
                        color={statusColor}
                        bg={statusColor + "22"}/>
                      <span style={{ color: C.sub, fontSize: 12 }}>
                        {o.message}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ── Trade History ─────────────────────────────── */}
        {history && (
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 14, padding: "20px 24px",
            marginBottom: 24, animation: "fadeIn 0.4s ease"
          }}>
            <h3 style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 600, fontSize: 14,
              color: C.white, marginBottom: 16
            }}>Trade History</h3>

            {history.length === 0 ? (
              <div style={{ color: C.muted, fontSize: 12 }}>
                No trades yet
              </div>
            ) : (
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(260px,1fr))",
                gap: 10
              }}>
                {history.map((t, i) => (
                  <div key={i} style={{
                    background: C.card, border: `1px solid ${C.border}`,
                    borderRadius: 10, padding: "12px 14px"
                  }}>
                    <div style={{
                      display: "flex", justifyContent: "space-between",
                      marginBottom: 6
                    }}>
                      <span style={{
                        color: C.accent, fontWeight: 700
                      }}>
                        ₹{t.budget?.toLocaleString("en-IN")}
                      </span>
                      <span style={{ fontSize: 10, color: C.muted }}>
                        {new Date(t.created_at).toLocaleDateString("en-IN")}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: C.sub }}>
                      {t.allocation?.holdings?.map(h =>
                        `${h.symbol}(${h.shares})`
                      ).join(" · ")}
                    </div>
                    <Badge label={t.risk_level} color={C.amber} bg={C.amberLo}/>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── SIP Setup ──────────────────────────────────── */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`,
          borderRadius: 14, padding: "20px 24px", marginBottom: 24
        }}>
          <div style={{
            display: "flex", justifyContent: "space-between",
            alignItems: "center", marginBottom: 4
          }}>
            <h3 style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 600, fontSize: 14, color: C.white
            }}>Monthly SIP</h3>
            <Badge label="AUTO-INVEST" color={C.green} bg={C.greenLo}/>
          </div>
          <p style={{ fontSize: 11, color: C.muted, marginBottom: 16 }}>
            Agent auto-executes on 1st of every month at 9:15 AM (NSE open)
          </p>

          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div style={{
              display: "flex", alignItems: "center",
              background: C.card, border: `1px solid ${C.border}`,
              borderRadius: 8, overflow: "hidden"
            }}>
              <span style={{
                padding: "10px 12px", color: C.sub, fontSize: 13
              }}>₹</span>
              <input type="number" value={sipAmt}
                onChange={e => setSipAmt(e.target.value)}
                style={{
                  background: "transparent", border: "none",
                  color: C.text, fontSize: 14, fontWeight: 600,
                  padding: "10px 12px 10px 0", outline: "none", width: 100,
                  fontFamily: "'Space Grotesk', sans-serif"
                }}
              />
            </div>
            <button onClick={setupSip}
              style={{
                padding: "10px 20px",
                background: "transparent",
                border: `1px solid ${C.green}`,
                color: C.green, borderRadius: 8,
                fontSize: 12, cursor: "pointer",
                fontFamily: "'DM Mono', monospace",
                fontWeight: 600
              }}>
              ACTIVATE SIP
            </button>
          </div>

          {sipStatus && (
            <div style={{
              marginTop: 12, padding: "10px 14px",
              background: C.greenLo,
              border: `1px solid ${C.green}`,
              borderRadius: 8, fontSize: 12, color: C.green
            }}>
              ✓ SIP active — ₹{sipStatus.monthly_amt?.toLocaleString()}/month
              · {sipStatus.runs_on}
            </div>
          )}
        </div>

      </div>{/* end main content */}
        {(scenarios || performance || rebalance) && (
  <div style={{
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px,1fr))",
    gap: 16, marginTop: 24
  }}>

    {/* Scenario Analysis */}
    {scenarios?.invested > 0 && (
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`,
        borderRadius: 14, padding: "20px 24px"
      }}>
        <h3 style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontWeight: 600, fontSize: 14,
          color: C.white, marginBottom: 16
        }}>Scenario Analysis</h3>
        {[
          { label: "Bull case",
            val: `₹${scenarios.bull_value?.toLocaleString("en-IN")}`,
            ret: `+${scenarios.bull_return}%`, color: C.green },
          { label: "Base case",
            val: `₹${scenarios.base_value?.toLocaleString("en-IN")}`,
            ret: `+${scenarios.base_return}%`, color: C.amber },
          { label: "Bear case",
            val: `₹${scenarios.bear_value?.toLocaleString("en-IN")}`,
            ret: `${scenarios.bear_return}%`,  color: C.red },
        ].map(s => (
          <div key={s.label} style={{
            display: "flex", justifyContent: "space-between",
            alignItems: "center",
            padding: "10px 0",
            borderBottom: `1px solid ${C.border}`
          }}>
            <span style={{ color: C.muted, fontSize: 12 }}>
              {s.label}
            </span>
            <span style={{ color: C.text, fontSize: 13 }}>
              {s.val}
            </span>
            <span style={{
              color: s.color, fontWeight: 700, fontSize: 13
            }}>
              {s.ret}
            </span>
          </div>
        ))}
        <div style={{
          marginTop: 12, fontSize: 11, color: C.muted
        }}>
          Based on last trade · 6-month horizon
        </div>
      </div>
    )}

    {/* Performance */}
    {performance && (
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`,
        borderRadius: 14, padding: "20px 24px"
      }}>
        <h3 style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontWeight: 600, fontSize: 14,
          color: C.white, marginBottom: 16
        }}>Agent Performance</h3>
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 1fr",
          gap: 12, marginBottom: 16
        }}>
          {[
            { label: "Total Trades",
              val: performance.total_trades },
            { label: "Stocks Traded",
              val: performance.unique_stocks },
            { label: "Most Traded",
              val: performance.most_traded },
            { label: "Liquid Heavy",
              val: `${performance.liquid_heavy_pct}% trades` },
          ].map(s => (
            <div key={s.label} style={{
              background: C.card, borderRadius: 8, padding: "10px 12px"
            }}>
              <div style={{
                fontSize: 10, color: C.muted,
                textTransform: "uppercase", marginBottom: 4
              }}>
                {s.label}
              </div>
              <div style={{
                fontSize: 15, fontWeight: 700, color: C.text
              }}>
                {s.val}
              </div>
            </div>
          ))}
        </div>
        {performance.improvement_tips?.map((tip, i) => (
          <div key={i} style={{
            fontSize: 11, color: C.amber,
            padding: "8px 10px",
            background: C.amberLo,
            borderRadius: 6, marginBottom: 6
          }}>
            {tip}
          </div>
        ))}
      </div>
    )}

    {/* Rebalance alert */}
    {rebalance && (
      <div style={{
        background: C.surface,
        border: `1px solid ${rebalance.should_rebalance
          ? C.amber : C.border}`,
        borderRadius: 14, padding: "20px 24px"
      }}>
        <h3 style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontWeight: 600, fontSize: 14,
          color: C.white, marginBottom: 16
        }}>Rebalance Check</h3>
        <div style={{
          display: "flex", alignItems: "center",
          gap: 10, marginBottom: 12
        }}>
          <div style={{
            width: 10, height: 10, borderRadius: "50%",
            background: rebalance.should_rebalance
              ? C.amber : C.green,
            animation: rebalance.should_rebalance
              ? "pulse 1s infinite" : "none"
          }}/>
          <span style={{
            color: rebalance.should_rebalance ? C.amber : C.green,
            fontWeight: 700, fontSize: 14
          }}>
            {rebalance.should_rebalance
              ? "REBALANCE NEEDED" : "BALANCED"}
          </span>
        </div>
        {rebalance.triggers?.map((t, i) => (
          <div key={i} style={{
            fontSize: 12, color: C.sub,
            padding: "6px 0",
            borderBottom: `1px solid ${C.border}`
          }}>
            → {t}
          </div>
        ))}
        <div style={{
          marginTop: 12, fontSize: 11, color: C.muted
        }}>
          {rebalance.recommendation}
        </div>
      </div>
    )}
  </div>
)}
    </div>
  )
} 
