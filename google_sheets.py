"""Google Sheets integration module."""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, Any, Optional
import config
from datetime import datetime
import pytz


class GoogleSheetsManager:
    """Manager for Google Sheets operations."""

    def __init__(self):
        """Initialize Google Sheets client."""
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        self._initialized = False

    def initialize(self):
        """Initialize connection to Google Sheets."""
        try:
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            # Authorize using service account credentials
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                config.GOOGLE_SHEETS_CREDENTIALS_FILE,
                scope
            )

            self.client = gspread.authorize(credentials)

            # Open the spreadsheet
            if config.GOOGLE_SPREADSHEET_ID:
                self.spreadsheet = self.client.open_by_key(config.GOOGLE_SPREADSHEET_ID)
                # Get or create the main worksheet
                try:
                    self.worksheet = self.spreadsheet.worksheet("Tadbirlar")
                except gspread.exceptions.WorksheetNotFound:
                    self.worksheet = self.spreadsheet.add_worksheet(
                        title="Tadbirlar",
                        rows=1000,
                        cols=10
                    )
                    self._setup_headers()

                self._initialized = True
                print("Google Sheets initialized successfully")
            else:
                print("Warning: GOOGLE_SPREADSHEET_ID not configured")

        except FileNotFoundError:
            print(f"Warning: Credentials file {config.GOOGLE_SHEETS_CREDENTIALS_FILE} not found")
        except Exception as e:
            print(f"Error initializing Google Sheets: {e}")

    def _setup_headers(self):
        """Setup header row in the worksheet."""
        if not self._initialized:
            return

        headers = [
            "ID",
            "Tadbir nomi",
            "Sana",
            "Vaqt",
            "Joy",
            "Izoh",
            "Bo'lim",
            "Mas'ul (F.I.Sh.)",
            "Telefon",
            "Yaratilgan vaqt"
        ]

        try:
            self.worksheet.update('A1:J1', [headers])
            # Format header row
            self.worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
        except Exception as e:
            print(f"Error setting up headers: {e}")

    def add_event(self, event: Dict[str, Any]) -> bool:
        """Add a new event to Google Sheets. Events will be reorganized automatically."""
        if not self._initialized:
            return False

        try:
            # Get current time in Tashkent timezone as fallback
            local_tz = pytz.timezone(config.TIMEZONE)
            local_now = datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')

            row_data = [
                event.get('id', ''),
                event.get('title', ''),
                event.get('date', ''),
                event.get('time', ''),
                event.get('place', ''),
                event.get('comment', 'Izoh yo\'q'),
                event.get('creator_department', ''),
                event.get('creator_name', ''),
                event.get('creator_phone', ''),
                event.get('created_at', local_now)
            ]

            # Simply append the event - reorganize_events() will sort and format later
            self.worksheet.append_row(row_data)
            print(f"✅ Added event {event.get('id')} to Google Sheets")

            # Immediately reorganize to maintain proper order
            self.reorganize_events()

            return True

        except Exception as e:
            print(f"❌ Error adding event to Google Sheets: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_event(self, event_id: int, event: Dict[str, Any]) -> bool:
        """Update an existing event in Google Sheets."""
        if not self._initialized:
            return False

        try:
            # Find and delete the old row
            cell = self.worksheet.find(str(event_id))
            if not cell:
                return False

            self.worksheet.delete_rows(cell.row)

            # Re-add the event with updated data (will be inserted in correct sorted position)
            return self.add_event(event)

        except Exception as e:
            print(f"Error updating event in Google Sheets: {e}")
            return False

    def delete_event(self, event_id: int) -> bool:
        """Delete an event from Google Sheets."""
        if not self._initialized:
            return False

        try:
            # Find the row with the event ID
            cell = self.worksheet.find(str(event_id))
            if not cell:
                return False

            self.worksheet.delete_rows(cell.row)
            return True

        except Exception as e:
            print(f"Error deleting event from Google Sheets: {e}")
            return False

    def mark_event_cancelled(self, event_id: int) -> bool:
        """Mark an event as cancelled in Google Sheets."""
        if not self._initialized:
            return False

        try:
            # Find the row with the event ID
            cell = self.worksheet.find(str(event_id))
            if not cell:
                return False

            row_num = cell.row

            # Add "[BEKOR QILINDI]" prefix to the title
            title_cell = self.worksheet.cell(row_num, 2)  # Column B (title)
            current_title = title_cell.value

            if not current_title.startswith("[BEKOR QILINDI]"):
                new_title = f"[BEKOR QILINDI] {current_title}"
                self.worksheet.update_cell(row_num, 2, new_title)

                # Also mark the row with red background
                self.worksheet.format(f'A{row_num}:J{row_num}', {
                    'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                })

            return True

        except Exception as e:
            print(f"Error marking event as cancelled in Google Sheets: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if Google Sheets is connected."""
        return self._initialized

    def mark_past_events(self):
        """Mark all past events with gray background."""
        if not self._initialized:
            return False

        try:
            local_tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(local_tz)

            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:  # Only header or empty
                return True

            for idx, row in enumerate(all_values[1:], start=2):  # Start from row 2
                if len(row) < 4:
                    continue

                try:
                    row_date = row[2]  # Sana column
                    row_time = row[3]  # Vaqt column

                    if not row_date or not row_time:
                        continue

                    # Parse row date/time
                    r_day, r_month, r_year = map(int, row_date.split('.'))
                    r_hour, r_minute = map(int, row_time.split(':'))
                    row_datetime = local_tz.localize(datetime(r_year, r_month, r_day, r_hour, r_minute))

                    # Mark as past if datetime < now
                    if row_datetime < now:
                        self.worksheet.format(f'A{idx}:J{idx}', {
                            'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                        })
                        print(f"Marked row {idx} as past event (gray background)")

                except Exception as e:
                    print(f"Error processing row {idx}: {e}")
                    continue

            print("Finished marking past events")
            return True

        except Exception as e:
            print(f"Error marking past events: {e}")
            import traceback
            traceback.print_exc()
            return False

    def reorganize_events(self):
        """Reorganize all events: future events at top sorted by date, past events at bottom with gray background."""
        if not self._initialized:
            return False

        try:
            local_tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(local_tz)

            # Get all existing rows (skip header)
            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:  # Only header or empty
                return True

            header = all_values[0]
            data_rows = all_values[1:]

            # Separate events into future and past
            future_events = []
            past_events = []
            skipped_rows = 0

            for idx, row in enumerate(data_rows, start=2):  # start=2 for row number
                if len(row) < 10:  # Skip incomplete rows
                    print(f"⚠️ Skipping row {idx}: incomplete data (only {len(row)} columns)")
                    skipped_rows += 1
                    continue

                try:
                    row_date = row[2]  # Sana column
                    row_time = row[3]  # Vaqt column

                    if not row_date or not row_time:
                        print(f"⚠️ Skipping row {idx}: missing date or time")
                        skipped_rows += 1
                        continue

                    # Validate date format (DD.MM.YYYY)
                    if len(row_date.split('.')) != 3:
                        print(f"⚠️ Skipping row {idx}: invalid date format '{row_date}'")
                        skipped_rows += 1
                        continue

                    # Validate time format (HH:MM)
                    if len(row_time.split(':')) != 2:
                        print(f"⚠️ Skipping row {idx}: invalid time format '{row_time}'")
                        skipped_rows += 1
                        continue

                    # Parse row date/time
                    r_day, r_month, r_year = map(int, row_date.split('.'))
                    r_hour, r_minute = map(int, row_time.split(':'))
                    row_datetime = local_tz.localize(datetime(r_year, r_month, r_day, r_hour, r_minute))

                    # Categorize as future or past
                    if row_datetime >= now:
                        future_events.append((row_datetime, row))
                    else:
                        past_events.append((row_datetime, row))

                except ValueError as e:
                    print(f"⚠️ Skipping row {idx}: invalid data - {e} (date='{row[2] if len(row) > 2 else 'N/A'}', time='{row[3] if len(row) > 3 else 'N/A'}')")
                    skipped_rows += 1
                    continue
                except Exception as e:
                    print(f"⚠️ Skipping row {idx}: unexpected error - {e}")
                    skipped_rows += 1
                    continue

            # Sort future events by datetime (ascending)
            future_events.sort(key=lambda x: x[0])

            # Sort past events by datetime (descending - most recent past events first)
            past_events.sort(key=lambda x: x[0], reverse=True)

            # Clear all data rows (keep header)
            if len(data_rows) > 0:
                self.worksheet.delete_rows(2, len(data_rows) + 1)

            # Reconstruct the sheet: future events first, then past events
            all_sorted_rows = [row for _, row in future_events] + [row for _, row in past_events]

            if all_sorted_rows:
                # Insert all rows at once
                for row_data in all_sorted_rows:
                    self.worksheet.append_row(row_data)

                # Apply gray background to past events
                if past_events:
                    start_past_row = len(future_events) + 2  # +2 for header and 1-indexed
                    end_past_row = start_past_row + len(past_events) - 1

                    for row_num in range(start_past_row, end_past_row + 1):
                        self.worksheet.format(f'A{row_num}:J{row_num}', {
                            'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                        })

                print(f"✅ Reorganized events: {len(future_events)} future, {len(past_events)} past, {skipped_rows} skipped (corrupted data)")

            else:
                print(f"⚠️ No valid events found. Skipped {skipped_rows} rows with corrupted data")

            return True

        except Exception as e:
            print(f"❌ Error reorganizing events: {e}")
            import traceback
            traceback.print_exc()
            return False


# Global Google Sheets manager instance
sheets_manager = GoogleSheetsManager()
