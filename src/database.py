"""
Database models and operations for SDS Auto-Updater.
Uses SQLAlchemy ORM with SQLite backend.
"""

import hashlib
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pathlib import Path

from .config import DATABASE_PATH

Base = declarative_base()


class Chemical(Base):
    """Chemical inventory table."""
    __tablename__ = 'chemicals'
    
    id = Column(Integer, primary_key=True)
    chemical_name = Column(String(255), nullable=False)
    cas_number = Column(String(50), nullable=False, index=True)
    supplier = Column(String(100), nullable=False)
    supplier_product_id = Column(String(100))  # Supplier's product code
    current_sds_version = Column(String(50))
    last_checked = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    
    # Relationships
    sds_versions = relationship("SDSVersion", back_populates="chemical", cascade="all, delete-orphan")
    changes = relationship("Change", back_populates="chemical", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chemical(name='{self.chemical_name}', CAS='{self.cas_number}')>"


class SDSVersion(Base):
    """Historical SDS versions table."""
    __tablename__ = 'sds_versions'
    
    id = Column(Integer, primary_key=True)
    chemical_id = Column(Integer, ForeignKey('chemicals.id'), nullable=False)
    version_date = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(500))
    file_hash = Column(String(64))  # SHA-256 hash for quick comparison
    extracted_text = Column(Text)
    
    # Extracted sections (stored as JSON strings)
    hazard_statements = Column(Text)
    ppe_requirements = Column(Text)
    first_aid_measures = Column(Text)
    storage_conditions = Column(Text)
    disposal_requirements = Column(Text)
    handling_precautions = Column(Text)
    
    # Relationship
    chemical = relationship("Chemical", back_populates="sds_versions")
    
    def __repr__(self):
        return f"<SDSVersion(chemical_id={self.chemical_id}, date='{self.version_date}')>"


class Change(Base):
    """Change log table for tracking SDS updates."""
    __tablename__ = 'changes'

    id = Column(Integer, primary_key=True)
    chemical_id = Column(Integer, ForeignKey('chemicals.id'), nullable=False)
    old_version_id = Column(Integer, ForeignKey('sds_versions.id'))
    new_version_id = Column(Integer, ForeignKey('sds_versions.id'))
    change_date = Column(DateTime, default=datetime.utcnow)
    severity = Column(String(20), nullable=False)  # CRITICAL, IMPORTANT, MINOR
    section_changed = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    ai_summary = Column(Text)

    # Review tracking
    is_reviewed = Column(Integer, default=0)  # 0 = not reviewed, 1 = reviewed
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)

    # Resolution tracking (NEW)
    is_resolved = Column(Integer, default=0)  # 0 = not resolved, 1 = resolved
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)  # User can add notes about what action they took

    # Relationship
    chemical = relationship("Chemical", back_populates="changes")

    def __repr__(self):
        return f"<Change(chemical_id={self.chemical_id}, severity='{self.severity}')>"


class Alert(Base):
    """Sent alerts tracking table."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    change_id = Column(Integer, ForeignKey('changes.id'))
    recipient = Column(String(255))
    alert_type = Column(String(50))  # email, sms, webhook
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # sent, failed, pending
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<Alert(change_id={self.change_id}, status='{self.status}')>"


class DatabaseManager:
    """Database manager for all CRUD operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    # Chemical CRUD operations
    def add_chemical(self, name: str, cas_number: str, supplier: str,
                     product_id: Optional[str] = None) -> Chemical:
        """Add a new chemical to the database."""
        from .utils import validate_cas_number, validate_supplier

        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Chemical name cannot be empty")

        if not validate_cas_number(cas_number):
            raise ValueError(f"Invalid CAS number format: {cas_number}")

        if not validate_supplier(supplier):
            raise ValueError(f"Invalid supplier: {supplier}. Must be one of: sigma_aldrich, merck, srl_chemicals")

        session = self.get_session()
        try:
            chemical = Chemical(
                chemical_name=name.strip(),
                cas_number=cas_number,
                supplier=supplier.lower(),
                supplier_product_id=product_id
            )
            session.add(chemical)
            session.commit()
            session.refresh(chemical)
            return chemical
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_chemical_by_cas(self, cas_number: str) -> Optional[Chemical]:
        """Get a chemical by CAS number."""
        session = self.get_session()
        try:
            return session.query(Chemical).filter(
                Chemical.cas_number == cas_number,
                Chemical.is_active == 1
            ).first()
        finally:
            session.close()
    
    def get_all_chemicals(self) -> List[Chemical]:
        """Get all active chemicals."""
        session = self.get_session()
        try:
            return session.query(Chemical).filter(Chemical.is_active == 1).all()
        finally:
            session.close()
    
    def get_chemicals_by_supplier(self, supplier: str) -> List[Chemical]:
        """Get all chemicals from a specific supplier."""
        session = self.get_session()
        try:
            return session.query(Chemical).filter(
                Chemical.supplier == supplier,
                Chemical.is_active == 1
            ).all()
        finally:
            session.close()
    
    def update_chemical_check_time(self, chemical_id: int):
        """Update the last_checked timestamp."""
        session = self.get_session()
        try:
            session.query(Chemical).filter(Chemical.id == chemical_id).update({
                "last_checked": datetime.utcnow()
            })
            session.commit()
        finally:
            session.close()
    
    # SDS Version operations
    def add_sds_version(self, chemical_id: int, file_path: str, 
                        extracted_data: dict) -> SDSVersion:
        """Add a new SDS version."""
        session = self.get_session()
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            sds_version = SDSVersion(
                chemical_id=chemical_id,
                file_path=file_path,
                file_hash=file_hash,
                extracted_text=extracted_data.get("full_text", ""),
                hazard_statements=extracted_data.get("hazard_statements", ""),
                ppe_requirements=extracted_data.get("ppe_requirements", ""),
                first_aid_measures=extracted_data.get("first_aid_measures", ""),
                storage_conditions=extracted_data.get("storage_conditions", ""),
                disposal_requirements=extracted_data.get("disposal_requirements", ""),
                handling_precautions=extracted_data.get("handling_precautions", "")
            )
            session.add(sds_version)
            
            # Update chemical's last_updated
            session.query(Chemical).filter(Chemical.id == chemical_id).update({
                "last_updated": datetime.utcnow(),
                "current_sds_version": file_hash[:8]
            })
            
            session.commit()
            session.refresh(sds_version)
            return sds_version
        finally:
            session.close()
    
    def get_latest_sds_version(self, chemical_id: int) -> Optional[SDSVersion]:
        """Get the most recent SDS version for a chemical."""
        session = self.get_session()
        try:
            return session.query(SDSVersion).filter(
                SDSVersion.chemical_id == chemical_id
            ).order_by(SDSVersion.version_date.desc()).first()
        finally:
            session.close()
    
    def get_sds_versions_for_chemical(self, chemical_id: int) -> List[SDSVersion]:
        """Get all SDS versions for a chemical."""
        session = self.get_session()
        try:
            return session.query(SDSVersion).filter(
                SDSVersion.chemical_id == chemical_id
            ).order_by(SDSVersion.version_date.desc()).all()
        finally:
            session.close()
    
    def check_sds_exists(self, file_hash: str) -> bool:
        """Check if an SDS with the given hash already exists."""
        session = self.get_session()
        try:
            return session.query(SDSVersion).filter(
                SDSVersion.file_hash == file_hash
            ).first() is not None
        finally:
            session.close()
    
    # Change operations
    def add_change(self, chemical_id: int, old_version_id: int, new_version_id: int,
                   severity: str, section: str, old_value: str, new_value: str,
                   ai_summary: str) -> Change:
        """Record a change between SDS versions."""
        session = self.get_session()
        try:
            change = Change(
                chemical_id=chemical_id,
                old_version_id=old_version_id,
                new_version_id=new_version_id,
                severity=severity,
                section_changed=section,
                old_value=old_value,
                new_value=new_value,
                ai_summary=ai_summary
            )
            session.add(change)
            session.commit()
            session.refresh(change)
            return change
        finally:
            session.close()
    
    def get_unreviewed_changes(self) -> List[Change]:
        """Get all changes that haven't been reviewed."""
        session = self.get_session()
        try:
            return session.query(Change).filter(Change.is_reviewed == 0).all()
        finally:
            session.close()
    
    def get_changes_since(self, since_date: datetime) -> List[Change]:
        """Get all changes since a specific date."""
        session = self.get_session()
        try:
            return session.query(Change).filter(
                Change.change_date >= since_date
            ).order_by(Change.change_date.desc()).all()
        finally:
            session.close()
    
    def mark_change_reviewed(self, change_id: int, reviewer: str):
        """Mark a change as reviewed."""
        session = self.get_session()
        try:
            session.query(Change).filter(Change.id == change_id).update({
                "is_reviewed": 1,
                "reviewed_by": reviewer,
                "reviewed_at": datetime.utcnow()
            })
            session.commit()
        finally:
            session.close()

    def mark_change_resolved(self, change_id: int, resolver: str, notes: str = ""):
        """Mark a change as resolved with optional notes."""
        session = self.get_session()
        try:
            session.query(Change).filter(Change.id == change_id).update({
                "is_resolved": 1,
                "resolved_by": resolver,
                "resolved_at": datetime.utcnow(),
                "resolution_notes": notes,
                "is_reviewed": 1,  # Auto-mark as reviewed when resolved
                "reviewed_by": resolver if not session.query(Change).filter(Change.id == change_id).first().reviewed_by else session.query(Change).filter(Change.id == change_id).first().reviewed_by,
                "reviewed_at": datetime.utcnow() if not session.query(Change).filter(Change.id == change_id).first().reviewed_at else session.query(Change).filter(Change.id == change_id).first().reviewed_at
            })
            session.commit()
        finally:
            session.close()

    def get_unresolved_changes(self) -> List[Change]:
        """Get all changes that haven't been resolved."""
        session = self.get_session()
        try:
            return session.query(Change).filter(Change.is_resolved == 0).all()
        finally:
            session.close()

    def get_resolved_changes(self) -> List[Change]:
        """Get all resolved changes."""
        session = self.get_session()
        try:
            return session.query(Change).filter(Change.is_resolved == 1).all()
        finally:
            session.close()
    
    # Alert operations
    def add_alert(self, change_id: int, recipient: str, alert_type: str,
                  status: str, error_message: Optional[str] = None) -> Alert:
        """Record a sent alert."""
        session = self.get_session()
        try:
            alert = Alert(
                change_id=change_id,
                recipient=recipient,
                alert_type=alert_type,
                status=status,
                error_message=error_message
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert
        finally:
            session.close()
    
    # Utility methods
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def import_chemicals_from_csv(self, csv_path: str) -> int:
        """Import chemicals from a CSV file. Returns count of imported chemicals."""
        import pandas as pd
        import logging

        logger = logging.getLogger(__name__)

        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")

        required_cols = ['chemical_name', 'cas_number', 'supplier']

        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"CSV missing required columns: {missing}")

        # Remove rows with missing required fields
        original_count = len(df)
        df = df.dropna(subset=required_cols)

        if len(df) < original_count:
            logger.warning(f"Dropped {original_count - len(df)} rows with missing required fields")

        count = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                # Check if already exists
                existing = self.get_chemical_by_cas(str(row['cas_number']).strip())
                if not existing:
                    self.add_chemical(
                        name=str(row['chemical_name']).strip(),
                        cas_number=str(row['cas_number']).strip(),
                        supplier=str(row['supplier']).strip(),
                        product_id=str(row.get('product_id', '')).strip() or None
                    )
                    count += 1
                else:
                    logger.info(f"Chemical with CAS {row['cas_number']} already exists, skipping")
            except Exception as e:
                error_msg = f"Row {idx + 2}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        if errors and len(errors) > 5:
            logger.warning(f"Total {len(errors)} errors occurred during import")

        return count
    
    def get_statistics(self) -> dict:
        """Get database statistics."""
        session = self.get_session()
        try:
            return {
                "total_chemicals": session.query(Chemical).filter(Chemical.is_active == 1).count(),
                "total_sds_versions": session.query(SDSVersion).count(),
                "total_changes": session.query(Change).count(),
                "unreviewed_changes": session.query(Change).filter(Change.is_reviewed == 0).count(),
                "unresolved_changes": session.query(Change).filter(Change.is_resolved == 0).count(),
                "critical_changes": session.query(Change).filter(Change.severity == "CRITICAL").count(),
                "critical_unresolved": session.query(Change).filter(
                    Change.severity == "CRITICAL",
                    Change.is_resolved == 0
                ).count(),
                "resolved_changes": session.query(Change).filter(Change.is_resolved == 1).count()
            }
        finally:
            session.close()


# Global database instance
db = DatabaseManager()
