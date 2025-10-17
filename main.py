from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session
import models, crud, security, database

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
def on_startup():
    database.init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to Rad Reads"}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_session),
) -> models.End_User:
    email = security.decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/register/", response_model=models.EndUserRead)
def register(user_in: models.EndUserCreate, db: Session = Depends(database.get_session)):
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_in)
    return user

@app.post("/login", response_model=models.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_session),
):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = security.create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me", response_model=models.EndUserRead)
def read_users_me(current_user: models.End_User = Depends(get_current_user)):
    return current_user

@app.post("/shelf/", response_model=models.Custom_Shelf)
def create_shelf(
    shelf_in: models.CustomShelfCreate,
    current_user: models.End_User = Depends(get_current_user),
    db: Session = Depends(database.get_session),
):
    return crud.create_custom_shelf(db, current_user.end_user_id, shelf_in)

@app.get("/shelves/me")
def read_shelves(
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user)
):
    shelves = crud.get_custom_shelves(db, current_user.end_user_id)
    return [shelf for shelf in shelves]

@app.get("/defaultShelves/me")
def read_all_default_shelves(
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),
):
    shelves = [crud.get_tbr_shelf(db, current_user.end_user_id),
               crud.get_dropped_shelf(db, current_user.end_user_id),
               crud.get_current_shelf(db, current_user.end_user_id),
               crud.get_read_shelf(db, current_user.end_user_id)]
    return shelves


@app.post("/shelves/tbr")
def add_book_to_tbr_shelf(
        book_in: models.Book,
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user)
):
    # Get the user's TBR shelf
    shelf = crud.get_tbr_shelf(db, current_user.end_user_id)
    print("BOOK ID ADDING: ", book_in.google_book_id)
    return crud.add_book_to_chosen_shelf(db, book_in, models.To_Read_Shelf(), shelf.shelf_id)


@app.post("/shelves/dropped")
def add_book_to_dropped_shelf(
        book_in: models.Book,
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user)
):
    shelf = crud.get_dropped_shelf(db, current_user.end_user_id)
    return crud.add_book_to_chosen_shelf(db, book_in, models.Dropped_Shelf(), shelf.shelf_id)


@app.post("/shelves/current")
def add_book_to_current_shelf(
        book_in: models.Book,

        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user)
):
    shelf = crud.get_current_shelf(db, current_user.end_user_id)
    return crud.add_book_to_chosen_shelf(db, book_in, models.Current_Shelf(), shelf.shelf_id)


@app.post("/shelves/read")
def add_book_to_read_shelf(
        book_in: models.Book,
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user)
):
    # Get the user's TBR shelf
    shelf = crud.get_read_shelf(db, current_user.end_user_id)
    return crud.add_book_to_chosen_shelf(db, book_in, models.Read_Shelf(), shelf.shelf_id)


@app.post("/shelves/custom/{shelf_name}")
def add_book_to_custom_shelf(
        shelf_name: str,
        book_in: models.Book,
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),
):
    # Get the user's TBR shelf
    shelves = crud.get_custom_shelves(db, current_user.end_user_id)
    for shelf in shelves:
        if shelf.shelf_name == shelf_name:
            return crud.add_book_to_chosen_shelf(db, book_in, models.Custom_Shelf(), shelf)

    return None


@app.get("/shelves/tbr")
def get_books_from_current_shelf(
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),
):
    return crud.get_books(db, current_user.end_user_id, models.To_Read_Shelf())


@app.get("/shelves/dropped")
def get_books_from_dropped_shelf(
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),
):
    return crud.get_books(db, current_user.end_user_id, models.Dropped_Shelf())

@app.get("/shelves/read")
def get_books_from_current_shelf(
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),
):
    return crud.get_books(db, current_user.end_user_id, models.Read_Shelf())


@app.get("/shelves/custom/{name}")
def get_books_from_current_shelf(
        name: str,
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),

):
    return crud.get_custom_books(db, current_user.end_user_id, name)


@app.get("/shelves/current")
def get_books_from_current_shelf(
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),
):
    return crud.get_books(db, current_user.end_user_id, models.Current_Shelf())


# PROMPT: can you make fastapi endpoints for reading goals so i can create, view, update, and delete them for the logged-in user? i also want endpoints for all goals, active goals, and completed goals, using my sqlmodel models readinggoalcreate, readinggoalupdate, and readinggoalread
@app.post("/goals/", response_model=models.ReadingGoalRead)
def create_goal(goal_in: models.ReadingGoalCreate, db: Session = Depends(database.get_session),
                current_user: models.End_User = Depends(get_current_user)):
    return crud.create_reading_goal(db, current_user.end_user_id, goal_in)


@app.get("/goals/me", response_model=list[models.ReadingGoalRead])
def get_my_goals(db: Session = Depends(database.get_session),
                 current_user: models.End_User = Depends(get_current_user)):
    return crud.get_reading_goals(db, current_user.end_user_id)


@app.get("/goals/active", response_model=list[models.ReadingGoalRead])
def get_active_goals(db: Session = Depends(database.get_session),
                     current_user: models.End_User = Depends(get_current_user)):
    return crud.get_active_goals(db, current_user.end_user_id)


@app.get("/goals/completed", response_model=list[models.ReadingGoalRead])
def get_completed_goals(db: Session = Depends(database.get_session),
                        current_user: models.End_User = Depends(get_current_user)):
    return crud.get_completed_goals(db, current_user.end_user_id)


@app.put("/goals/{goal_id}", response_model=models.ReadingGoalRead)
def update_goal(goal_id: int, goal_in: models.ReadingGoalUpdate, db: Session = Depends(database.get_session),
                current_user: models.End_User = Depends(get_current_user)):
    return crud.update_reading_goal(db, current_user.end_user_id, goal_id, goal_in)


@app.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(database.get_session),
                current_user: models.End_User = Depends(get_current_user)):
    return crud.delete_reading_goal(db, current_user.end_user_id, goal_id)


@app.put("/shelves/custom/{shelf_name}/{new_shelf_name}")
def update_shelf(
        shelf_name: str,
        new_shelf_name: str,
        db: Session = Depends(database.get_session),
        current_user: models.End_User = Depends(get_current_user),
):
    return crud.update_custom_shelf_name(db, current_user.end_user_id, shelf_name, new_shelf_name)
