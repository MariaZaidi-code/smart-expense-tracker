import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api.js'

export default function Register() {
  const [form, setForm] = useState({ username: '', password: '' })
  const [err, setErr] = useState('')
  const navigate = useNavigate()
  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      await api.post('/auth/register', form)
      const res = await api.post('/auth/login', form)
      localStorage.setItem('token', res.data.access_token)
      navigate('/')
    } catch (e) {
      setErr(e.response?.data?.detail || 'Register failed')
    }
  }
  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={submit} className="bg-white p-6 rounded shadow w-80 space-y-3">
        <h2 className="text-xl font-bold">Register</h2>
        <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} placeholder="Username" required className="w-full border rounded px-3 py-2" />
        <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Password" required className="w-full border rounded px-3 py-2" />
        {err && <p className="text-red-600 text-sm">{err}</p>}
        <button className="w-full bg-blue-600 text-white py-2 rounded">Register</button>
        <p className="text-sm text-center">Have account? <Link to="/login" className="text-blue-600">Login</Link></p>
      </form>
    </div>
  )
}
