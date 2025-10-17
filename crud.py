from typing import Any
from warnings import catch_warnings

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import Row
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, update

import models
from models import End_User, EndUserCreate, Custom_Shelf, CustomShelfCreate, To_Read_Shelf, Dropped_Shelf, \
    Current_Shelf, Read_Shelf, Book, To_Read_Shelf_Book, Dropped_Shelf_Book, Read_Shelf_Book, \
    Current_Shelf_Book, Custom_Shelf_Book_Link, Reading_Goal
from security import get_password_hash

def get_user_by_email(db: Session, email: str):
    statement = select(End_User).where(End_User.email == email)
    return db.exec(statement).first()


def create_user(db: Session, user_in: EndUserCreate) -> End_User:
    user = End_User(
        email=user_in.email,
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_custom_shelf(db: Session, owner_id: int, shelf_in: CustomShelfCreate) -> Custom_Shelf:
    custom_shelf = Custom_Shelf(end_user_id=owner_id, shelf_name=shelf_in.shelf_name)
    db.add(custom_shelf)
    db.commit()
    db.refresh(custom_shelf)
    return custom_shelf


def get_custom_shelves(db: Session, owner_id: int) -> list[Custom_Shelf]:
    statement = select(Custom_Shelf).where(Custom_Shelf.end_user_id == owner_id)
    return db.exec(statement).all()


def get_tbr_shelf(db: Session, owner_id: int) -> To_Read_Shelf:
    statement = select(To_Read_Shelf).where(To_Read_Shelf.end_user_id == owner_id)
    return db.exec(statement).first()


def get_dropped_shelf(db: Session, owner_id: int) -> Dropped_Shelf:
    statement = select(Dropped_Shelf).where(Dropped_Shelf.end_user_id == owner_id)
    return db.exec(statement).first()


def get_current_shelf(db: Session, owner_id: int) -> Current_Shelf:
    statement = select(Current_Shelf).where(Current_Shelf.end_user_id == owner_id)
    return db.exec(statement).first()


def get_read_shelf(db: Session, owner_id: int) -> Read_Shelf:
    statement = select(Read_Shelf).where(Read_Shelf.end_user_id == owner_id)
    return db.exec(statement).first()


def add_book_to_chosen_shelf(db: Session, book: Book, shelf, shelf_id) -> Book:
    found_book_statement = select(Book).where(Book.google_book_id == book.google_book_id)
    print("Book ID: ", book.google_book_id)
    found_book = db.exec(found_book_statement).first()

    # Add the book to database if not found
    if not found_book:
        # does it not read the book properly
        add_book = models.Book(
            google_book_id=book.google_book_id,
            title=book.title,
            authors=book.authors,
            description=book.description,
            number_of_pages=book.number_of_pages,
            categories=book.categories,
            published_date=book.published_date,
        )
        db.add(add_book)
        db.commit()
        db.refresh(add_book)
        found_book = db.exec(found_book_statement).first()

    match (type(shelf)):
        case models.To_Read_Shelf:
            print("This is to be added to the to read shelf")
            add_book = models.To_Read_Shelf_Book(
                to_read_shelf_id=shelf_id,
                book_id=found_book.book_id
            )
            try:
                db.add(add_book)
                db.commit()
                db.refresh(add_book)
            except IntegrityError as e:
                raise HTTPException(status_code=500, detail="This book already exists in this shelf")
        case models.Dropped_Shelf:
            print("This is to be added to the dropped shelf")
            add_book = models.Dropped_Shelf_Book(
                dropped_shelf_id=shelf_id,
                book_id=found_book.book_id
            )
            try:
                db.add(add_book)
                db.commit()
                db.refresh(add_book)
            except IntegrityError as e:
                raise HTTPException(status_code=500,
                                    detail="This book already exists in this shelf")
            print("This is to be added to the current shelf")
            add_book = models.Current_Shelf_Book(
                current_shelf_id=shelf_id,
                book_id=found_book.book_id
            )
            try:
                db.add(add_book)
                db.commit()
                db.refresh(add_book)
            except IntegrityError as e:
                raise HTTPException(status_code=500,
                                    detail="This book already exists in this shelf")
        case models.Read_Shelf:
            print("This is to be added to the read shelf")
            add_book = models.Read_Shelf_Book(
                read_shelf_id=shelf_id,
                book_id=found_book.book_id
            )
            try:
                db.add(add_book)
                db.commit()
                db.refresh(add_book)
            except IntegrityError as e:
                raise HTTPException(status_code=500,
                                    detail="This book already exists in this shelf")
        case models.Custom_Shelf:
            print("This is to be added to the custom shelf")
            statement = select(Read_Shelf_Book).where(
                Read_Shelf_Book.book_id == found_book.book_id and
                Read_Shelf_Book.read_shelf_id == shelf_id
            )
            book_in_read_shelf = db.exec(statement).first()

            # If it is not in the read book shelve
            if not book_in_read_shelf:
                add_book = models.Read_Shelf_Book(
                    read_shelf_id=shelf_id.shelf_id,
                    book_id=found_book.book_id
                )
                try:
                    db.add(add_book)
                    db.commit()
                    db.refresh(add_book)
                    add_to_custom(db, found_book.book_id, shelf_id.shelf_id, shelf_id)
                except IntegrityError as e:
                    raise HTTPException(status_code=500,
                                        detail="This book already exists in this shelf")
            else:
                try:
                    add_to_custom(db, found_book.book_id, shelf_id.shelf_id, shelf_id)
                except IntegrityError as e:
                    raise HTTPException(status_code=500,
                                        detail="This book already exists in this shelf")
        case _:
            raise HTTPException(status_code=400, detail="Unknown shelf type")

    return book


def add_to_custom(db, book_id, read_shelf_id, custom_shelf):
    print("Adding to custom shelf")
    read_shelf_book_statement = select(Read_Shelf_Book).where(
        Read_Shelf_Book.book_id == book_id and
        Read_Shelf_Book.read_shelf_id == read_shelf_id
    )
    print("READ SHELF STMT: ", read_shelf_book_statement)

    custom_shelf_statement = select(Custom_Shelf).where(
        Custom_Shelf.shelf_id == custom_shelf.shelf_id and
        Custom_Shelf.shelf_name == custom_shelf.shelf_name
    )

    print("CUSTOM SHELF STMT: ", custom_shelf_statement)
    custom_shelf = db.exec(custom_shelf_statement).first()
    read_shelf_book = db.exec(read_shelf_book_statement).first()
    print("Custom Shelf (Shelf books) is: ", custom_shelf.shelf_books)
    custom_shelf.shelf_books.append(read_shelf_book)
    db.add(custom_shelf)
    db.commit()
    db.refresh(custom_shelf)


def get_books(
        db: Session,
        owner_id: int,
        shelf
):
    print("I am getting the books")
    match (type(shelf)):
        case models.To_Read_Shelf:
            statement = select(To_Read_Shelf.shelf_id).where(
                To_Read_Shelf.end_user_id == owner_id)
            shelf_id = db.exec(statement).first()

            second_statement = select(To_Read_Shelf_Book.book_id).where(
                To_Read_Shelf_Book.to_read_shelf_id == shelf_id
            )
            all_book_ids = db.exec(second_statement).all()
            books = []

            for book_id in all_book_ids:
                statement = select(Book).where(Book.book_id == book_id)
                books.append(db.exec(statement).first())
            return books
        case models.Dropped_Shelf:
            statement = select(Dropped_Shelf.shelf_id).where(
                Dropped_Shelf.end_user_id == owner_id)
            shelf_id = db.exec(statement).first()

            second_statement = select(Dropped_Shelf_Book.book_id).where(
                Dropped_Shelf_Book.dropped_shelf_id == shelf_id
            )
            all_book_ids = db.exec(second_statement).all()
            books = []

            for book_id in all_book_ids:
                statement = select(Book).where(Book.book_id == book_id)
                books.append(db.exec(statement).first())
            return books
        case models.Current_Shelf:
            statement = select(Current_Shelf.shelf_id).where(
                Current_Shelf.end_user_id == owner_id)
            shelf_id = db.exec(statement).first()

            second_statement = select(Current_Shelf_Book.book_id).where(
                Current_Shelf_Book.current_shelf_id == shelf_id
            )
            all_book_ids = db.exec(second_statement).all()
            books = []

            for book_id in all_book_ids:
                statement = select(Book).where(Book.book_id == book_id)
                books.append(db.exec(statement).first())
            return books
        case models.Read_Shelf:
            statement = select(Read_Shelf.shelf_id).where(
                Read_Shelf.end_user_id == owner_id)
            shelf_id = db.exec(statement).first()

            second_statement = select(Read_Shelf_Book.book_id).where(
                Read_Shelf_Book.read_shelf_id == shelf_id
            )
            all_book_ids = db.exec(second_statement).all()
            books = []

            for book_id in all_book_ids:
                statement = select(Book).where(Book.book_id == book_id)
                books.append(db.exec(statement).first())
            return books
        case _:
            raise HTTPException(status_code=400, detail="Unknown shelf type")


def get_custom_books(
        db: Session,
        owner_id: int,
        shelf_name
):
    # Find the custom shelf by name and owner
    custom_shelf_statement = select(Custom_Shelf).where(
        Custom_Shelf.end_user_id == owner_id,
        Custom_Shelf.shelf_name == shelf_name
    )
    custom_shelf = db.exec(custom_shelf_statement).first()

    if not custom_shelf:
        raise HTTPException(status_code=404, detail="Custom shelf not found")

    # Get the read shelf books associated with this custom shelf
    read_shelf_books = custom_shelf.shelf_books

    # Get the actual book objects
    books = []
    for book in read_shelf_books:
        statement = select(Book).where(
            Book.book_id == book.book_id
        )
        book_to_add = db.exec(statement).first()
        if book:
            books.append(book_to_add)
    return books


# PROMPT: can you make the crud functions for reading goals so i can create, read, update, and delete them for a specific user using sqlmodel?
def create_reading_goal(db: Session, user_id: int, goal_in: models.ReadingGoalCreate):
    goal = models.Reading_Goal(
        end_user_id=user_id,
        title=goal_in.title,
        progress=goal_in.progress or 0,
        target=goal_in.target,
        active=goal_in.active if hasattr(goal_in, "active") else True
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_reading_goals(db: Session, user_id: int):
    return db.query(models.Reading_Goal).filter(models.Reading_Goal.end_user_id == user_id).all()


def get_active_goals(db: Session, user_id: int):
    return db.query(models.Reading_Goal).filter(
        models.Reading_Goal.end_user_id == user_id,
        models.Reading_Goal.active == True
    ).all()


def get_completed_goals(db: Session, user_id: int):
    return db.query(models.Reading_Goal).filter(
        models.Reading_Goal.end_user_id == user_id,
        models.Reading_Goal.active == False
    ).all()


def update_reading_goal(db: Session, user_id: int, goal_id: int, goal_in: models.ReadingGoalUpdate):
    goal = db.get(models.Reading_Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Reading goal not found")
    if goal.end_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this goal")
    for key, value in goal_in.dict(exclude_unset=True).items():
        setattr(goal, key, value)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def delete_reading_goal(db: Session, user_id: int, goal_id: int):
    goal = db.get(models.Reading_Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Reading goal not found")
    if goal.end_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this goal")
    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted"}


def update_custom_shelf_name(db: Session, user_id: int, shelf_name: str, new_shelf_name: str):
    statement = select(Custom_Shelf).where(
        Custom_Shelf.end_user_id == user_id and
        Custom_Shelf.shelf_name == shelf_name
    )
    shelf = db.exec(statement).first()
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    shelf.shelf_name = new_shelf_name
    print("SHELF NEW NAME IS :", new_shelf_name)
    try :
        db.add(shelf)
        db.commit()
        db.refresh(shelf)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Shelf name already exists for user")
    return new_shelf_name