"""SQLite table definitions."""

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        accommodation_type TEXT NOT NULL,
        location TEXT NOT NULL,
        price_per_night REAL NOT NULL CHECK (price_per_night > 0),
        capacity INTEGER NOT NULL CHECK (capacity >= 1),
        amenities TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '',
        is_active INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        room_id INTEGER NOT NULL REFERENCES rooms(id),
        check_in TEXT NOT NULL,
        check_out TEXT NOT NULL,
        guests INTEGER NOT NULL CHECK (guests >= 1),
        total_price REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Confirmed',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        notes TEXT NOT NULL DEFAULT '',
        CHECK (check_out > check_in)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_bookings_room_dates ON bookings(room_id, check_in, check_out)",
    """
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        price REAL NOT NULL CHECK (price >= 0),
        description TEXT NOT NULL DEFAULT '',
        is_active INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS service_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL REFERENCES bookings(id),
        service_id INTEGER NOT NULL REFERENCES services(id),
        quantity INTEGER NOT NULL CHECK (quantity >= 1),
        total_price REAL NOT NULL,
        details TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Requested',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        intent TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)",
]