from pydantic import BaseModel
from typing import List, Optional

class ImageSet(BaseModel):
    portrait_small: Optional[str] = None
    portrait_large: Optional[str] = None
    landscape_small: Optional[str] = None
    landscape_large: Optional[str] = None

class MenuItem(BaseModel):
    id: str
    label: str
    subText: Optional[str] = None
    description: Optional[str] = None
    images: Optional[ImageSet] = None
    template: str = "LIST_ITEM"
    childrenLink: Optional[str] = None
    actionLink: Optional[str] = None
    duration: Optional[int] = None
    position: Optional[int] = None

class BrowseResponse(BaseModel):
    title: str
    viewType: str = "ARC_LIST"
    items: List[MenuItem]
    page: int = 1
    totalPages: int = 1
    totalItems: Optional[int] = None
    currentApp: Optional[str] = None
