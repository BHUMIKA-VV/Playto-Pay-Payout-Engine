import { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const MERCHANT_ID = 1

function uuidv4() {
  return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c) =>
    (
      c ^
      (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))
    ).toString(16),
  )
}

function App() {
  const [dashboard, setDashboard] = useState(null)
  const [amount, setAmount] = useState('')
  const [bankAccountId, setBankAccountId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchDashboard = async () => {
    setError('')
    try {
      const response = await fetch(`${API_BASE}/api/v1/merchants/${MERCHANT_ID}/dashboard/`)
      const body = await response.json()
      if (!response.ok) {
        setError(body.detail || 'Unable to load dashboard')
        setDashboard(null)
        return
      }
      setDashboard(body)
      setBankAccountId(body?.name ? body.name.replace(/\s+/g, '-').toUpperCase() : '')
    } catch (err) {
      setError('Unable to load dashboard')
      setDashboard(null)
    }
  }

  const submitPayout = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    const payload = {
      merchant_id: MERCHANT_ID,
      amount_paise: Number(amount) * 100,
      bank_account_id: bankAccountId || 'BANK-DEFAULT',
    }
    const response = await fetch(`${API_BASE}/api/v1/payouts/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': uuidv4(),
      },
      body: JSON.stringify(payload),
    })
    const body = await response.json()
    if (!response.ok) {
      setError(body.detail || 'Unable to submit payout')
    } else {
      fetchDashboard()
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg">
        <h1 className="text-3xl font-semibold text-slate-900">Playto Payout Dashboard</h1>
        <p className="mt-2 text-slate-600">Merchant payout engine demo with balance, holds, idempotency, and retry.</p>

        {dashboard ? (
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm text-slate-500">Ledger balance</p>
              <p className="mt-2 text-3xl font-semibold">₹{(dashboard.ledger_balance / 100).toFixed(2)}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm text-slate-500">Held balance</p>
              <p className="mt-2 text-3xl font-semibold">₹{(dashboard.held_balance / 100).toFixed(2)}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm text-slate-500">Available balance</p>
              <p className="mt-2 text-3xl font-semibold">₹{(dashboard.available_balance / 100).toFixed(2)}</p>
            </div>
          </div>
        ) : (
          <>
            <p className="mt-8 text-slate-600">Loading dashboard...</p>
            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          </>
        )}

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 className="text-lg font-semibold text-slate-900">Request payout</h2>
            <form className="mt-4 space-y-4" onSubmit={submitPayout}>
              <div>
                <label className="block text-sm font-medium text-slate-700">Amount (INR)</label>
                <input
                  type="number"
                  min="1"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3"
                  placeholder="1000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Bank account ID</label>
                <input
                  type="text"
                  value={bankAccountId}
                  onChange={(e) => setBankAccountId(e.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3"
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                disabled={loading}
                className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {loading ? 'Submitting...' : 'Submit payout'}
              </button>
            </form>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Recent payouts</h2>
            <div className="mt-4 space-y-3">
              {dashboard?.payout_history?.length ? (
                dashboard.payout_history.map((payout) => (
                  <div key={payout.id} className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <span className="font-semibold">₹{(payout.amount_paise / 100).toFixed(2)}</span>
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs uppercase tracking-wide text-slate-600">
                        {payout.state}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-500">Bank: {payout.bank_account_id}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No recent payouts yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
