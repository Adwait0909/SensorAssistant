from datetime import datetime
from typing import Dict, Any, Optional
from database.models import db, BuildSession, BuildStep, Project, ProjectHistory

class BuildService:
    @staticmethod
    def get_or_create_session(user_id: int, project_id: str) -> Dict[str, Any]:
        """Get existing active build session or create a new one."""
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return {"error": "Project not found"}

        session = BuildSession.query.filter_by(
            user_id=user_id,
            project_id=project_id,
            status="in_progress"
        ).order_by(BuildSession.started_at.desc()).first()

        project_steps = project.steps or []
        total_steps = len(project_steps)

        if not session:
            session = BuildSession(
                user_id=user_id,
                project_id=project_id,
                progress_percent=0,
                status="in_progress"
            )
            db.session.add(session)
            db.session.commit()

            # Initialize step tracking rows
            for step_data in project_steps:
                b_step = BuildStep(
                    session_id=session.id,
                    step_number=step_data.get("step_number", 1),
                    completed=False
                )
                db.session.add(b_step)
            db.session.commit()

            # Record in user history that project was started/attempted
            existing_hist = ProjectHistory.query.filter_by(
                user_id=user_id,
                project_id=project_id,
                action="attempted"
            ).first()
            if not existing_hist:
                db.session.add(ProjectHistory(
                    user_id=user_id,
                    project_id=project_id,
                    action="attempted",
                    notes="Started interactive step-by-step build"
                ))
                db.session.commit()

        # Load steps status
        step_records = {s.step_number: s for s in BuildStep.query.filter_by(session_id=session.id).all()}
        
        enriched_steps = []
        completed_count = 0
        for s_data in project_steps:
            s_num = s_data.get("step_number", 1)
            is_done = step_records.get(s_num).completed if s_num in step_records else False
            if is_done:
                completed_count += 1
            enriched_steps.append({
                **s_data,
                "completed": is_done
            })

        progress_pct = int((completed_count / total_steps * 100)) if total_steps > 0 else 0
        if session.progress_percent != progress_pct:
            session.progress_percent = progress_pct
            db.session.commit()

        return {
            "session_id": session.id,
            "project_id": project.id,
            "project_name": project.name,
            "progress_percent": progress_pct,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_steps": completed_count,
            "total_steps": total_steps,
            "steps": enriched_steps
        }

    @staticmethod
    def update_step_progress(session_id: int, step_number: int, completed: bool, user_id: int) -> Dict[str, Any]:
        """Update step completion status and recalculate session progress."""
        session = BuildSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not session:
            return {"error": "Build session not found or unauthorized"}

        step = BuildStep.query.filter_by(session_id=session.id, step_number=step_number).first()
        if not step:
            step = BuildStep(session_id=session.id, step_number=step_number)
            db.session.add(step)

        step.completed = completed
        step.completed_at = datetime.utcnow() if completed else None
        db.session.commit()

        # Recalculate progress
        project = Project.query.filter_by(id=session.project_id).first()
        total_steps = len(project.steps or [])
        completed_steps = BuildStep.query.filter_by(session_id=session.id, completed=True).count()

        new_progress = int((completed_steps / total_steps * 100)) if total_steps > 0 else 0
        session.progress_percent = new_progress

        if new_progress == 100 and session.status != "completed":
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            
            # Record in user history as completed
            db.session.add(ProjectHistory(
                user_id=user_id,
                project_id=session.project_id,
                action="completed",
                notes=f"Successfully built all {total_steps} steps."
            ))

        db.session.commit()

        return {
            "session_id": session.id,
            "step_number": step_number,
            "completed": completed,
            "progress_percent": session.progress_percent,
            "status": session.status
        }
