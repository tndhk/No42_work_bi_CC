import { apiClient } from '@/lib/api-client';
import type { ApiResponse } from '@/types';
import type {
  Group,
  GroupDetail,
  GroupCreateRequest,
  GroupUpdateRequest,
  GroupMember,
  AddMemberRequest,
} from '@/types/group';

export const groupsApi = {
  list: async (): Promise<Group[]> => {
    const response = await apiClient.get('groups').json<ApiResponse<Group[]>>();
    return response.data;
  },

  get: async (groupId: string): Promise<GroupDetail> => {
    const response = await apiClient.get(`groups/${groupId}`).json<ApiResponse<GroupDetail>>();
    return response.data;
  },

  create: async (data: GroupCreateRequest): Promise<Group> => {
    const response = await apiClient.post('groups', { json: data }).json<ApiResponse<Group>>();
    return response.data;
  },

  update: async (groupId: string, data: GroupUpdateRequest): Promise<Group> => {
    const response = await apiClient.put(`groups/${groupId}`, { json: data }).json<ApiResponse<Group>>();
    return response.data;
  },

  delete: async (groupId: string): Promise<void> => {
    await apiClient.delete(`groups/${groupId}`);
  },

  addMember: async (groupId: string, data: AddMemberRequest): Promise<GroupMember> => {
    const response = await apiClient.post(`groups/${groupId}/members`, { json: data }).json<ApiResponse<GroupMember>>();
    return response.data;
  },

  removeMember: async (groupId: string, userId: string): Promise<void> => {
    await apiClient.delete(`groups/${groupId}/members/${userId}`);
  },
};
