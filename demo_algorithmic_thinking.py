"""
Simple demo: how FastAPI avoids doing the same work twice.

Story: imagine opening a database connection is slow. If two different
parts of your code both need that connection, FastAPI is smart enough to
open it only ONCE and reuse it. This file proves that, using FastAPI's
real code (not a copy) from fastapi/dependencies/utils.py.
"""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

# Counts how many times the "slow" function actually runs.
times_db_was_opened = 0


def open_database_connection():
    """Pretend this is slow and expensive, like a real database connection."""
    global times_db_was_opened
    times_db_was_opened += 1
    return f"connection #{times_db_was_opened}"


def get_current_user(db=Depends(open_database_connection)):
    # This needs the database connection.
    return f"user using {db}"


def get_settings(db=Depends(open_database_connection)):
    # This ALSO needs the database connection.
    return f"settings using {db}"


@app.get("/items")
def read_items(user=Depends(get_current_user), settings=Depends(get_settings)):
    # Both "user" and "settings" need open_database_connection().
    # Question: does FastAPI open it twice, or share one connection?
    return {"user": user, "settings": settings}


def show_dependency_tree(dependant, depth=0):
    """Prints who-needs-who, so you can see the structure FastAPI built."""
    name = getattr(dependant.call, "__name__", "read_items (the endpoint)")
    print("  " * depth + f"- {name}")
    for sub in dependant.dependencies:
        show_dependency_tree(sub, depth + 1)


if __name__ == "__main__":
    route = next(r for r in app.routes if getattr(r, "path", None) == "/items")

    print("Step 1: What FastAPI figured out needs what:")
    show_dependency_tree(route.dependant)

    print("\nStep 2: Make one real request to /items...")
    response = TestClient(app).get("/items")
    print("Server replied:", response.json())

    print(f"\nStep 3: open_database_connection() actually ran {times_db_was_opened} time(s).")
    assert times_db_was_opened == 1, "it ran more than once - something is wrong"
    print("Confirmed: FastAPI reused the same connection instead of opening it twice.")
