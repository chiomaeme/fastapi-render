from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, ARRAY, String, UniqueConstraint
from pydantic import EmailStr
from datetime import datetime
from enum import Enum

class Token(SQLModel):
    access_token: str
    token_type: str


class Image_Url(SQLModel, table=True):
    image_url_id: int | None = Field(default=None, primary_key=True)
    url: str


class Goal_Label(Enum):
    COMPLETE = 'Completed'
    INCOMPLETE = 'Ongoing'


class Goal_Status(SQLModel, table=True):
    goal_status_id: int | None = Field(default=None, primary_key=True)
    label: Goal_Label = Field(Goal_Label.INCOMPLETE)


class Transfer_History(SQLModel, table=True):
    transfer_history_id: int | None = Field(default=None, primary_key=True)


class EndUserBase(SQLModel):
    username: str
    email: str = Field(index=True, unique=True)


class End_User(EndUserBase, table=True):
    end_user_id: int | None = Field(default=None, primary_key=True)
    image_url_id: int | None = Field(default=None, foreign_key="image_url.image_url_id")
    transfer_history_id: int | None = Field(default=None, foreign_key="transfer_history.transfer_history_id")
    password_hash: str
    created_at: datetime =Field(default=datetime.now())


class EndUserCreate(EndUserBase):
    password: str

class EndUserRead(EndUserBase):
    end_user_id: int

    class Config:
        from_attributes = True


class EndUserLogin(SQLModel):
    email: EmailStr
    password: str

# PROMPT: create SQLModel classes for a reading goal system. make a table model with id, user id, title, target, and active status. a model for creating a goal with title, target, optional progress, and active bool. a model for updating a goal.
class Reading_Goal(SQLModel, table=True):
    reading_goal_id: Optional[int] = Field(default=None, primary_key=True)
    end_user_id: int
    title: str
    target: int
    active: bool = False

class ReadingGoalCreate(SQLModel):
    title: str
    target: int
    progress: Optional[int] = 0
    active: Optional[bool] = True

class ReadingGoalUpdate(SQLModel):
    title: Optional[str] = None
    target: Optional[int] = None
    active: Optional[bool] = None

class ReadingGoalRead(Reading_Goal):
    reading_goal_id: int
    end_user_id: int

    class Config:
        from_attributes = True

class Recommendation(SQLModel, table=True):
    recommendation_id: int | None = Field(default=None, primary_key=True)
    end_user_id: int | None = Field(default=None, foreign_key="end_user.end_user_id")


class CustomShelfBase(SQLModel):
    shelf_name: str


class Custom_Shelf_Book_Link(SQLModel, table=True):
    custom_shelf_id: Optional[int] = Field(default=None, foreign_key="custom_shelf.shelf_id", primary_key=True)
    bookshelf_id: Optional[int] = Field(default=None, foreign_key="read_shelf_book.bookshelf_id", primary_key=True)


class Custom_Shelf(CustomShelfBase, table=True):
    shelf_id: Optional[int] = Field(default=None, primary_key=True)
    end_user_id: Optional[int] = Field(default=None, foreign_key="end_user.end_user_id")
    shelf_books: List["Read_Shelf_Book"] = Relationship(back_populates="custom_shelves", link_model=Custom_Shelf_Book_Link)


class CustomShelfCreate(CustomShelfBase):
    pass


class CustomShelfUpdate(CustomShelfBase):
    shelf_name: Optional[str] = None


class To_Read_Shelf(SQLModel, table=True):
    shelf_id: int | None = Field(default=None, primary_key=True)
    end_user_id: int | None = Field(default=None, foreign_key="end_user.end_user_id")
    shelf_name: str = Field(default="Want to Read")


class Dropped_Shelf(SQLModel, table=True):
    shelf_id: int | None = Field(default=None, primary_key=True)
    end_user_id: int | None = Field(default=None, foreign_key="end_user.end_user_id")
    shelf_name: str = Field(default="Dropped")


class Current_Shelf(SQLModel, table=True):
    shelf_id: int | None = Field(default=None, primary_key=True)
    end_user_id: int | None = Field(default=None, foreign_key="end_user.end_user_id")
    shelf_name: str = Field(default="Currently Reading")


class Read_Shelf(SQLModel, table=True):
    shelf_id: int | None = Field(default=None, primary_key=True)
    end_user_id: int | None = Field(default=None, foreign_key="end_user.end_user_id")
    shelf_name: str = Field(default="Read")


class Book(SQLModel, table=True):
    book_id: Optional[int] = Field(default=None, primary_key=True)
    google_book_id: str = Field(unique=True)
    title: str
    authors: List[str] | None = Field(sa_column=Column(ARRAY(String)), default_factory=list)
    description: str
    number_of_pages: int
    categories: List[str] | None = Field(sa_column=Column(ARRAY(String)), default_factory=list)
    published_date: str | None
    # date_read: datetime
    # rating: float | None


class Read_Shelf_Book(SQLModel, table=True):
    bookshelf_id: int | None = Field(default=None, primary_key=True)
    read_shelf_id: int | None = Field(default=None, foreign_key="read_shelf.shelf_id")
    custom_shelves: List["Custom_Shelf"] = Relationship(
        back_populates="shelf_books",
        link_model=Custom_Shelf_Book_Link
    )
    book_id: int | None = Field(default=None, foreign_key="book.book_id")
    reading_goal_id: int | None = Field(default=None, foreign_key="reading_goal.reading_goal_id")
    date_read: datetime
    rating: float | None
    __table_args__ = (UniqueConstraint("book_id", "read_shelf_id", name="unique_read_shelf_book"),)

class To_Read_Shelf_Book(SQLModel, table=True):
    bookshelf_id: int | None = Field(default=None, primary_key=True)
    to_read_shelf_id: int | None = Field(default=None, foreign_key="to_read_shelf.shelf_id")
    book_id: int | None = Field(default=None, foreign_key="book.book_id")
    upcoming_book_value: int | None
    __table_args__ = (UniqueConstraint("book_id", "to_read_shelf_id", name="unique_to_read_shelf_book"),)


class Dropped_Shelf_Book(SQLModel, table=True):
    bookshelf_id: int | None = Field(default=None, primary_key=True)
    dropped_shelf_id: int = Field(default=None, foreign_key="dropped_shelf.shelf_id")
    book_id: int | None = Field(default=None, foreign_key="book.book_id")
    __table_args__ = (UniqueConstraint("book_id", "dropped_shelf_id", name="unique_dropped_shelf_book"),)


class Current_Shelf_Book(SQLModel, table=True):
    bookshelf_id: int | None = Field(default=None, primary_key=True)
    current_shelf_id: int = Field(default=None, foreign_key="current_shelf.shelf_id")
    book_id: int | None = Field(default=None, foreign_key="book.book_id")
    __table_args__ = (UniqueConstraint("book_id", "current_shelf_id", name="unique_current_shelf_book"),)


class Imported_Book(SQLModel, table=True):
    imported_book_id: int | None = Field(default=None, primary_key=True)
    book_id: int | None = Field(default=None, foreign_key="book.book_id", unique=True)
    transfer_history_id: int | None = Field(default=None, foreign_key="transfer_history.transfer_history_id")
    review: str
    date_read: datetime
    original_shelf: str


class Journal_Entry(SQLModel, table=True):
    journal_entry_id: int | None = Field(default=None, primary_key=True)
    book_id: int | None = Field(default=None, foreign_key="book.book_id")
    end_user_id: int | None = Field(default=None, foreign_key="end_user.end_user_id")


class Log_Section(SQLModel, table=True):
    log_section_id: int | None = Field(default=None, primary_key=True)
    journal_entry_id: int | None = Field(default=None, foreign_key="journal_entry.journal_entry_id")
    section_name: str
    entry_text: str
    original_date: datetime
    edited_date: datetime