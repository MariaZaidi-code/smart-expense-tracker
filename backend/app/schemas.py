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
    currency: str = "USD"
    description: Optional[str] = None
    category_id: Optional[int] = None
    date: Optional[datetime] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    currency: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    date: Optional[datetime] = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: float
    currency: str = "USD"
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
    currency: str = "USD"
    source: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    currency: Optional[str] = None
    source: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None


class IncomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: float
    currency: str = "USD"
    source: Optional[str] = None
    date: datetime
    notes: Optional[str] = None
    created_at: datetime


class RecurringExpenseBase(BaseModel):
    amount: float = Field(gt=0)
    currency: str = "USD"
    description: Optional[str] = None
    category_id: Optional[int] = None
    frequency: str = "monthly"
    next_run: Optional[datetime] = None
    active: bool = True


class RecurringExpenseCreate(RecurringExpenseBase):
    pass


class RecurringExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    currency: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    frequency: Optional[str] = None
    next_run: Optional[datetime] = None
    active: Optional[bool] = None


class RecurringExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: float
    currency: str = "USD"
    description: Optional[str] = None
    category_id: Optional[int] = None
    frequency: str
    next_run: datetime
    active: bool
    created_at: datetime


class CurrencyBase(BaseModel):
    code: str
    rate: float = Field(gt=0)


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(BaseModel):
    rate: float = Field(gt=0)


class CurrencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    rate: float
    updated_at: datetime
