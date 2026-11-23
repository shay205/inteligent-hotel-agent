# AI-Powered Intelligent Hotel Booking and Guest Assistance Agent

A university project built with **Python, Streamlit, SQLite and Pandas**. It collects guest
preferences, ranks rooms with an explainable scoring algorithm, answers questions through a
keyword-based NLP chatbot, prevents double-booking and produces reports and confirmations.

The hotel is called **Luxury Grand Hotel**.

## Setup (Windows PowerShell)

```powershell
cd hotel_ai_agent                                                                      
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks the activation script, run once:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

The database file `data/hotel.db` is created and filled with initial data on first start.
Delete that file to reset the initial data.

## Run the tests

```powershell
python -m unittest discover -s tests -t . -v
```

(With pytest installed, `pytest` also works.)

## Pages

| Page | What it does |
|---|---|
| Dashboard | Total rooms, available today, bookings, revenue, recent bookings, charts |
| Find a Room | Preference form, ranked recommendations with scores and reasons, filters, alternatives, service suggestions |
| AI Hotel Assistant | Chatbot with saved history and a visible intent label |
| Room Management | Add, edit, delete rooms and view availability by date |
| Booking Management | Reserve, check availability, view details, cancel, download confirmations |
| Additional Services | Catalogue, suggestions, ordering, managing services |
| Reports and Analytics | Customer, booking, occupancy and revenue reports with CSV download |

## Architecture

```
UI (app.py, ui/)  ->  AI (hotel_agent/ai/)  ->  Services (hotel_agent/services/)  ->  Database (hotel_agent/database/)
                      Reporting (hotel_agent/reporting/)  ->  Database
```

Each layer only talks to the layer below it. All SQL lives in `database/` and the service classes.

## How the AI works

**Recommendation (`ai/recommender.py`)** - every room gets points: location 30, budget 25,
accommodation type 20, capacity 15, amenities 10 (total 100). Rooms are sorted by score and each
point source becomes a plain-English reason. Rooms that are too small or already booked are
detected; if nothing fits, preferences are relaxed step by step and alternatives are suggested.

**NLP (`ai/nlp/`)** - clean text -> tokenize -> remove stop-words -> light stemming. The intent
classifier counts keyword hits (+1) and phrase hits (+2) per intent and picks the highest, with a
priority list for ties. The entity extractor finds room types, locations, budgets, guests, dates
and amenities. The chatbot reads real data from SQLite, so it never invents prices.

**Service suggestions (`ai/service_recommender.py`)** - rules link interests, location, stay length,
group size and room type to service categories, then rank the matching services.

## Double-booking prevention

Two stays overlap when `new_check_in < existing_check_out AND new_check_out > existing_check_in`.
The check and the insert run inside one `BEGIN IMMEDIATE` SQLite transaction
(`BookingManager.create_booking`), so simultaneous requests cannot both succeed.
Check-out day is free for the next guest, and cancelled bookings free the room.

## Demo script

1. Dashboard: point out the demo-data banner and the live numbers.
2. Find a Room: Beachfront, Deluxe, budget 150, 2 guests, next week. Show scores and reasons.
3. Book the top room. Download the confirmation.
4. Try booking the same room for the same dates. It is refused.
5. Assistant: "How much is a deluxe room?", "Which rooms have a sea view?", "Suggest a room under $150 for 2 guests".
6. Additional Services: order a spa session for your booking.
7. Reports: show occupancy and revenue, then download a CSV.
8. Close and reopen the app: the booking is still there.