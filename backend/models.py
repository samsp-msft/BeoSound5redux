from pydantic import BaseModel
from typing import List, Optional

class MenuItem(BaseModel):
    id: str
    label: str
    subText: Optional[str] = None
    thumbnail: Optional[str] = None
    template: str = "LIST_ITEM"
    childrenLink: Optional[str] = None
    actionLink: Optional[str] = None

class BrowseResponse(BaseModel):
    title: str
    viewType: str = "ARC_LIST"
    items: List[MenuItem]
    page: int = 1
    totalPages: int = 1
    totalItems: Optional[int] = None
