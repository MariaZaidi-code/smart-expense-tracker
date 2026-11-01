import { useEffect, useState } from 'react'
import api from '../api.js'
import CategoryPie from '../components/CategoryPie.jsx'
import TrendChart from '../components/TrendChart.jsx'

export default function Dashboard() {
  const [expenses, setExpenses] = useState([])
  const [budgets, setBudgets] = useState([])

  useEffect(() => {
    api.get('/expenses').then((r) => setExpenses(r.data || [])).catch(() => {})
    api.get('/budgets').then((r) => setBudgets(r.data || [])).catch(() => {})
  }, [])

  const total = expenses.reduce((s, e) => s + Number(e.amount || 0), 0)
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
  )
    .sort()
    .map(([date, amount]) => ({ date, amount }))

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <p className="text-gray-500 text-sm">Total Spent</p>
          <p className="text-2xl font-bold">${total.toFixed(2)}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-gray-500 text-sm">Expenses</p>
          <p className="text-2xl font-bold">{expenses.length}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-gray-500 text-sm">Budgets</p>
          <p className="text-2xl font-bold">{budgets.length}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-semibold mb-2">By Category</h3>
          <CategoryPie data={byCat} />
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-semibold mb-2">Trend</h3>
          <TrendChart data={byDate} />
        </div>
      </div>
    </div>
  )
}
