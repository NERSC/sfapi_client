from __future__ import annotations
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class BatchGroupAction(Enum):
    batch_add = 'batch_add'
    batch_remove = 'batch_remove'

class BodyCreateGroupAccountGroupsPost(BaseModel):
    name: str = Field(..., title='Name')
    repo_name: str = Field(..., title='Repo Name')

class BodyRunCommandUtilitiesCommandMachinePost(BaseModel):
    executable: str = Field(..., title='Executable')

class BodyStartTransferStorageTransferPost(BaseModel):
    source: str = Field(..., title='Source')
    target: str = Field(..., title='Target')
    outdir: str = Field(..., title='Outdir')
    infiles: str = Field(..., title='Infiles')
    username: Optional[str] = Field(None, title='Username')

class BodySubmitJobComputeJobsMachinePost(BaseModel):
    isPath: bool = Field(..., title='Ispath')
    job: str = Field(..., title='Job')
    args: Optional[List[str]] = Field([], title='Args')

class BodyUpdateGroupMembershipAccountGroupsGroupPut(BaseModel):
    usernames: str = Field(..., title='Usernames')
    action: BatchGroupAction

class BodyUploadFileUtilitiesUploadMachinePathPut(BaseModel):
    file: bytes = Field(..., title='File')

class Changelog(BaseModel):
    date: Optional[date] = Field(None, title='Date')
    change: Optional[str] = Field(None, title='Change')

class Config(BaseModel):
    key: str = Field(..., title='Key')
    value: Optional[str] = Field(None, title='Value')

class DirectoryEntry(BaseModel):
    perms: Optional[str] = Field(None, title='Perms')
    hardlinks: Optional[int] = Field(0, title='Hardlinks')
    user: Optional[str] = Field(None, title='User')
    group: Optional[str] = Field(None, title='Group')
    size: Optional[float] = Field(0, title='Size')
    date: Optional[str] = Field(None, title='Date')
    name: Optional[str] = Field(None, title='Name')

class Note(BaseModel):
    name: str = Field(..., title='Name')
    notes: Optional[str] = Field(None, title='Notes')
    active: Optional[bool] = Field(False, title='Active')
    timestamp: Optional[datetime] = Field(None, title='Timestamp')

class Outage(BaseModel):
    name: str = Field(..., title='Name')
    start_at: Optional[datetime] = Field(None, title='Start At')
    end_at: Optional[datetime] = Field(None, title='End At')
    description: Optional[str] = Field(None, title='Description')
    notes: Optional[str] = Field(None, title='Notes')
    status: Optional[str] = Field(None, title='Status')
    swo: Optional[str] = Field(None, title='Swo')
    update_at: Optional[datetime] = Field(None, title='Update At')

class PublicHost(Enum):
    """Possible compute resources.
    :cvar cori:
    :cvar dtn01:
    :cvar perlmutter:
"""
    dtn01 = 'dtn01'
    perlmutter = 'perlmutter'

class StatusValue(Enum):
    active = 'active'
    unavailable = 'unavailable'
    degraded = 'degraded'
    other = 'other'

class StorageStats(BaseModel):
    name: str = Field(..., title='Name')
    bytes_given: Optional[float] = Field(None, title='Bytes Given')
    bytes_used: Optional[float] = Field(None, title='Bytes Used')
    bytes_given_human: Optional[str] = Field(None, title='Bytes Given Human')
    bytes_used_human: Optional[str] = Field(None, title='Bytes Used Human')
    files_given: Optional[float] = Field(None, title='Files Given')
    files_used: Optional[float] = Field(None, title='Files Used')

class Task(BaseModel):
    id: str = Field(..., title='Id')
    uuid: Optional[str] = Field(None, title='Uuid')
    status: Optional[str] = Field(None, title='Status')
    result: Optional[str] = Field(None, title='Result')

class Tasks(BaseModel):
    tasks: Optional[List[Task]] = Field(None, title='Tasks')

class UserInfo(BaseModel):
    uid: int = Field(..., title='Uid')
    name: str = Field(..., title='Name')
    firstname: str = Field(..., title='Firstname')
    lastname: str = Field(..., title='Lastname')
    middlename: str = Field(..., title='Middlename')
    workphone: str = Field(..., title='Workphone')
    otherPhones: str = Field(..., title='Otherphones')
    email: str = Field(..., title='Email')

class UserStats(BaseModel):
    uid: int = Field(..., title='Uid')
    name: str = Field(..., title='Name')

class ValidationError(BaseModel):
    loc: List[str] = Field(..., title='Location')
    msg: str = Field(..., title='Message')
    type: str = Field(..., title='Error Type')

class AppRoutersComputeModelsStatus(Enum):
    OK = 'OK'
    ERROR = 'ERROR'

class AppRoutersStatusModelsStatus(BaseModel):
    name: str = Field(..., title='Name')
    full_name: Optional[str] = Field(None, title='Full Name')
    description: Optional[str] = Field(None, title='Description')
    system_type: Optional[str] = Field(None, title='System Type')
    notes: Optional[List[str]] = Field(None, title='Notes')
    status: StatusValue
    updated_at: Optional[datetime] = Field(None, title='Updated At')

class AppRoutersStorageModelsStatus(Enum):
    OK = 'OK'
    ERROR = 'ERROR'

class AppRoutersUtilsModelsStatus(Enum):
    OK = 'OK'
    ERROR = 'ERROR'

class DirectoryOutput(BaseModel):
    status: AppRoutersUtilsModelsStatus
    entries: List[DirectoryEntry] = Field(..., title='Entries')
    error: Optional[str] = Field(None, title='Error')
    file: Optional[str] = Field(None, title='File')
    is_binary: Optional[bool] = Field(False, title='Is Binary')

class FileDownload(BaseModel):
    status: AppRoutersUtilsModelsStatus
    file: Optional[str] = Field(None, title='File')
    is_binary: Optional[bool] = Field(False, title='Is Binary')
    error: Optional[str] = Field(None, title='Error')

class GroupStats(BaseModel):
    gid: int = Field(..., title='Gid')
    name: str = Field(..., title='Name')
    users: Optional[List[UserStats]] = Field(None, title='Users')

class HTTPValidationError(BaseModel):
    detail: Optional[List[ValidationError]] = Field(None, title='Detail')

class JobOutput(BaseModel):
    status: AppRoutersComputeModelsStatus
    output: List[Dict[str, str]] = Field(..., title='Output')
    error: Optional[str] = Field(None, title='Error')

class ProjectStats(BaseModel):
    id: int = Field(..., title='Id')
    description: str = Field(..., title='Description')
    repo_name: str = Field(..., title='Repo Name')
    iris_role: Optional[str] = Field(None, title='Iris Role')
    hours_given: Optional[float] = Field(None, title='Hours Given')
    hours_used: Optional[float] = Field(None, title='Hours Used')
    project_hours_given: Optional[float] = Field(None, title='Project Hours Given')
    project_hours_used: Optional[float] = Field(None, title='Project Hours Used')
    projdir_usage: Optional[List[StorageStats]] = Field(None, title='Projdir Usage')
    project_projdir_usage: Optional[StorageStats] = None
    hpss_usage: Optional[List[StorageStats]] = Field(None, title='Hpss Usage')

class QueueOutput(BaseModel):
    status: AppRoutersComputeModelsStatus
    output: List[Dict[str, str]] = Field(..., title='Output')
    error: Optional[str] = Field(None, title='Error')

class TransferResult(BaseModel):
    task_id: str = Field(..., title='Task Id')
    status: AppRoutersStorageModelsStatus
    reason: Optional[str] = Field(None, title='Reason')

class UploadResult(BaseModel):
    status: AppRoutersUtilsModelsStatus
    output: Optional[str] = Field(None, title='Output')
    error: Optional[str] = Field(None, title='Error')

class AppRoutersComputeModelsCommandOutput(BaseModel):
    task_id: str = Field(..., title='Task Id')
    status: AppRoutersComputeModelsStatus
    error: Optional[str] = Field(None, title='Error')

class AppRoutersUtilsModelsCommandOutput(BaseModel):
    task_id: str = Field(..., title='Task Id')
    status: AppRoutersUtilsModelsStatus
    error: Optional[str] = Field(None, title='Error')

class GroupList(BaseModel):
    groups: Optional[List[GroupStats]] = Field(None, title='Groups')