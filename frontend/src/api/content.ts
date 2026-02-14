import request from './request'

export const contentApi = {
  getList: (params = {}) => request.get('/contents', { params }),
  getById: (id) => request.get(`/contents/${id}`),
  create: (data) => request.post('/contents', data),
  update: (id, data) => request.put(`/contents/${id}`, data),
  delete: (id) => request.delete(`/contents/${id}`),
  approve: (id) => request.post(`/contents/${id}/approve`),
  reject: (id) => request.post(`/contents/${id}/reject`),
  publish: (id) => request.post(`/contents/${id}/publish`)
}
