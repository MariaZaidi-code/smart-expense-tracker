import { Link, useNavigate, useLocation } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Dashboard' },
  { to: '/expenses', label: 'Expenses' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/reports', label: 'Reports' }
]

export default function Layout({ children }) {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-white border-r p-4 flex flex-col gap-2">
        <h1 className="text-lg font-bold mb-4">Smart Expense</h1>
        {nav.map((n) => (
          <Link
            key={n.to}
            to={n.to}
            className={`px-3 py-2 rounded ${location.pathname === n.to ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
          >
            {n.label}
          </Link>
        ))}
        <button onClick={logout} className="mt-auto px-3 py-2 text-red-600 hover:bg-red-50 rounded">
          Logout
        </button>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
