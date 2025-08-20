import logging
from typing import Optional, List
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class PortAllocator:
    """Database-safe port allocator with race condition prevention"""
    
    def __init__(self, start_port: int = 13001, max_port: int = 65535):
        self.start_port = start_port
        self.max_port = max_port
        self.port_range = max_port - start_port + 1
        
    def allocate_port(self, db: Session, workspace_id: int, 
                     username: str) -> Optional[int]:
        """
        Allocate a unique port for a workspace
        
        Args:
            db: Database session
            workspace_id: Workspace ID to associate with port
            username: Username for logging
            
        Returns:
            Allocated port number or None if allocation failed
        """
        # Get all currently used ports
        used_ports = self._get_used_ports(db)
        
        # Find next available port
        allocated_port = self._find_available_port(used_ports)
        
        if not allocated_port:
            logger.error(f"No available ports in range {self.start_port}-{self.max_port}")
            return None
        
        # Try to insert the port allocation with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use database-level locking to prevent race conditions
                # This assumes you have a workspaces table with a port column
                result = db.execute(
                    text("""
                        UPDATE workspaces 
                        SET port = :port 
                        WHERE id = :workspace_id 
                        AND port IS NULL
                        RETURNING port
                    """),
                    {"port": allocated_port, "workspace_id": workspace_id}
                )
                
                if result.rowcount > 0:
                    logger.info(f"Port {allocated_port} allocated for workspace {workspace_id} ({username})")
                    db.commit()
                    return allocated_port
                else:
                    # Port was already allocated by another worker
                    logger.warning(f"Port allocation failed for workspace {workspace_id} - already allocated")
                    return None
                    
            except IntegrityError as e:
                # Port constraint violation - another worker got it first
                db.rollback()
                logger.warning(f"Port {allocated_port} already allocated by another worker (attempt {attempt + 1})")
                
                if attempt < max_retries - 1:
                    # Try to find another available port
                    used_ports.add(allocated_port)
                    allocated_port = self._find_available_port(used_ports)
                    if not allocated_port:
                        logger.error("No more available ports after retry")
                        return None
                else:
                    logger.error(f"Failed to allocate port after {max_retries} attempts")
                    return None
                    
            except Exception as e:
                db.rollback()
                logger.error(f"Unexpected error during port allocation: {e}")
                return None
        
        return None
    
    def _get_used_ports(self, db: Session) -> set:
        """Get all currently used ports from database"""
        try:
            # This assumes you have a workspaces table with a port column
            result = db.execute(
                text("SELECT port FROM workspaces WHERE port IS NOT NULL")
            )
            used_ports = {row[0] for row in result.fetchall()}
            logger.debug(f"Found {len(used_ports)} used ports")
            return used_ports
            
        except Exception as e:
            logger.error(f"Error fetching used ports: {e}")
            return set()
    
    def _find_available_port(self, used_ports: set) -> Optional[int]:
        """Find next available port in range"""
        for port in range(self.start_port, self.max_port + 1):
            if port not in used_ports:
                return port
        return None
    
    def release_port(self, db: Session, workspace_id: int) -> bool:
        """
        Release a port back to the pool
        
        Args:
            db: Database session
            workspace_id: Workspace ID to release port for
            
        Returns:
            True if port was released, False otherwise
        """
        try:
            result = db.execute(
                text("""
                    UPDATE workspaces 
                    SET port = NULL 
                    WHERE id = :workspace_id 
                    AND port IS NOT NULL
                    RETURNING port
                """),
                {"workspace_id": workspace_id}
            )
            
            if result.rowcount > 0:
                released_port = result.fetchone()[0]
                logger.info(f"Port {released_port} released for workspace {workspace_id}")
                db.commit()
                return True
            else:
                logger.warning(f"No port to release for workspace {workspace_id}")
                return False
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error releasing port for workspace {workspace_id}: {e}")
            return False
    
    def get_port_status(self, db: Session) -> dict:
        """
        Get current port allocation status
        
        Returns:
            Dictionary with port allocation statistics
        """
        try:
            # Get total allocated ports
            result = db.execute(
                text("SELECT COUNT(*) FROM workspaces WHERE port IS NOT NULL")
            )
            allocated_count = result.fetchone()[0]
            
            # Get port range usage
            result = db.execute(
                text("""
                    SELECT MIN(port), MAX(port), COUNT(*) 
                    FROM workspaces 
                    WHERE port IS NOT NULL
                """)
            )
            min_port, max_port, total = result.fetchone()
            
            # Get gaps in port allocation
            result = db.execute(
                text("""
                    WITH port_sequence AS (
                        SELECT generate_series(:start_port, :max_port) AS port
                    )
                    SELECT COUNT(*) 
                    FROM port_sequence ps
                    LEFT JOIN workspaces w ON ps.port = w.port
                    WHERE w.port IS NULL
                """),
                {"start_port": self.start_port, "max_port": self.max_port}
            )
            available_count = result.fetchone()[0]
            
            return {
                "total_ports": self.port_range,
                "allocated_ports": allocated_count,
                "available_ports": available_count,
                "port_range": {
                    "start": self.start_port,
                    "end": self.max_port,
                    "min_allocated": min_port,
                    "max_allocated": max_port
                },
                "utilization_percent": (allocated_count / self.port_range) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting port status: {e}")
            return {}

class PortPool:
    """Port pool with pre-allocation for high-throughput scenarios"""
    
    def __init__(self, allocator: PortAllocator, pool_size: int = 10):
        self.allocator = allocator
        self.pool_size = pool_size
        self.available_ports: List[int] = []
        self.allocated_ports: set = set()
    
    def get_port_from_pool(self, db: Session, workspace_id: int) -> Optional[int]:
        """Get port from pool or allocate new one"""
        if self.available_ports:
            port = self.available_ports.pop()
            self.allocated_ports.add(port)
            logger.info(f"Port {port} allocated from pool for workspace {workspace_id}")
            return port
        
        # Pool is empty, allocate new port
        return self.allocator.allocate_port(db, workspace_id, "pool_user")
    
    def return_port_to_pool(self, port: int):
        """Return port to pool for reuse"""
        if port in self.allocated_ports:
            self.allocated_ports.remove(port)
            self.available_ports.append(port)
            logger.info(f"Port {port} returned to pool")
    
    def refill_pool(self, db: Session):
        """Refill pool with newly allocated ports"""
        while len(self.available_ports) < self.pool_size:
            # This would need to be implemented based on your specific needs
            # For now, we'll just log the intention
            logger.debug("Pool refill requested")
            break
