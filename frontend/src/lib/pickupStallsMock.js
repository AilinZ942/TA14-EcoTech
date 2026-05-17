export const CATEGORIES = [
  { value: 'phone', label: 'Phones', icon: '📱' },
  { value: 'laptop', label: 'Laptops', icon: '💻' },
  { value: 'tablet', label: 'Tablets', icon: '📲' },
  { value: 'audio', label: 'Audio', icon: '🎧' },
  { value: 'accessory', label: 'Accessories', icon: '🔌' },
]

export const NETWORK_CENTER = {
  lat: -37.8136,
  lng: 144.9631,
}

export function haversineKm(a, b) {
  const R = 6371
  const toRad = (n) => (n * Math.PI) / 180
  const dLat = toRad(b.lat - a.lat)
  const dLng = toRad(b.lng - a.lng)
  const lat1 = toRad(a.lat)
  const lat2 = toRad(b.lat)
  const sinLat = Math.sin(dLat / 2)
  const sinLng = Math.sin(dLng / 2)
  const h =
    sinLat * sinLat +
    Math.cos(lat1) * Math.cos(lat2) * sinLng * sinLng
  return 2 * R * Math.asin(Math.sqrt(h))
}

export const stalls = [
  {
    id: 'melbourne-01',
    name: 'EcoReviva Melbourne Central',
    address: '211 La Trobe St',
    suburb: 'Melbourne',
    postcode: '3000',
    state: 'VIC',
    lat: -37.8104,
    lng: 144.9622,
    open: true,
    hours: 'Mon-Sat 9am-6pm',
    phone: '03 9000 0101',
    inventory: [
      { id: 'm1', category: 'phone', brand: 'Apple', model: 'iPhone 13', condition: 'Good', year: '2021', storage: '128GB', price: 437 },
      { id: 'm2', category: 'laptop', brand: 'Dell', model: 'XPS 13', condition: 'Excellent', year: '2022', storage: '512GB', price: 899 },
      { id: 'm3', category: 'tablet', brand: 'Apple', model: 'iPad Air', condition: 'Good', year: '2020', storage: '64GB', price: 399 },
    ],
  },
  {
    id: 'richmond-01',
    name: 'EcoReviva Richmond Hub',
    address: '45 Swan St',
    suburb: 'Richmond',
    postcode: '3121',
    state: 'VIC',
    lat: -37.8216,
    lng: 144.9987,
    open: true,
    hours: 'Daily 10am-5pm',
    phone: '03 9000 0102',
    inventory: [
      { id: 'r1', category: 'phone', brand: 'Samsung', model: 'Galaxy S23', condition: 'Good', year: '2023', storage: '256GB', price: 549 },
      { id: 'r2', category: 'audio', brand: 'Sony', model: 'WH-1000XM5', condition: 'Good', year: '2022', storage: '', price: 279 },
      { id: 'r3', category: 'accessory', brand: 'Anker', model: '65W Charger', condition: 'Good', year: '2023', storage: '', price: 29 },
    ],
  },
  {
    id: 'footscray-01',
    name: 'EcoReviva West Footscray',
    address: '18 Barkly St',
    suburb: 'Footscray',
    postcode: '3011',
    state: 'VIC',
    lat: -37.8006,
    lng: 144.8996,
    open: false,
    hours: 'Tue-Sun 11am-4pm',
    phone: '03 9000 0103',
    inventory: [
      { id: 'f1', category: 'phone', brand: 'Apple', model: 'iPhone SE (3rd Gen)', condition: 'Good', year: '2022', storage: '64GB', price: 329 },
      { id: 'f2', category: 'laptop', brand: 'HP', model: 'EliteBook 840', condition: 'Good', year: '2021', storage: '256GB', price: 479 },
      { id: 'f3', category: 'tablet', brand: 'Samsung', model: 'Galaxy Tab S8', condition: 'Good', year: '2022', storage: '128GB', price: 629 },
    ],
  },
]
