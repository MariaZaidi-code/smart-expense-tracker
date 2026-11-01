import { useEffect, useState } from 'react'
import api from '../api.js'
import CategoryPie from '../components/CategoryPie.jsx'
import TrendChart from '../components/TrendChart.jsx'

export default function Reports() {
  const [expenses, setExpenses] = useState([])
  useEffect(() => { api.get('/expenses').then((r) => setExpenses(r.data || [])).catch(() => {}) }, [])

  const byCat = Object.entries(
    expenses.reduce((acc, e) => {
      acc[e.category] = (acc[e.category] || 0) + Number(e.amount || 0)
      return acc
    }, {})
  ).map(([category, amount]) => ({ category, amount }))

  const byDate = Object.entries(
    expenses.reduce((acc, e) => {
      const d = (e.date || '').slice(0, 10)
      acc[d] = (acc[d] || 0) + Number(e.amount || 0)
      return acc
    }, {})
  ).sort().map(([date, amount]) => ({ date, amount }))

  const total = expenses.reduce((s, e) => s + Number(e.amount || 0), 0)

  const exportCsv = () => {
    const rows = [['Title', 'Amount', 'Category', 'Date', 'Note']]
    expenses.forEach((e) => rows.push([e.title, e.amount, e.category, e.date, e.note || '']))
    const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'expenses.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Reports</h2>
        <button onClick={exportCsv} className="bg-green-600 text-white px-4 py-2 rounded">Export CSV</button>
      </div>
      <div className="bg-white p-4 rounded shadow">
        <p className="text-lg font-semibold">Total: ${total.toFixed(2)}</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-semibold mb-2">By Category</h3>
          <CategoryPie data={byCat} />
          <table className="w-full text-sm mt-2">
            <tbody>
              {byCat.map((c) => (
                <tr key={c.category} className="border-b">
                  <td className="py-1">{c.category}</td>
                  <td className="text-right">${c.amount.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-semibold mb-2">Trend</h3>
          <TrendChart data={byDate} />
        </div>
      </div>
    </div>
  )
}
