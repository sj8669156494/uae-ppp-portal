import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api`
  : '/api'

export function useProjects(filters = {}) {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== null && v !== undefined && v !== '')
  )
  return useQuery({
    queryKey: ['projects', params],
    queryFn: () => axios.get(`${API_BASE}/projects`, { params }).then(r => r.data),
  })
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => axios.get(`${API_BASE}/stats`).then(r => r.data),
    staleTime: 60000,
  })
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => axios.get(`${API_BASE}/health`).then(r => r.data),
    staleTime: 30000,
  })
}
