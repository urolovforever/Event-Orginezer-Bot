"""Google Sheets integration module."""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, Any, Optional
import config
from datetime import datetime


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
        """Add a new event to Google Sheets."""
        if not self._initialized:
            return False

        try:
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
                event.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            ]

            self.worksheet.append_row(row_data)
            return True

        except Exception as e:
            print(f"Error adding event to Google Sheets: {e}")
            return False

    def update_event(self, event_id: int, event: Dict[str, Any]) -> bool:
        """Update an existing event in Google Sheets."""
        if not self._initialized:
            return False

        try:
            # Find the row with the event ID
            cell = self.worksheet.find(str(event_id))
            if not cell:
                return False

            row_num = cell.row

            # Update the row
            row_data = [
                event.get('id', event_id),
                event.get('title', ''),
                event.get('date', ''),
                event.get('time', ''),
                event.get('place', ''),
                event.get('comment', 'Izoh yo\'q'),
                event.get('creator_department', ''),
                event.get('creator_name', ''),
                event.get('creator_phone', ''),
                event.get('created_at', '')
            ]

            self.worksheet.update(f'A{row_num}:J{row_num}', [row_data])
            return True

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


# Global Google Sheets manager instance
sheets_manager = GoogleSheetsManager()
