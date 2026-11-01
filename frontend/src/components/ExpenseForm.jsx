import { useState } from 'react'

const CATEGORIES = ['Food', 'Transport', 'Shopping', 'Bills', 'Entertainment', 'Health', 'Other']

export default function ExpenseForm({ initial, onSubmit, submitLabel = 'Save' }) {
  const [form, setForm] = useState({
    title: initial?.title || '',
    amount: initial?.amount || '',
    category: initial?.category || 'Food',
    date: initial?.date ? initial.date.slice(0, 10) : new Date().toISOString().slice(0, 10),
    note: initial?.note || ''
  })
  const [err, setErr] = useState('')

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      await onSubmit({ ...form, amount: Number(form.amount) })
    } catch (e) {
      setErr(e.response?.data?.detail || 'Failed')
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <input name="title" value={form.title} onChange={change} placeholder="Title" required className="w-full border rounded px-3 py-2" />
      <input name="amount" type="number" step="0.01" value={form.amount} onChange={change} placeholder="Amount" required className="w-full border rounded px-3 py-2" />
      <select name="category" value={form.category} onChange={change} className="w-full border rounded px-3 py-2">
        {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
      </select>
      <input name="date" type="date" value={form.date} onChange={change} required className="w-full border rounded px-3 py-2" />
      <textarea name="note" value={form.note} onChange={change} placeholder="Note" className="w-full border rounded px-3 py-2" />
      {err && <p className="text-red-600 text-sm">{err}</p>}
      <button className="bg-blue-600 text-white px-4 py-2 rounded">{submitLabel}</button>
    </form>
  )
}
