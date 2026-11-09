import uuid
from datetime import date
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Genre(models.Model):
    name = models.CharField(max_length=200, help_text="Enter a book genre (e.g. Science Fiction)")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField("Died", null=True, blank=True)
    author_image = models.ImageField(upload_to="images/", null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        permissions = [
            ("create_author", "Can create author"),
            ("edit_author", "Can edit author"),
        ]

    def get_absolute_url(self):
        return reverse("author_detail", args=[str(self.id)])

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.RESTRICT, null=True, related_name="books")
    summary = models.TextField(max_length=3000, help_text="Enter a brief description of the book")
    isbn = models.CharField("ISBN", max_length=20, unique=True)
    genre = models.ManyToManyField(Genre, help_text="Select a genre for this book")
    book_image = models.ImageField(upload_to="images/", null=True, blank=True)

    class Meta:
        ordering = ["title"]
        permissions = [
            ("create_book", "Can create book"),
            ("edit_book", "Can edit book"),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("book_detail", args=[str(self.id)])


class BookInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.RESTRICT, null=True, related_name="instances")
    imprint = models.CharField(max_length=200, help_text="Paperback, hardcover, etc.")
    due_back = models.DateField(null=True, blank=True)
    LOAN_STATUS = (
        ("m", "Maintenance"),
        ("o", "On loan"),
        ("a", "Available"),
        ("r", "Reserved"),
    )
    status = models.CharField(max_length=1, choices=LOAN_STATUS, blank=True, default="m")
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["due_back"]
        permissions = [
            ("edit_bookinstance", "Can loan and manage book instances"),
        ]

    @property
    def is_overdue(self):
        return bool(self.due_back and date.today() > self.due_back)

    def __str__(self):
        return f"{self.id} ({self.book.title if self.book else 'No book'})"
