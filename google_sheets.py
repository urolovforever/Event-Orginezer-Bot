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
        self.worksheet = None  # Main sheet for upcoming events
        self.past_worksheet = None  # Sheet for past events
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

                # Get or create the main worksheet for upcoming events
                try:
                    self.worksheet = self.spreadsheet.worksheet("Tadbirlar")
                except gspread.exceptions.WorksheetNotFound:
                    self.worksheet = self.spreadsheet.add_worksheet(
                        title="Tadbirlar",
                        rows=1000,
                        cols=10
                    )
                    self._setup_headers(self.worksheet)

                # Get or create the worksheet for past events
                try:
                    self.past_worksheet = self.spreadsheet.worksheet("Otgan tadbirlar")
                except gspread.exceptions.WorksheetNotFound:
                    self.past_worksheet = self.spreadsheet.add_worksheet(
                        title="Otgan tadbirlar",
                        rows=1000,
                        cols=10
                    )
                    self._setup_headers(self.past_worksheet)

                self._initialized = True
                print("Google Sheets initialized successfully (Tadbirlar + Otgan tadbirlar)")
            else:
                print("Warning: GOOGLE_SPREADSHEET_ID not configured")

        except FileNotFoundError:
            print(f"Warning: Credentials file {config.GOOGLE_SHEETS_CREDENTIALS_FILE} not found")
        except Exception as e:
            print(f"Error initializing Google Sheets: {e}")

    def _setup_headers(self, worksheet):
        """Setup header row in the worksheet."""
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
            worksheet.update('A1:J1', [headers])
            # Format header row
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
        except Exception as e:
            print(f"Error setting up headers: {e}")

    def add_event(self, event: Dict[str, Any]) -> bool:
        """
        Add a new event to Google Sheets, sorted by date and time.

        Sorting logic:
        - Future events are sorted chronologically at the top
        - Past events are sorted chronologically at the bottom
        - Maintains separation between future and past events

        Color logic:
        - Future events: WHITE background (no color)
        - Past events: GRAY background
        """
        if not self._initialized:
            return False

        try:
            # Get current time in Tashkent timezone
            local_tz = pytz.timezone(config.TIMEZONE)
            local_now = datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')

            # Prepare row data for insertion
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

            # Parse event date and time for sorting and past/future check
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
                # If parsing fails, append to the end without formatting
                self.worksheet.append_row(row_data)
                return True

            # Get all existing rows (skip header)
            all_values = self.worksheet.get_all_values()

            # Case 1: Empty sheet (only header or no data)
            if len(all_values) <= 1:
                self.worksheet.append_row(row_data)
                new_row_num = 2  # First data row
                # Apply gray background for past events
                if is_past:
                    self.worksheet.format(f'A{new_row_num}:J{new_row_num}', {
                        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                    })
                    print(f"Added first event (past) to row {new_row_num} with gray background")
                else:
                    print(f"Added first event (future) to row {new_row_num}")
                return True

            # Case 2: Event is in the past - add to the very bottom with gray background
            if is_past:
                self.worksheet.append_row(row_data)
                # Get the row number of the newly added row
                all_values = self.worksheet.get_all_values()
                new_row_num = len(all_values)
                # Apply gray background for past events
                self.worksheet.format(f'A{new_row_num}:J{new_row_num}', {
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                })
                print(f"Added past event to bottom row {new_row_num} with gray background")
                return True

            # Case 3: Event is in the future - find correct sorted position
            # We need to insert in chronological order among future events
            insert_position = None
            last_future_event_row = None

            for idx, row in enumerate(all_values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) < 4:  # Not enough columns
                    continue

                try:
                    row_date = row[2]  # Sana column (index 2)
                    row_time = row[3]  # Vaqt column (index 3)

                    if not row_date or not row_time:
                        continue

                    # Parse existing row date/time
                    r_day, r_month, r_year = map(int, row_date.split('.'))
                    r_hour, r_minute = map(int, row_time.split(':'))
                    row_datetime = local_tz.localize(datetime(r_year, r_month, r_day, r_hour, r_minute))

                    # Track last future event row
                    if row_datetime >= now:
                        last_future_event_row = idx
                        # If new event is earlier than this future event, insert here
                        if event_datetime < row_datetime:
                            insert_position = idx
                            break
                except Exception as e:
                    print(f"Error parsing row {idx}: {e}")
                    continue

            # Insert at the correct position
            if insert_position:
                # Insert before the found future event
                self.worksheet.insert_row(row_data, insert_position)
                print(f"Inserted future event at row {insert_position}")
            elif last_future_event_row:
                # Insert after the last future event (before past events section)
                self.worksheet.insert_row(row_data, last_future_event_row + 1)
                print(f"Inserted future event after last future event at row {last_future_event_row + 1}")
            else:
                # No future events found, insert at row 2 (becomes first future event)
                self.worksheet.insert_row(row_data, 2)
                print(f"Inserted as first future event at row 2")

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
        """
        Move all past events from "Tadbirlar" to "Otgan tadbirlar" sheet.

        Logic:
        - Past events (datetime < now): Move to "Otgan tadbirlar" with gray background
        - Cancelled past events: Move to "Otgan tadbirlar" with red background
        - Future events (datetime >= now): Keep in "Tadbirlar" (including cancelled ones)
        """
        if not self._initialized:
            return False

        try:
            local_tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(local_tz)

            # Get all events from "Tadbirlar" sheet
            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:  # Only header or empty
                print("No events to process in Tadbirlar sheet")
                return True

            # Track rows to delete (in reverse order to avoid index shifting)
            rows_to_delete = []

            # Process each row to find past events
            for idx, row in enumerate(all_values[1:], start=2):  # Start from row 2
                if len(row) < 4:
                    continue

                try:
                    # Get event data
                    row_title = row[1] if len(row) > 1 else ""  # Tadbir nomi column
                    row_date = row[2]  # Sana column
                    row_time = row[3]  # Vaqt column

                    if not row_date or not row_time:
                        continue

                    # Parse row date/time
                    r_day, r_month, r_year = map(int, row_date.split('.'))
                    r_hour, r_minute = map(int, row_time.split(':'))
                    row_datetime = local_tz.localize(datetime(r_year, r_month, r_day, r_hour, r_minute))

                    # Check if event is in the past
                    if row_datetime < now:
                        # Add entire row to "Otgan tadbirlar" sheet
                        self.past_worksheet.append_row(row)

                        # Get the row number of newly added row in past sheet
                        past_all_values = self.past_worksheet.get_all_values()
                        new_past_row_num = len(past_all_values)

                        # Apply appropriate background color
                        if row_title.startswith("[BEKOR QILINDI]"):
                            # Cancelled past event - RED background
                            self.past_worksheet.format(f'A{new_past_row_num}:J{new_past_row_num}', {
                                'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                            })
                            print(f"✅ Moved cancelled past event from row {idx} to Otgan tadbirlar (red)")
                        else:
                            # Regular past event - GRAY background
                            self.past_worksheet.format(f'A{new_past_row_num}:J{new_past_row_num}', {
                                'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                            })
                            print(f"✅ Moved past event '{row_title[:30]}...' from row {idx} to Otgan tadbirlar (gray)")

                        # Mark row for deletion
                        rows_to_delete.append(idx)

                    else:
                        # Future event - ensure white background (even for cancelled ones)
                        if row_title.startswith("[BEKOR QILINDI]"):
                            # Keep cancelled future events with RED background
                            self.worksheet.format(f'A{idx}:J{idx}', {
                                'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                            })
                        else:
                            # Regular future events - WHITE background
                            self.worksheet.format(f'A{idx}:J{idx}', {
                                'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                            })

                except Exception as e:
                    print(f"❌ Error processing row {idx}: {e}")
                    continue

            # Delete moved rows from "Tadbirlar" sheet (in reverse order to maintain indices)
            if rows_to_delete:
                print(f"🗑️ Deleting {len(rows_to_delete)} moved events from Tadbirlar sheet...")
                for row_num in reversed(rows_to_delete):
                    self.worksheet.delete_rows(row_num)
                print(f"✅ Successfully moved {len(rows_to_delete)} past events to Otgan tadbirlar")
            else:
                print("ℹ️ No past events found to move")

            return True

        except Exception as e:
            print(f"❌ Error in mark_past_events: {e}")
            import traceback
            traceback.print_exc()
            return False


# Global Google Sheets manager instance
sheets_manager = GoogleSheetsManager()
