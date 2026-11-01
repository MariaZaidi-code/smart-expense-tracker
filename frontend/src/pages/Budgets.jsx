import { useEffect, useState } from 'react'
import api from '../api.js'

const CATEGORIES = ['Food', 'Transport', 'Shopping', 'Bills', 'Entertainment', 'Health', 'Other']

export default function Budgets() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ category: 'Food', amount: '', period: 'monthly' })
  const load = () => api.get('/budgets').then((r) => setItems(r.data || [])).catch(() => {})
  useEffect(() => { load() }, [])

  const submit = async (e) => {
    e.preventDefault()
    await api.post('/budgets', { ...form, amount: Number(form.amount) })
    setForm({ category: 'Food', amount: '', period: 'monthly' })
    load()
  }
  const remove = async (id) => {
    await api.delete(`/budgets/${id}`)
    load()
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Budgets</h2>
      <form onSubmit={submit} className="bg-white p-4 rounded shadow flex gap-2 flex-wrap">
        <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="border rounded px-3 py-2">
          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
        </select>
        <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="Amount" required className="border rounded px-3 py-2" />
        <select value={form.period} onChange={(e) => setForm({ ...form, period: e.target.value })} className="border rounded px-3 py-2">
          <option value="monthly">Monthly</option>
          <option value="weekly">Weekly</option>
        </select>
        <button className="bg-blue-600 text-white px-4 py-2 rounded">Add</button>
      </form>
      <div className="bg-white p-4 rounded shadow">
        <table className="w-full text-sm">
          <thead><tr className="border-b text-left"><th className="py-2">Category</th><th>Amount</th><th>Period</th><th></th></tr></thead>
          <tbody>
            {items.map((b) => (
              <tr key={b.id} className="border-b">
                <td className="py-2">{b.category}</td>
                <td>${Number(b.amount).toFixed(2)}</td>
                <td>{b.period}</td>
                <td><button onClick={() => remove(b.id)} className="text-red-600">Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <p className="text-gray-500 py-4">No budgets.</p>}
      </div>
    </div>
  )
}
