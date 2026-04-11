const BASE = "https://ta14-ecotech-backend-ecf9e5hca9fpf7da.australiaeast-01.azurewebsites.net/api"

export const api = {
  getPerson: async () => {
    const response = await fetch(`${BASE}/GetPerson`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  }
}