import request from './request'

export const taskApi = {
  getList: (params = {}) => request.get('/tasks', { params }),
  getById: (id) => request.get(`/tasks/${id}`),
  create: (data) => request.post('/tasks', data),
  update: (id, data) => request.put(`/tasks/${id}`, data),
  delete: (id) => request.delete(`/tasks/${id}`),
  start: (id) => request.post(`/tasks/${id}/start`),
  complete: (id) => request.post(`/tasks/${id}/complete`)
}
