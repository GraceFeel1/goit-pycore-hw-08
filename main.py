from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps
import pickle


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")

        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        found_phone = self.find_phone(phone)

        if found_phone:
            self.phones.remove(found_phone)
        else:
            raise ValueError("Phone number not found")

    def edit_phone(self, old_phone, new_phone):
        found_phone = self.find_phone(old_phone)

        if found_phone:
            found_phone.value = Phone(new_phone).value
        else:
            raise ValueError("Phone number not found")

    def find_phone(self, phone):
        for existing_phone in self.phones:
            if existing_phone.value == phone:
                return existing_phone

        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(phone.value for phone in self.phones)

        result = f"Contact name: {self.name.value}, phones: {phones}"

        if self.birthday:
            result += f", birthday: {self.birthday}"

        return result


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Contact not found")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value

            try:
                birthday_this_year = birthday.replace(year=today.year)
            except ValueError:
                birthday_this_year = birthday.replace(
                    year=today.year,
                    day=28
                )

            if birthday_this_year < today:
                try:
                    birthday_this_year = birthday_this_year.replace(
                        year=today.year + 1
                    )
                except ValueError:
                    birthday_this_year = birthday_this_year.replace(
                        year=today.year + 1,
                        day=28
                    )

            days_until_birthday = (birthday_this_year - today).days

            if 0 <= days_until_birthday <= 7:
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime(
                            "%d.%m.%Y"
                        ),
                    }
                )

        return upcoming_birthdays



def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()
    except (pickle.PickleError, EOFError, AttributeError, ValueError):
        return AddressBook()



def input_error(func):
    @wraps(func)
    def inner(args, book):
        try:
            return func(args, book)

        except ValueError as error:
            return str(error)

        except KeyError as error:
            return str(error)

        except IndexError:
            return "Please provide all required arguments."

        except TypeError:
            return "Invalid command arguments."

    return inner



@input_error
def add_contact(args, book):
    name, phone, *_ = args

    record = book.find(name)

    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)

        return "Contact added."

    record.add_phone(phone)

    return "Contact updated."


@input_error
def change_contact(args, book):
    name, old_phone, new_phone, *_ = args

    record = book.find(name)

    if record is None:
        return "Contact not found."

    record.edit_phone(old_phone, new_phone)

    return "Contact updated."


@input_error
def show_phone(args, book):
    name, *_ = args

    record = book.find(name)

    if record is None:
        return "Contact not found."

    if not record.phones:
        return "No phone numbers."

    return "; ".join(phone.value for phone in record.phones)


@input_error
def add_birthday(args, book):
    name, birthday, *_ = args

    record = book.find(name)

    if record is None:
        return "Contact not found."

    record.add_birthday(birthday)

    return "Birthday added."


@input_error
def show_birthday(args, book):
    name, *_ = args

    record = book.find(name)

    if record is None:
        return "Contact not found."

    if record.birthday is None:
        return "Birthday not set."

    return str(record.birthday)


@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "No upcoming birthdays."

    result = []

    for birthday in upcoming:
        result.append(
            f"{birthday['name']}: {birthday['congratulation_date']}"
        )

    return "\n".join(result)



def parse_input(user_input):
    parts = user_input.strip().split()

    if not parts:
        return "", []

    command = parts[0].lower()
    args = parts[1:]

    return command, args



def main():

    book = load_data()

    print("Welcome to the assistant bot!")

    while True:
        try:
            user_input = input("Enter a command: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGood bye!")
            save_data(book)
            break

        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)

            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            if not book.data:
                print("No contacts found.")
            else:
                for record in book.data.values():
                    print(record)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()