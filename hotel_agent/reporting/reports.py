"""Pandas-based reports and analytics."""
from datetime import date, timedelta
from typing import Dict, Optional

import pandas as pd

from hotel_agent.database.connection import Database
from hotel_agent.models.entities import make_reference
from hotel_agent.services.booking_manager import _DETAIL_SELECT

BOOKING_COLUMNS = [
    "booking_id", "status", "created_at", "check_in", "check_out", "guests", "total_price", "notes",
    "nights", "customer_id", "customer", "email", "phone", "room_id", "room_number", "room_name",
    "accommodation_type", "location", "price_per_night", "amenities",
]


class ReportGenerator:
    def __init__(self, db: Database):
        self.db = db

    # ---------- raw data frames ----------
    def bookings_df(self) -> pd.DataFrame:
        rows = self.db.query(_DETAIL_SELECT + " ORDER BY b.id")
        df = pd.DataFrame(rows, columns=BOOKING_COLUMNS)
        df["reference"] = df["booking_id"].apply(make_reference)
        return df

    def service_orders_df(self) -> pd.DataFrame:
        rows = self.db.query(
            """SELECT so.id, so.booking_id, s.name AS service, s.category, so.quantity,
                      so.total_price, so.status, so.created_at
               FROM service_orders so JOIN services s ON s.id = so.service_id ORDER BY so.id""")
        return pd.DataFrame(rows, columns=["id", "booking_id", "service", "category", "quantity",
                                           "total_price", "status", "created_at"])

    # ---------- dashboard ----------
    def dashboard_metrics(self, today: date = None) -> Dict:
        today = today or date.today()
        total_rooms = self.db.query_one("SELECT COUNT(*) AS c FROM rooms WHERE is_active = 1")["c"]
        occupied = self.db.query_one(
            """SELECT COUNT(DISTINCT b.room_id) AS c FROM bookings b JOIN rooms r ON r.id = b.room_id
               WHERE b.status = 'Confirmed' AND r.is_active = 1 AND b.check_in <= ? AND b.check_out > ?""",
            (today.isoformat(), today.isoformat()))["c"]
        bookings = self.bookings_df()
        confirmed = bookings[bookings["status"] == "Confirmed"]
        revenue = self.revenue_summary()
        return {
            "total_rooms": int(total_rooms),
            "occupied_rooms": int(occupied),
            "available_rooms": int(total_rooms - occupied),
            "occupancy_pct": round(100.0 * occupied / total_rooms, 1) if total_rooms else 0.0,
            "total_bookings": int(len(bookings)),
            "active_bookings": int(len(confirmed)),
            "cancelled_bookings": int(len(bookings) - len(confirmed)),
            "revenue_total": revenue["total"],
            "revenue_rooms": revenue["rooms"],
            "revenue_services": revenue["services"],
        }

    def recent_bookings(self, n: int = 5) -> pd.DataFrame:
        df = self.bookings_df().sort_values("booking_id", ascending=False).head(n)
        return df[["reference", "customer", "room_number", "accommodation_type", "check_in",
                   "check_out", "total_price", "status"]].reset_index(drop=True)

    # ---------- reports ----------
    def customer_report(self) -> pd.DataFrame:
        columns = ["Customer", "Email", "Phone", "Total bookings", "Active bookings",
                   "Nights booked", "Room spend", "Service spend", "Total spend"]
        customers = pd.DataFrame(self.db.query("SELECT id, full_name, email, phone FROM customers"))
        if customers.empty:
            return pd.DataFrame(columns=columns)
        bookings = self.bookings_df()
        orders = self.service_orders_df()
        orders = orders[orders["status"] != "Cancelled"].merge(
            bookings[["booking_id", "customer_id"]], on="booking_id", how="left")
        active = bookings[bookings["status"] == "Confirmed"]
        report = customers.rename(columns={"full_name": "Customer", "email": "Email", "phone": "Phone"})
        report["Total bookings"] = report["id"].map(bookings.groupby("customer_id").size()).fillna(0).astype(int)
        report["Active bookings"] = report["id"].map(active.groupby("customer_id").size()).fillna(0).astype(int)
        report["Nights booked"] = report["id"].map(active.groupby("customer_id")["nights"].sum()).fillna(0).astype(int)
        report["Room spend"] = report["id"].map(active.groupby("customer_id")["total_price"].sum()).fillna(0.0).round(2)
        report["Service spend"] = report["id"].map(orders.groupby("customer_id")["total_price"].sum()).fillna(0.0).round(2)
        report["Total spend"] = (report["Room spend"] + report["Service spend"]).round(2)
        return report[columns].sort_values("Total spend", ascending=False).reset_index(drop=True)

    def booking_report(self, status: Optional[str] = None, start: Optional[date] = None,
                       end: Optional[date] = None) -> pd.DataFrame:
        """Bookings whose stay overlaps the [start, end] window (optional) and match the status."""
        df = self.bookings_df()
        if status and status != "All":
            df = df[df["status"] == status]
        if start:
            df = df[df["check_out"] > start.isoformat()]
        if end:
            df = df[df["check_in"] <= end.isoformat()]
        out = df[["reference", "customer", "email", "room_number", "accommodation_type", "location",
                  "check_in", "check_out", "nights", "guests", "total_price", "status"]]
        return out.sort_values("check_in", ascending=False).reset_index(drop=True)

    def _night_records(self, start: date, end: date) -> pd.DataFrame:
        """One row per (room, occupied night) inside [start, end]."""
        confirmed = self.bookings_df()
        confirmed = confirmed[confirmed["status"] == "Confirmed"]
        records = []
        for _, b in confirmed.iterrows():
            day = max(date.fromisoformat(b["check_in"]), start)
            last = min(date.fromisoformat(b["check_out"]) - timedelta(days=1), end)
            while day <= last:
                records.append({"date": day, "room_id": b["room_id"], "room_number": b["room_number"],
                                "accommodation_type": b["accommodation_type"]})
                day += timedelta(days=1)
        return pd.DataFrame(records, columns=["date", "room_id", "room_number", "accommodation_type"])

    def daily_occupancy(self, start: date, end: date) -> pd.DataFrame:
        total = self.db.query_one("SELECT COUNT(*) AS c FROM rooms WHERE is_active = 1")["c"]
        nights = self._night_records(start, end)
        counts = nights.groupby("date").size() if not nights.empty else pd.Series(dtype=int)
        days = pd.date_range(start, end).date
        df = pd.DataFrame({"Date": days})
        df["Occupied rooms"] = df["Date"].map(counts).fillna(0).astype(int)
        df["Total rooms"] = int(total)
        df["Occupancy %"] = (100.0 * df["Occupied rooms"] / total).round(1) if total else 0.0
        return df

    def room_occupancy(self, start: date, end: date) -> pd.DataFrame:
        days = (end - start).days + 1
        rooms = pd.DataFrame(self.db.query(
            "SELECT id, room_number, name, accommodation_type, location FROM rooms WHERE is_active = 1 ORDER BY room_number"))
        if rooms.empty:
            return pd.DataFrame(columns=["Room", "Name", "Type", "Location", "Nights booked", "Days in period", "Occupancy %"])
        nights = self._night_records(start, end)
        booked = nights.groupby("room_id").size() if not nights.empty else pd.Series(dtype=int)
        rooms["Nights booked"] = rooms["id"].map(booked).fillna(0).astype(int)
        rooms["Days in period"] = days
        rooms["Occupancy %"] = (100.0 * rooms["Nights booked"] / days).round(1)
        rooms = rooms.rename(columns={"room_number": "Room", "name": "Name",
                                      "accommodation_type": "Type", "location": "Location"})
        return rooms[["Room", "Name", "Type", "Location", "Nights booked", "Days in period", "Occupancy %"]]

    def revenue_summary(self) -> Dict:
        bookings = self.bookings_df()
        rooms_rev = float(bookings.loc[bookings["status"] == "Confirmed", "total_price"].sum())
        orders = self.service_orders_df()
        svc_rev = float(orders.loc[orders["status"] != "Cancelled", "total_price"].sum())
        lost = float(bookings.loc[bookings["status"] == "Cancelled", "total_price"].sum())
        return {"rooms": round(rooms_rev, 2), "services": round(svc_rev, 2),
                "total": round(rooms_rev + svc_rev, 2), "cancelled_value": round(lost, 2)}

    def revenue_by_month(self) -> pd.DataFrame:
        df = self.bookings_df()
        df = df[df["status"] == "Confirmed"].copy()
        if df.empty:
            return pd.DataFrame(columns=["Month", "Bookings", "Revenue"])
        df["Month"] = df["check_in"].str[:7]
        out = df.groupby("Month").agg(Bookings=("booking_id", "count"), Revenue=("total_price", "sum")).reset_index()
        out["Revenue"] = out["Revenue"].round(2)
        return out

    def revenue_by_room_type(self) -> pd.DataFrame:
        df = self.bookings_df()
        df = df[df["status"] == "Confirmed"]
        if df.empty:
            return pd.DataFrame(columns=["Room type", "Bookings", "Nights", "Revenue"])
        out = df.groupby("accommodation_type").agg(
            Bookings=("booking_id", "count"), Nights=("nights", "sum"), Revenue=("total_price", "sum")).reset_index()
        out = out.rename(columns={"accommodation_type": "Room type"})
        out["Revenue"] = out["Revenue"].round(2)
        return out.sort_values("Revenue", ascending=False).reset_index(drop=True)

    def revenue_by_service_category(self) -> pd.DataFrame:
        df = self.service_orders_df()
        df = df[df["status"] != "Cancelled"]
        if df.empty:
            return pd.DataFrame(columns=["Category", "Orders", "Revenue"])
        out = df.groupby("category").agg(Orders=("id", "count"), Revenue=("total_price", "sum")).reset_index()
        out = out.rename(columns={"category": "Category"})
        out["Revenue"] = out["Revenue"].round(2)
        return out.sort_values("Revenue", ascending=False).reset_index(drop=True)

    @staticmethod
    def to_csv_bytes(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")