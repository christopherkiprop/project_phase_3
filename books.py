import psycopg2
import click

# Database connection details
DATABASE_URL = "dbname=chris user=chris password=kiprop host=localhost"

# Function to connect to the database
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Function to initialize the database and create tables
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE
        );
    ''')

    # Create Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE
        );
    ''')

    # Create Books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            author VARCHAR(255),
            publication_year INTEGER,
            status VARCHAR(50),
            user_id INTEGER,
            category_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
    ''')

    # Commit and close the connection
    conn.commit()
    cursor.close()
    conn.close()

# Initialize the database when the script is run
init_db()

# CLI interface using click
@click.group()
def cli():
    pass

# Command to create a new user
@click.command()
@click.argument('username')
def create_user(username):
    """Add a new user."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username) VALUES (%s);", (username,))
        conn.commit()
        click.echo(f"User '{username}' created.")
    except Exception as e:
        conn.rollback()
        click.echo(f"Error creating user: {e}")
    finally:
        cursor.close()
        conn.close()

# Command to add a new book (prompting for details interactively)
@click.command()
def add_book():
    """Add a new book to the user's collection."""
    
    # Prompt the user for input via the terminal
    title = click.prompt("Enter the book title")
    author = click.prompt("Enter the author name")
    year = click.prompt("Enter the publication year", type=int)
    status = click.prompt("Enter the status (e.g., Read, To Read, etc.)")
    category_name = click.prompt("Enter the category (e.g., Fiction, Non-Fiction, etc.)")
    username = click.prompt("Enter the username for this book collection")
    
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if the user exists
        cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
        user = cursor.fetchone()

        if not user:
            click.echo(f"User '{username}' does not exist.")
            return

        user_id = user[0]

        # Check if the category exists or create it
        cursor.execute("SELECT id FROM categories WHERE name = %s;", (category_name,))
        category = cursor.fetchone()

        if not category:
            cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id;", (category_name,))
            category_id = cursor.fetchone()[0]
        else:
            category_id = category[0]

        # Add the book
        cursor.execute('''
            INSERT INTO books (title, author, publication_year, status, user_id, category_id)
            VALUES (%s, %s, %s, %s, %s, %s);
        ''', (title, author, year, status, user_id, category_id))
        
        conn.commit()
        click.echo(f"Book '{title}' by {author} added to '{username}' collection.")
    except Exception as e:
        conn.rollback()
        click.echo(f"Error adding book: {e}")
    finally:
        cursor.close()
        conn.close()

# Command to list all books for a user
@click.command()
@click.argument('username')
def list_books(username):
    """List all books for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
        user = cursor.fetchone()

        if not user:
            click.echo(f"User '{username}' does not exist.")
            return

        user_id = user[0]

        cursor.execute('''
            SELECT books.title, books.author, books.publication_year, books.status, categories.name
            FROM books
            JOIN categories ON books.category_id = categories.id
            WHERE books.user_id = %s;
        ''', (user_id,))

        books = cursor.fetchall()

        if books:
            for book in books:
                title, author, year, status, category = book
                click.echo(f"{title} by {author} ({year}) - {status} [{category}]")
        else:
            click.echo(f"No books found for '{username}'.")

    except Exception as e:
        click.echo(f"Error fetching books: {e}")
    finally:
        cursor.close()
        conn.close()

# Registering the commands to the CLI
cli.add_command(create_user)
cli.add_command(add_book)
cli.add_command(list_books)

# Entry point to run the CLI
if __name__ == '__main__':
    cli()
