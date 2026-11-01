from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CategoryBase(BaseModel):
    name: str
    type: str = "expense"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str
    user_id: Optional[int] = None
    is_default: bool = False


class ExpenseBase(BaseModel):
    amount: float = Field(gt=0)
    description: Optional[str] = None
    category_id: Optional[int] = None
    date: Optional[datetime] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = None
    category_id: Optional[int] = None
    date: Optional[datetime] = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: float
    description: Optional[str] = None
    category_id: Optional[int] = None
    date: datetime
    created_at: datetime


class BudgetBase(BaseModel):
    amount: float = Field(gt=0)
    period: str = "monthly"
    category_id: Optional[int] = None
    start_date: Optional[datetime] = None


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    period: Optional[str] = None
    category_id: Optional[int] = None
    start_date: Optional[datetime] = None


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    category_id: Optional[int] = None
    amount: float
    period: str
    start_date: datetime
    created_at: datetime


class IncomeBase(BaseModel):
    amount: float = Field(gt=0)
    source: Optional[str] = None
    date: Optional[datetime] = None


class IncomeCreate(IncomeBase):
    pass


class IncomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: float
    source: Optional[str] = None
    date: datetime
    created_at: datetime
