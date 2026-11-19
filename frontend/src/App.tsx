import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [health, setHealth] = useState<any>(null)
  const [users, setUsers] = useState<any[]>([])

  useEffect(() => {
    fetch(`${API}/api/health`).then((r) => r.json()).then(setHealth).catch(() => setHealth(null))
    fetch(`${API}/api/auth/dev-accounts`).then((r) => r.json()).then(setUsers).catch(() => {})
  }, [])

  return (
    <div className="p-8 font-sans">
      <h1 className="text-2xl font-bold">NurseShift</h1>
      <p className="text-gray-600">Kostra projektu (krok 2): React + FastAPI + Firestore emulator</p>
      <pre className="mt-4 bg-gray-100 p-3 rounded text-sm">
        {health ? JSON.stringify(health, null, 2) : 'Backend neodpovídá'}
      </pre>
      <h2 className="mt-6 font-semibold">Testovací uživatelé (seed)</h2>
      <ul className="list-disc ml-6">
        {users.map((u) => (
          <li key={u.id}>{u.name} – {u.role} – úvazek {u.workload}</li>
        ))}
      </ul>
    </div>
  )
}
