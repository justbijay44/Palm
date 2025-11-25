from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.services.rag.rag_pipeline import RAGPipeline
from app.services.rag.booking_service import BookingService
from app.db.models import Booking
from app.db.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()

rag_pipeline = RAGPipeline()

class QueryRequest(BaseModel):
    query: str = Field(..., description="User's Question")
    session_id: str = Field(..., description="Users unique identifier")
    top_k: int = Field(5, description="Top 5 relvant chunk")

class QueryRespond(BaseModel):
    answer: str
    sources: List[Dict]
    session_id: str

@router.post('/query', response_model=QueryRespond)
async def query_document(request: QueryRequest):
    """
    - Retrive relavant chunks
    - Use redis for conversation history
    - Generate answer with llm
    """

    try:
        answer, source = await rag_pipeline.query(
            user_query= request.query,
            session_id= request.session_id,
            top_k= request.top_k
        )

        return QueryRespond(
            answer=answer,
            sources=source,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query Failed: {str(e)}")
    
@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """ Clear the chat history for a session. """
    try:
        await rag_pipeline.redis_service.clear_session(session_id)
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Booking Service

booking_service = BookingService()

class BookingRequest(BaseModel):
    message: str = Field(..., description="Natural language booking request")

class BookingRespond(BaseModel):
    success: bool
    booking_id: Optional[int] = None
    details: Optional[Dict] = None
    message: str

@router.post("/book-interview", response_model=BookingRespond)
async def book_interview(request: BookingRequest, session: AsyncSession = Depends(get_session)):
    """
    Book interview with natural language
    """
    try:
        booking_data = await booking_service.extract_booking_info(request.message)

        is_valid, error_msg = booking_service.validate_booking(booking_data)

        if not is_valid:
            return BookingRespond(success=False, message=f"{error_msg}")
        
        try:
            booking = await booking_service.create_booking(booking_data, session)

            return BookingRespond(
                success=True,
                booking_id=booking.id,
                details={
                    "name": booking.name,
                    "email": booking.email,
                    "phone_number": booking.phone_number,
                    "date": booking.date,
                    "time": booking.time
                },
                message=f"Interview booking confirmed!\n\nDetails:\n- Name: {booking.name}\n- Email: {booking.email}\n- Phone Number: {booking.phone_number}\n- Date: {booking.date}\n- Time: {booking.time}\n\nBooking ID: {booking.id}"
            )
        
        except Exception as db_error:
            if "UNIQUE constraint failed" in str(db_error) or "unique_booking" in str(db_error):
                return BookingRespond(
                    success=False,
                    message=f"Duplicate booking! A booking already exists for:\n- Email: {booking_data['email']}\n- Phone: {booking_data['phone_number']}\n- Date: {booking_data['date']}\n- Time: {booking_data['time']}"
                )
            raise
    
    except Exception as e:
        print(f"Booking error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")
    
@router.get("/bookings", response_model=list)
async def list_bookings(session: AsyncSession = Depends(get_session)):
    """ List all booking. """
    from sqlalchemy import select

    result = await session.execute(select(Booking).order_by(Booking.created_at.desc()))
    bookings = result.scalars().all()

    return [
        {
            "id": b.id,
            "name": b.name,
            "email": b.email,
            "phone_number": b.phone_number,
            "date": b.date,
            "time": b.time,
            "status": b.status,
            "created_at": b.created_at.isoformat()
        }
        for b in bookings
    ]

# Update the Status

class UpdateStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|cancelled)$")

@router.patch("/booking/{booking_id}/status")
async def update_booking_status(booking_id: int, status_update: UpdateStatusRequest, session: AsyncSession = Depends(get_session)):
    """ Update the booking status"""

    result = await session.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()   # returns val if one, if no value None and if multiple values raise error

    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")
    
    old_status = booking.status
    booking.status = status_update.status
    await session.commit()

    return{
        "success": True,
        "booking_id": booking.id,
        "old_status": old_status,
        "new_status": status_update.status,
        "message": f"Booking {booking_id} status updated to {status_update.status}"
    }

@router.delete("/booking/{booking_id}")
async def cancel_booking(booking_id: int, session: AsyncSession = Depends(get_session)):
    """ Cancel the booking """
    result = await session.execute(
        select(Booking).where(Booking.id == booking_id)
    )

    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")
    
    booking.status = "cancelled"
    await session.commit()

    return {
        "success": True,
        "message": f"Booking for {booking.name} was cancelled successfully"
    }