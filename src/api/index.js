const BASE = "https://ta14-ecotech-backend-ecf9e5hca9fpf7da.australiaeast-01.azurewebsites.net/api"

export const api = {

  // write your functions here, for example:

  //GetPerson
  //iput//
  
  getPerson: async () => {
    const response = await fetch(`${BASE}/GetPerson`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  },


  //GetMapLocation
  /**
 * 获取地图位置信息
 * @param {string} postcode - 邮政编码
 * @returns {Promise<any>} 位置信息
 */

  getMapLocation: async (postcode) => {
    if (typeof postcode !== 'string') {
    throw new Error("Parameter must be a string");
  }

    const response = await fetch(`${BASE}/map/disposal-locations/${postcode}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  }

}