from pydantic import BaseModel, field_validator, UUID4


class MeetingPrepRequest(BaseModel):
    company_data: str
    catalog_data: str
    model: str | None = None

    @field_validator("company_data", "catalog_data", mode="after")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be empty or blank")
        return stripped


class MeetingPrepResponse(BaseModel):
    id: UUID4
    markdown: str
    model: str
