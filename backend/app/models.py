from pydantic import BaseModel, Field


class TraitEntry(BaseModel):
    description: str = Field(min_length=1)
    weight: float = Field(ge=0.0, le=1.0)


class TraitSummary(BaseModel):
    relational_orientation: TraitEntry
    creativity: TraitEntry
    intellectualism: TraitEntry
    humor: TraitEntry
    interests: TraitEntry
    cultural_identity: TraitEntry
    political_orientation: TraitEntry
