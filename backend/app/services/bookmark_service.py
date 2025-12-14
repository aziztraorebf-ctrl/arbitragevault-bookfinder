"""Service for managing user bookmarked niches."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from ..models.bookmark import SavedNiche
from ..schemas.bookmark import NicheCreateSchema, NicheUpdateSchema

logger = logging.getLogger(__name__)


class BookmarkService:
    """Service for managing saved niches and bookmarks."""

    def __init__(self, db: Session):
        """Initialize the bookmark service.
        
        Args:
            db: Database session
        """
        self.db = db

    def create_niche(self, user_id: str, niche_data: NicheCreateSchema) -> SavedNiche:
        """Create a new saved niche for a user.
        
        Args:
            user_id: ID of the user saving the niche
            niche_data: Niche data to save
            
        Returns:
            The created SavedNiche instance
            
        Raises:
            HTTPException: If creation fails or niche name already exists for user
        """
        try:
            # Check if user already has a niche with this name
            existing_niche = self.db.query(SavedNiche).filter(
                SavedNiche.user_id == user_id,
                SavedNiche.niche_name == niche_data.niche_name
            ).first()
            
            if existing_niche:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Niche with name '{niche_data.niche_name}' already exists"
                )

            # Create new SavedNiche
            saved_niche = SavedNiche(
                user_id=user_id,
                niche_name=niche_data.niche_name,
                category_id=niche_data.category_id,
                category_name=niche_data.category_name,
                filters=niche_data.filters,
                last_score=niche_data.last_score,
                description=niche_data.description
            )

            self.db.add(saved_niche)
            self.db.commit()
            self.db.refresh(saved_niche)

            logger.info(f"Created saved niche '{niche_data.niche_name}' for user {user_id}")
            return saved_niche

        except HTTPException:
            # Re-raise HTTPExceptions as-is (like our 409 conflict)
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error creating niche: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create niche due to data constraints"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating niche: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create saved niche"
            )

    def get_niche_by_id(self, user_id: str, niche_id: str) -> Optional[SavedNiche]:
        """Get a specific saved niche by ID for a user.
        
        Args:
            user_id: ID of the user who owns the niche
            niche_id: ID of the niche to retrieve
            
        Returns:
            The SavedNiche instance or None if not found
        """
        try:
            niche = self.db.query(SavedNiche).filter(
                SavedNiche.id == niche_id,
                SavedNiche.user_id == user_id
            ).first()
            
            return niche
            
        except Exception as e:
            logger.error(f"Error retrieving niche {niche_id} for user {user_id}: {e}")
            return None

    def list_niches_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[SavedNiche], int]:
        """Get all saved niches for a user with pagination.

        Args:
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of SavedNiche instances, total count)
        """
        # Validate inputs at service layer (defense in depth)
        if skip < 0:
            raise ValueError("skip must be >= 0")
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")

        try:
            # Get total count
            total_count = self.db.query(SavedNiche).filter(
                SavedNiche.user_id == user_id
            ).count()

            # Get paginated results ordered by creation date (newest first)
            niches = self.db.query(SavedNiche).filter(
                SavedNiche.user_id == user_id
            ).order_by(SavedNiche.created_at.desc()).offset(skip).limit(limit).all()

            logger.info(f"Retrieved {len(niches)} saved niches for user {user_id}")
            return niches, total_count

        except Exception as e:
            logger.error(f"Error listing niches for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve saved niches"
            )

    def update_niche(
        self, 
        user_id: str, 
        niche_id: str, 
        niche_data: NicheUpdateSchema
    ) -> Optional[SavedNiche]:
        """Update an existing saved niche.
        
        Args:
            user_id: ID of the user who owns the niche
            niche_id: ID of the niche to update
            niche_data: Updated niche data
            
        Returns:
            The updated SavedNiche instance or None if not found
            
        Raises:
            HTTPException: If update fails or niche not found
        """
        try:
            niche = self.get_niche_by_id(user_id, niche_id)
            if not niche:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Saved niche not found"
                )

            # Check for name conflicts if updating name
            if niche_data.niche_name and niche_data.niche_name != niche.niche_name:
                existing_niche = self.db.query(SavedNiche).filter(
                    SavedNiche.user_id == user_id,
                    SavedNiche.niche_name == niche_data.niche_name,
                    SavedNiche.id != niche_id
                ).first()
                
                if existing_niche:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Niche with name '{niche_data.niche_name}' already exists"
                    )

            # Update fields
            update_data = niche_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(niche, field, value)

            self.db.commit()
            self.db.refresh(niche)

            logger.info(f"Updated saved niche {niche_id} for user {user_id}")
            return niche

        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error updating niche {niche_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A niche with this name already exists"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating niche {niche_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update saved niche"
            )

    def delete_niche(self, user_id: str, niche_id: str) -> bool:
        """Delete a saved niche.
        
        Args:
            user_id: ID of the user who owns the niche
            niche_id: ID of the niche to delete
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            niche = self.get_niche_by_id(user_id, niche_id)
            if not niche:
                return False

            self.db.delete(niche)
            self.db.commit()

            logger.info(f"Deleted saved niche {niche_id} for user {user_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting niche {niche_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete saved niche"
            )

    def get_niche_filters_for_analysis(self, user_id: str, niche_id: str) -> Optional[Dict[str, Any]]:
        """Get the saved filters from a niche for re-running analysis.
        
        Args:
            user_id: ID of the user who owns the niche
            niche_id: ID of the niche
            
        Returns:
            Dictionary of filters or None if niche not found
        """
        niche = self.get_niche_by_id(user_id, niche_id)
        if niche:
            return niche.filters
        return None