export interface Group {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface GroupDetail extends Group {
  members: GroupMember[];
}

export interface GroupMember {
  group_id: string;
  user_id: string;
  added_at: string;
}

export interface GroupCreateRequest {
  name: string;
}

export interface GroupUpdateRequest {
  name?: string;
}

export interface AddMemberRequest {
  user_id: string;
}

export function isGroup(value: unknown): value is Group {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.name === 'string'
  );
}
