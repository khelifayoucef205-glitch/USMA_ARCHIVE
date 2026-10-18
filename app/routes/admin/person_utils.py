from app.utils import parse_date, clean_text


def _person_values(form):
    """Validate the person fields and return the 10 column values.

    Raises ValueError with a fixed, user-facing message if invalid.
    """
    display_name = clean_text(form.get("display_name"))
    if display_name is None:
        raise ValueError("Display name is required")

    birth_date = parse_date(form.get("birth_date"))
    death_date = parse_date(form.get("death_date"))

    if birth_date and death_date and death_date < birth_date:
        raise ValueError("Death date cannot be before birth date")

    return (
        clean_text(form.get("first_name")),
        clean_text(form.get("last_name")),
        display_name,
        clean_text(form.get("first_name_ar")),
        clean_text(form.get("last_name_ar")),
        clean_text(form.get("display_name_ar")),
        birth_date,
        death_date,
        clean_text(form.get("sex")),
        form.get("country_id", type=int),
    )


def create_person(cursor, form):
    """Insert a Person from form data and return its id."""
    cursor.execute("""
        INSERT INTO Person (
            Person_First_Name, Person_Last_Name, Person_Display_Name,
            Person_First_Name_ar, Person_Last_Name_ar, Person_Display_Name_ar,
            Person_birth_date, Person_death_date, Sex, Country_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, _person_values(form))

    return cursor.lastrowid


def update_person(cursor, person_id, form):
    """Update an existing Person from form data."""
    cursor.execute("""
        UPDATE Person
        SET
            Person_First_Name = %s,
            Person_Last_Name = %s,
            Person_Display_Name = %s,
            Person_First_Name_ar = %s,
            Person_Last_Name_ar = %s,
            Person_Display_Name_ar = %s,
            Person_birth_date = %s,
            Person_death_date = %s,
            Sex = %s,
            Country_id = %s
        WHERE Person_id = %s
    """, _person_values(form) + (person_id,))