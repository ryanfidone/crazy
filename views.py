import os
from io import BytesIO
from datetime import date, timedelta

import requests
from PIL import Image, UnidentifiedImageError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView

from .forms import LoanBookForm
from .models import Author, Book, BookInstance, Genre


def index(request):
    context = {
        "num_books": Book.objects.count(),
        "num_instances": BookInstance.objects.count(),
        "num_instances_available": BookInstance.objects.filter(status="a").count(),
        "num_authors": Author.objects.count(),
    }
    return render(request, "catalog/index.html", context)


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = "catalog/my_books.html"
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(
            borrower=self.request.user, status="o"
        ).select_related("book").order_by("due_back")


class AvailBooksListView(PermissionRequiredMixin, generic.ListView):
    permission_required = "catalog.edit_bookinstance"
    model = BookInstance
    template_name = "catalog/bookinstance_list_available.html"
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status="a").select_related("book").order_by("book__title")


class LibrarianRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    raise_exception = True


class AuthorCreate(LibrarianRequiredMixin, CreateView):
    permission_required = "catalog.create_author"
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death", "author_image"]
    template_name = "catalog/author_form.html"

    def form_valid(self, form):
        author = form.save(commit=False)
        if not author.author_image:
            filename = f"{author.last_name}_{author.first_name}.jpg"
            _save_stock_image(author.author_image, "StockAuthor.jpg", filename)
        author.save()
        return redirect("author_detail", pk=author.pk)


class AuthorUpdate(LibrarianRequiredMixin, UpdateView):
    permission_required = "catalog.edit_author"
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death", "author_image"]
    template_name = "catalog/author_form.html"

    def form_valid(self, form):
        author = form.save(commit=False)
        if not author.author_image:
            filename = f"{author.last_name}_{author.first_name}.jpg"
            _save_stock_image(author.author_image, "StockAuthor.jpg", filename)
        author.save()
        return redirect("author_detail", pk=author.pk)


class BookCreate(LibrarianRequiredMixin, CreateView):
    permission_required = "catalog.create_book"
    model = Book
    fields = ["title", "author", "summary", "isbn", "genre", "book_image"]
    template_name = "catalog/book_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.object.book_image:
            book_image_from_api(self.object, form.cleaned_data["isbn"], form.cleaned_data["title"])
        return response


class BookUpdate(LibrarianRequiredMixin, UpdateView):
    permission_required = "catalog.edit_book"
    model = Book
    fields = ["title", "author", "summary", "isbn", "genre", "book_image"]
    template_name = "catalog/book_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.object.book_image:
            book_image_from_api(self.object, form.cleaned_data["isbn"], form.cleaned_data["title"])
        return response


def author_delete(request, pk):
    if not request.user.has_perm("catalog.delete_author"):
        messages.error(request, "You do not have permission to delete authors.")
        return redirect("author_list")
    author = get_object_or_404(Author, pk=pk)
    if request.method == "POST":
        name = f"{author.first_name} {author.last_name}"
        try:
            author.delete()
            messages.success(request, f"{name} has been deleted.")
        except Exception:
            messages.warning(request, f"{name} cannot be deleted because books exist for this author.")
        return redirect("author_list")
    return render(request, "catalog/author_delete.html", {"author": author})


def book_delete(request, pk):
    if not request.user.has_perm("catalog.delete_book"):
        messages.error(request, "You do not have permission to delete books.")
        return redirect("book_list")
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        title = book.title
        try:
            book.delete()
            messages.success(request, f"{title} has been deleted.")
        except Exception:
            messages.warning(request, f"{title} cannot be deleted because book copies exist.")
        return redirect("book_list")
    return render(request, "catalog/book_delete.html", {"book": book})


def loan_book_librarian(request, pk):
    if not request.user.has_perm("catalog.edit_bookinstance"):
        messages.error(request, "You do not have permission to loan books.")
        return redirect("index")
    book_instance = get_object_or_404(BookInstance, pk=pk)
    if request.method == "POST":
        form = LoanBookForm(request.POST, instance=book_instance)
        if form.is_valid():
            book_instance = form.save(commit=False)
            book_instance.due_back = date.today() + timedelta(weeks=4)
            book_instance.status = "o"
            book_instance.save()
            messages.success(request, "The book has been loaned successfully.")
            return redirect("all_available")
    else:
        form = LoanBookForm(instance=book_instance, initial={"book_title": book_instance.book.title})
    return render(request, "catalog/loan_book_librarian.html", {"form": form, "book_instance": book_instance})


class BookCopyCreate(LibrarianRequiredMixin, CreateView):
    permission_required = "catalog.create_bookinstance"
    model = BookInstance
    fields = ["imprint"]
    template_name = "catalog/bookinstance_form.html"

    def form_valid(self, form):
        form.instance.book = get_object_or_404(Book, pk=self.kwargs["pk"])
        form.instance.status = "a"
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("book_detail", kwargs={"pk": self.kwargs["pk"]})


def validate_image(image_bytes):
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        extrema = image.getextrema()
        # Reject completely black or completely white images.
        if all(high == 0 for low, high in extrema):
            return False
        if all(low == 255 for low, high in extrema):
            return False
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def _save_stock_image(field, stock_filename, target_filename):
    stock_path = settings.MEDIA_ROOT / "images" / stock_filename
    if stock_path.exists():
        field.save(target_filename, ContentFile(stock_path.read_bytes()), save=True)


def book_image_from_api(book, isbn, title=""):
    api_key = settings.GOOGLEBOOKS_API_KEY
    if api_key:
        try:
            response = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": f"isbn:{isbn}", "key": api_key, "maxResults": 1},
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
            items = payload.get("items", [])
            if items:
                volume = items[0].get("volumeInfo", {})
                api_title = volume.get("title", "")
                # Assignment 3 extension: avoid an unrelated ISBN result.
                if title and api_title and title.casefold() not in api_title.casefold() and api_title.casefold() not in title.casefold():
                    items = []
                if items:
                    image_url = volume.get("imageLinks", {}).get("thumbnail") or volume.get("imageLinks", {}).get("smallThumbnail")
                    if image_url:
                        image_response = requests.get(image_url.replace("http://", "https://"), timeout=8)
                        if image_response.ok and validate_image(image_response.content):
                            book.book_image.save(f"{isbn}.jpg", ContentFile(image_response.content), save=True)
                            return True
        except requests.RequestException:
            pass
    _save_stock_image(book.book_image, "StockBook.jpg", f"{isbn}.jpg")
    return False


def author_get_books_api(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Only a librarian/superuser can import books.")
        return redirect("author_detail", pk=pk)
    author = get_object_or_404(Author, pk=pk)
    api_key = settings.GOOGLEBOOKS_API_KEY
    if not api_key:
        messages.error(request, "Google Books API key is missing. Set GOOGLEBOOKS_API_KEY in your .env file.")
        return redirect("author_detail", pk=author.pk)

    author_name = f"{author.first_name} {author.last_name}"
    try:
        response = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": f'inauthor:"{author_name}"', "key": api_key, "maxResults": 40},
            timeout=10,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
    except requests.RequestException:
        messages.error(request, "Google Books API request failed. Please try again.")
        return redirect("author_detail", pk=author.pk)

    if not items:
        messages.warning(request, f"No books returned for {author_name}.")
        return redirect("author_detail", pk=author.pk)

    created_count = existing_count = error_count = 0
    for item in items:
        volume = item.get("volumeInfo", {})
        title = volume.get("title")
        if not title:
            continue
        identifiers = volume.get("industryIdentifiers", [])
        isbn = next((x.get("identifier") for x in identifiers if x.get("type") == "ISBN_13"), None)
        if not isbn:
            isbn = next((x.get("identifier") for x in identifiers if x.get("type") == "ISBN_10"), None)
        if not isbn:
            continue
        try:
            book, created = Book.objects.get_or_create(
                isbn=isbn,
                defaults={"title": title, "author": author, "summary": volume.get("description", "")[:3000]},
            )
            if created:
                created_count += 1
                image_url = volume.get("imageLinks", {}).get("thumbnail") or volume.get("imageLinks", {}).get("smallThumbnail")
                saved = False
                if image_url:
                    img_response = requests.get(image_url.replace("http://", "https://"), timeout=8)
                    if img_response.ok and validate_image(img_response.content):
                        book.book_image.save(f"{isbn}.jpg", ContentFile(img_response.content), save=True)
                        saved = True
                if not saved:
                    _save_stock_image(book.book_image, "StockBook.jpg", f"{isbn}.jpg")
            else:
                existing_count += 1
            for category in volume.get("categories", []):
                genre, _ = Genre.objects.get_or_create(name=category[:200])
                book.genre.add(genre)
            book.save()
        except Exception:
            error_count += 1

    messages.success(
        request,
        f"{created_count} books added for {author_name}. {existing_count} already existed. {error_count} processing errors.",
    )
    return redirect("author_detail", pk=author.pk)
