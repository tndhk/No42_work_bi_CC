"""Group API routes."""
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_dynamodb_resource, require_admin
from app.api.response import api_response
from app.models.user import User
from app.models.group import GroupCreate, GroupUpdate
from app.repositories.group_repository import GroupRepository
from app.repositories.group_member_repository import GroupMemberRepository

router = APIRouter()


class AddMemberRequest(BaseModel):
    user_id: str


@router.get("")
async def list_groups(
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    repo = GroupRepository()
    groups = await repo.list_all(dynamodb)
    return api_response([g.model_dump() for g in groups])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    repo = GroupRepository()

    existing = await repo.get_by_name(group_data.name.strip(), dynamodb)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group name already exists",
        )

    create_data = {
        'id': f"group_{uuid.uuid4().hex[:12]}",
        'name': group_data.name.strip(),
    }
    group = await repo.create(create_data, dynamodb)
    return api_response(group.model_dump())


@router.get("/{group_id}")
async def get_group(
    group_id: str,
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    repo = GroupRepository()
    group = await repo.get_by_id(group_id, dynamodb)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member_repo = GroupMemberRepository()
    members = await member_repo.list_members(group_id, dynamodb)

    result = group.model_dump()
    result["members"] = [m.model_dump() for m in members]
    return api_response(result)


@router.put("/{group_id}")
async def update_group(
    group_id: str,
    update_data: GroupUpdate,
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    repo = GroupRepository()
    group = await repo.get_by_id(group_id, dynamodb)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    update_dict = update_data.model_dump(exclude_unset=True)

    if 'name' in update_dict:
        existing = await repo.get_by_name(update_dict['name'].strip(), dynamodb)
        if existing and existing.id != group_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group name already exists")

    updated = await repo.update(group_id, update_dict, dynamodb)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found after update")
    return api_response(updated.model_dump())


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    repo = GroupRepository()
    group = await repo.get_by_id(group_id, dynamodb)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    await repo.delete(group_id, dynamodb)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: str,
    member_data: AddMemberRequest,
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    group_repo = GroupRepository()
    group = await group_repo.get_by_id(group_id, dynamodb)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member_repo = GroupMemberRepository()
    member = await member_repo.add_member(group_id, member_data.user_id, dynamodb)
    return api_response(member.model_dump())


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    user_id: str,
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    group_repo = GroupRepository()
    group = await group_repo.get_by_id(group_id, dynamodb)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member_repo = GroupMemberRepository()
    await member_repo.remove_member(group_id, user_id, dynamodb)
