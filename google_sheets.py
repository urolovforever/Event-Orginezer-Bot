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
        """Add a new event to Google Sheets, sorted by date and time."""
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

            # Parse event date and time for sorting and checking if past
            try:
                event_date = event.get('date', '')
                event_time = event.get('time', '')
                day, month, year = map(int, event_date.split('.'))
                hour, minute = map(int, event_time.split(':'))
                event_datetime = local_tz.localize(datetime(year, month, day, hour, minute))

                # Check if event is in the past
                now = datetime.now(local_tz)
                is_past = event_datetime < now

            except Exception as e:
                print(f"Error parsing event datetime: {e}")
                # If parsing fails, append to the end
                self.worksheet.append_row(row_data)
                return True

            # Get all existing rows (skip header)
            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:  # Only header or empty
                row_num = self.worksheet.append_row(row_data)
                # Apply gray background for past events
                if is_past:
                    new_row_num = 2  # First data row
                    self.worksheet.format(f'A{new_row_num}:J{new_row_num}', {
                        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                    })
                return True

            # If event is in the past, add to the very bottom with gray background
            if is_past:
                self.worksheet.append_row(row_data)
                # Get the row number of the newly added row
                all_values = self.worksheet.get_all_values()
                new_row_num = len(all_values)
                # Apply gray background
                self.worksheet.format(f'A{new_row_num}:J{new_row_num}', {
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                })
                print(f"Added past event to bottom row {new_row_num} with gray background")
                return True

            # For future events, find the correct position to insert (sorted by date/time)
            # We need to separate past and future events
            insert_position = None
            last_future_event_row = None

            for idx, row in enumerate(all_values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) < 4:  # Not enough columns
                    continue

                try:
                    row_date = row[2]  # Sana column
                    row_time = row[3]  # Vaqt column

                    if not row_date or not row_time:
                        continue

                    # Parse existing row date/time
                    r_day, r_month, r_year = map(int, row_date.split('.'))
                    r_hour, r_minute = map(int, row_time.split(':'))
                    row_datetime = local_tz.localize(datetime(r_year, r_month, r_day, r_hour, r_minute))

                    # Track last future event
                    if row_datetime >= now:
                        last_future_event_row = idx
                        # If new event is earlier than this future event, insert here
                        if event_datetime < row_datetime:
                            insert_position = idx
                            break
                except Exception as e:
                    print(f"Error parsing row {idx}: {e}")
                    continue

            # Insert at the correct position or after the last future event
            if insert_position:
                self.worksheet.insert_row(row_data, insert_position)
            elif last_future_event_row:
                # Insert after the last future event (before past events)
                self.worksheet.insert_row(row_data, last_future_event_row + 1)
            else:
                # No future events found, this is the first future event
                self.worksheet.insert_row(row_data, 2)

            return True

        except Exception as e:
            print(f"Error adding event to Google Sheets: {e}")
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


# Global Google Sheets manager instance
sheets_manager = GoogleSheetsManager()
