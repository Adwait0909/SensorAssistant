import re
from typing import List, Dict, Any, Optional
from database.models import db, Component, ComponentAlias

class ComponentService:
    @staticmethod
    def normalize_name(raw_name: str) -> str:
        """Resolve component name through aliases table or return title-cased string."""
        if not raw_name:
            return ""
        clean = raw_name.strip().lower()
        alias_record = ComponentAlias.query.filter_by(alias=clean).first()
        if alias_record:
            return alias_record.standard_name
        return raw_name.strip().title()

    @staticmethod
    def get_components(
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        voltage: Optional[str] = None,
        availability: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Component]:
        query = Component.query
        if user_id is not None:
            # Show strictly user's components
            query = query.filter_by(user_id=user_id)
        
        if category and category != "All":
            query = query.filter(Component.category == category)
            
        if voltage and voltage != "All":
            query = query.filter(Component.voltage.ilike(f"%{voltage}%"))
            
        if availability and availability != "All":
            query = query.filter(Component.availability == availability)
            
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                (Component.name.ilike(search_pattern)) | 
                (Component.description.ilike(search_pattern)) |
                (Component.category.ilike(search_pattern))
            )
            
        return query.order_by(Component.category, Component.name).all()

    @staticmethod
    def get_by_id(component_id: str) -> Optional[Component]:
        return Component.query.filter_by(id=component_id).first()

    @staticmethod
    def create_component(data: Dict[str, Any], user_id: Optional[int] = None) -> Component:
        name = data.get("name", "").strip()
        standard_name = ComponentService.normalize_name(name)
        
        # generate slug id if not provided
        comp_id = data.get("id")
        if not comp_id:
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', standard_name.lower()).strip('-')
            comp_id = slug or "comp-" + str(int(db.func.random()))

        existing = Component.query.filter_by(id=comp_id).first()
        if existing:
            # update quantity if it already exists
            existing.quantity += int(data.get("quantity", 1))
            db.session.commit()
            return existing

        component = Component(
            id=comp_id,
            user_id=user_id,
            name=standard_name,
            category=data.get("category", "General"),
            sub_category=data.get("sub_category"),
            quantity=int(data.get("quantity", 1)),
            voltage=data.get("voltage", "5V"),
            current_rating=data.get("current_rating"),
            description=data.get("description", ""),
            aliases=data.get("aliases", []),
            datasheet_url=data.get("datasheet_url"),
            cost=float(data.get("cost", 0.0)),
            availability=data.get("availability", "In Stock"),
            safety_notes=data.get("safety_notes", "")
        )
        db.session.add(component)
        db.session.commit()
        return component

    @staticmethod
    def update_component(comp_id: str, data: Dict[str, Any]) -> Optional[Component]:
        component = Component.query.filter_by(id=comp_id).first()
        if not component:
            return None
        
        if "name" in data:
            component.name = ComponentService.normalize_name(data["name"])
        if "category" in data:
            component.category = data["category"]
        if "sub_category" in data:
            component.sub_category = data["sub_category"]
        if "quantity" in data:
            component.quantity = int(data["quantity"])
        if "voltage" in data:
            component.voltage = data["voltage"]
        if "current_rating" in data:
            component.current_rating = data["current_rating"]
        if "description" in data:
            component.description = data["description"]
        if "datasheet_url" in data:
            component.datasheet_url = data["datasheet_url"]
        if "cost" in data:
            component.cost = float(data["cost"])
        if "availability" in data:
            component.availability = data["availability"]
        if "safety_notes" in data:
            component.safety_notes = data["safety_notes"]

        db.session.commit()
        return component

    @staticmethod
    def delete_component(comp_id: str) -> bool:
        component = Component.query.filter_by(id=comp_id).first()
        if not component:
            return False
        db.session.delete(component)
        db.session.commit()
        return True
