"""
Version management and change detection for Mordor Intelligence reports.
Handles snapshot creation and historical tracking in DuckDB.
"""

import json
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import duckdb

from src.models.schema import Report, ReportVersion


class VersionManager:
    """Manage report versions and change detection in DuckDB."""

    def __init__(self, db_path: str):
        """
        Initialize version manager with DuckDB connection.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)

    def should_create_version(self, report: Report) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Check if a version should be created for this report.

        Args:
            report: Report instance to check

        Returns:
            Tuple of (should_create, reason, changed_fields)
            - reason: "new_report" or "field_change"
            - changed_fields: List of field names that changed (None for new_report)
        """
        # Get existing report by slug
        existing = self._get_existing_report(report.slug)

        if not existing:
            # New report
            return True, "new_report", None

        # Compare hashes
        if existing['content_hash'] != report.content_hash:
            # Changes detected
            changed_fields = report.get_changed_fields(
                self._dict_to_report(existing)
            )
            return True, "field_change", changed_fields

        # No changes
        return False, None, None

    def create_version(
        self,
        report: Report,
        reason: str,
        changed_fields: Optional[List[str]] = None
    ) -> int:
        """
        Create a new version snapshot in the database.

        Args:
            report: Report to snapshot
            reason: "new_report" or "field_change"
            changed_fields: List of fields that changed (for field_change)

        Returns:
            Version ID created
        """
        # Get or create report ID
        report_id = self._get_or_create_report_id(report)

        # Get next version number
        version_number = self._get_next_version_number(report_id)

        # Flatten report to dict
        report_dict = self._flatten_report(report)

        # Create version record - exclude timestamp fields not in report_versions
        version_dict = {
            'report_id': report_id,
            'version_number': version_number,
            'snapshot_reason': reason,
            'changed_fields': json.dumps(changed_fields) if changed_fields else None,
            'scraped_at': report.scraped_at or datetime.utcnow(),
        }

        # Add all report fields except id and tracking fields specific to reports table
        exclude_fields = {'id', 'first_seen_at', 'last_updated_at', 'version_count'}
        for key, value in report_dict.items():
            if key not in exclude_fields:
                version_dict[key] = value

        # Insert into report_versions
        # Generate new version_id manually
        max_vid_result = self.conn.execute("SELECT COALESCE(MAX(version_id), 0) FROM report_versions").fetchone()
        version_id = (max_vid_result[0] if max_vid_result else 0) + 1
        version_dict['version_id'] = version_id

        fields = ', '.join(f'"{k}"' for k in version_dict.keys())
        placeholders = ', '.join(['?' for _ in version_dict.keys()])
        query = f"INSERT INTO report_versions ({fields}) VALUES ({placeholders})"

        try:
            self.conn.execute(query, list(version_dict.values()))

            # Update reports table with current version
            update_query = """
                UPDATE reports
                SET
                    last_updated_at = ?,
                    version_count = ?,
                    content_hash = ?
                WHERE id = ?
            """
            self.conn.execute(
                update_query,
                [
                    report.scraped_at or datetime.utcnow(),
                    version_number,
                    report.content_hash,
                    report_id
                ]
            )
            self.conn.commit()

            return version_id

        except Exception as e:
            raise RuntimeError(f"Failed to create version: {e}")

    def update_report_table(self, report: Report, report_id: int):
        """
        Update the reports table with latest report data.
        """
        report_dict = self._flatten_report(report)

        set_clause = ', '.join(f'"{k}" = ?' for k in report_dict.keys())
        set_clause += ', last_updated_at = ?, version_count = version_count + 1'

        query = f"UPDATE reports SET {set_clause} WHERE id = ?"

        values = list(report_dict.values()) + [datetime.utcnow(), report_id]

        try:
            self.conn.execute(query, values)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to update report: {e}")

    def get_version_history(self, slug: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a report by slug.

        Returns:
            List of dicts with version data in chronological order
        """
        query = """
            SELECT rv.* FROM report_versions rv
            JOIN reports r ON rv.report_id = r.id
            WHERE r.slug = ?
            ORDER BY rv.version_number ASC
        """

        try:
            result = self.conn.execute(query, [slug]).fetchall()

            if not result:
                return []

            # Get column names
            columns = [desc[0] for desc in self.conn.description]

            versions = []
            for row in result:
                version_dict = dict(zip(columns, row))

                # Deserialize JSON fields
                json_fields = [
                    'transaction_types', 'components', 'deployment_types',
                    'enterprise_sizes', 'end_user_industries', 'geographies',
                    'major_players', 'image_urls', 'changed_fields'
                ]

                for field in json_fields:
                    if field in version_dict and version_dict[field] and isinstance(version_dict[field], str):
                        try:
                            version_dict[field] = json.loads(version_dict[field])
                        except:
                            pass

                versions.append(version_dict)

            return versions
        except Exception as e:
            raise RuntimeError(f"Failed to get version history: {e}")

    def get_changes_between_versions(
        self,
        slug: str,
        v1: int,
        v2: int
    ) -> Dict[str, Tuple[Any, Any]]:
        """
        Compare two versions of a report.

        Args:
            slug: Report slug
            v1: First version number
            v2: Second version number

        Returns:
            Dict of field_name -> (old_value, new_value)
        """
        query = """
            SELECT rv.* FROM report_versions rv
            JOIN reports r ON rv.report_id = r.id
            WHERE r.slug = ? AND rv.version_number IN (?, ?)
            ORDER BY rv.version_number ASC
        """

        try:
            result = self.conn.execute(query, [slug, v1, v2]).fetchall()
            if len(result) != 2:
                raise ValueError(f"Could not find both versions {v1} and {v2}")

            old_version = self._dict_to_report_version(result[0])
            new_version = self._dict_to_report_version(result[1])

            changes = {}
            exclude_fields = {
                'version_id', 'report_id', 'version_number',
                'snapshot_reason', 'changed_fields', 'scraped_at'
            }

            for field in old_version.model_fields.keys():
                if field in exclude_fields:
                    continue

                old_val = getattr(old_version, field)
                new_val = getattr(new_version, field)

                if old_val != new_val:
                    changes[field] = (old_val, new_val)

            return changes

        except Exception as e:
            raise RuntimeError(f"Failed to get changes between versions: {e}")

    def _get_or_create_report_id(self, report: Report) -> int:
        """Get existing report ID by slug or create new one."""
        query = "SELECT id FROM reports WHERE slug = ?"
        result = self.conn.execute(query, [report.slug]).fetchone()

        if result:
            return result[0]

        # Create new report
        report_dict = self._flatten_report(report)

        # Generate new ID manually (max id + 1)
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM reports").fetchone()
        new_id = (max_id_result[0] if max_id_result else 0) + 1
        report_dict['id'] = new_id

        # Ensure timestamps are set
        if not report_dict.get('first_seen_at'):
            report_dict['first_seen_at'] = datetime.utcnow()
        if not report_dict.get('last_updated_at'):
            report_dict['last_updated_at'] = datetime.utcnow()
        if not report_dict.get('scraped_at'):
            report_dict['scraped_at'] = datetime.utcnow()

        fields = ', '.join(f'"{k}"' for k in report_dict.keys())
        placeholders = ', '.join(['?' for _ in report_dict.keys()])
        query = f"INSERT INTO reports ({fields}) VALUES ({placeholders})"

        try:
            self.conn.execute(query, list(report_dict.values()))
            self.conn.commit()
            return new_id
        except Exception as e:
            raise RuntimeError(f"Failed to create report record: {e}")

    def _get_next_version_number(self, report_id: int) -> int:
        """Get the next version number for a report."""
        query = "SELECT MAX(version_number) FROM report_versions WHERE report_id = ?"
        result = self.conn.execute(query, [report_id]).fetchone()

        max_version = result[0] if result[0] else 0
        return max_version + 1

    def _get_existing_report(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get existing report by slug."""
        query = "SELECT * FROM reports WHERE slug = ?"
        result = self.conn.execute(query, [slug]).fetchone()

        if not result:
            return None

        # Convert to dict
        columns = [desc[0] for desc in self.conn.description]
        return dict(zip(columns, result))

    def _flatten_report(self, report: Report) -> Dict[str, Any]:
        """
        Flatten Report model to dict for database insertion.
        Converts JSON fields to strings.
        """
        data = report.model_dump()

        # Convert lists to JSON strings
        json_fields = [
            'transaction_types', 'components', 'deployment_types',
            'enterprise_sizes', 'end_user_industries', 'geographies',
            'major_players', 'image_urls'
        ]

        for field in json_fields:
            if data.get(field) is not None:
                data[field] = json.dumps(data[field])

        # Convert FAQ list to JSON
        if data.get('faq_questions_answers') is not None:
            faq_list = []
            for faq in data['faq_questions_answers']:
                if isinstance(faq, dict):
                    faq_list.append(faq)
                else:
                    # FAQPair object
                    faq_list.append({'question': faq.question, 'answer': faq.answer})
            data['faq_questions_answers'] = json.dumps(faq_list)

        return data

    def _dict_to_report(self, data: Dict[str, Any]) -> Report:
        """Convert database row dict to Report model."""
        # Deserialize JSON fields
        json_fields = [
            'transaction_types', 'components', 'deployment_types',
            'enterprise_sizes', 'end_user_industries', 'geographies',
            'major_players', 'image_urls'
        ]

        for field in json_fields:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except:
                    data[field] = None

        # Deserialize FAQ
        if data.get('faq_questions_answers') and isinstance(data['faq_questions_answers'], str):
            try:
                faq_data = json.loads(data['faq_questions_answers'])
                data['faq_questions_answers'] = [
                    type('FAQPair', (), faq)() for faq in faq_data
                ]
            except:
                data['faq_questions_answers'] = None

        return Report(**data)

    def _dict_to_report_version(self, row: tuple) -> Dict[str, Any]:
        """Convert database row tuple to dict (deprecated - use get_version_history instead)."""
        raise NotImplementedError("Use get_version_history() instead")
