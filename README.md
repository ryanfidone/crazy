# Local Library — PyCharm Django Project

This project combines the supplied Assignment 1, Assignment 2, and Assignment 3 tutorials:
- Django Local Library catalog (books, authors, genres, book copies)
- LibraryMember group, sign-up/login, "My Books"
- Librarian author/book management, author/book images, loans and available-copy list
- Google Books API import by author and automatic book image lookup
- Custom CSS, Bootstrap templates, and a Back button

## Open in PyCharm
1. Extract `LocalLibrary_PyCharm.zip`.
2. In PyCharm choose **Open** and select the extracted `LocalLibrary_PyCharm` folder.
3. Open the PyCharm Terminal.
4. Create a virtual environment if PyCharm did not create one: `python -m venv .venv`
5. Activate it:
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
   - Windows CMD: `.venv\Scripts\activate.bat`
   - macOS/Linux: `source .venv/bin/activate`
6. Install packages: `python -m pip install -r requirements.txt`
7. Set your Google Books key as an environment variable (do not paste it into Python source):
   - Windows PowerShell: `$env:GOOGLEBOOKS_API_KEY="YOUR_NEW_RESTRICTED_KEY"`
   - Windows CMD: `set GOOGLEBOOKS_API_KEY=YOUR_NEW_RESTRICTED_KEY`
   - macOS/Linux: `export GOOGLEBOOKS_API_KEY="YOUR_NEW_RESTRICTED_KEY"`
   You can also copy `.env.example` to `.env` and fill in the key; `python-dotenv` loads it locally.
8. Run database setup:
   ```
   python manage.py makemigrations catalog
   python manage.py migrate
   python manage.py createsuperuser
   ```
9. Start the site: `python manage.py runserver`
10. Open http://127.0.0.1:8000/

## First-time setup
- Sign in at `/admin/` with your superuser.
- A `LibraryMember` group is created automatically when migrations run. The group receives view-only permissions for the catalog models.
- Add authors, genres, books, and book copies in the admin site, or use the librarian pages.
- Register new users at `/register/`; registration automatically assigns them to `LibraryMember`.
- To import books for an author, sign in as a superuser, open that author's detail page, and choose **Get Books From Google Books**.

## Google Books API key security
The key supplied in chat is not included in this project. Since it has been exposed in a chat message, rotate it in Google Cloud Console, restrict the replacement key to the Books API, and keep it in your local environment or `.env` file. Never commit `.env`.

## Notes
- The tutorial's sample `StockBook.jpg` and `StockAuthor.jpg` were not included in the uploaded documents, so this project includes generated neutral placeholder images with those exact filenames.
- Run `makemigrations` and `migrate` after opening the project. The generated database is intentionally not included.
- Assignment 2's optional PythonAnywhere deployment and Assignment 2's extra-credit email password-reset setup require account/provider configuration and are not enabled by default. Django's password reset routes/templates are included; configure SMTP settings in `locallibrary/settings.py` to send real email.
