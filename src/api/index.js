const BASE = import.meta.env.VITE_API_BASE

export const api = {
  getPerson: async () => {
    const response = await fetch(`${BASE}/GetPerson`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  }
}