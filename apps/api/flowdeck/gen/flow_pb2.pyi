from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RecordStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RECORD_STATUS_UNSPECIFIED: _ClassVar[RecordStatus]
    RECORD_STATUS_OPEN: _ClassVar[RecordStatus]
    RECORD_STATUS_IN_PROGRESS: _ClassVar[RecordStatus]
    RECORD_STATUS_RESOLVED: _ClassVar[RecordStatus]
    RECORD_STATUS_REJECTED: _ClassVar[RecordStatus]
    RECORD_STATUS_SNOOZED: _ClassVar[RecordStatus]

class RecordPriority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RECORD_PRIORITY_UNSPECIFIED: _ClassVar[RecordPriority]
    RECORD_PRIORITY_LOW: _ClassVar[RecordPriority]
    RECORD_PRIORITY_NORMAL: _ClassVar[RecordPriority]
    RECORD_PRIORITY_HIGH: _ClassVar[RecordPriority]
    RECORD_PRIORITY_URGENT: _ClassVar[RecordPriority]

class ActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ACTION_TYPE_UNSPECIFIED: _ClassVar[ActionType]
    ACTION_TYPE_RESOLVE: _ClassVar[ActionType]
    ACTION_TYPE_REJECT: _ClassVar[ActionType]
    ACTION_TYPE_SNOOZE: _ClassVar[ActionType]
    ACTION_TYPE_REOPEN: _ClassVar[ActionType]
    ACTION_TYPE_CLAIM: _ClassVar[ActionType]
RECORD_STATUS_UNSPECIFIED: RecordStatus
RECORD_STATUS_OPEN: RecordStatus
RECORD_STATUS_IN_PROGRESS: RecordStatus
RECORD_STATUS_RESOLVED: RecordStatus
RECORD_STATUS_REJECTED: RecordStatus
RECORD_STATUS_SNOOZED: RecordStatus
RECORD_PRIORITY_UNSPECIFIED: RecordPriority
RECORD_PRIORITY_LOW: RecordPriority
RECORD_PRIORITY_NORMAL: RecordPriority
RECORD_PRIORITY_HIGH: RecordPriority
RECORD_PRIORITY_URGENT: RecordPriority
ACTION_TYPE_UNSPECIFIED: ActionType
ACTION_TYPE_RESOLVE: ActionType
ACTION_TYPE_REJECT: ActionType
ACTION_TYPE_SNOOZE: ActionType
ACTION_TYPE_REOPEN: ActionType
ACTION_TYPE_CLAIM: ActionType

class Record(_message.Message):
    __slots__ = ("id", "title", "body", "status", "priority", "queue", "assignee", "created_at", "updated_at", "version")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    ASSIGNEE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    body: str
    status: RecordStatus
    priority: RecordPriority
    queue: str
    assignee: str
    created_at: str
    updated_at: str
    version: int
    def __init__(self, id: _Optional[str] = ..., title: _Optional[str] = ..., body: _Optional[str] = ..., status: _Optional[_Union[RecordStatus, str]] = ..., priority: _Optional[_Union[RecordPriority, str]] = ..., queue: _Optional[str] = ..., assignee: _Optional[str] = ..., created_at: _Optional[str] = ..., updated_at: _Optional[str] = ..., version: _Optional[int] = ...) -> None: ...

class FacetBucket(_message.Message):
    __slots__ = ("value", "count")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    value: str
    count: int
    def __init__(self, value: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class FacetCounts(_message.Message):
    __slots__ = ("status", "priority", "queue")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    status: _containers.RepeatedCompositeFieldContainer[FacetBucket]
    priority: _containers.RepeatedCompositeFieldContainer[FacetBucket]
    queue: _containers.RepeatedCompositeFieldContainer[FacetBucket]
    def __init__(self, status: _Optional[_Iterable[_Union[FacetBucket, _Mapping]]] = ..., priority: _Optional[_Iterable[_Union[FacetBucket, _Mapping]]] = ..., queue: _Optional[_Iterable[_Union[FacetBucket, _Mapping]]] = ...) -> None: ...

class ListRecordsRequest(_message.Message):
    __slots__ = ("status", "priority", "queue", "assignee", "search", "page_size", "page_token")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    ASSIGNEE_FIELD_NUMBER: _ClassVar[int]
    SEARCH_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    status: _containers.RepeatedScalarFieldContainer[RecordStatus]
    priority: _containers.RepeatedScalarFieldContainer[RecordPriority]
    queue: _containers.RepeatedScalarFieldContainer[str]
    assignee: str
    search: str
    page_size: int
    page_token: str
    def __init__(self, status: _Optional[_Iterable[_Union[RecordStatus, str]]] = ..., priority: _Optional[_Iterable[_Union[RecordPriority, str]]] = ..., queue: _Optional[_Iterable[str]] = ..., assignee: _Optional[str] = ..., search: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListRecordsResponse(_message.Message):
    __slots__ = ("records", "next_page_token", "total", "facets")
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    FACETS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[Record]
    next_page_token: str
    total: int
    facets: FacetCounts
    def __init__(self, records: _Optional[_Iterable[_Union[Record, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total: _Optional[int] = ..., facets: _Optional[_Union[FacetCounts, _Mapping]] = ...) -> None: ...

class GetRecordRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ActOnRecordRequest(_message.Message):
    __slots__ = ("id", "action", "note", "expected_version")
    ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    NOTE_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VERSION_FIELD_NUMBER: _ClassVar[int]
    id: str
    action: ActionType
    note: str
    expected_version: int
    def __init__(self, id: _Optional[str] = ..., action: _Optional[_Union[ActionType, str]] = ..., note: _Optional[str] = ..., expected_version: _Optional[int] = ...) -> None: ...

class ActOnRecordResponse(_message.Message):
    __slots__ = ("record",)
    RECORD_FIELD_NUMBER: _ClassVar[int]
    record: Record
    def __init__(self, record: _Optional[_Union[Record, _Mapping]] = ...) -> None: ...

class GetFacetsRequest(_message.Message):
    __slots__ = ("status", "priority", "queue", "search")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    SEARCH_FIELD_NUMBER: _ClassVar[int]
    status: _containers.RepeatedScalarFieldContainer[RecordStatus]
    priority: _containers.RepeatedScalarFieldContainer[RecordPriority]
    queue: _containers.RepeatedScalarFieldContainer[str]
    search: str
    def __init__(self, status: _Optional[_Iterable[_Union[RecordStatus, str]]] = ..., priority: _Optional[_Iterable[_Union[RecordPriority, str]]] = ..., queue: _Optional[_Iterable[str]] = ..., search: _Optional[str] = ...) -> None: ...

class AuditEntry(_message.Message):
    __slots__ = ("id", "record_id", "actor", "action", "note", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    RECORD_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    NOTE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    record_id: str
    actor: str
    action: ActionType
    note: str
    created_at: str
    def __init__(self, id: _Optional[str] = ..., record_id: _Optional[str] = ..., actor: _Optional[str] = ..., action: _Optional[_Union[ActionType, str]] = ..., note: _Optional[str] = ..., created_at: _Optional[str] = ...) -> None: ...

class ListAuditLogRequest(_message.Message):
    __slots__ = ("record_id", "page_size", "page_token")
    RECORD_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    record_id: str
    page_size: int
    page_token: str
    def __init__(self, record_id: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListAuditLogResponse(_message.Message):
    __slots__ = ("entries", "next_page_token")
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[AuditEntry]
    next_page_token: str
    def __init__(self, entries: _Optional[_Iterable[_Union[AuditEntry, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...
