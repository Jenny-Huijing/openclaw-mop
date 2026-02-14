import { api } from './api'

export const hotspotApi = {
  getList: (limit = 20) => 
    api.get(`/hotspots?limit=${limit}`),
  
  adopt: (id: string) =>
    api.post(`/hotspots/${id}/adopt`)
}
