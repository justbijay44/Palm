import re
import json
from datetime import datetime
from typing import Dict, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Booking
from app.services.rag.llm_services import LLMServices

class BookingService:
    def __init__(self):
        self.llm_service = LLMServices()

    async def extract_booking_info(self, user_message: str) -> Dict[str, Optional[str]]:
        """
        Using llm extract the info
        """

        extraction_prompt = f"""
            Extract following information from the user's message. Return only JSON object with exact keys:
            - "name": person's full name or null if not provided
            - "email": email address or null if not provided
            - "phone_number": contact detail or null if not provided
            - "date": date in YYYY-MM-DD format or null if not provided
            - "time": time in HH:MM 24-hours format or null if not provided

        User message: "{user_message}"

        Rules:
        - If date is relative (like "tomorrow", "next Monday"), convert to actual date
        - Convert time to 24-hour format (3pm -> 15:00)
        - Today's date is {datetime.now().strftime('%Y-%m-%d')}
        - Return ONLY valid JSON, no explanations

        Example Output:
        {{"name": "John Doe", "email": "john@example.com","phone_number": "9812345678", "date": "2024-12-01", "time": "15:00"}}

        """

        messages = [
            {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
            {"role": "user", "content": extraction_prompt},
        ]

        print("Extracting the information with LLM")
        response = await self.llm_service.generate_response(messages,  temperature=0.1)

        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            booking_data = json.loads(response.strip())
            print(f"Extracted: {booking_data}")
            return booking_data
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response: {e}")
            print(f"Raw response: {response}")
            return {"name": None, "email": None, "phone_number": None, "date": None, "time": None}

    def validate_booking(self, booking_data: Dict) -> Tuple[bool, str]:
        """
        Validate the extracted info
        returns [is_valid, error_message]
        """

        date_obj = datetime.strptime(booking_data['date'], "%Y-%m-%d").date()
        today = datetime.utcnow().date()

        if date_obj < today:
            return False, "Date cannot be in the past"
        
        required = ["name", "email", "phone_number", "date", "time"]
        missing = [field for field in required if not booking_data.get(field)]

        if missing:
            return False, f"Missing required information: {', '.join(missing)}"
        
        # validation
        email = booking_data["email"]
        number = booking_data["phone_number"]
        # test@example.com
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not re.match(email_pattern, email):
            return False, f"Invalid email format: {email}"
        
        phone_number_pattern = r'^(97|98)\d{8}$'
        if not re.match(phone_number_pattern, number):
            return False, "Invalid phone number format"

        # time format validate
        try:
            datetime.strptime(booking_data['time'], "%H:%M")
        except ValueError:
            return False, f"Invalid time format: {booking_data['time']} (expected HH:MM)"

        # date format validate
        try:
            datetime.strptime(booking_data['date'], "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: {booking_data['date']} (expected YYYY-MM-DD)"
        
        return True, ""

    async def create_booking(self, booking_data: Dict, session: AsyncSession) -> Booking:
        booking = Booking(
            name=booking_data["name"],
            email=booking_data["email"],
            phone_number=booking_data["phone_number"],
            date=booking_data["date"],
            time=booking_data["time"],
            status="pending",
        )

        try:
            session.add(booking)
            await session.commit()
            await session.refresh(booking)
        except Exception:
            await session.rollback()
            raise

        print(f"Booking created with ID: {booking.id}")
        return booking
    
    
