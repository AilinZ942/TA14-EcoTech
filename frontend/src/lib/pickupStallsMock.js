/*
 * MOCK DATA — EcoReviva pickup stalls.
 *
 * Replace with a backend call to `/api/pickup-stalls` once the endpoint is live.
 * Each stall represents a physical EcoReviva-operated booth where:
 *   - sellers hand over working second-hand devices
 *   - buyers can collect a listed device
 *
 * Coverage: 38 stalls across all 8 Australian states/territories
 *   VIC: 13   NSW: 8   QLD: 5   WA: 4
 *   SA: 3    TAS: 2   ACT: 2   NT: 1
 *
 * Schema:
 *   id, name, address, suburb, postcode, state, lat, lng,
 *   hours, phone, open, region,
 *   inventory: [{ id, brand, model, category, condition, price, year, storage, color }]
 *
 * Categories: phone, laptop, tablet, audio, charger, accessory
 */

export const CATEGORIES = [
  { value: 'phone', label: 'Phones', icon: '📱' },
  { value: 'laptop', label: 'Laptops', icon: '💻' },
  { value: 'tablet', label: 'Tablets', icon: '📲' },
  { value: 'audio', label: 'Audio', icon: '🎧' },
  { value: 'charger', label: 'Chargers', icon: '🔌' },
  { value: 'accessory', label: 'Accessories', icon: '🖱️' },
]

export const stalls = [
  // ============ VICTORIA — Melbourne metro ============
  {
    id: 'stall-carlton', region: 'Melbourne',
    name: 'EcoReviva Stall — Carlton',
    address: '15 Faraday Street', suburb: 'Carlton', postcode: '3053', state: 'VIC',
    lat: -37.7989, lng: 144.9667,
    hours: 'Mon–Sat, 9 am – 6 pm', phone: '(03) 9001 0001', open: true,
    inventory: [
      { id: 'd1', brand: 'Samsung', model: 'Galaxy S24', category: 'phone', condition: 'Refurbished', price: 720, year: 2024, storage: '256 GB', color: 'Onyx Black' },
      { id: 'd2', brand: 'Apple', model: 'iPhone 13', category: 'phone', condition: 'Good', price: 480, year: 2021, storage: '128 GB', color: 'Midnight' },
      { id: 'd3', brand: 'Apple', model: 'MacBook Air M1', category: 'laptop', condition: 'Refurbished', price: 750, year: 2020, storage: '256 GB SSD', color: 'Silver' },
      { id: 'd4', brand: 'Anker', model: '65W GaN charger', category: 'charger', condition: 'New', price: 35, year: 2024 },
      { id: 'd5', brand: 'Apple', model: 'AirPods Pro (2nd gen)', category: 'audio', condition: 'Good', price: 180, year: 2022 },
    ],
  },
  {
    id: 'stall-brunswick', region: 'Melbourne',
    name: 'EcoReviva Stall — Brunswick',
    address: '88 Sydney Road', suburb: 'Brunswick', postcode: '3056', state: 'VIC',
    lat: -37.7676, lng: 144.9602,
    hours: 'Mon–Sun, 10 am – 7 pm', phone: '(03) 9001 0002', open: true,
    inventory: [
      { id: 'd6', brand: 'Samsung', model: 'Galaxy S22', category: 'phone', condition: 'Good', price: 360, year: 2022, storage: '128 GB', color: 'Phantom White' },
      { id: 'd7', brand: 'Google', model: 'Pixel 7', category: 'phone', condition: 'Refurbished', price: 420, year: 2022, storage: '128 GB', color: 'Snow' },
      { id: 'd8', brand: 'Dell', model: 'XPS 13 (2021)', category: 'laptop', condition: 'Refurbished', price: 680, year: 2021, storage: '512 GB SSD', color: 'Platinum' },
      { id: 'd9', brand: 'Apple', model: 'iPad Air 4', category: 'tablet', condition: 'Good', price: 380, year: 2020, storage: '64 GB', color: 'Sky Blue' },
      { id: 'd10', brand: 'Logitech', model: 'MX Master 3', category: 'accessory', condition: 'Good', price: 85, year: 2023 },
    ],
  },
  {
    id: 'stall-footscray', region: 'Melbourne',
    name: 'EcoReviva Stall — Footscray',
    address: '8 Hopkins Street', suburb: 'Footscray', postcode: '3011', state: 'VIC',
    lat: -37.7997, lng: 144.9000,
    hours: 'Tue–Sat, 10 am – 5 pm', phone: '(03) 9001 0003', open: false,
    inventory: [
      { id: 'd11', brand: 'Apple', model: 'iPhone 12', category: 'phone', condition: 'Good', price: 380, year: 2020, storage: '64 GB', color: 'Blue' },
      { id: 'd12', brand: 'Lenovo', model: 'ThinkPad T14', category: 'laptop', condition: 'Refurbished', price: 620, year: 2021, storage: '512 GB SSD', color: 'Black' },
      { id: 'd13', brand: 'Microsoft', model: 'Surface Pro 7', category: 'tablet', condition: 'Good', price: 420, year: 2020, storage: '256 GB SSD', color: 'Platinum' },
      { id: 'd14', brand: 'Anker', model: 'USB-C cable bundle (3)', category: 'charger', condition: 'New', price: 18, year: 2024 },
      { id: 'd15', brand: 'Logitech', model: 'M325 Wireless Mouse', category: 'accessory', condition: 'Good', price: 22, year: 2023 },
    ],
  },
  {
    id: 'stall-richmond', region: 'Melbourne',
    name: 'EcoReviva Stall — Richmond',
    address: '120 Bridge Road', suburb: 'Richmond', postcode: '3121', state: 'VIC',
    lat: -37.8164, lng: 145.0009,
    hours: 'Mon–Fri, 9 am – 6 pm', phone: '(03) 9001 0004', open: true,
    inventory: [
      { id: 'd16', brand: 'Samsung', model: 'Galaxy S24 Ultra', category: 'phone', condition: 'Refurbished', price: 1180, year: 2024, storage: '256 GB', color: 'Titanium Grey' },
      { id: 'd17', brand: 'Apple', model: 'iPad Mini 5', category: 'tablet', condition: 'Good', price: 260, year: 2019, storage: '64 GB', color: 'Space Gray' },
      { id: 'd18', brand: 'Sony', model: 'WH-1000XM4', category: 'audio', condition: 'Refurbished', price: 220, year: 2020 },
      { id: 'd19', brand: 'Apple', model: 'MacBook Pro 13" M2', category: 'laptop', condition: 'Refurbished', price: 1280, year: 2022, storage: '512 GB SSD', color: 'Space Gray' },
    ],
  },
  {
    id: 'stall-st-kilda', region: 'Melbourne',
    name: 'EcoReviva Stall — St Kilda',
    address: '40 Acland Street', suburb: 'St Kilda', postcode: '3182', state: 'VIC',
    lat: -37.8676, lng: 144.9805,
    hours: 'Wed–Sun, 11 am – 7 pm', phone: '(03) 9001 0005', open: true,
    inventory: [
      { id: 'd20', brand: 'Apple', model: 'iPhone XR', category: 'phone', condition: 'Good', price: 220, year: 2018, storage: '64 GB', color: 'Coral' },
      { id: 'd21', brand: 'Microsoft', model: 'Surface Laptop 3', category: 'laptop', condition: 'Refurbished', price: 540, year: 2019, storage: '256 GB SSD', color: 'Cobalt Blue' },
      { id: 'd22', brand: 'Samsung', model: 'Galaxy Buds 2', category: 'audio', condition: 'Good', price: 75, year: 2021 },
      { id: 'd23', brand: 'Anker', model: 'Power Bank 20K', category: 'charger', condition: 'New', price: 48, year: 2024 },
    ],
  },
  {
    id: 'stall-northcote', region: 'Melbourne',
    name: 'EcoReviva Stall — Northcote',
    address: '170 High Street', suburb: 'Northcote', postcode: '3070', state: 'VIC',
    lat: -37.7693, lng: 144.9994,
    hours: 'Thu–Sat, 10 am – 6 pm', phone: '(03) 9001 0006', open: true,
    inventory: [
      { id: 'd24', brand: 'OnePlus', model: 'OnePlus 9', category: 'phone', condition: 'Good', price: 320, year: 2021, storage: '128 GB', color: 'Astral Black' },
      { id: 'd25', brand: 'HP', model: 'Pavilion 14', category: 'laptop', condition: 'Fair', price: 290, year: 2020, storage: '256 GB SSD', color: 'Silver' },
      { id: 'd26', brand: 'Apple', model: 'iPad Air 2', category: 'tablet', condition: 'Fair', price: 140, year: 2014, storage: '32 GB', color: 'Silver' },
      { id: 'd27', brand: 'JBL', model: 'Tune 510BT', category: 'audio', condition: 'Good', price: 45, year: 2022 },
      { id: 'd28', brand: 'Logitech', model: 'K380 Keyboard', category: 'accessory', condition: 'New', price: 65, year: 2024 },
    ],
  },
  {
    id: 'stall-fitzroy', region: 'Melbourne',
    name: 'EcoReviva Stall — Fitzroy',
    address: '320 Brunswick Street', suburb: 'Fitzroy', postcode: '3065', state: 'VIC',
    lat: -37.7986, lng: 144.9789,
    hours: 'Mon–Sat, 10 am – 6 pm', phone: '(03) 9001 0007', open: true,
    inventory: [
      { id: 'd29', brand: 'Samsung', model: 'Galaxy S24', category: 'phone', condition: 'Good', price: 690, year: 2024, storage: '128 GB', color: 'Marble Grey' },
      { id: 'd30', brand: 'Apple', model: 'iPhone 14', category: 'phone', condition: 'Refurbished', price: 720, year: 2022, storage: '128 GB', color: 'Starlight' },
      { id: 'd31', brand: 'Asus', model: 'ZenBook 14', category: 'laptop', condition: 'Refurbished', price: 720, year: 2022, storage: '512 GB SSD', color: 'Pine Grey' },
      { id: 'd32', brand: 'Bose', model: 'QC45', category: 'audio', condition: 'Good', price: 240, year: 2022 },
    ],
  },
  {
    id: 'stall-south-yarra', region: 'Melbourne',
    name: 'EcoReviva Stall — South Yarra',
    address: '500 Chapel Street', suburb: 'South Yarra', postcode: '3141', state: 'VIC',
    lat: -37.8400, lng: 144.9938,
    hours: 'Mon–Sat, 10 am – 7 pm', phone: '(03) 9001 0008', open: true,
    inventory: [
      { id: 'd33', brand: 'Apple', model: 'iPhone 15', category: 'phone', condition: 'Refurbished', price: 980, year: 2023, storage: '128 GB', color: 'Pink' },
      { id: 'd34', brand: 'Apple', model: 'MacBook Air M2', category: 'laptop', condition: 'Refurbished', price: 1180, year: 2022, storage: '256 GB SSD', color: 'Midnight' },
      { id: 'd35', brand: 'Apple', model: 'iPad Pro 11"', category: 'tablet', condition: 'Refurbished', price: 740, year: 2021, storage: '128 GB', color: 'Space Gray' },
      { id: 'd36', brand: 'Sony', model: 'LinkBuds S', category: 'audio', condition: 'Good', price: 140, year: 2022 },
    ],
  },
  {
    id: 'stall-box-hill', region: 'Melbourne',
    name: 'EcoReviva Stall — Box Hill',
    address: '15 Whitehorse Road', suburb: 'Box Hill', postcode: '3128', state: 'VIC',
    lat: -37.8190, lng: 145.1218,
    hours: 'Tue–Sun, 9 am – 6 pm', phone: '(03) 9001 0009', open: true,
    inventory: [
      { id: 'd37', brand: 'Xiaomi', model: 'Redmi Note 12', category: 'phone', condition: 'Good', price: 240, year: 2023, storage: '128 GB', color: 'Onyx Gray' },
      { id: 'd38', brand: 'Lenovo', model: 'IdeaPad 5', category: 'laptop', condition: 'Refurbished', price: 540, year: 2021, storage: '512 GB SSD', color: 'Graphite' },
      { id: 'd39', brand: 'Samsung', model: 'Galaxy Tab A8', category: 'tablet', condition: 'Good', price: 180, year: 2021, storage: '32 GB', color: 'Dark Gray' },
      { id: 'd40', brand: 'Anker', model: '20W USB-C Charger', category: 'charger', condition: 'New', price: 18, year: 2024 },
    ],
  },
  {
    id: 'stall-doncaster', region: 'Melbourne',
    name: 'EcoReviva Stall — Doncaster',
    address: '619 Doncaster Road', suburb: 'Doncaster', postcode: '3108', state: 'VIC',
    lat: -37.7891, lng: 145.1283,
    hours: 'Mon–Fri, 10 am – 6 pm', phone: '(03) 9001 0010', open: true,
    inventory: [
      { id: 'd41', brand: 'Samsung', model: 'Galaxy A54', category: 'phone', condition: 'Good', price: 380, year: 2023, storage: '128 GB', color: 'Awesome Lime' },
      { id: 'd42', brand: 'Apple', model: 'MacBook Pro 14" M1 Pro', category: 'laptop', condition: 'Refurbished', price: 1690, year: 2021, storage: '512 GB SSD', color: 'Space Gray' },
      { id: 'd43', brand: 'JBL', model: 'Flip 6', category: 'audio', condition: 'Good', price: 95, year: 2022 },
    ],
  },
  {
    id: 'stall-frankston', region: 'Melbourne',
    name: 'EcoReviva Stall — Frankston',
    address: '54 Wells Street', suburb: 'Frankston', postcode: '3199', state: 'VIC',
    lat: -38.1458, lng: 145.1228,
    hours: 'Wed–Sun, 10 am – 5 pm', phone: '(03) 9001 0011', open: true,
    inventory: [
      { id: 'd44', brand: 'Apple', model: 'iPhone 11', category: 'phone', condition: 'Good', price: 320, year: 2019, storage: '128 GB', color: 'Black' },
      { id: 'd45', brand: 'Acer', model: 'Aspire 5', category: 'laptop', condition: 'Fair', price: 320, year: 2020, storage: '256 GB SSD', color: 'Silver' },
      { id: 'd46', brand: 'Logitech', model: 'H390 Headset', category: 'accessory', condition: 'New', price: 38, year: 2024 },
    ],
  },
  // VIC regional
  {
    id: 'stall-geelong', region: 'Geelong',
    name: 'EcoReviva Stall — Geelong',
    address: '85 Moorabool Street', suburb: 'Geelong', postcode: '3220', state: 'VIC',
    lat: -38.1499, lng: 144.3617,
    hours: 'Tue–Sat, 9 am – 5 pm', phone: '(03) 9001 0012', open: true,
    inventory: [
      { id: 'd47', brand: 'Samsung', model: 'Galaxy S23', category: 'phone', condition: 'Refurbished', price: 540, year: 2023, storage: '128 GB', color: 'Cream' },
      { id: 'd48', brand: 'HP', model: 'Envy 15', category: 'laptop', condition: 'Refurbished', price: 760, year: 2022, storage: '512 GB SSD', color: 'Natural Silver' },
      { id: 'd49', brand: 'Apple', model: 'iPad 9th gen', category: 'tablet', condition: 'Good', price: 280, year: 2021, storage: '64 GB', color: 'Silver' },
      { id: 'd50', brand: 'Apple', model: 'AirPods 3', category: 'audio', condition: 'Good', price: 140, year: 2021 },
    ],
  },
  {
    id: 'stall-ballarat', region: 'Ballarat',
    name: 'EcoReviva Stall — Ballarat',
    address: '12 Sturt Street', suburb: 'Ballarat', postcode: '3350', state: 'VIC',
    lat: -37.5622, lng: 143.8503,
    hours: 'Wed–Sat, 10 am – 4 pm', phone: '(03) 9001 0013', open: false,
    inventory: [
      { id: 'd51', brand: 'Google', model: 'Pixel 6a', category: 'phone', condition: 'Good', price: 280, year: 2022, storage: '128 GB', color: 'Charcoal' },
      { id: 'd52', brand: 'Dell', model: 'Inspiron 15', category: 'laptop', condition: 'Fair', price: 380, year: 2020, storage: '256 GB SSD', color: 'Black' },
      { id: 'd53', brand: 'Anker', model: '30W Charger', category: 'charger', condition: 'New', price: 22, year: 2024 },
    ],
  },

  // ============ NSW — Sydney + Newcastle ============
  {
    id: 'stall-newtown', region: 'Sydney',
    name: 'EcoReviva Stall — Newtown',
    address: '320 King Street', suburb: 'Newtown', postcode: '2042', state: 'NSW',
    lat: -33.8980, lng: 151.1788,
    hours: 'Mon–Sun, 10 am – 7 pm', phone: '(02) 9001 0001', open: true,
    inventory: [
      { id: 'd54', brand: 'Samsung', model: 'Galaxy S24', category: 'phone', condition: 'Good', price: 700, year: 2024, storage: '128 GB', color: 'Cobalt Violet' },
      { id: 'd55', brand: 'Apple', model: 'iPhone 13 Pro', category: 'phone', condition: 'Refurbished', price: 720, year: 2021, storage: '128 GB', color: 'Sierra Blue' },
      { id: 'd56', brand: 'Apple', model: 'MacBook Air M1', category: 'laptop', condition: 'Refurbished', price: 740, year: 2020, storage: '256 GB SSD', color: 'Gold' },
      { id: 'd57', brand: 'Sony', model: 'WF-1000XM4', category: 'audio', condition: 'Good', price: 180, year: 2021 },
      { id: 'd58', brand: 'Logitech', model: 'MX Anywhere 3', category: 'accessory', condition: 'Good', price: 75, year: 2023 },
    ],
  },
  {
    id: 'stall-surry-hills', region: 'Sydney',
    name: 'EcoReviva Stall — Surry Hills',
    address: '450 Crown Street', suburb: 'Surry Hills', postcode: '2010', state: 'NSW',
    lat: -33.8855, lng: 151.2107,
    hours: 'Mon–Sat, 9 am – 6 pm', phone: '(02) 9001 0002', open: true,
    inventory: [
      { id: 'd59', brand: 'Apple', model: 'iPhone 15 Pro', category: 'phone', condition: 'Refurbished', price: 1320, year: 2023, storage: '256 GB', color: 'Natural Titanium' },
      { id: 'd60', brand: 'Apple', model: 'MacBook Pro 16" M2 Pro', category: 'laptop', condition: 'Refurbished', price: 2640, year: 2023, storage: '512 GB SSD', color: 'Space Black' },
      { id: 'd61', brand: 'Apple', model: 'iPad Pro 12.9"', category: 'tablet', condition: 'Refurbished', price: 980, year: 2022, storage: '256 GB', color: 'Silver' },
      { id: 'd62', brand: 'Bose', model: 'QC Ultra Headphones', category: 'audio', condition: 'Refurbished', price: 380, year: 2023 },
    ],
  },
  {
    id: 'stall-bondi', region: 'Sydney',
    name: 'EcoReviva Stall — Bondi Junction',
    address: '500 Oxford Street', suburb: 'Bondi Junction', postcode: '2022', state: 'NSW',
    lat: -33.8915, lng: 151.2483,
    hours: 'Mon–Sun, 10 am – 7 pm', phone: '(02) 9001 0003', open: true,
    inventory: [
      { id: 'd63', brand: 'Samsung', model: 'Galaxy Z Fold 5', category: 'phone', condition: 'Refurbished', price: 1640, year: 2023, storage: '256 GB', color: 'Phantom Black' },
      { id: 'd64', brand: 'Microsoft', model: 'Surface Laptop 5', category: 'laptop', condition: 'Refurbished', price: 1180, year: 2022, storage: '512 GB SSD', color: 'Sage' },
      { id: 'd65', brand: 'Apple', model: 'AirPods Max', category: 'audio', condition: 'Good', price: 480, year: 2020 },
    ],
  },
  {
    id: 'stall-parramatta', region: 'Sydney',
    name: 'EcoReviva Stall — Parramatta',
    address: '120 Church Street', suburb: 'Parramatta', postcode: '2150', state: 'NSW',
    lat: -33.8136, lng: 151.0034,
    hours: 'Mon–Fri, 9 am – 6 pm', phone: '(02) 9001 0004', open: true,
    inventory: [
      { id: 'd66', brand: 'Samsung', model: 'Galaxy A54', category: 'phone', condition: 'Good', price: 380, year: 2023, storage: '128 GB', color: 'Awesome Black' },
      { id: 'd67', brand: 'Lenovo', model: 'Yoga Slim 7', category: 'laptop', condition: 'Refurbished', price: 720, year: 2021, storage: '512 GB SSD', color: 'Slate Grey' },
      { id: 'd68', brand: 'Samsung', model: 'Galaxy Tab S7', category: 'tablet', condition: 'Good', price: 480, year: 2020, storage: '128 GB', color: 'Mystic Black' },
      { id: 'd69', brand: 'Anker', model: 'Soundcore Liberty 4', category: 'audio', condition: 'New', price: 120, year: 2024 },
    ],
  },
  {
    id: 'stall-chatswood', region: 'Sydney',
    name: 'EcoReviva Stall — Chatswood',
    address: '345 Victoria Avenue', suburb: 'Chatswood', postcode: '2067', state: 'NSW',
    lat: -33.7969, lng: 151.1819,
    hours: 'Mon–Sun, 9 am – 7 pm', phone: '(02) 9001 0005', open: true,
    inventory: [
      { id: 'd70', brand: 'Google', model: 'Pixel 8', category: 'phone', condition: 'Good', price: 580, year: 2023, storage: '128 GB', color: 'Hazel' },
      { id: 'd71', brand: 'Apple', model: 'iPhone 12 Mini', category: 'phone', condition: 'Good', price: 320, year: 2020, storage: '64 GB', color: 'Green' },
      { id: 'd72', brand: 'Asus', model: 'ROG Strix G15', category: 'laptop', condition: 'Refurbished', price: 1180, year: 2022, storage: '1 TB SSD', color: 'Eclipse Gray' },
      { id: 'd73', brand: 'Logitech', model: 'G502 Hero', category: 'accessory', condition: 'New', price: 75, year: 2024 },
    ],
  },
  {
    id: 'stall-marrickville', region: 'Sydney',
    name: 'EcoReviva Stall — Marrickville',
    address: '210 Marrickville Road', suburb: 'Marrickville', postcode: '2204', state: 'NSW',
    lat: -33.9106, lng: 151.1554,
    hours: 'Wed–Sun, 10 am – 6 pm', phone: '(02) 9001 0006', open: true,
    inventory: [
      { id: 'd74', brand: 'OnePlus', model: 'Nord 3', category: 'phone', condition: 'Good', price: 380, year: 2023, storage: '128 GB', color: 'Tempest Gray' },
      { id: 'd75', brand: 'HP', model: 'EliteBook 840', category: 'laptop', condition: 'Refurbished', price: 580, year: 2020, storage: '512 GB SSD', color: 'Silver' },
      { id: 'd76', brand: 'Apple', model: 'iPad Mini 6', category: 'tablet', condition: 'Refurbished', price: 480, year: 2021, storage: '64 GB', color: 'Purple' },
      { id: 'd77', brand: 'Anker', model: 'PowerLine III', category: 'charger', condition: 'New', price: 14, year: 2024 },
    ],
  },
  {
    id: 'stall-manly', region: 'Sydney',
    name: 'EcoReviva Stall — Manly',
    address: '78 The Corso', suburb: 'Manly', postcode: '2095', state: 'NSW',
    lat: -33.7995, lng: 151.2855,
    hours: 'Mon–Sun, 10 am – 6 pm', phone: '(02) 9001 0007', open: true,
    inventory: [
      { id: 'd78', brand: 'Samsung', model: 'Galaxy S23 FE', category: 'phone', condition: 'Good', price: 480, year: 2023, storage: '128 GB', color: 'Mint' },
      { id: 'd79', brand: 'Apple', model: 'MacBook Air M3', category: 'laptop', condition: 'Refurbished', price: 1480, year: 2024, storage: '256 GB SSD', color: 'Starlight' },
      { id: 'd80', brand: 'Sennheiser', model: 'Momentum 4', category: 'audio', condition: 'Good', price: 320, year: 2022 },
    ],
  },
  {
    id: 'stall-newcastle', region: 'Newcastle',
    name: 'EcoReviva Stall — Newcastle',
    address: '110 Hunter Street', suburb: 'Newcastle', postcode: '2300', state: 'NSW',
    lat: -32.9272, lng: 151.7770,
    hours: 'Tue–Sat, 10 am – 5 pm', phone: '(02) 9001 0008', open: true,
    inventory: [
      { id: 'd81', brand: 'Google', model: 'Pixel 7a', category: 'phone', condition: 'Good', price: 380, year: 2023, storage: '128 GB', color: 'Sea' },
      { id: 'd82', brand: 'Apple', model: 'MacBook Air 2019', category: 'laptop', condition: 'Refurbished', price: 540, year: 2019, storage: '256 GB SSD', color: 'Space Gray' },
      { id: 'd83', brand: 'JBL', model: 'Charge 5', category: 'audio', condition: 'Good', price: 140, year: 2022 },
    ],
  },

  // ============ QUEENSLAND — Brisbane + Gold Coast ============
  {
    id: 'stall-fortitude-valley', region: 'Brisbane',
    name: 'EcoReviva Stall — Fortitude Valley',
    address: '215 Brunswick Street', suburb: 'Fortitude Valley', postcode: '4006', state: 'QLD',
    lat: -27.4565, lng: 153.0344,
    hours: 'Mon–Sun, 10 am – 7 pm', phone: '(07) 3001 0001', open: true,
    inventory: [
      { id: 'd84', brand: 'Samsung', model: 'Galaxy S24+', category: 'phone', condition: 'Refurbished', price: 980, year: 2024, storage: '256 GB', color: 'Amber Yellow' },
      { id: 'd85', brand: 'Apple', model: 'iPhone 14 Pro', category: 'phone', condition: 'Refurbished', price: 1080, year: 2022, storage: '128 GB', color: 'Deep Purple' },
      { id: 'd86', brand: 'Razer', model: 'Blade 15', category: 'laptop', condition: 'Refurbished', price: 1480, year: 2022, storage: '1 TB SSD', color: 'Black' },
      { id: 'd87', brand: 'Apple', model: 'AirPods Pro 2', category: 'audio', condition: 'Refurbished', price: 240, year: 2022 },
    ],
  },
  {
    id: 'stall-west-end', region: 'Brisbane',
    name: 'EcoReviva Stall — West End',
    address: '180 Boundary Street', suburb: 'West End', postcode: '4101', state: 'QLD',
    lat: -27.4840, lng: 153.0099,
    hours: 'Tue–Sun, 10 am – 6 pm', phone: '(07) 3001 0002', open: true,
    inventory: [
      { id: 'd88', brand: 'OnePlus', model: 'OnePlus 11', category: 'phone', condition: 'Good', price: 580, year: 2023, storage: '256 GB', color: 'Titan Black' },
      { id: 'd89', brand: 'Apple', model: 'MacBook Pro 13" 2020', category: 'laptop', condition: 'Refurbished', price: 880, year: 2020, storage: '256 GB SSD', color: 'Silver' },
      { id: 'd90', brand: 'Apple', model: 'iPad Air 5', category: 'tablet', condition: 'Refurbished', price: 680, year: 2022, storage: '64 GB', color: 'Blue' },
      { id: 'd91', brand: 'Logitech', model: 'Pebble M350', category: 'accessory', condition: 'New', price: 32, year: 2024 },
    ],
  },
  {
    id: 'stall-south-brisbane', region: 'Brisbane',
    name: 'EcoReviva Stall — South Brisbane',
    address: '78 Grey Street', suburb: 'South Brisbane', postcode: '4101', state: 'QLD',
    lat: -27.4778, lng: 153.0185,
    hours: 'Mon–Fri, 9 am – 6 pm', phone: '(07) 3001 0003', open: false,
    inventory: [
      { id: 'd92', brand: 'Samsung', model: 'Galaxy A34', category: 'phone', condition: 'Good', price: 320, year: 2023, storage: '128 GB', color: 'Awesome Silver' },
      { id: 'd93', brand: 'Dell', model: 'Latitude 7420', category: 'laptop', condition: 'Refurbished', price: 720, year: 2021, storage: '512 GB SSD', color: 'Carbon' },
      { id: 'd94', brand: 'Anker', model: 'Soundcore Q30', category: 'audio', condition: 'Good', price: 75, year: 2022 },
    ],
  },
  {
    id: 'stall-indooroopilly', region: 'Brisbane',
    name: 'EcoReviva Stall — Indooroopilly',
    address: '42 Station Road', suburb: 'Indooroopilly', postcode: '4068', state: 'QLD',
    lat: -27.5018, lng: 152.9737,
    hours: 'Mon–Sat, 10 am – 6 pm', phone: '(07) 3001 0004', open: true,
    inventory: [
      { id: 'd95', brand: 'Apple', model: 'iPhone 13 Mini', category: 'phone', condition: 'Good', price: 380, year: 2021, storage: '128 GB', color: 'Pink' },
      { id: 'd96', brand: 'Lenovo', model: 'ThinkPad X1 Carbon', category: 'laptop', condition: 'Refurbished', price: 1180, year: 2022, storage: '1 TB SSD', color: 'Carbon Black' },
      { id: 'd97', brand: 'Anker', model: '2-pack USB-C Cable', category: 'charger', condition: 'New', price: 16, year: 2024 },
    ],
  },
  {
    id: 'stall-surfers-paradise', region: 'Gold Coast',
    name: 'EcoReviva Stall — Surfers Paradise',
    address: '32 Cavill Avenue', suburb: 'Surfers Paradise', postcode: '4217', state: 'QLD',
    lat: -28.0023, lng: 153.4145,
    hours: 'Mon–Sun, 11 am – 7 pm', phone: '(07) 3001 0005', open: true,
    inventory: [
      { id: 'd98', brand: 'Samsung', model: 'Galaxy S24 FE', category: 'phone', condition: 'Refurbished', price: 540, year: 2024, storage: '128 GB', color: 'Graphite' },
      { id: 'd99', brand: 'Apple', model: 'iPad 10th gen', category: 'tablet', condition: 'Refurbished', price: 480, year: 2022, storage: '64 GB', color: 'Yellow' },
      { id: 'd100', brand: 'Beats', model: 'Studio Buds', category: 'audio', condition: 'Good', price: 140, year: 2021 },
      { id: 'd101', brand: 'Apple', model: 'MagSafe Charger', category: 'charger', condition: 'New', price: 48, year: 2024 },
    ],
  },

  // ============ WESTERN AUSTRALIA — Perth ============
  {
    id: 'stall-northbridge', region: 'Perth',
    name: 'EcoReviva Stall — Northbridge',
    address: '120 William Street', suburb: 'Northbridge', postcode: '6003', state: 'WA',
    lat: -31.9479, lng: 115.8588,
    hours: 'Mon–Sun, 10 am – 7 pm', phone: '(08) 9001 0001', open: true,
    inventory: [
      { id: 'd102', brand: 'Samsung', model: 'Galaxy S23', category: 'phone', condition: 'Refurbished', price: 540, year: 2023, storage: '256 GB', color: 'Lavender' },
      { id: 'd103', brand: 'Apple', model: 'MacBook Pro 14" M3', category: 'laptop', condition: 'Refurbished', price: 2180, year: 2023, storage: '512 GB SSD', color: 'Space Black' },
      { id: 'd104', brand: 'Apple', model: 'iPad Mini 6', category: 'tablet', condition: 'Good', price: 460, year: 2021, storage: '64 GB', color: 'Space Gray' },
      { id: 'd105', brand: 'Sony', model: 'WH-CH720N', category: 'audio', condition: 'Good', price: 140, year: 2023 },
    ],
  },
  {
    id: 'stall-fremantle', region: 'Perth',
    name: 'EcoReviva Stall — Fremantle',
    address: '85 High Street', suburb: 'Fremantle', postcode: '6160', state: 'WA',
    lat: -32.0569, lng: 115.7475,
    hours: 'Wed–Sun, 10 am – 6 pm', phone: '(08) 9001 0002', open: true,
    inventory: [
      { id: 'd106', brand: 'Apple', model: 'iPhone 14', category: 'phone', condition: 'Refurbished', price: 720, year: 2022, storage: '128 GB', color: 'Blue' },
      { id: 'd107', brand: 'HP', model: 'Spectre x360', category: 'laptop', condition: 'Refurbished', price: 1180, year: 2022, storage: '512 GB SSD', color: 'Nightfall Black' },
      { id: 'd108', brand: 'Logitech', model: 'MX Keys Mini', category: 'accessory', condition: 'Good', price: 95, year: 2023 },
    ],
  },
  {
    id: 'stall-joondalup', region: 'Perth',
    name: 'EcoReviva Stall — Joondalup',
    address: '420 Joondalup Drive', suburb: 'Joondalup', postcode: '6027', state: 'WA',
    lat: -31.7448, lng: 115.7660,
    hours: 'Mon–Fri, 9 am – 6 pm', phone: '(08) 9001 0003', open: true,
    inventory: [
      { id: 'd109', brand: 'Google', model: 'Pixel 7', category: 'phone', condition: 'Good', price: 420, year: 2022, storage: '128 GB', color: 'Lemongrass' },
      { id: 'd110', brand: 'Acer', model: 'Swift 3', category: 'laptop', condition: 'Refurbished', price: 580, year: 2021, storage: '512 GB SSD', color: 'Pure Silver' },
      { id: 'd111', brand: 'Anker', model: '737 Power Bank', category: 'charger', condition: 'New', price: 140, year: 2024 },
    ],
  },
  {
    id: 'stall-perth-cbd', region: 'Perth',
    name: 'EcoReviva Stall — Perth CBD',
    address: '580 Hay Street', suburb: 'Perth', postcode: '6000', state: 'WA',
    lat: -31.9522, lng: 115.8614,
    hours: 'Mon–Sat, 9 am – 6 pm', phone: '(08) 9001 0004', open: true,
    inventory: [
      { id: 'd112', brand: 'Samsung', model: 'Galaxy S24 Ultra', category: 'phone', condition: 'Good', price: 1180, year: 2024, storage: '256 GB', color: 'Titanium Black' },
      { id: 'd113', brand: 'Apple', model: 'iPhone 12 Pro', category: 'phone', condition: 'Refurbished', price: 540, year: 2020, storage: '128 GB', color: 'Pacific Blue' },
      { id: 'd114', brand: 'Microsoft', model: 'Surface Pro 9', category: 'tablet', condition: 'Refurbished', price: 980, year: 2022, storage: '256 GB SSD', color: 'Platinum' },
      { id: 'd115', brand: 'Apple', model: 'AirPods 2', category: 'audio', condition: 'Good', price: 95, year: 2019 },
    ],
  },

  // ============ SOUTH AUSTRALIA — Adelaide ============
  {
    id: 'stall-adelaide-cbd', region: 'Adelaide',
    name: 'EcoReviva Stall — Adelaide CBD',
    address: '120 Rundle Mall', suburb: 'Adelaide', postcode: '5000', state: 'SA',
    lat: -34.9224, lng: 138.6014,
    hours: 'Mon–Sat, 9 am – 6 pm', phone: '(08) 8001 0001', open: true,
    inventory: [
      { id: 'd116', brand: 'Apple', model: 'iPhone 15', category: 'phone', condition: 'Refurbished', price: 980, year: 2023, storage: '128 GB', color: 'Yellow' },
      { id: 'd117', brand: 'Samsung', model: 'Galaxy A24', category: 'phone', condition: 'Good', price: 280, year: 2023, storage: '128 GB', color: 'Black' },
      { id: 'd118', brand: 'Apple', model: 'MacBook Pro 13" M1', category: 'laptop', condition: 'Refurbished', price: 1080, year: 2020, storage: '256 GB SSD', color: 'Silver' },
      { id: 'd119', brand: 'Bose', model: 'SoundLink Flex', category: 'audio', condition: 'Good', price: 180, year: 2022 },
    ],
  },
  {
    id: 'stall-glenelg', region: 'Adelaide',
    name: 'EcoReviva Stall — Glenelg',
    address: '32 Jetty Road', suburb: 'Glenelg', postcode: '5045', state: 'SA',
    lat: -34.9802, lng: 138.5158,
    hours: 'Wed–Sun, 10 am – 6 pm', phone: '(08) 8001 0002', open: true,
    inventory: [
      { id: 'd120', brand: 'Google', model: 'Pixel 8 Pro', category: 'phone', condition: 'Refurbished', price: 980, year: 2023, storage: '128 GB', color: 'Bay' },
      { id: 'd121', brand: 'Lenovo', model: 'Yoga 9i', category: 'laptop', condition: 'Refurbished', price: 1280, year: 2023, storage: '512 GB SSD', color: 'Storm Grey' },
      { id: 'd122', brand: 'Apple', model: 'iPad 8th gen', category: 'tablet', condition: 'Good', price: 240, year: 2020, storage: '32 GB', color: 'Silver' },
    ],
  },
  {
    id: 'stall-norwood', region: 'Adelaide',
    name: 'EcoReviva Stall — Norwood',
    address: '95 The Parade', suburb: 'Norwood', postcode: '5067', state: 'SA',
    lat: -34.9197, lng: 138.6306,
    hours: 'Tue–Sat, 10 am – 5 pm', phone: '(08) 8001 0003', open: true,
    inventory: [
      { id: 'd123', brand: 'Samsung', model: 'Galaxy Z Flip 5', category: 'phone', condition: 'Refurbished', price: 980, year: 2023, storage: '256 GB', color: 'Mint' },
      { id: 'd124', brand: 'Asus', model: 'VivoBook 15', category: 'laptop', condition: 'Refurbished', price: 540, year: 2021, storage: '512 GB SSD', color: 'Indie Black' },
      { id: 'd125', brand: 'Logitech', model: 'C920 Webcam', category: 'accessory', condition: 'New', price: 95, year: 2024 },
    ],
  },

  // ============ TASMANIA — Hobart + Launceston ============
  {
    id: 'stall-hobart', region: 'Hobart',
    name: 'EcoReviva Stall — Hobart',
    address: '88 Liverpool Street', suburb: 'Hobart', postcode: '7000', state: 'TAS',
    lat: -42.8826, lng: 147.3257,
    hours: 'Mon–Sat, 10 am – 5 pm', phone: '(03) 6001 0001', open: true,
    inventory: [
      { id: 'd126', brand: 'Apple', model: 'iPhone 13', category: 'phone', condition: 'Refurbished', price: 540, year: 2021, storage: '128 GB', color: 'Starlight' },
      { id: 'd127', brand: 'Samsung', model: 'Galaxy A53', category: 'phone', condition: 'Good', price: 320, year: 2022, storage: '128 GB', color: 'Awesome Blue' },
      { id: 'd128', brand: 'Apple', model: 'MacBook Air M2', category: 'laptop', condition: 'Refurbished', price: 1180, year: 2022, storage: '256 GB SSD', color: 'Space Gray' },
      { id: 'd129', brand: 'JBL', model: 'Live 460NC', category: 'audio', condition: 'Good', price: 140, year: 2022 },
    ],
  },
  {
    id: 'stall-launceston', region: 'Launceston',
    name: 'EcoReviva Stall — Launceston',
    address: '95 Brisbane Street', suburb: 'Launceston', postcode: '7250', state: 'TAS',
    lat: -41.4391, lng: 147.1357,
    hours: 'Wed–Sat, 10 am – 4 pm', phone: '(03) 6001 0002', open: false,
    inventory: [
      { id: 'd130', brand: 'Google', model: 'Pixel 6a', category: 'phone', condition: 'Good', price: 280, year: 2022, storage: '128 GB', color: 'Sage' },
      { id: 'd131', brand: 'HP', model: 'Pavilion 15', category: 'laptop', condition: 'Refurbished', price: 580, year: 2021, storage: '256 GB SSD', color: 'Natural Silver' },
      { id: 'd132', brand: 'Anker', model: 'PowerCore 10K', category: 'charger', condition: 'New', price: 38, year: 2024 },
    ],
  },

  // ============ ACT — Canberra ============
  {
    id: 'stall-canberra-civic', region: 'Canberra',
    name: 'EcoReviva Stall — Civic',
    address: '32 Garema Place', suburb: 'Canberra', postcode: '2601', state: 'ACT',
    lat: -35.2802, lng: 149.1310,
    hours: 'Mon–Fri, 9 am – 6 pm', phone: '(02) 6001 0001', open: true,
    inventory: [
      { id: 'd133', brand: 'Samsung', model: 'Galaxy S23 Ultra', category: 'phone', condition: 'Refurbished', price: 980, year: 2023, storage: '256 GB', color: 'Phantom Black' },
      { id: 'd134', brand: 'Apple', model: 'MacBook Pro 14" M2', category: 'laptop', condition: 'Refurbished', price: 1880, year: 2023, storage: '512 GB SSD', color: 'Space Gray' },
      { id: 'd135', brand: 'Microsoft', model: 'Surface Go 3', category: 'tablet', condition: 'Good', price: 380, year: 2021, storage: '128 GB SSD', color: 'Platinum' },
      { id: 'd136', brand: 'Logitech', model: 'Brio Webcam', category: 'accessory', condition: 'Good', price: 140, year: 2023 },
    ],
  },
  {
    id: 'stall-belconnen', region: 'Canberra',
    name: 'EcoReviva Stall — Belconnen',
    address: '88 Benjamin Way', suburb: 'Belconnen', postcode: '2617', state: 'ACT',
    lat: -35.2390, lng: 149.0686,
    hours: 'Tue–Sat, 10 am – 6 pm', phone: '(02) 6001 0002', open: true,
    inventory: [
      { id: 'd137', brand: 'Apple', model: 'iPhone 14 Plus', category: 'phone', condition: 'Refurbished', price: 880, year: 2022, storage: '128 GB', color: 'Midnight' },
      { id: 'd138', brand: 'Dell', model: 'XPS 15', category: 'laptop', condition: 'Refurbished', price: 1280, year: 2022, storage: '512 GB SSD', color: 'Platinum' },
      { id: 'd139', brand: 'Sony', model: 'WH-1000XM5', category: 'audio', condition: 'Refurbished', price: 380, year: 2022 },
    ],
  },

  // ============ NORTHERN TERRITORY — Darwin ============
  {
    id: 'stall-darwin', region: 'Darwin',
    name: 'EcoReviva Stall — Darwin',
    address: '52 Mitchell Street', suburb: 'Darwin', postcode: '0800', state: 'NT',
    lat: -12.4633, lng: 130.8456,
    hours: 'Mon–Sat, 9 am – 5 pm', phone: '(08) 8901 0001', open: true,
    inventory: [
      { id: 'd140', brand: 'Samsung', model: 'Galaxy A14', category: 'phone', condition: 'Good', price: 220, year: 2023, storage: '64 GB', color: 'Black' },
      { id: 'd141', brand: 'Apple', model: 'iPhone 12', category: 'phone', condition: 'Good', price: 380, year: 2020, storage: '64 GB', color: 'White' },
      { id: 'd142', brand: 'Lenovo', model: 'IdeaPad 3', category: 'laptop', condition: 'Refurbished', price: 480, year: 2021, storage: '256 GB SSD', color: 'Arctic Grey' },
      { id: 'd143', brand: 'JBL', model: 'Go 3', category: 'audio', condition: 'New', price: 55, year: 2024 },
    ],
  },
]

// Centre of the stall network — Melbourne CBD by default
export const NETWORK_CENTER = { lat: -37.81, lng: 144.97 }

// Helpers
export function haversineKm(a, b) {
  const R = 6371
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(b.lat - a.lat)
  const dLng = toRad(b.lng - a.lng)
  const lat1 = toRad(a.lat)
  const lat2 = toRad(b.lat)
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}
