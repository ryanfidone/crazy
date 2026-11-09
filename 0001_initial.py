import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Genre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Enter a book genre (e.g. Science Fiction)", max_length=200)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Author",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("date_of_death", models.DateField(blank=True, null=True, verbose_name="Died")),
                ("author_image", models.ImageField(blank=True, null=True, upload_to="images/")),
            ],
            options={
                "ordering": ["last_name", "first_name"],
                "permissions": [("create_author", "Can create author"), ("edit_author", "Can edit author")],
            },
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("summary", models.TextField(help_text="Enter a brief description of the book", max_length=3000)),
                ("isbn", models.CharField(max_length=20, unique=True, verbose_name="ISBN")),
                ("book_image", models.ImageField(blank=True, null=True, upload_to="images/")),
                ("author", models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name="books", to="catalog.author")),
                ("genre", models.ManyToManyField(help_text="Select a genre for this book", to="catalog.genre")),
            ],
            options={
                "ordering": ["title"],
                "permissions": [("create_book", "Can create book"), ("edit_book", "Can edit book")],
            },
        ),
        migrations.CreateModel(
            name="BookInstance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("imprint", models.CharField(help_text="Paperback, hardcover, etc.", max_length=200)),
                ("due_back", models.DateField(blank=True, null=True)),
                ("status", models.CharField(blank=True, choices=[("m", "Maintenance"), ("o", "On loan"), ("a", "Available"), ("r", "Reserved")], default="m", max_length=1)),
                ("book", models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name="instances", to="catalog.book")),
                ("borrower", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["due_back"],
                "permissions": [("edit_bookinstance", "Can loan and manage book instances")],
            },
        ),
    ]
