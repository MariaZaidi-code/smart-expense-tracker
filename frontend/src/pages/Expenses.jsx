import { useEffect, useState } from 'react'
import api from '../api.js'
import ExpenseForm from '../components/ExpenseForm.jsx'
import ExpenseList from '../components/ExpenseList.jsx'

export default function Expenses() {
  const [items, setItems] = useState([])
  const [editing, setEditing] = useState(null)
  const [showForm, setShowForm] = useState(false)

  const load = () => api.get('/expenses').then((r) => setItems(r.data || [])).catch(() => {})
  useEffect(() => { load() }, [])

  const create = async (data) => {
    await api.post('/expenses', data)
    setShowForm(false)
    load()
  }
  const update = async (data) => {
    await api.put(`/expenses/${editing.id}`, data)
    setEditing(null)
    load()
  }
  const remove = async (id) => {
    await api.delete(`/expenses/${id}`)
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Expenses</h2>
        <button onClick={() => { setEditing(null); setShowForm(true) }} className="bg-blue-600 text-white px-4 py-2 rounded">
          Add Expense
        </button>
      </div>
      {(showForm || editing) && (
        <div className="bg-white p-4 rounded shadow">
          <ExpenseForm
            initial={editing}
            submitLabel={editing ? 'Update' : 'Create'}
            onSubmit={editing ? update : create}
          />
          <button onClick={() => { setShowForm(false); setEditing(null) }} className="mt-2 text-gray-600">Cancel</button>
        </div>
      )}
      <div className="bg-white p-4 rounded shadow">
        <ExpenseList items={items} onEdit={(x) => { setEditing(x); setShowForm(false) }} onDelete={remove} />
      </div>
    </div>
  )
}
