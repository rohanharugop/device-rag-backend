import json
import uuid
from app.db.database import get_connection

# JSON helpers
def _dumps(val):
    return json.dumps(val) if val is not None else None

def _loads(val):
    return json.loads(val) if val else None


def create_project(device_id: str, device_name: str) -> str:
    project_id = "proj_" + str(uuid.uuid4())
    conn = get_connection()
    conn.execute("""
        INSERT INTO projects (project_id, device_id, device_name)
        VALUES (?, ?, ?)
    """, (project_id, device_id, device_name))
    conn.commit()
    conn.close()
    return project_id


def get_project(project_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM projects WHERE project_id = ?", (project_id,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "project_id":   row["project_id"],
        "device_id":    row["device_id"],
        "device_name":  row["device_name"],
        "plan":         _loads(row["plan"]),
        "steps":        _loads(row["steps"]) or [],
        "current_step": row["current_step"],
        "history":      _loads(row["history"]) or [],
        "flowchart":    row["flowchart"],
        "step_videos":  _loads(row["step_videos"]) or [],
        "status":       row["status"],
        "created_at":   row["created_at"],
        "updated_at":   row["updated_at"],
    }


def update_project(project_id: str, **fields):
    """
    Pass only the fields you want to update, e.g.:
        update_project(project_id, current_step=3, history=[...])
    """
    json_fields = {"plan", "steps", "history", "step_videos"}

    set_clauses = []
    values = []

    for key, val in fields.items():
        set_clauses.append(f"{key} = ?")
        values.append(_dumps(val) if key in json_fields else val)

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    values.append(project_id)

    conn = get_connection()
    conn.execute(
        f"UPDATE projects SET {', '.join(set_clauses)} WHERE project_id = ?",
        values
    )
    conn.commit()
    conn.close()


def mark_complete(project_id: str):
    update_project(project_id, status="complete")